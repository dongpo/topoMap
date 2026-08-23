"use strict";

const BASE = "/nma/";
const api = `${BASE}api/v1`;
let map = null;

const byId = (id) => document.getElementById(id);
const clear = (node) => { while (node.firstChild) node.removeChild(node.firstChild); };
const element = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = String(text);
  return node;
};

async function readJson(url, options) {
  const response = await fetch(url, { credentials: "same-origin", ...options });
  const value = await response.json();
  if (!response.ok) throw new Error(value.error?.message || "The controlled request failed.");
  return value;
}

async function boot() {
  try {
    const health = await readJson(`${api}/health/ready`);
    byId("service-status").textContent = health.status === "ready" ? "Integrity verified · ready" : "Not ready";
    byId("status-dot").classList.toggle("ready", health.status === "ready");
    const catalog = await readJson(`${api}/scenarios`);
    renderScenarios(catalog.scenarios);
  } catch (error) {
    byId("service-status").textContent = "Service unavailable";
    byId("message").textContent = error.message;
  }
}

function renderScenarios(scenarios) {
  const root = byId("scenarios");
  clear(root);
  scenarios.forEach((scenario) => {
    const button = element("button", "scenario");
    button.type = "button";
    button.append(element("span", "domain", scenario.domain));
    button.append(element("span", "code", scenario.scenario_id));
    button.append(element("strong", "", scenario.title));
    button.append(element("small", "", scenario.mode));
    button.addEventListener("click", () => submitRun({ scenario_id: scenario.scenario_id, input_type: "guided" }));
    root.append(button);
  });
}

byId("language-form").addEventListener("submit", (event) => {
  event.preventDefault();
  submitRun({ request: byId("request").value, input_type: "bounded-natural-language" });
});

async function submitRun(payload) {
  const message = byId("message");
  message.textContent = "Running the accepted controlled path…";
  document.querySelectorAll("button").forEach((button) => { button.disabled = true; });
  try {
    const created = await readJson(`${api}/runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const [result, evidence, mapResult] = await Promise.all([
      readJson(created.result_url),
      readJson(`${created.result_url}/evidence`),
      readJson(`${created.result_url}/map`),
    ]);
    renderResult(result, evidence, mapResult);
    message.textContent = "";
    byId("result").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    message.textContent = error.message;
  } finally {
    document.querySelectorAll("button").forEach((button) => { button.disabled = false; });
  }
}

function renderResult(result, evidence, mapResult) {
  byId("result").classList.remove("hidden");
  byId("result-summary").textContent = `${result.domain} · ${result.intent}`;
  const lifecycle = byId("lifecycle");
  clear(lifecycle);
  const stages = [
    ["Plan", result.plan.status, `${result.plan.identity} — ${result.plan.action}`],
    ["Authority", result.authorization.status, `${result.authorization.identity} — ${result.authorization.scope}`],
    ["Execution", result.execution.status, result.execution.identity],
    ["Verification", result.verification.status, result.verification.identity],
    ["Provenance", result.provenance.status, result.provenance.identity],
  ];
  stages.forEach(([name, status, detail]) => {
    const card = element("article", "stage");
    card.append(element("span", "stage-name", name));
    card.append(element("strong", "", status));
    card.append(element("p", "", detail));
    lifecycle.append(card);
  });
  renderEvidence(evidence);
  renderMap(mapResult);
}

function renderEvidence(evidence) {
  const root = byId("evidence");
  clear(root);
  const graph = evidence.graphrag;
  const intro = element("div", "evidence-item");
  intro.append(element("code", "", graph.mode));
  intro.append(element("p", "", graph.boundary));
  root.append(intro);
  (graph.nodes || []).forEach((node) => {
    const item = element("div", "evidence-item");
    item.append(element("code", "", node.id));
    const summary = Object.entries(node.summary || {}).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : value}`).join(" · ");
    item.append(element("p", "", `${node.type}${summary ? ` — ${summary}` : ""}`));
    root.append(item);
  });
  if (evidence.mapping_rules) {
    const item = element("div", "evidence-item");
    item.append(element("code", "", `mapping rule ${evidence.mapping_rules.feature_code}`));
    item.append(element("p", "", evidence.mapping_rules.portrayal));
    root.append(item);
  }
  const link = element("div", "evidence-item");
  link.append(element("code", "", `plan ${evidence.plan_link.plan_id}`));
  link.append(element("p", "", `Uses ${evidence.plan_link.uses_rule_ids.join(", ")}`));
  root.append(link);
}

