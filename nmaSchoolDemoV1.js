import parseZip from "./assets/vendor/shpjs-6.2.0/shp.esm.min.js";
import {
  SCHOOL_CODES,
  SchoolUploadError,
  inspectSchoolFeatures,
  listZipEntries,
  sha256Hex,
  validateSchoolArchive,
} from "./assets/js/nma-school-upload-v1.js";

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
  const button = document.querySelector(`[data-step="${step}"]`);
  button.disabled = false;
}

function goTo(step) {
  if (!state.enabledSteps.has(step)) return;
  state.currentStep = step;
  for (const panel of document.querySelectorAll("[data-panel]")) {
    panel.classList.toggle("is-active", panel.dataset.panel === step);
  }
  for (const button of document.querySelectorAll("[data-step]")) {
    const isCurrent = button.dataset.step === step;
    button.classList.toggle("is-active", isCurrent);
    button.classList.toggle("is-complete", state.enabledSteps.has(button.dataset.step) && !isCurrent);
    if (isCurrent) button.setAttribute("aria-current", "step");
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
  if (!response.ok) {
    throw new Error(body.error?.message || body.error?.code || `Agent API HTTP ${response.status}`);
  }
  return body;
}

function resetAfterUpload() {
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
  byId("upload-result").hidden = true;
  byId("upload-error").hidden = true;
  byId("continue-verify").disabled = true;
  clearMapArtifacts();
}

function renderUploadResult(file, archive, inspection, digest) {
  byId("upload-facts").innerHTML = [
    ["檔案", file.name],
    ["ZIP 大小", `${formatBytes(file.size)} bytes`],
    ["Archive SHA-256", shortHash(digest)],
    ["圖層", archive.layerName.toUpperCase()],
    ["Geometry", inspection.observation.geometryType],
    ["圖徵數", inspection.observation.featureCount],
    ["實際 School 類別", Object.keys(inspection.observation.observedClassCounts).length],
    ["Browser output CRS", inspection.observation.outputCrs],
  ]
    .map(([term, value]) => `<dt>${escapeHtml(term)}</dt><dd>${escapeHtml(value)}</dd>`)
    .join("");
  const required = archive.requiredComponents.map(
    (name) => `<span class="component is-required">必要 · ${escapeHtml(name.split("/").at(-1))}</span>`,
  );
  const optional = archive.optionalComponents.length
    ? archive.optionalComponents.map(
        (name) => `<span class="component">可選 · ${escapeHtml(name.split("/").at(-1))}</span>`,
      )
    : ['<span class="component">可選 · .cpg 未提供</span>'];
  byId("component-list").innerHTML = [...required, ...optional].join("");
  byId("upload-result").hidden = false;
}

function observationPayload() {
  const observed = state.local.inspection.observation;
  return {
    schema: "nma.school-dataset-observation/1.0",
    goal: byId("goal").value.trim(),
    source: "user-shapefile",
    source_layer: observed.sourceLayer,
    geometry_type: observed.geometryType,
    classification_field: observed.classificationField,
    identity_field: observed.identityField,
    label_field: observed.labelField,
    observed_class_counts: observed.observedClassCounts,
    source_identity_rule: observed.sourceIdentityRule,
    raw_feature_bytes_transmitted: false,
  };
}

function renderPlan() {
  const plan = state.plan;
  const status = byId("plan-status");
  status.textContent = plan.status.includes("replanned") ? "Agent 已重新規劃" : "等待人工授權";
  status.className = `status-pill ${plan.status.includes("replanned") ? "is-warning" : "is-success"}`;
  byId("evidence-rows").innerHTML = plan.entries
    .map((entry) => {
      const mode = entry.render_mode === "school-flag-marker" ? "校旗＋名稱" : "只註記名稱";
      const citation = entry.evidence.portrayal_citation;
      return `<tr><td><strong>${escapeHtml(entry.feature_name)}</strong><small>${escapeHtml(entry.feature_code)}</small></td><td>${escapeHtml(entry.feature_count)}</td><td><strong>${mode}</strong><small>${escapeHtml(entry.rule.symbol_family)}</small></td><td><strong>${escapeHtml(citation.filename)}</strong><small>p.${escapeHtml(entry.rule.page)} · 附件七 p.${escapeHtml(entry.evidence.classification_citation.page)}</small></td></tr>`;
    })
    .join("");
  const first = plan.entries[0];
  const kg = first.evidence.knowledge_service;
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
  byId("plan-detail").innerHTML = `<dl class="fact-grid"><dt>Plan SHA-256</dt><dd>${escapeHtml(plan.plan_sha256)}</dd><dt>Classification root</dt><dd>${escapeHtml(plan.classification_root)}（只作為父分類）</dd><dt>Official activation</dt><dd>${plan.governance.official_rule_activation ? "YES" : "held / false"}</dd><dt>Production activation</dt><dd>${plan.governance.production_activation ? "YES" : "disabled / false"}</dd></dl><div class="path-list">${plan.entries
    .map(
      (entry) => `<div class="path-item"><strong>${escapeHtml(entry.feature_code)} ${escapeHtml(entry.feature_name)}</strong><code>${entry.evidence.knowledge_node_ids.map(escapeHtml).join(" → ")}</code></div>`,
    )
    .join("")}</div>`;
  renderAuthorizationFacts();
}

function renderAuthorizationFacts() {
  if (!state.plan) return;
  byId("authorization-facts").innerHTML = [
    ["Plan", shortHash(state.plan.plan_sha256)],
    ["Revision depth", state.plan.revision.depth],
    ["實際分類", state.plan.entries.map((entry) => entry.feature_code).join("、")],
    ["預計圖徵", state.plan.entries.reduce((sum, entry) => sum + entry.feature_count, 0)],
    ["允許操作", "compile-maplibre-preview"],
    ["資料輸出", "禁止"],
  ]
    .map(([term, value]) => `<dt>${escapeHtml(term)}</dt><dd>${escapeHtml(value)}</dd>`)
    .join("");
}

async function processSelectedFile(file) {
  resetAfterUpload();
  const button = byId("inspect-button");
  const errorBox = byId("upload-error");
  button.disabled = true;
  try {
    if (!file) throw new SchoolUploadError("zip-required", "請先選擇 ZIP 檔案。");
    const goal = byId("goal").value.trim();
    if (!goal) throw new SchoolUploadError("goal-required", "請輸入要完成的地圖目標。");
    setStatus("正在瀏覽器內檢查 ZIP 結構；尚未呼叫 Agent…");
    const buffer = await file.arrayBuffer();
    const entries = listZipEntries(buffer);
    const archive = validateSchoolArchive(file, entries);
    const digest = await sha256Hex(buffer);
    const parsed = await parseZip(buffer.slice(0));
    const inspection = inspectSchoolFeatures(parsed, archive);
    state.local = {fileName: file.name, archive, digest, inspection};
    renderUploadResult(file, archive, inspection, digest);
    setStatus("資料 gate 通過。正在以分類 observation 查詢唯讀 Knowledge Service…");
    state.plan = await post("school-portrayal/proposals", observationPayload());
    renderPlan();
    enableStep("evidence");
    setStatus("Agent plan 已建立；Shapefile 與 GeoJSON 仍只存在這個瀏覽器分頁。", "success");
  } catch (error) {
    state.local = null;
    errorBox.hidden = false;
    errorBox.innerHTML = `<strong>資料檢查終止</strong><br>${escapeHtml(error.message)}`;
    setStatus(`未建立 plan：${error.message}`, "error");
  } finally {
    button.disabled = false;
  }
}

async function handleUpload(event) {
  event.preventDefault();
  await processSelectedFile(byId("school-archive").files[0]);
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
    setStatus("正在建立只綁定目前 plan 的 preview authorization…");
    state.authorization = await post("school-portrayal/authorizations", {
      plan: state.plan,
      actor: byId("authorization-actor").value.trim(),
      decision: "authorize-preview",
    });
    const result = byId("authorization-result");
    result.hidden = false;
    result.className = "message";
    result.textContent = `已授權 preview：${shortHash(state.authorization.authorization_sha256)}`;
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
    state.authorization = await post("school-portrayal/authorizations", {
      plan: state.plan,
      actor: byId("authorization-actor").value.trim() || "browser-human-reviewer",
      decision: "reject",
    });
    byId("authorization-result").hidden = false;
    byId("authorization-result").className = "message message-warning";
    byId("authorization-result").textContent = "Plan 已拒絕；沒有編譯 style，也沒有建立地圖圖層。";
    setStatus("人工決策：拒絕 plan。流程已停止。", "error");
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

function clearMapArtifacts() {
  const map = state.map;
  if (!map?.isStyleLoaded()) return;
  for (const record of [...state.mapIds].reverse()) {
    if (record.kind === "layer" && map.getLayer(record.id)) map.removeLayer(record.id);
    if (record.kind === "source" && map.getSource(record.id)) map.removeSource(record.id);
    if (record.kind === "image" && map.hasImage(record.id)) map.removeImage(record.id);
  }
  state.mapIds = [];
}

function collectionBounds(collection) {
  const coordinates = collection.features.map((feature) => feature.geometry.coordinates);
  if (!coordinates.length) return null;
  return coordinates.reduce(
    (bounds, coordinate) => bounds.extend(coordinate),
    new maplibregl.LngLatBounds(coordinates[0], coordinates[0]),
  );
}

async function addImageResource(resource) {
  const image = new Image();
  image.decoding = "async";
  image.src = new URL(resource.path, document.baseURI).href;
  await new Promise((resolve, reject) => {
    image.onload = resolve;
    image.onerror = () => {
      const error = new Error(`無法載入 portrayal resource：${resource.path}`);
      error.code = "sdf-resource-load-failed";
      reject(error);
    };
  });
  state.map.addImage(resource.id, image, {sdf: Boolean(resource.sdf)});
  state.mapIds.push({kind: "image", id: resource.id});
}

async function renderCompiledMap() {
  initializeMap();
  await mapReady();
  clearMapArtifacts();
  const map = state.map;
  for (const resource of state.compiled.resources) await addImageResource(resource);
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
  await new Promise((resolve) => map.once("idle", resolve));
  const renderedLayers = state.compiled.layers.filter((layer) => map.getLayer(layer.id)).length;
  if (renderedLayers !== state.compiled.layers.length) {
    throw new Error(`MapLibre 只建立 ${renderedLayers}/${state.compiled.layers.length} 個 portrayal layers。`);
  }
  return {status: "pass", renderedLayers, sourceBound: Boolean(map.getSource(sourceId))};
}

async function observeTool(outcome, detail) {
  const result = await post("school-portrayal/observations", {
    plan: state.plan,
    observation: {
      schema: "nma.school-portrayal-tool-observation/1.0",
      tool: "maplibre-school-preview-compiler",
      plan_sha256: state.plan.plan_sha256,
      outcome,
      detail,
    },
  });
  if (result.schema === "nma.school-portrayal-agent-decision/1.0") {
    state.decisionTrace.push({
      outcome,
      decision: result.decision,
    });
  }
  return result;
}

function renderMapFacts() {
  const counts = state.plan.entries.map((entry) => `${entry.feature_code} · ${entry.feature_count}`).join("；");
  byId("map-facts").innerHTML = [
    ["Browser-local source", state.local.fileName],
    ["Feature count", state.compiled.expected_feature_count],
    ["Class counts", counts],
    ["MapLibre layers", state.compiled.layers.length],
    ["Flag resource", state.compiled.resources.length ? "reviewed derived SVG" : "not required"],
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
  setStatus("已授權；正在編譯 evidence-bound MapLibre style，尚未繪製資料…");
  try {
    state.compiled = await post("school-portrayal/compile", {
      plan: state.plan,
      authorization: state.authorization,
    });
    state.decision = await observeTool("compiled", "Server compiled the authorized MapLibre style fragment.");
    state.qa = await post("school-portrayal/verify", {
      plan: state.plan,
      authorization: state.authorization,
      adapter_result: state.compiled,
    });
    if (!state.qa.browser_render_authorized) throw new Error("QA 未授權 browser render。" );
    setStatus("Plan、authorization、style 與 QA 綁定完成；現在才建立 browser-local map layers…");
    state.browserResult = await renderCompiledMap();
    state.decision = await observeTool(
      "browser-render-verified",
      `${state.browserResult.renderedLayers} governed MapLibre layers rendered after QA authorization.`,
    );
    renderMapFacts();
    byId("map-state").textContent = "地圖已驗證";
    byId("map-state").className = "status-pill is-success";
    byId("map-message").hidden = false;
    byId("map-message").className = "message";
    byId("map-message").textContent = `MapLibre 已建立 ${state.browserResult.renderedLayers} 個分類圖層；使用者 GeoJSON 未離開瀏覽器。`;
    enableStep("verify");
    byId("continue-verify").disabled = false;
    renderVerification();
    setStatus("School map preview 完成；請查看 QA、Agent decision 與 provenance。", "success");
  } catch (error) {
    clearMapArtifacts();
    const hasSdf = state.compiled?.resources?.some((resource) => resource.sdf);
    if (hasSdf && error.code === "sdf-resource-load-failed") {
      try {
        const revised = await observeTool("sdf-resource-load-failed", error.message);
        if (revised.schema === "nma.school-portrayal-plan/1.0") {
          state.plan = revised;
          state.authorization = null;
          state.compiled = null;
          state.qa = null;
          state.decision = null;
          state.decisionTrace = [];
          renderPlan();
          byId("revision-notice").hidden = false;
          byId("revision-notice").textContent = "MapLibre 無法使用 SDF resource。Agent 已改用同一 reviewed SVG 的 non-SDF black preview；新 plan 必須重新授權。";
          byId("confirm-evidence").checked = false;
          byId("confirm-boundary").checked = false;
          updateAuthorizationButton();
          goTo("authorize");
          setStatus("工具 observation 改變了 plan；舊授權已失效，等待重新授權。", "error");
          return;
        }
      } catch (observationError) {
        error = observationError;
      }
    } else if (state.plan) {
      try {
        state.decision = await observeTool("style-validation-failed", error.message);
      } catch {
        // The original render error remains the user-facing cause.
      }
    }
    state.browserResult = {status: "fail", detail: error.message};
    byId("map-state").textContent = "已停止";
    byId("map-state").className = "status-pill is-error";
    byId("map-message").hidden = false;
    byId("map-message").className = "message message-error";
    byId("map-message").textContent = `MapLibre render 失敗；Agent 已停止：${error.message}`;
    enableStep("verify");
    byId("continue-verify").disabled = false;
    renderVerification();
    setStatus(`地圖未通過 browser render：${error.message}`, "error");
  }
}

function renderVerification() {
  if (!state.qa) return;
  const passed = state.qa.status === "pass-ready-for-browser-render" && state.browserResult?.status === "pass";
  byId("qa-status").textContent = passed ? "PASS" : "FAIL CLOSED";
  byId("qa-status").className = `status-pill ${passed ? "is-success" : "is-error"}`;
  const checks = [
    ...state.qa.checks,
    {
      id: "browser-maplibre-render",
      passed: state.browserResult?.status === "pass",
      detail:
        state.browserResult?.status === "pass"
          ? `${state.browserResult.renderedLayers} layers exist in the actual MapLibre style.`
          : state.browserResult?.detail || "Browser render did not complete.",
    },
  ];
  byId("qa-checks").innerHTML = checks
    .map(
      (check) => `<li class="${check.passed ? "" : "is-failed"}"><strong>${escapeHtml(check.id)}</strong><small>${escapeHtml(check.detail)}</small></li>`,
    )
    .join("");
  const decision = state.decision || {};
  byId("agent-decision").textContent = decision.decision || (passed ? "stop" : "abstain-and-stop");
  byId("agent-decision").className = `status-pill ${passed ? "is-success" : "is-error"}`;
  byId("agent-reason").textContent = decision.reason || "Browser render observation recorded.";
  const fullTrace = [
    ...state.plan.agent_trace,
    ...state.decisionTrace.flatMap((item, index) => [
      {
        sequence: state.plan.agent_trace.length + index * 2 + 1,
        state: "observe-tool-result",
        outcome: item.outcome,
      },
      {
        sequence: state.plan.agent_trace.length + index * 2 + 2,
        state: "decide",
        outcome: item.decision,
      },
    ]),
  ];
  byId("agent-trace").innerHTML = fullTrace
    .map((item) => `<span class="trace-item">${escapeHtml(item.sequence)} · ${escapeHtml(item.state)} · ${escapeHtml(item.outcome)}</span>`)
    .join("");
  byId("provenance-facts").innerHTML = [
    ["Local archive SHA-256", state.local.digest],
    ["Graph SHA-256", state.plan.graph_identity.canonical_graph_sha256],
    ["Plan SHA-256", state.plan.plan_sha256],
    ["Authorization SHA-256", state.authorization?.authorization_sha256],
    ["Adapter result SHA-256", state.compiled?.adapter_result_sha256],
    ["QA SHA-256", state.qa.qa_sha256],
    ["Raw feature bytes transmitted", "false"],
    ["Production activation", "false"],
  ]
    .map(([term, value]) => `<dt>${escapeHtml(term)}</dt><dd>${escapeHtml(value)}</dd>`)
    .join("");
}

async function checkServer() {
  try {
    const response = await fetch(apiUrl("agent/status"), {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const body = await response.json();
    const backend = body.graph_backend?.active_backend || "unavailable";
    setServerStatus(`唯讀 KG ready · ${backend}`, "ready");
  } catch {
    setServerStatus("Agent server unavailable", "error");
    setStatus("無法連線 Agent server；仍可選擇 ZIP，但不能建立 KG-grounded plan。", "error");
  }
}

async function loadLocalQaFixture() {
  const parameters = new URLSearchParams(location.search);
  const fixture = parameters.get("qaFixture");
  if (!fixture || !["127.0.0.1", "localhost"].includes(location.hostname)) return;
  try {
    const response = await fetch(new URL(fixture, document.baseURI), {cache: "no-store"});
    if (!response.ok) throw new Error(`QA fixture HTTP ${response.status}`);
    const blob = await response.blob();
    const name = fixture.split("/").at(-1) || "school-qa.zip";
    await processSelectedFile(new File([blob], name, {type: "application/zip"}));
  } catch (error) {
    setStatus(`Local browser QA fixture failed: ${error.message}`, "error");
  }
}

byId("upload-form").addEventListener("submit", handleUpload);
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
