"use strict";

const FROZEN_AUTHORITY = "eb87bde775333811529efb6f651573ea21cf456b";
const MAX_ARCHIVE_BYTES = 250 * 1024 * 1024;
const MAX_UNCOMPRESSED_BYTES = 900 * 1024 * 1024;
const MAX_ENTRIES = 5000;
const SIDECARS = ["shp", "shx", "dbf", "prj"];

const PROFILES = {
  school: {
    domain: "School · Point portrayal",
    title: "使用者 School SHP → 15-point result",
    subtitle: "從使用者 *_MARK 圖層檢索 9920103；保留 MARKID，檢查 frozen 15-point contract。",
    intent: "依測圖規範從我的 Shapefile 建立 School 點位圖，保留來源 ID，並提供可驗證 evidence。",
    geometry: "point",
    layerExact: null,
    layerSuffix: "_MARK",
    codeField: "TERRAINID",
    codeValue: "9920103",
    idField: "MARKID",
    labelField: "MARKNAME1",
    expectedCount: 15,
    rule: "School symbol portrayal：TERRAINID 9920103 → school point symbol；MARKID 必須保持一對一。",
    nodes: ["FeatureCode:9920103", "LayerRole:MARK", "IdentityRule:MARKID", "PortrayalRule:SCHOOL_POINT"],
    plan: "讀取使用者 *_MARK → code filter → preserve MARKID → MapLibre point portrayal。",
    mapKind: "POINT",
  },
  road: {
    domain: "ROAD · Line portrayal",
    title: "使用者 K14_ROAD → 中山街",
    subtitle: "只從使用者 line geometry 建立 line-following label；驗證 ROADSEGID 與實際 4/3/4 vertices。",
    intent: "從我的 K14_ROAD Shapefile 選出中山街，保留 ROADSEGID，建立 line-following road label 並驗證頂點。",
    geometry: "line",
    layerExact: "K14_ROAD",
    layerSuffix: "_ROAD",
    codeField: "TERRAINID",
    codeValue: "9420400",
    nameField: "ROADNAME",
    nameValue: "中山街",
    idField: "ROADSEGID",
    labelField: "ROADNAME",
    expectedCount: 3,
    expectedVertices: [4, 3, 4],
    expectedIds: ["K0000004671", "K0000004913", "K0000005348"],
    rule: "K14_ROAD：TERRAINID 9420400 且 ROADNAME=中山街 → line-following label；ROADSEGID 與 vertex sequence 不得改寫。",
    nodes: ["Layer:K14_ROAD", "FeatureCode:9420400", "NameConstraint:中山街", "PortrayalRule:LINE_LABEL"],
    plan: "讀取使用者 K14_ROAD → code/name filter → preserve ROADSEGID/vertices → MapLibre line label。",
    mapKind: "LINE",
  },
  build: {
    domain: "BUILD · Polygon portrayal",
    title: "使用者 J17_BUILD → boundary + hatch",
    subtitle: "從使用者 polygon/MultiPolygonZ 建立 boundary/hatch preview；production activation 始終 held/disabled。",
    intent: "從我的 J17_BUILD Shapefile 建立建物 boundary 與 hatch，保留 BUILD_ID；只允許 browser preview，production activation disabled。",
    geometry: "polygon",
    layerExact: "J17_BUILD",
    layerSuffix: "_BUILD",
    codeField: "TERRAINID",
    codeValue: "9310100",
    idField: "BUILD_ID",
    labelField: null,
    expectedCount: 2769,
    rule: "BUILD 9310100 → solid boundary + 45° hatch；可預覽，不得取得 production activation authority。",
    nodes: ["Layer:J17_BUILD", "FeatureCode:9310100", "Geometry:Polygon/MultiPolygonZ", "Governance:PRODUCTION_HELD"],
    plan: "讀取使用者 J17_BUILD → code filter → preserve BUILD_ID/Z evidence → MapLibre boundary + hatch；production writeback disabled。",
    mapKind: "POLYGON",
  },
};

const state = {
  profileId: "school",
  file: null,
  archiveBytes: null,
  archiveHash: null,
  inventory: null,
  collections: null,
  proposal: null,
  authorized: false,
  map: null,
  buildToken: 0,
};

const byId = (id) => document.getElementById(id);
const asset = (path) => new URL(path, document.baseURI).href;

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = String(text);
  return element;
}

