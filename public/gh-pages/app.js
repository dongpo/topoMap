"use strict";

const state = { data: null, current: null, map: null };
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

async function readJson(path) {
  const response = await fetch(asset(path), { cache: "no-store" });
  if (!response.ok) throw new Error(`Unable to load ${path}`);
  return response.json();
}

async function boot() {
  try {
    const [data, release] = await Promise.all([readJson("data/scenarios.json"), readJson("release.json")]);
    state.data = data;
    renderTabs();
    selectScenario(data.scenarios[0].id, false);
    document.querySelector(".integrity").classList.add("ready");
    byId("integrity-text").textContent = `${release.files.length} artifact files · frozen authority verified`;
  } catch (error) {
    byId("integrity-text").textContent = "Replay artifact unavailable";
    byId("request-status").textContent = error.message;
  }
}

function renderTabs() {
  const root = byId("scenario-tabs");
  clear(root);
  state.data.scenarios.forEach((scenario, index) => {
    const button = node("button", "scenario-tab");
    button.type = "button";
    button.role = "tab";
    button.id = `tab-${scenario.id}`;
    button.setAttribute("aria-controls", "workspace");
    button.setAttribute("aria-selected", "false");
    button.append(node("span", "tab-number", `0${index + 1} / ${scenario.domain.toUpperCase()}`));
    button.append(node("span", "arrow", "↗"));
    button.append(node("strong", "", scenario.title));
    button.append(node("small", "", scenario.subtitle));
    button.addEventListener("click", () => selectScenario(scenario.id, true));
    root.append(button);
  });
}

function selectScenario(id, scroll) {
  const scenario = state.data.scenarios.find((item) => item.id === id);
  if (!scenario) return;
  state.current = scenario;
  document.querySelectorAll(".scenario-tab").forEach((tab) => {
    tab.setAttribute("aria-selected", String(tab.id === `tab-${id}`));
  });
  byId("request-input").value = scenario.request;
  byId("request-status").textContent = "";
  byId("scenario-domain").textContent = scenario.domain;
  byId("scenario-title").textContent = scenario.title;
  byId("scenario-subtitle").textContent = scenario.subtitle;
  byId("map-kind").textContent = scenario.map.type.toUpperCase();
  byId("map-caption").textContent = scenario.map.caption;
  renderEvidence(scenario);
  renderPipeline(scenario);
  renderMap(scenario);
  if (scroll) byId("workspace").scrollIntoView({ behavior: "smooth", block: "start" });
}

function evidenceGroup(title, status, body, hashes = []) {
  const group = node("section", "evidence-group");
  group.append(node("h4", "", title));
  if (status) group.append(node("p", "evidence-status", status));
  if (Array.isArray(body)) {
    const list = node("ul");
    body.forEach((item) => list.append(node("li", "", item)));
    group.append(list);
  } else if (body) {
    group.append(node("p", "", body));
  }
  hashes.filter(Boolean).forEach((value) => group.append(node("code", "", value)));
  return group;
}

function renderEvidence(scenario) {
  const root = byId("evidence-detail");
  clear(root);
  root.append(evidenceGroup("Agent interpretation", scenario.interpretation.status, scenario.interpretation.summary));
  const knowledgeLines = [scenario.knowledge.mapping_rule, scenario.knowledge.boundary];
  scenario.knowledge.nodes.forEach((item) => knowledgeLines.push(`${item.id} · ${item.type}`));
  root.append(evidenceGroup("GraphRAG / mapping rules", scenario.knowledge.status, knowledgeLines));
  root.append(evidenceGroup("Accepted authorization", scenario.authorization.status, scenario.authorization.scope, [scenario.authorization.id, scenario.authorization.sha256]));
  root.append(evidenceGroup("QA / verification", scenario.qa.status, scenario.qa.checks, [scenario.qa.sha256]));
  root.append(evidenceGroup("Receipt / provenance", scenario.provenance.status, "Frozen identities and source commitments remain linked to this replay.", [scenario.provenance.receipt_sha256, scenario.provenance.sha256, scenario.provenance.fixture_sha256]));
}

function renderPipeline(scenario) {
  const stages = [
    ["Request", "accepted", scenario.request],
    ["Agent interpretation", scenario.interpretation.status, scenario.interpretation.summary],
    ["GraphRAG / rules", scenario.knowledge.status, scenario.knowledge.mapping_rule],
    ["Plan", scenario.plan.status, scenario.plan.action],
    ["Authorization", scenario.authorization.status, scenario.authorization.scope],
    ["Execution replay", scenario.execution.status, scenario.execution.mode],
    ["QA / verification", scenario.qa.status, scenario.qa.checks.join(" · ")],
    ["Provenance", scenario.provenance.status, `receipt ${scenario.provenance.receipt_sha256.slice(0, 12)}…`],
  ];
  const root = byId("pipeline");
  clear(root);
  stages.forEach(([title, status, summary], index) => {
    const card = node("article", "stage");
    card.setAttribute("role", "listitem");
    card.append(node("span", "stage-number", String(index + 1).padStart(2, "0")));
    card.append(node("h4", "", title));
    card.append(node("p", "", summary));
    card.append(node("span", "stage-status", status));
    root.append(card);
  });
}

function baseStyle() {
  return {
    version: 8,
    glyphs: `${asset("assets/")}{fontstack}-{range}.pbf`,
    sources: {},
    layers: [
      { id: "background", type: "background", paint: { "background-color": "#e7eee8" } },
      { id: "grid-minor", type: "background", paint: { "background-color": "#e7eee8" } },
    ],
  };
}