function boundsFor(collection) {
  const bounds = new maplibregl.LngLatBounds();
  const visit = (coordinates) => {
    if (typeof coordinates[0] === "number") bounds.extend(coordinates);
    else coordinates.forEach(visit);
  };
  collection.features.forEach((feature) => visit(feature.geometry.coordinates));
  return bounds;
}

function baseStyle() {
  return { version: 8, glyphs: `${location.origin}${BASE}assets/{fontstack}-{range}.pbf`, sources: {}, layers: [{ id: "background", type: "background", paint: { "background-color": "#e8e4da" } }] };
}

function renderMap(result) {
  if (map) map.remove();
  clear(byId("map"));
  byId("map-kind").textContent = result.type.toUpperCase();
  byId("map-caption").textContent = result.type === "build" ? "Normalized public demo geometry · production activation disabled/unavailable" : result.type === "road" ? "Exact accepted 4/3/4-vertex derivative · line-following 中山街" : "Controlled 15-point result · official blue School symbol and labels";
  map = new maplibregl.Map({ container: "map", style: baseStyle(), center: [121, 24], zoom: 6, attributionControl: false });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.on("load", () => {
    map.addSource("result", { type: "geojson", data: result.geojson });
    if (result.type === "school") renderSchool(result);
    if (result.type === "road") renderRoad(result);
    if (result.type === "build") renderBuild(result);
    map.fitBounds(boundsFor(result.geojson), { padding: 55, maxZoom: result.type === "build" ? 8 : 16, duration: 0 });
  });
}

function renderSchool(result) {
  const image = new Image();
  image.onload = () => {
    map.addImage("school-symbol", image, { sdf: true });
    map.addLayer({ id: "school", type: "symbol", source: "result", layout: { "icon-image": "school-symbol", "icon-size": .75, "icon-allow-overlap": false, "text-field": ["to-string", ["get", "MARKNAME1"]], "text-font": ["NotoSansRegular"], "text-size": 12, "text-offset": [0, 1.5], "text-optional": true }, paint: { "icon-color": "#1565c0", "text-color": "#0b4d91", "text-halo-color": "#fffdf8", "text-halo-width": 1.5 } });
  };
  image.src = result.image;
}

function renderRoad(result) {
  map.addLayer({ id: "road-casing", type: "line", source: "result", paint: { "line-color": "#fffdf8", "line-width": 10 } });
  map.addLayer({ id: "road", type: "line", source: "result", paint: { "line-color": "#b84a30", "line-width": 6 } });
  map.addLayer({ id: "road-label", type: "symbol", source: "result", layout: { "symbol-placement": "line", "text-field": result.label, "text-font": ["NotoSansRegular"], "text-size": 14, "text-keep-upright": true }, paint: { "text-color": "#5c1e14", "text-halo-color": "#fffdf8", "text-halo-width": 2 } });
}

function renderBuild() {
  const canvas = document.createElement("canvas");
  canvas.width = 12; canvas.height = 12;
  const context = canvas.getContext("2d");
  context.clearRect(0, 0, 12, 12); context.strokeStyle = "#111"; context.lineWidth = 1;
  context.beginPath(); context.moveTo(-2, 12); context.lineTo(12, -2); context.moveTo(4, 14); context.lineTo(14, 4); context.stroke();
  map.addImage("build-hatch", context.getImageData(0, 0, 12, 12), { pixelRatio: 1 });
  map.addLayer({ id: "build-fill", type: "fill", source: "result", paint: { "fill-pattern": "build-hatch", "fill-opacity": .72 } });
  map.addLayer({ id: "build-boundary", type: "line", source: "result", paint: { "line-color": "#111", "line-width": 2 } });
}

boot();