function clear(element) {
  while (element.firstChild) element.firstChild.remove();
}

function formatBytes(value) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 ** 2) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 ** 2).toFixed(1)} MB`;
}

function baseName(path) {
  return path.replace(/\\/g, "/").split("/").pop();
}

function stem(path) {
  return path.replace(/\.[^.]+$/, "");
}

function canonical(path) {
  return path.replace(/\\/g, "/").replace(/^\.\//, "").toLocaleLowerCase();
}

function extension(path) {
  const match = path.match(/\.([^.\/]+)$/);
  return match ? match[1].toLocaleLowerCase() : "";
}

function safeEntryName(path) {
  const normalized = path.replace(/\\/g, "/");
  return !normalized.includes("\0") && !normalized.startsWith("/") && !/^[a-z]:\//i.test(normalized) && !normalized.split("/").includes("..");
}

function isMetadataNoise(path) {
  const normalized = path.replace(/\\/g, "/");
  const name = baseName(normalized);
  return normalized.startsWith("__MACOSX/") || name.startsWith("._") || name === ".DS_Store";
}

async function sha256(data) {
  const view = data instanceof Uint8Array ? data : new Uint8Array(data);
  const digest = await crypto.subtle.digest("SHA-256", view);
  return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, "0")).join("");
}

function geometryFamily(type) {
  if (/point/i.test(type || "")) return "point";
  if (/line/i.test(type || "")) return "line";
  if (/polygon/i.test(type || "")) return "polygon";
  return "unknown";
}

function countVertices(geometry) {
  if (!geometry) return 0;
  let count = 0;
  const walk = (value) => {
    if (!Array.isArray(value)) return;
    if (typeof value[0] === "number") count += 1;
    else value.forEach(walk);
  };
  walk(geometry.coordinates);
  return count;
}

function hasZ(geometry) {
  let observed = false;
  const walk = (value) => {
    if (observed || !Array.isArray(value)) return;
    if (typeof value[0] === "number") observed = value.length >= 3;
    else value.forEach(walk);
  };
  if (geometry) walk(geometry.coordinates);
  return observed;
}

function equalArray(left, right) {
  return left.length === right.length && left.every((value, index) => String(value) === String(right[index]));
}

function preflightArchive(bytes) {
  const entries = [];
  let uncompressedBytes = 0;
  const textFiles = window.fflate.unzipSync(bytes, {
    filter(info) {
      const path = info.name.replace(/\\/g, "/");
      entries.push({ path, bytes: info.originalSize || 0, directory: path.endsWith("/") });
      uncompressedBytes += info.originalSize || 0;
      return !isMetadataNoise(path) && /\.(?:prj|cpg)$/i.test(path) && (info.originalSize || 0) < 1024 * 1024;
    },
  });

  if (entries.length > MAX_ENTRIES) throw new Error(`ZIP 有 ${entries.length} 個 entries，超過安全上限 ${MAX_ENTRIES}。`);
  if (uncompressedBytes > MAX_UNCOMPRESSED_BYTES) throw new Error(`ZIP 解壓後約 ${formatBytes(uncompressedBytes)}，超過 browser-local 安全上限。`);
  const unsafe = entries.find((entry) => !safeEntryName(entry.path));
  if (unsafe) throw new Error(`ZIP 包含不安全路徑：${unsafe.path}`);

  const groups = new Map();
  entries.filter((entry) => !entry.directory && !isMetadataNoise(entry.path)).forEach((entry) => {
    const ext = extension(entry.path);
    if (![...SIDECARS, "cpg"].includes(ext)) return;
    const key = canonical(stem(entry.path));
    if (!groups.has(key)) groups.set(key, { key, stem: stem(entry.path), name: baseName(stem(entry.path)), components: {} });
    groups.get(key).components[ext] = entry;
  });
  const shapefiles = [...groups.values()].filter((group) => group.components.shp);
  if (!shapefiles.length) throw new Error("ZIP 中找不到 .shp。");

  const textByPath = new Map(Object.entries(textFiles).map(([path, data]) => [canonical(path), data]));
  return { entries, uncompressedBytes, groups, shapefiles, textByPath };
}

function normalizeCollections(parsed, inventory) {
  const values = Array.isArray(parsed) ? parsed : [parsed];
  return values.filter((value) => value && value.type === "FeatureCollection").map((collection, index) => {
    const fallback = inventory.shapefiles[index] ? inventory.shapefiles[index].stem : `layer-${index + 1}`;
    const name = collection.fileName || fallback;
    const geometryTypes = [...new Set(collection.features.map((feature) => feature.geometry && feature.geometry.type).filter(Boolean))];
    const fields = [...new Set(collection.features.flatMap((feature) => Object.keys(feature.properties || {})))];
    return { name, collection, geometryTypes, fields, family: geometryFamily(geometryTypes[0]) };
  });
}

function chooseLayers(profile, collections) {
  if (profile.layerExact) {
    const exact = collections.filter((layer) => layer.family === profile.geometry && baseName(layer.name).toLocaleUpperCase() === profile.layerExact);
    if (exact.length) return exact;
  }
  const suffix = collections.filter((layer) => layer.family === profile.geometry && baseName(layer.name).toLocaleUpperCase().endsWith(profile.layerSuffix));
  if (suffix.length) return suffix;
  return collections.filter((layer) => layer.family === profile.geometry);
}

function featureMatchesProfile(feature, profile) {
  const properties = feature.properties || {};
  if (String(properties[profile.codeField] ?? "") !== profile.codeValue) return false;
  if (profile.nameField && String(properties[profile.nameField] ?? "").trim() !== profile.nameValue) return false;
  return true;
}

function groupForLayer(layer, inventory) {
  const exact = inventory.groups.get(canonical(layer.name));
  if (exact) return exact;
  const wanted = baseName(layer.name).toLocaleLowerCase();
  const candidates = inventory.shapefiles.filter((group) => group.name.toLocaleLowerCase() === wanted);
  return candidates.length === 1 ? candidates[0] : null;
}

function decodeText(bytes) {
  if (!bytes) return "";
  return new TextDecoder("utf-8", { fatal: false }).decode(bytes).replace(/\0/g, "").trim();
}

function crsSummary(wkt) {
  if (!wkt) return "PRJ missing";
  const match = wkt.match(/^(?:PROJCS|GEOGCS|PROJCRS|GEODCRS)\s*\[\s*[\"']([^\"']+)/i);
  return match ? match[1] : `${wkt.slice(0, 52)}${wkt.length > 52 ? "…" : ""}`;
}

async function selectedComponentHashes(layers, inventory, bytes) {
  const selectedKeys = new Set(layers.map((layer) => groupForLayer(layer, inventory)).filter(Boolean).map((group) => group.key));
  const unpacked = window.fflate.unzipSync(bytes, {
    filter(info) {
      if (isMetadataNoise(info.name)) return false;
      const ext = extension(info.name);
      return [...SIDECARS, "cpg"].includes(ext) && selectedKeys.has(canonical(stem(info.name)));
    },
  });
  const results = [];
  for (const [path, data] of Object.entries(unpacked)) {
    results.push({ path, bytes: data.byteLength, sha256: await sha256(data) });
  }
  return results.sort((left, right) => left.path.localeCompare(right.path));
}

async function createProposal(token) {
  const profile = PROFILES[state.profileId];
  const layers = chooseLayers(profile, state.collections);
  const outputFeatures = [];
  layers.forEach((layer) => {
    layer.collection.features.forEach((feature, index) => {
      if (!featureMatchesProfile(feature, profile)) return;
      const properties = { ...(feature.properties || {}) };
      const sourceId = properties[profile.idField];
      outputFeatures.push({
        type: "Feature",
        id: sourceId === undefined || sourceId === null || sourceId === "" ? undefined : String(sourceId),
        properties: { ...properties, __nma_source_layer: layer.name, __nma_source_index: index },
        geometry: feature.geometry,
      });
    });
  });
  if (token !== state.buildToken) return;

  const groups = layers.map((layer) => groupForLayer(layer, state.inventory));
  const missingSidecars = [];
  groups.forEach((group, index) => {
    if (!group) {
      missingSidecars.push(`${layers[index].name}: component group unresolved`);
      return;
    }
    SIDECARS.filter((ext) => !group.components[ext]).forEach((ext) => missingSidecars.push(`${group.name}.${ext}`));
  });
  const crsTexts = groups.filter(Boolean).map((group) => {
    const entry = group.components.prj;
    const bytes = entry ? state.inventory.textByPath.get(canonical(entry.path)) : null;
    return { layer: group.name, wkt: decodeText(bytes) };
  });
  const ids = outputFeatures.map((feature) => feature.properties[profile.idField]);
  const missingIds = ids.filter((value) => value === undefined || value === null || String(value).trim() === "").length;
  const presentIds = ids.filter((value) => value !== undefined && value !== null && String(value).trim() !== "").map(String);
  const uniqueIds = new Set(presentIds);
  const geometryMismatch = outputFeatures.filter((feature) => geometryFamily(feature.geometry && feature.geometry.type) !== profile.geometry).length;
  const vertices = outputFeatures.map((feature) => countVertices(feature.geometry));
  const observedZ = outputFeatures.some((feature) => hasZ(feature.geometry));
  const expectedCountMatch = outputFeatures.length === profile.expectedCount;
  const expectedVerticesMatch = profile.expectedVertices ? equalArray(vertices, profile.expectedVertices) : null;
  const expectedIdsMatch = profile.expectedIds ? equalArray(presentIds, profile.expectedIds) : null;
  const hardGate = layers.length > 0 && outputFeatures.length > 0 && missingSidecars.length === 0 && missingIds === 0 && uniqueIds.size === presentIds.length && geometryMismatch === 0;
  const componentHashes = await selectedComponentHashes(layers, state.inventory, state.archiveBytes);
  if (token !== state.buildToken) return;

  const proposalCore = {
    authority: FROZEN_AUTHORITY,
    archive_sha256: state.archiveHash,
    profile: state.profileId,
    user_intent: byId("intent").value.trim(),
    selected_layers: layers.map((layer) => layer.name),
    filters: { [profile.codeField]: profile.codeValue, ...(profile.nameField ? { [profile.nameField]: profile.nameValue } : {}) },
    feature_ids: presentIds,
    component_hashes: componentHashes,
    output_crs: "EPSG:4326 browser preview",
    production_activation: false,
  };
  const proposalHash = await sha256(new TextEncoder().encode(JSON.stringify(proposalCore)));
  if (token !== state.buildToken) return;

  state.proposal = {
    profile,
    layers,
    collection: { type: "FeatureCollection", features: outputFeatures },
    missingSidecars,
    crsTexts,
    missingIds,
    uniqueIds: uniqueIds.size,
    geometryMismatch,
    vertices,
    observedZ,
    expectedCountMatch,
    expectedVerticesMatch,
    expectedIdsMatch,
    hardGate,
    componentHashes,
    proposalHash,
    proposalCore,
  };
  state.authorized = false;
  renderProposal();
}

function evidenceGroup(title, status, tone, lines, hashes = []) {
  const group = node("section", "evidence-group");
  group.append(node("h4", "", title));
  group.append(node("p", `evidence-status ${tone || ""}`, status));
  const list = node("ul");
  lines.forEach((line) => list.append(node("li", "", line)));
  group.append(list);
  hashes.filter(Boolean).forEach((value) => group.append(node("code", "", value)));
  return group;
}

function renderSourceStrip() {
  const root = byId("source-strip");
  clear(root);
  const values = [
    ["User archive", state.file.name],
    ["Archive SHA-256", state.archiveHash],
    ["Parsed SHP layers", state.collections.length],
    ["Local bytes", formatBytes(state.file.size)],
  ];
  values.forEach(([label, value], index) => {
    const item = node("div", "source-stat");
    item.append(node("span", "", label));
    item.append(node(index === 1 ? "code" : "strong", "", value));
    root.append(item);
  });
}

function qaLines(proposal) {
  const profile = proposal.profile;
  const lines = [
    `feature count：實際 ${proposal.collection.features.length} / frozen contract ${profile.expectedCount} — ${proposal.expectedCountMatch ? "MATCH" : "DIFF"}`,
    `${profile.idField}：missing ${proposal.missingIds} / unique ${proposal.uniqueIds} / total ${proposal.collection.features.length}`,
    `geometry family：${profile.geometry}；mismatch ${proposal.geometryMismatch}`,
    `CRS：${proposal.crsTexts.map((item) => `${item.layer}=${crsSummary(item.wkt)}`).join(" · ") || "PRJ unavailable"} → WGS84 browser preview`,
    `Hausdorff distance：未執行（沒有使用者提供的 reference geometry）`,
  ];
  if (profile.expectedVertices) lines.push(`vertex counts：${proposal.vertices.join("/")} / expected ${profile.expectedVertices.join("/")} — ${proposal.expectedVerticesMatch ? "MATCH" : "DIFF"}`);
  if (profile.expectedIds) lines.push(`accepted ROADSEGID sequence：${proposal.expectedIdsMatch ? "MATCH" : "DIFF"}`);
  if (state.profileId === "build") lines.push(`Z coordinate observed after browser parse：${proposal.observedZ ? "YES" : "NO / parser output 2D"}`);
  return lines;
}

function renderEvidence() {
  const proposal = state.proposal;
  const profile = proposal.profile;
  const root = byId("evidence-detail");
  clear(root);
  const selected = proposal.layers.length ? proposal.layers.map((layer) => `${layer.name} · ${layer.collection.features.length} source features`) : ["沒有符合 profile geometry 的使用者 layer"];
  root.append(evidenceGroup("1 · User SHP intake", proposal.missingSidecars.length ? "INPUT GATE FAILED" : "LOCAL INPUT INVENTORIED", proposal.missingSidecars.length ? "fail" : "", [
    `${state.inventory.entries.length} ZIP entries；${state.inventory.shapefiles.length} Shapefile component groups`,
    ...selected,
    ...(proposal.missingSidecars.length ? proposal.missingSidecars.map((item) => `missing ${item}`) : ["required .shp/.shx/.dbf/.prj complete"]),
  ], [`archive sha256 ${state.archiveHash}`]));
  root.append(evidenceGroup("2 · Agent interpretation", "DETERMINISTIC FROZEN REPLAY", "", [
    `intent：${byId("intent").value.trim()}`,
    `interpreted profile：${state.profileId.toUpperCase()} / ${profile.geometry}`,
    `requested identity field：${profile.idField}`,
  ]));
  root.append(evidenceGroup("3 · GraphRAG / mapping rules", "REVIEWED KNOWLEDGE RETRIEVED", "", [profile.rule, ...profile.nodes.map((item) => `KG node · ${item}`), `authority · nma-v1.0-final ${FROZEN_AUTHORITY.slice(0, 12)}…`]));
  root.append(evidenceGroup("4 · Plan", proposal.hardGate ? "PROPOSABLE" : "BLOCKED", proposal.hardGate ? "" : "fail", [profile.plan, `filter · ${profile.codeField}=${profile.codeValue}${profile.nameField ? ` AND ${profile.nameField}=${profile.nameValue}` : ""}`, `output · ${proposal.collection.features.length} user-source features`]));
  root.append(evidenceGroup("5 · Authorization", state.authorized ? "AUTHORIZED FOR THIS BROWSER SESSION" : "NOT AUTHORIZED", state.authorized ? "" : "warn", [
    state.authorized ? "使用者已核准此 proposal hash 的 browser-local preview。" : "尚未執行；地圖區不含任何 geometry。",
    state.profileId === "build" ? "production activation：HELD / DISABLED" : "production writeback：not available",
  ], [`proposal sha256 ${proposal.proposalHash}`]));
  root.append(evidenceGroup("6 · QA / verification", proposal.expectedCountMatch && proposal.hardGate ? "FROZEN CONTRACT MATCH" : proposal.hardGate ? "EXECUTABLE WITH CONTRACT DIFF" : "HARD GATE FAILED", proposal.hardGate ? (proposal.expectedCountMatch ? "" : "warn") : "fail", qaLines(proposal)));
  root.append(evidenceGroup("7 · Provenance", state.authorized ? "RECEIPT READY" : "PROPOSED RECEIPT", "", [
    `${proposal.componentHashes.length} selected sidecar component hashes`,
    `source layer(s)：${proposal.layers.map((layer) => layer.name).join(" · ") || "none"}`,
    "No SHP, DBF, SHX, PRJ, or CPG bytes are persisted by this page.",
  ], [`proposal/receipt sha256 ${proposal.proposalHash}`, ...proposal.componentHashes.slice(0, 4).map((item) => `${extension(item.path).toUpperCase()} component · ${item.sha256}`)]));
}

function renderPipeline() {
  const proposal = state.proposal;
  const stages = [
    ["Request", "captured", byId("intent").value.trim(), ""],
    ["Agent interpretation", "replayed", `${state.profileId.toUpperCase()} / ${proposal.profile.geometry}`, ""],
    ["GraphRAG / rules", "retrieved", proposal.profile.rule, ""],
    ["Plan", proposal.hardGate ? "proposed" : "blocked", proposal.profile.plan, proposal.hardGate ? "" : "is-warn"],
    ["Authorization", state.authorized ? "authorized" : "pending", state.authorized ? "browser-local scope only" : "requires user action", state.authorized ? "" : "is-pending"],
    ["Execution", state.authorized ? "executed" : "not run", state.authorized ? `${proposal.collection.features.length} user features rendered` : "no geometry rendered", state.authorized ? "" : "is-pending"],
    ["QA / verification", state.authorized ? "reported" : "preflight", qaLines(proposal).join(" · "), state.authorized ? "" : "is-pending"],
    ["Provenance", state.authorized ? "receipt ready" : "proposed", `sha256 ${proposal.proposalHash.slice(0, 12)}…`, state.authorized ? "" : "is-pending"],
  ];
  const root = byId("pipeline");
  clear(root);
  stages.forEach(([title, status, summary, className], index) => {
    const card = node("article", `stage ${className}`.trim());
    card.setAttribute("role", "listitem");
    card.append(node("span", "stage-number", String(index + 1).padStart(2, "0")));
    card.append(node("h4", "", title));
    card.append(node("p", "", summary));
    card.append(node("span", "stage-status", status));
    root.append(card);
  });
}

function resetMapLocked() {
  if (state.map) {
    state.map.remove();
    state.map = null;
  }
  const root = byId("map");
  clear(root);
  const locked = node("div", "map-locked");
  locked.append(node("span", "", "AUTHORIZATION REQUIRED"));
  locked.append(node("p", "", "先檢視提案與 gate，再授權 browser-local execution。"));
  root.append(locked);
  byId("map-heading").textContent = "等待授權";
  byId("map-caption").textContent = "尚未執行；沒有預製 geometry。";
}

function renderProposal() {
  const proposal = state.proposal;
  const profile = proposal.profile;
  byId("workspace").classList.remove("is-empty");
  byId("empty-state").hidden = true;
  byId("workspace-content").hidden = false;
  byId("scenario-domain").textContent = profile.domain;
  byId("scenario-title").textContent = profile.title;
  byId("scenario-subtitle").textContent = profile.subtitle;
  byId("map-kind").textContent = profile.mapKind;
  byId("run-chip").className = "run-chip";
  byId("run-chip").innerHTML = "<span>●</span> PROPOSAL · NOT AUTHORIZED";
  byId("evidence-badge").className = "proposal-badge";
  byId("evidence-badge").textContent = proposal.hardGate ? "PROPOSED" : "BLOCKED";
  byId("authorization-title").textContent = proposal.hardGate ? "提案尚未授權" : "輸入 gate 未通過";
  byId("authorization-summary").textContent = proposal.hardGate
    ? `將只在瀏覽器 render ${proposal.collection.features.length} 個使用者來源 feature；不寫回來源或 production。`
    : "缺少合格圖層、必要 sidecars、來源 ID 或 geometry；禁止執行。";
  byId("authorize-button").disabled = !proposal.hardGate;
  byId("authorize-button").textContent = state.profileId === "build" ? "授權 browser preview（production held）" : "授權 browser-local execution";
  renderSourceStrip();
  renderEvidence();
  renderPipeline();
  resetMapLocked();
  byId("workspace").scrollIntoView({ behavior: "smooth", block: "start" });
}

function baseStyle() {
  return {
    version: 8,
    glyphs: `${asset("assets/")}{fontstack}-{range}.pbf`,
    sources: {},
    layers: [{ id: "background", type: "background", paint: { "background-color": "#e7eee8" } }],
  };
}

function collectionBounds(collection) {
  const bounds = new maplibregl.LngLatBounds();
  const visit = (coordinates) => {
    if (!Array.isArray(coordinates)) return;
    if (typeof coordinates[0] === "number" && Number.isFinite(coordinates[0]) && Number.isFinite(coordinates[1])) bounds.extend([coordinates[0], coordinates[1]]);
    else coordinates.forEach(visit);
  };
  collection.features.forEach((feature) => feature.geometry && visit(feature.geometry.coordinates));
  return bounds;
}

function addSchoolLayers(map, profile) {
  map.addLayer({ id: "school-halo", type: "circle", source: "user-result", paint: { "circle-radius": 8, "circle-color": "#ffffff", "circle-stroke-color": "#176bc1", "circle-stroke-width": 2 } });
  map.addLayer({ id: "school-core", type: "circle", source: "user-result", paint: { "circle-radius": 3.5, "circle-color": "#176bc1" } });
  map.addLayer({
    id: "school-label", type: "symbol", source: "user-result",
    layout: { "text-field": ["coalesce", ["get", profile.labelField], ["get", profile.idField]], "text-font": ["NotoSansRegular"], "text-size": 11, "text-offset": [0, 1.45], "text-optional": true },
    paint: { "text-color": "#124b82", "text-halo-color": "#f8fbf7", "text-halo-width": 1.5 },
  });
}

function addRoadLayers(map, profile) {
  map.addLayer({ id: "road-casing", type: "line", source: "user-result", paint: { "line-color": "#fffaf3", "line-width": 12 } });
  map.addLayer({ id: "road-line", type: "line", source: "user-result", paint: { "line-color": "#d65c36", "line-width": 6 } });
  map.addLayer({
    id: "road-label", type: "symbol", source: "user-result",
    layout: { "symbol-placement": "line", "symbol-spacing": 130, "text-field": ["get", profile.labelField], "text-font": ["NotoSansRegular"], "text-size": 15, "text-keep-upright": true },
    paint: { "text-color": "#3e2419", "text-halo-color": "#fffaf3", "text-halo-width": 2 },
  });
}

function addBuildLayers(map) {
  const size = 16;
  const pixels = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      if ((x + y) % 9 < 2) {
        const offset = (y * size + x) * 4;
        pixels[offset] = 35; pixels[offset + 1] = 31; pixels[offset + 2] = 27; pixels[offset + 3] = 190;
      }
    }
  }
  map.addImage("build-hatch", { width: size, height: size, data: pixels });
  map.addLayer({ id: "build-fill", type: "fill", source: "user-result", paint: { "fill-color": "#f4d6a8", "fill-opacity": .55 } });
  map.addLayer({ id: "build-hatch", type: "fill", source: "user-result", paint: { "fill-pattern": "build-hatch" } });
  map.addLayer({ id: "build-boundary", type: "line", source: "user-result", paint: { "line-color": "#16130f", "line-width": 1.7 } });
}

function renderExecutedMap() {
  const proposal = state.proposal;
  const root = byId("map");
  clear(root);
  const map = new maplibregl.Map({ container: "map", style: baseStyle(), center: [121, 24.78], zoom: 10, attributionControl: false });
  state.map = map;
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.on("load", () => {
    map.addSource("user-result", { type: "geojson", data: proposal.collection });
    if (state.profileId === "school") addSchoolLayers(map, proposal.profile);
    if (state.profileId === "road") addRoadLayers(map, proposal.profile);
    if (state.profileId === "build") addBuildLayers(map);
    const bounds = collectionBounds(proposal.collection);
    if (!bounds.isEmpty()) map.fitBounds(bounds, { padding: 55, duration: 0, maxZoom: state.profileId === "build" ? 16 : 15 });
  });
  byId("map-heading").textContent = "使用者 Shapefile 執行結果";
  byId("map-caption").textContent = `${proposal.collection.features.length} 個 user-source features；shpjs 在瀏覽器轉為 WGS84，MapLibre 即時呈現。沒有外部資料 substitution。`;
}

async function analyzeFile(file) {
  if (!file || !/\.zip$/i.test(file.name)) throw new Error("請選擇 .zip Shapefile archive。");
  if (file.size > MAX_ARCHIVE_BYTES) throw new Error(`ZIP 為 ${formatBytes(file.size)}，超過 ${formatBytes(MAX_ARCHIVE_BYTES)} 上限。`);
  if (!window.fflate || !window.shp || !window.maplibregl) throw new Error("必要的本地 browser libraries 未載入。");
  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  byId("form-status").textContent = "正在做 ZIP safety gate、SHA-256 與 Shapefile/CRS parsing…";
  const inventory = preflightArchive(bytes);
  const [archiveHash, parsed] = await Promise.all([sha256(bytes), window.shp(buffer)]);
  const collections = normalizeCollections(parsed, inventory);
  if (!collections.length) throw new Error("Shapefile parser 沒有產生可用的 GeoJSON layer。");
  state.file = file;
  state.archiveBytes = bytes;
  state.archiveHash = archiveHash;
  state.inventory = inventory;
  state.collections = collections;
  state.buildToken += 1;
  byId("form-status").textContent = `本地解析完成：${collections.length} 個 SHP layers。正在建立 ${state.profileId.toUpperCase()} proposal…`;
  await createProposal(state.buildToken);
  byId("form-status").textContent = `完成：所有資料仍在此瀏覽器；archive SHA-256 ${archiveHash.slice(0, 16)}…`;
}

function setBusy(busy) {
  byId("analyze-button").disabled = busy;
  byId("analyze-button").textContent = busy ? "本地分析中…" : "分析我的 Shapefile";
}

function showFile(file) {
  byId("dropzone").classList.toggle("has-file", Boolean(file));
  byId("file-title").textContent = file ? file.name : "選擇或拖放 ZIP";
  byId("file-subtitle").textContent = file ? `${formatBytes(file.size)} · 尚未傳送；按「分析」在瀏覽器內解析。` : "包含 .shp + .shx + .dbf + .prj；檔案只在此瀏覽器記憶體內解析。";
}

document.querySelectorAll(".scenario-tab").forEach((button) => {
  button.addEventListener("click", async () => {
    const profileId = button.dataset.profile;
    if (!PROFILES[profileId] || profileId === state.profileId) return;
    state.profileId = profileId;
    document.querySelectorAll(".scenario-tab").forEach((tab) => tab.setAttribute("aria-selected", String(tab === button)));
    byId("intent").value = PROFILES[profileId].intent;
    if (state.collections) {
      state.buildToken += 1;
      byId("form-status").textContent = `使用相同的 user SHP 建立 ${profileId.toUpperCase()} proposal…`;
      try {
        await createProposal(state.buildToken);
        byId("form-status").textContent = `${profileId.toUpperCase()} proposal 已從同一份 user SHP 建立。`;
      } catch (error) {
        byId("form-status").classList.add("is-error");
        byId("form-status").textContent = error.message;
      }
    }
  });
});

byId("shp-file").addEventListener("change", (event) => {
  showFile(event.target.files && event.target.files[0]);
});

const dropzone = byId("dropzone");
["dragenter", "dragover"].forEach((type) => dropzone.addEventListener(type, (event) => { event.preventDefault(); dropzone.classList.add("is-dragging"); }));
["dragleave", "drop"].forEach((type) => dropzone.addEventListener(type, (event) => { event.preventDefault(); dropzone.classList.remove("is-dragging"); }));
dropzone.addEventListener("drop", (event) => {
  const file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
  if (!file) return;
  const transfer = new DataTransfer();
  transfer.items.add(file);
  byId("shp-file").files = transfer.files;
  showFile(file);
});

byId("input-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = byId("shp-file").files && byId("shp-file").files[0];
  byId("form-status").classList.remove("is-error");
  setBusy(true);
  try {
    await analyzeFile(file);
  } catch (error) {
    byId("form-status").classList.add("is-error");
    byId("form-status").textContent = `分析失敗：${error.message}`;
  } finally {
    setBusy(false);
  }
});

byId("authorize-button").addEventListener("click", () => {
  const proposal = state.proposal;
  if (!proposal || !proposal.hardGate) return;
  state.authorized = true;
  byId("run-chip").className = "run-chip is-authorized";
  byId("run-chip").innerHTML = "<span>●</span> AUTHORIZED · BROWSER EXECUTED";
  byId("evidence-badge").className = "proposal-badge is-pass";
  byId("evidence-badge").textContent = proposal.expectedCountMatch ? "CONTRACT MATCH" : "EXECUTED · DIFF REPORTED";
  byId("authorization-title").textContent = "已授權此 browser session";
  byId("authorization-summary").textContent = state.profileId === "build"
    ? "Boundary/hatch preview 已執行；production activation 仍為 HELD / DISABLED。"
    : "只 render proposal hash 對應的使用者 features；沒有來源或 production writeback。";
  byId("authorize-button").disabled = true;
  byId("authorize-button").textContent = "已授權並執行";
  renderExecutedMap();
  renderEvidence();
  renderPipeline();
});

showFile(null);