function boundsFor(collection) {
  const bounds = new maplibregl.LngLatBounds();
  function visit(coordinates) {
    if (typeof coordinates[0] === "number") bounds.extend(coordinates);
    else coordinates.forEach(visit);
  }
  collection.features.forEach((feature) => visit(feature.geometry.coordinates));
  return bounds;
}

function renderMap(scenario) {
  if (state.map) state.map.remove();
  clear(byId("map"));
  const map = new maplibregl.Map({
    container: "map",
    style: baseStyle(),
    center: [121, 24.78],
    zoom: 10,
    attributionControl: false,
  });
  state.map = map;
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.on("load", () => {
    map.addSource("accepted-result", { type: "geojson", data: scenario.map.geojson });
    if (scenario.map.type === "school") renderSchool(map);
    if (scenario.map.type === "road") renderRoad(map);
    if (scenario.map.type === "build") renderBuild(map, scenario.map.geojson);
    map.fitBounds(boundsFor(scenario.map.geojson), { padding: 70, duration: 0, maxZoom: scenario.map.type === "build" ? 9 : 14 });
  });
}

function renderSchool(map) {
  const image = new Image();
  image.onload = () => {
    map.addImage("school-blue", image, { sdf: true });
    map.addLayer({
      id: "school-points",
      type: "symbol",
      source: "accepted-result",
      layout: {
        "icon-image": "school-blue",
        "icon-size": .42,
        "icon-allow-overlap": true,
        "text-field": ["get", "display_label"],
        "text-font": ["NotoSansRegular"],
        "text-size": 11,
        "text-offset": [0, 1.55],
        "text-optional": true,
      },
      paint: { "icon-color": "#176bc1", "text-color": "#124b82", "text-halo-color": "#f8fbf7", "text-halo-width": 1.5 },
    });
  };
  image.src = asset("assets/school-blue.svg");
}

function renderRoad(map) {
  map.addLayer({ id: "road-casing", type: "line", source: "accepted-result", paint: { "line-color": "#fffaf3", "line-width": 13 } });
  map.addLayer({ id: "road-line", type: "line", source: "accepted-result", paint: { "line-color": "#d65c36", "line-width": 7 } });
  map.addLayer({
    id: "road-name",
    type: "symbol",
    source: "accepted-result",
    layout: { "symbol-placement": "line", "symbol-spacing": 140, "text-field": "中山街", "text-font": ["NotoSansRegular"], "text-size": 15, "text-keep-upright": true },
    paint: { "text-color": "#3e2419", "text-halo-color": "#fffaf3", "text-halo-width": 2 },
  });
  map.on("click", "road-line", (event) => {
    const feature = event.features[0];
    new maplibregl.Popup().setLngLat(event.lngLat).setText(`${feature.properties.ROADSEGID} · ${feature.properties.vertex_count} vertices`).addTo(map);
  });
  map.on("mouseenter", "road-line", () => { map.getCanvas().style.cursor = "pointer"; });
  map.on("mouseleave", "road-line", () => { map.getCanvas().style.cursor = ""; });
}

function renderBuild(map, collection) {
  const ring = collection.features[0].geometry.coordinates[0];
  const size = 16;
  const pixels = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      if ((x + y) % 9 < 2) {
        const offset = (y * size + x) * 4;
        pixels[offset] = 35;
        pixels[offset + 1] = 31;
        pixels[offset + 2] = 27;
        pixels[offset + 3] = 210;
      }
    }
  }
  map.addImage("build-hatch", { width: size, height: size, data: pixels });
  map.addLayer({ id: "build-fill", type: "fill", source: "accepted-result", paint: { "fill-color": "#f4d6a8", "fill-opacity": .68 } });
  map.addLayer({ id: "hatch", type: "fill", source: "accepted-result", paint: { "fill-pattern": "build-hatch" } });
  map.addLayer({ id: "build-boundary", type: "line", source: "accepted-result", paint: { "line-color": "#111111", "line-width": 3 } });
  const polygon = ring.map(([x, y]) => `${x * 100}% ${100 - y * 100}%`).join(",");
  map.once("idle", () => {
    const canvas = map.getCanvas();
    canvas.dataset.normalizedPolygonVertices = String(ring.length - 1);
    canvas.parentElement.style.setProperty("--accepted-polygon", `polygon(${polygon})`);
  });
}

byId("request-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const request = byId("request-input").value.trim().toLocaleLowerCase();
  const blocked = /(?:https?:|file:|upload|path|secret|token|password|neo4j|openai|activate|production|writeback|\/|\\)/i;
  if (!request || blocked.test(request)) {
    byId("request-status").textContent = "Request rejected: choose one bounded replay without URLs, paths, credentials, or production actions.";
    return;
  }
  const matches = state.data.scenarios.filter((scenario) => {
    const terms = scenario.id === "school" ? ["school", "學校", "9920103"] : scenario.id === "road" ? ["road", "道路", "中山街", "k14", "9420400"] : ["build", "building", "建物", "建築", "9310100"];
    return terms.some((term) => request.includes(term));
  });
  if (matches.length !== 1) {
    byId("request-status").textContent = "Request rejected: resolve exactly one of School, ROAD, or BUILD.";
    return;
  }
  selectScenario(matches[0].id, true);
  byId("request-status").textContent = "Resolved locally to the accepted frozen replay.";
});

boot();
