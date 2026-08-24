import parseZip from "./assets/vendor/shpjs-6.2.0/shp.esm.min.js";
import {
  ROAD_CODES,
  RoadUploadError,
  inspectRoadFeatures,
  validateRoadArchive,
} from "./assets/js/nma-road-upload-v1.js";
import {listZipEntries, sha256Hex} from "./assets/js/nma-school-upload-v1.js";

const apiRoot = new URL(
  document.querySelector('meta[name="nma-api-root"]')?.content || "./api/",
  document.baseURI,
);
const localBasemap = new URLSearchParams(location.search).get("basemap") !== "nlsc";
const state = {
  currentStep: "upload",
  enabledSteps: new Set(["upload"]),
  local: null,
  plan: null,
  authorization: null,
  compiled: null,
  qa: null,
  decision: null,
  decisionTrace: [],
  browserResult: null,
  map: null,
  mapIds: [],
};

const byId = (id) => document.getElementById(id);
const escapeHtml = (value) =>
  String(value ?? "—").replace(
    /[&<>'"]/g,
    (character) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"})[character],
  );
const shortHash = (value) => (value ? `${value.slice(0, 12)}…${value.slice(-8)}` : "—");
const formatBytes = (value) => new Intl.NumberFormat("zh-TW").format(value);
const apiUrl = (path) => new URL(path.replace(/^\//, ""), apiRoot);

function setStatus(message, kind = "info") {
  const element = byId("app-status");
  element.textContent = message;
  element.className = `app-status${kind === "error" ? " is-error" : kind === "success" ? " is-success" : ""}`;
}

function setServerStatus(message, kind = "pending") {
  byId("server-status").textContent = message;
  const container = document.querySelector(".runtime-state");
  container.classList.toggle("is-ready", kind === "ready");
  container.classList.toggle("is-error", kind === "error");
}

function enableStep(step) {
  state.enabledSteps.add(step);
  document.querySelector(`[data-step="${step}"]`).disabled = false;
}

function goTo(step) {
  if (!state.enabledSteps.has(step)) return;
  state.currentStep = step;
  for (const panel of document.querySelectorAll("[data-panel]")) {
    panel.classList.toggle("is-active", panel.dataset.panel === step);
  }
  for (const button of document.querySelectorAll("[data-step]")) {
    const current = button.dataset.step === step;
    button.classList.toggle("is-active", current);
    button.classList.toggle("is-complete", state.enabledSteps.has(button.dataset.step) && !current);
    if (current) button.setAttribute("aria-current", "step");
    else button.removeAttribute("aria-current");
  }
  byId("stage-content").focus({preventScroll: true});
  scrollTo({top: 0, behavior: "smooth"});
}

async function post(path, payload) {
  const response = await fetch(apiUrl(path), {
    method: "POST",
    headers: {"content-type": "application/json"},
    body: JSON.stringify(payload),
  });
  let body;
  try {
    body = await response.json();
  } catch {
    throw new Error(`Agent API 回傳非 JSON 結果（HTTP ${response.status}）。`);
  }
  if (!response.ok) throw new Error(body.error?.message || body.error?.code || `Agent API HTTP ${response.status}`);
  return body;
}

function clearMapArtifacts() {
  const map = state.map;
  if (!map?.isStyleLoaded()) return;
  for (const record of [...state.mapIds].reverse()) {
    if (record.kind === "layer" && map.getLayer(record.id)) map.removeLayer(record.id);
    if (record.kind === "source" && map.getSource(record.id)) map.removeSource(record.id);
  }
  state.mapIds = [];
}

function resetAfterUpload() {
  state.local = null;
  state.plan = null;
  state.authorization = null;
  state.compiled = null;
  state.qa = null;
  state.decision = null;
  state.decisionTrace = [];
  state.browserResult = null;
  state.enabledSteps = new Set(["upload"]);
  for (const button of document.querySelectorAll("[data-step]")) {
    button.disabled = button.dataset.step !== "upload";
    button.classList.remove("is-complete");
  }
  byId("upload-error").hidden = true;
  byId("clarification-card").hidden = true;
  byId("upload-result").hidden = true;
  byId("continue-verify").disabled = true;
  clearMapArtifacts();
}

function renderComponents(archive) {
  const required = archive.requiredComponents.map(
    (name) => `<span class="component is-required">必要 · ${escapeHtml(name.split("/").at(-1))}</span>`,
  );
  const optional = archive.optionalComponents.length
    ? archive.optionalComponents.map(
        (name) => `<span class="component">可選 · ${escapeHtml(name.split("/").at(-1))}</span>`,
      )
    : ['<span class="component">可選 · .cpg 未提供</span>'];
  byId("component-list").innerHTML = [...required, ...optional].join("");
}

function renderClarifications(result) {
  const card = byId("clarification-card");
  card.hidden = false;
  byId("clarification-summary").textContent = `資料結構可讀，但 ${result.clarifications.length} 個 mapping 問題尚未回答；現在不會建立 Agent plan。`;
  byId("clarification-questions").innerHTML = result.clarifications
    .map((item) => {
      if (item.type === "schema-field-mapping") {
        return `<label class="check-row"><input id="confirm-schema-mapping" type="checkbox"><span>${escapeHtml(item.question)}<small>本次確認只存在這個 browser session，不寫入正式 KG。</small></span></label>`;
      }
      const options = Object.entries(item.options)
        .map(([code, name]) => `<option value="${escapeHtml(code)}">${escapeHtml(code)} · ${escapeHtml(name)}</option>`)
        .join("");
      return `<label for="parent-${escapeHtml(item.sourceCode)}">${escapeHtml(item.question)}</label><select id="parent-${escapeHtml(item.sourceCode)}" data-parent-code="${escapeHtml(item.sourceCode)}"><option value="">請選擇，不可猜測</option>${options}</select>`;
    })
    .join("");
  setStatus("需要人工回答 schema／分類 mapping；尚未呼叫 Agent。", "error");
}

function renderUploadResult(file, archive, inspection, digest) {
  const observed = inspection.observation;
  byId("upload-facts").innerHTML = [
    ["檔案", file.name],
    ["ZIP 大小", `${formatBytes(file.size)} bytes`],
    ["Archive SHA-256", shortHash(digest)],
    ["圖層", archive.layerName.toUpperCase()],
    ["Geometry", observed.geometryTypes.join(" + ")],
    ["圖徵數", observed.featureCount],
    ["Vertex count", observed.totalVertexCount],
    ["Per-feature vertices", observed.vertexCounts.join(" / ")],
    ["MultiLineString", observed.multipartFeatureCount],
    ["有效道路分類", Object.keys(observed.observedClassCounts).length],
    ["Classification field", `${observed.classificationField} → ROADCLASS2`],
    ["Browser output CRS", observed.outputCrs],
  ]
    .map(([term, value]) => `<dt>${escapeHtml(term)}</dt><dd>${escapeHtml(value)}</dd>`)
    .join("");
  renderComponents(archive);
  byId("clarification-card").hidden = true;
  byId("upload-result").hidden = false;
}

function observationPayload() {
  const observed = state.local.inspection.observation;
  return {
    schema: "nma.road-dataset-observation/1.0",
    goal: byId("goal").value.trim(),
    source: "user-shapefile",
    source_layer: observed.sourceLayer,
    geometry_family: observed.geometryFamily,
    classification_field_mapping: observed.classificationFieldMapping,
    identity_field: observed.identityField,
    label_field: observed.labelField,
    route_number_fields: observed.routeNumberFields,
    observed_class_counts: observed.observedClassCounts,
    classification_resolutions: observed.classificationResolutions,
    feature_count: observed.featureCount,
    total_vertex_count: observed.totalVertexCount,
    multipart_feature_count: observed.multipartFeatureCount,
    source_identity_rule: observed.sourceIdentityRule,
    raw_feature_bytes_transmitted: false,
  };
}

function renderPlan() {
  const plan = state.plan;
  byId("plan-status").textContent = "等待人工授權";
  byId("plan-status").className = "status-pill is-success";
  byId("evidence-rows").innerHTML = plan.entries
    .map((entry) => {
      const citation = entry.evidence.portrayal_citation;
      const shield = entry.shield_binding
        ? `${entry.shield_binding.shield_code} semantic only`
        : "沒有已綁定 shield recipe";
      return `<tr><td><strong>${escapeHtml(entry.feature_name)}</strong><small>${escapeHtml(entry.feature_code)}</small></td><td>${escapeHtml(entry.feature_count)}</td><td><strong>道路線＋沿線名稱</strong><small>${escapeHtml(shield)}</small></td><td><strong>${escapeHtml(citation.filename)}</strong><small>p.${escapeHtml(entry.rule.page)} · 附件七 p.${escapeHtml(entry.evidence.classification_citation.page)}</small></td></tr>`;
    })
    .join("");
  const kg = plan.entries[0].evidence.knowledge_service;
  byId("kg-facts").innerHTML = [
    ["Backend", kg.active_backend],
    ["Graph revision", kg.graph_revision],
    ["Graph SHA-256", shortHash(kg.canonical_graph_sha256)],
    ["Read transactions", plan.entries.reduce((sum, entry) => sum + entry.evidence.knowledge_service.read_transaction_calls, 0)],
    ["Agent Cypher", kg.arbitrary_cypher_allowed ? "允許" : "禁止"],
    ["KG mutation", kg.mutation_allowed ? "允許" : "禁止"],
  ]
    .map(([term, value]) => `<dt>${escapeHtml(term)}</dt><dd>${escapeHtml(value)}</dd>`)
    .join("");
  const mapping = plan.source_binding.classification_field_mapping;
  const resolutions = plan.source_binding.classification_resolutions;
  byId("plan-detail").innerHTML = `<dl class="fact-grid"><dt>Plan SHA-256</dt><dd>${escapeHtml(plan.plan_sha256)}</dd><dt>Schema mapping</dt><dd>${escapeHtml(mapping.source_field)} → ${escapeHtml(mapping.canonical_field)} · ${escapeHtml(mapping.status)}</dd><dt>Parent resolutions</dt><dd>${resolutions.length ? resolutions.map((item) => `${item.source_code} → ${item.effective_code}`).join("；") : "none"}</dd><dt>Surveyed-width boundary</dt><dd>held / false</dd><dt>Shield graphic</dt><dd>held / false</dd><dt>Production activation</dt><dd>disabled / false</dd></dl><div class="path-list">${plan.entries
    .map(
      (entry) => `<div class="path-item"><strong>${escapeHtml(entry.feature_code)} ${escapeHtml(entry.feature_name)}</strong><code>${entry.evidence.knowledge_node_ids.map(escapeHtml).join(" → ")}</code></div>`,
    )
    .join("")}</div>`;
  renderAuthorizationFacts();
}

function renderAuthorizationFacts() {
  const plan = state.plan;
  byId("authorization-facts").innerHTML = [
    ["Plan", shortHash(plan.plan_sha256)],
    ["有效分類", plan.entries.map((entry) => entry.feature_code).join("、")],
    ["預計圖徵", plan.geometry_observation.feature_count],
    ["預計 vertices", plan.geometry_observation.total_vertex_count],
    ["允許操作", "compile-maplibre-preview"],
    ["ROADA 實寬／shield／輸出", "禁止"],
  ]
    .map(([term, value]) => `<dt>${escapeHtml(term)}</dt><dd>${escapeHtml(value)}</dd>`)
    .join("");
}

async function createPlanFromInspection(file, archive, digest, inspection) {
  state.local = {...state.local, fileName: file.name, file, archive, digest, inspection};
  renderUploadResult(file, archive, inspection, digest);
  setStatus("資料 gate 通過。正在以有效分類 observation 查詢唯讀 Knowledge Service…");
  state.plan = await post("road-portrayal/proposals", observationPayload());
  renderPlan();
  enableStep("evidence");
  setStatus("ROAD Agent plan 已建立；Shapefile 與 GeoJSON 仍只存在這個瀏覽器分頁。", "success");
}

async function processSelectedFile(file) {
  resetAfterUpload();
  const button = byId("inspect-button");
  button.disabled = true;
  try {
    if (!file) throw new RoadUploadError("zip-required", "請先選擇 ZIP 檔案。");
    if (!byId("goal").value.trim()) throw new RoadUploadError("goal-required", "請輸入道路製圖目標。");
    setStatus("正在瀏覽器內檢查 ZIP、線 geometry 與 schema；尚未呼叫 Agent…");
    const buffer = await file.arrayBuffer();
    const archive = validateRoadArchive(file, listZipEntries(buffer));
    const digest = await sha256Hex(buffer);
    const parsed = await parseZip(buffer.slice(0));
    const preliminary = inspectRoadFeatures(parsed, archive);
    state.local = {fileName: file.name, file, archive, digest, parsed, preliminary};
    if (preliminary.status === "clarification-required") {
      renderClarifications(preliminary);
      return;
    }
    await createPlanFromInspection(file, archive, digest, preliminary);
  } catch (error) {
    state.local = null;
    byId("upload-error").hidden = false;
    byId("upload-error").innerHTML = `<strong>資料檢查終止</strong><br>${escapeHtml(error.message)}`;
    setStatus(`未建立 plan：${error.message}`, "error");
  } finally {
    button.disabled = false;
  }
}

async function resolveClarifications(event) {
  event.preventDefault();
  try {
    const reviewer = byId("mapping-reviewer").value.trim();
    const needsSchema = state.local.preliminary.clarifications.some(
      (item) => item.type === "schema-field-mapping",
    );
    if (needsSchema && !byId("confirm-schema-mapping")?.checked) {
      throw new RoadUploadError("schema-mapping-unconfirmed", "必須明確回答 TERRAINID mapping 問題。");
    }
    const parentResolutions = {};
    for (const select of document.querySelectorAll("[data-parent-code]")) {
      if (!select.value) throw new RoadUploadError("parent-unresolved", `${select.dataset.parentCode} 尚未選擇子類。`);
      parentResolutions[select.dataset.parentCode] = select.value;
    }
    const inspection = inspectRoadFeatures(state.local.parsed, state.local.archive, {
      schemaMappingConfirmedBy: reviewer,
      parentResolutionConfirmedBy: reviewer,
      parentResolutions,
    });
    await createPlanFromInspection(
      state.local.file,
      state.local.archive,
      state.local.digest,
      inspection,
    );
  } catch (error) {
    setStatus(`Mapping 尚未完成：${error.message}`, "error");
  }
}

function updateAuthorizationButton() {
  byId("authorize-plan").disabled = !(
    byId("confirm-evidence").checked &&
    byId("confirm-boundary").checked &&
    byId("authorization-actor").value.trim()
  );
}

async function authorizePlan(event) {
  event.preventDefault();
  const button = byId("authorize-plan");
  button.disabled = true;
  try {
    state.authorization = await post("road-portrayal/authorizations", {
      plan: state.plan,
      actor: byId("authorization-actor").value.trim(),
      decision: "authorize-preview",
    });
    byId("authorization-result").hidden = false;
    byId("authorization-result").className = "message";
    byId("authorization-result").textContent = `已授權 ROAD preview：${shortHash(state.authorization.authorization_sha256)}`;
    enableStep("map");
    goTo("map");
    await compileVerifyAndRender();
  } catch (error) {
    byId("authorization-result").hidden = false;
    byId("authorization-result").className = "message message-error";
    byId("authorization-result").textContent = error.message;
    setStatus(`授權失敗：${error.message}`, "error");
    updateAuthorizationButton();
  }
}

async function rejectPlan() {
  try {
    state.authorization = await post("road-portrayal/authorizations", {
      plan: state.plan,
      actor: byId("authorization-actor").value.trim() || "browser-road-reviewer",
      decision: "reject",
    });
    byId("authorization-result").hidden = false;
    byId("authorization-result").className = "message message-warning";
    byId("authorization-result").textContent = "Plan 已拒絕；沒有建立道路 MapLibre layers。";
    setStatus("人工決策：拒絕 ROAD plan。流程已停止。", "error");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

function mapReady() {
  if (!state.map) return Promise.reject(new Error("MapLibre 尚未初始化。"));
  if (state.map.loaded()) return Promise.resolve();
  return new Promise((resolve) => state.map.once("load", resolve));
}

function initializeMap() {
  if (state.map) return;
  if (!window.maplibregl) throw new Error("MapLibre GL JS 無法載入。");
  byId("map").innerHTML = "";
  const style = {
    version: 8,
    glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
    sources: {},
    layers: [{id: "nma-background", type: "background", paint: {"background-color": "#edf1ed"}}],
  };
  if (!localBasemap) {
    style.sources["nlsc-emap"] = {
      type: "raster",
      tiles: ["https://wmts.nlsc.gov.tw/wmts/EMAP/default/GoogleMapsCompatible/{z}/{y}/{x}"],
      tileSize: 256,
      maxzoom: 19,
      attribution: "© 內政部國土測繪中心",
    };
    style.layers.push({id: "nlsc-emap", type: "raster", source: "nlsc-emap", paint: {"raster-opacity": 0.72}});
  }
  state.map = new maplibregl.Map({container: "map", center: [121, 23.7], zoom: 6.5, style});
  state.map.addControl(new maplibregl.NavigationControl(), "top-right");
}

function everyCoordinate(geometry) {
  return geometry.type === "LineString" ? geometry.coordinates : geometry.coordinates.flat();
}

function collectionBounds(collection) {
  const coordinates = collection.features.flatMap((feature) => everyCoordinate(feature.geometry));
  if (!coordinates.length) return null;
  return coordinates.reduce(
    (bounds, coordinate) => bounds.extend(coordinate),
    new maplibregl.LngLatBounds(coordinates[0], coordinates[0]),
  );
}

async function renderCompiledMap() {
  initializeMap();
  await mapReady();
  clearMapArtifacts();
  const map = state.map;
  const sourceId = state.compiled.source.id;
  map.addSource(sourceId, {type: "geojson", data: state.local.inspection.collection});
  state.mapIds.push({kind: "source", id: sourceId});
  for (const layer of state.compiled.layers) {
    const copy = structuredClone(layer);
    copy.source = sourceId;
    delete copy["source-layer"];
    map.addLayer(copy);
    state.mapIds.push({kind: "layer", id: copy.id});
  }
  const bounds = collectionBounds(state.local.inspection.collection);
  if (bounds) map.fitBounds(bounds, {padding: 70, maxZoom: 17, duration: 0});
  await Promise.race([
    new Promise((resolve) => map.once("idle", resolve)),
    new Promise((resolve) => setTimeout(resolve, 8_000)),
  ]);
  const renderedLayers = state.compiled.layers.filter((layer) => map.getLayer(layer.id)).length;
  if (renderedLayers !== state.compiled.layers.length) {
    throw new Error(`MapLibre 只建立 ${renderedLayers}/${state.compiled.layers.length} 個 ROAD layers。`);
  }
  const lineLayerIds = state.compiled.layers.filter((layer) => layer.type === "line").map((layer) => layer.id);
  const labelLayerIds = state.compiled.layers.filter((layer) => layer.type === "symbol").map((layer) => layer.id);
  const renderedLineFeatures = map.queryRenderedFeatures({layers: lineLayerIds}).length;
  const renderedLabelFeatures = map.queryRenderedFeatures({layers: labelLayerIds}).length;
  if (renderedLineFeatures < 1) throw new Error("MapLibre 沒有可見的 ROAD line feature。");
  if (state.local.inspection.observation.namedFeatureCount > 0 && renderedLabelFeatures < 1) {
    throw new Error("MapLibre 沒有可見的 line-following ROADNAME。");
  }
  return {status: "pass", renderedLayers, renderedLineFeatures, renderedLabelFeatures};
}

async function observeTool(outcome, detail) {
  const result = await post("road-portrayal/observations", {
    plan: state.plan,
    observation: {
      schema: "nma.road-portrayal-tool-observation/1.0",
      tool: "maplibre-road-preview-compiler",
      plan_sha256: state.plan.plan_sha256,
      outcome,
      detail,
    },
  });
  if (result.schema === "nma.road-portrayal-agent-decision/1.0") {
    state.decisionTrace.push({outcome, decision: result.decision});
  }
  return result;
}

function renderMapFacts() {
  const counts = state.plan.entries.map((entry) => `${entry.feature_code} · ${entry.feature_count}`).join("；");
  byId("map-facts").innerHTML = [
    ["Browser-local source", state.local.fileName],
    ["Feature count", state.compiled.expected_feature_count],
    ["Vertex count", state.compiled.expected_total_vertex_count],
    ["Class counts", counts],
    ["MapLibre layers", state.compiled.layers.length],
    ["Visible line render hits", state.browserResult.renderedLineFeatures],
    ["Visible label render hits", state.browserResult.renderedLabelFeatures],
    ["ROADA surveyed width", "not rendered"],
    ["Route shield graphic", "not rendered"],
    ["Basemap", localBasemap ? "local blank canvas（default privacy mode）" : "NLSC EMAP（opt-in）"],
    ["Data transmitted", "none"],
  ]
    .map(([term, value]) => `<dt>${escapeHtml(term)}</dt><dd>${escapeHtml(value)}</dd>`)
    .join("");
}

async function compileVerifyAndRender() {
  byId("map-state").textContent = "編譯與 QA 中";
  byId("map-state").className = "status-pill is-warning";
  byId("map-message").hidden = true;
  setStatus("已授權；正在編譯 evidence-bound ROAD style，尚未繪製資料…");
  try {
    state.compiled = await post("road-portrayal/compile", {
      plan: state.plan,
      authorization: state.authorization,
    });
    state.decision = await observeTool("compiled", "Server compiled the authorized ROAD style fragment.");
    state.qa = await post("road-portrayal/verify", {
      plan: state.plan,
      authorization: state.authorization,
      adapter_result: state.compiled,
    });
    if (!state.qa.browser_render_authorized) throw new Error("QA 未授權 ROAD browser render。");
    setStatus("Plan、authorization、line style 與 QA 綁定完成；現在才建立 browser-local ROAD layers…");
    state.browserResult = await renderCompiledMap();
    state.decision = await observeTool(
      "browser-render-verified",
      `${state.browserResult.renderedLineFeatures} visible ROAD line features and ${state.browserResult.renderedLabelFeatures} visible line labels.`,
    );
    renderMapFacts();
    byId("map-state").textContent = "道路圖已驗證";
    byId("map-state").className = "status-pill is-success";
    byId("map-message").hidden = false;
    byId("map-message").className = "message";
    byId("map-message").textContent = `MapLibre 已建立 ${state.browserResult.renderedLayers} 個 ROAD layers；使用者 GeoJSON 未離開瀏覽器。`;
    enableStep("verify");
    byId("continue-verify").disabled = false;
    renderVerification();
    setStatus("ROAD map preview 完成；請查看 QA、Agent decision 與 provenance。", "success");
  } catch (error) {
    clearMapArtifacts();
    try {
      state.decision = await observeTool("style-validation-failed", error.message);
    } catch {
      // Preserve the actual browser failure as the user-facing cause.
    }
    state.browserResult = {status: "fail", detail: error.message};
    byId("map-state").textContent = "已停止";
    byId("map-state").className = "status-pill is-error";
    byId("map-message").hidden = false;
    byId("map-message").className = "message message-error";
    byId("map-message").textContent = `ROAD render 失敗；Agent 已停止：${error.message}`;
    enableStep("verify");
    byId("continue-verify").disabled = false;
    renderVerification();
    setStatus(`道路圖未通過 browser render：${error.message}`, "error");
  }
}

function renderVerification() {
  if (!state.qa) return;
  const passed = state.qa.status === "pass-ready-for-browser-render" && state.browserResult?.status === "pass";
  byId("qa-status").textContent = passed ? "PASS" : "FAIL CLOSED";
  byId("qa-status").className = `status-pill ${passed ? "is-success" : "is-error"}`;
  const browserChecks = [
    {
      id: "browser-road-line-render",
      passed: state.browserResult?.renderedLineFeatures > 0,
      detail: state.browserResult?.renderedLineFeatures
        ? `${state.browserResult.renderedLineFeatures} visible line render hits observed; exact source feature count is verified separately.`
        : state.browserResult?.detail || "No visible ROAD line observed.",
    },
    {
      id: "browser-line-following-label",
      passed:
        state.local.inspection.observation.namedFeatureCount === 0 ||
        state.browserResult?.renderedLabelFeatures > 0,
      detail: `${state.browserResult?.renderedLabelFeatures || 0} visible ROADNAME render hits observed.`,
    },
  ];
  byId("qa-checks").innerHTML = [...state.qa.checks, ...browserChecks]
    .map(
      (check) => `<li class="${check.passed ? "" : "is-failed"}"><strong>${escapeHtml(check.id)}</strong><small>${escapeHtml(check.detail)}</small></li>`,
    )
    .join("");
  const decision = state.decision || {};
  byId("agent-decision").textContent = decision.decision || (passed ? "stop" : "abstain-and-stop");
  byId("agent-decision").className = `status-pill ${passed ? "is-success" : "is-error"}`;
  byId("agent-reason").textContent = decision.reason || "Browser ROAD observation recorded.";
  const trace = [
    ...state.plan.agent_trace,
    ...state.decisionTrace.flatMap((item, index) => [
      {sequence: state.plan.agent_trace.length + index * 2 + 1, state: "observe-tool-result", outcome: item.outcome},
      {sequence: state.plan.agent_trace.length + index * 2 + 2, state: "decide", outcome: item.decision},
    ]),
  ];
  byId("agent-trace").innerHTML = trace
    .map((item) => `<span class="trace-item">${escapeHtml(item.sequence)} · ${escapeHtml(item.state)} · ${escapeHtml(item.outcome)}</span>`)
    .join("");
  byId("provenance-facts").innerHTML = [
    ["Local archive SHA-256", state.local.digest],
    ["Graph SHA-256", state.plan.graph_identity.canonical_graph_sha256],
    ["Plan SHA-256", state.plan.plan_sha256],
    ["Authorization SHA-256", state.authorization?.authorization_sha256],
    ["Adapter result SHA-256", state.compiled?.adapter_result_sha256],
    ["QA SHA-256", state.qa.qa_sha256],
    ["Feature / vertex count", `${state.local.inspection.observation.featureCount} / ${state.local.inspection.observation.totalVertexCount}`],
    ["Local per-feature vertices", state.local.inspection.observation.vertexCounts.join(" / ")],
    ["Raw feature bytes transmitted", "false"],
    ["Surveyed-width / shield / production", "false / false / false"],
  ]
    .map(([term, value]) => `<dt>${escapeHtml(term)}</dt><dd>${escapeHtml(value)}</dd>`)
    .join("");
}

async function checkServer() {
  try {
    const response = await fetch(apiUrl("agent/status"), {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const body = await response.json();
    setServerStatus(`唯讀 KG ready · ${body.graph_backend?.active_backend || "unavailable"}`, "ready");
  } catch {
    setServerStatus("Agent server unavailable", "error");
    setStatus("無法連線 Agent server；仍可檢查 ZIP，但不能建立 KG-grounded ROAD plan。", "error");
  }
}

async function loadLocalQaFixture() {
  const fixture = new URLSearchParams(location.search).get("qaFixture");
  if (!fixture || !["127.0.0.1", "localhost"].includes(location.hostname)) return;
  try {
    const response = await fetch(new URL(fixture, document.baseURI), {cache: "no-store"});
    if (!response.ok) throw new Error(`QA fixture HTTP ${response.status}`);
    const blob = await response.blob();
    await processSelectedFile(new File([blob], fixture.split("/").at(-1) || "road-qa.zip", {type: "application/zip"}));
  } catch (error) {
    setStatus(`Local browser QA fixture failed: ${error.message}`, "error");
  }
}

byId("upload-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await processSelectedFile(byId("road-archive").files[0]);
});
byId("clarification-form").addEventListener("submit", resolveClarifications);
byId("continue-evidence").addEventListener("click", () => goTo("evidence"));
byId("continue-authorize").addEventListener("click", () => {
  enableStep("authorize");
  goTo("authorize");
});
byId("authorization-form").addEventListener("submit", authorizePlan);
byId("reject-plan").addEventListener("click", rejectPlan);
for (const id of ["confirm-evidence", "confirm-boundary", "authorization-actor"]) {
  byId(id).addEventListener("input", updateAuthorizationButton);
  byId(id).addEventListener("change", updateAuthorizationButton);
}
byId("continue-verify").addEventListener("click", () => goTo("verify"));
byId("restart-demo").addEventListener("click", () => location.reload());
for (const button of document.querySelectorAll("[data-step]")) {
  button.addEventListener("click", () => goTo(button.dataset.step));
}
for (const button of document.querySelectorAll("[data-go]")) {
  button.addEventListener("click", () => goTo(button.dataset.go));
}

updateAuthorizationButton();
checkServer();
loadLocalQaFixture();
