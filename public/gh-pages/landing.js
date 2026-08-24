"use strict";

const status = document.getElementById("knowledge-status");
const statusText = status.querySelector("span");
const knowledgeUrl = new URL("data/nma-runtime-knowledge-v0.4.json", document.baseURI);

fetch(knowledgeUrl, {cache: "no-store"})
  .then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then((knowledge) => {
    if (knowledge?.source?.graph_id !== "nma-canonical-graph-v0.4") throw new Error("graph identity mismatch");
    status.classList.add("is-ready");
    statusText.textContent = `Canonical KG ready · ${knowledge.statistics.nodes} nodes`;
  })
  .catch((error) => {
    status.classList.add("is-error");
    statusText.textContent = "Canonical KG unavailable · 工作已停用";
    status.title = String(error);
  });
