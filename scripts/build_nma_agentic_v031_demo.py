#!/usr/bin/env python3
"""Build the v0.31 runtime-spine Demo while preserving v0.4."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "nmaAgentDemoV04.html"
TARGET = ROOT / "nmaAgentDemoV031.html"
WORKER_SOURCE = ROOT / "nmaDemoWorkerV04.js"
WORKER_TARGET = ROOT / "nmaDemoWorkerV031.js"


RUNTIME_CSS = """
    .runtime-spine{display:grid;grid-template-columns:repeat(4,minmax(115px,1fr));gap:6px;margin:9px 0}.runtime-stage{position:relative;border:1px solid var(--line);border-top:4px solid var(--green);border-radius:8px;padding:8px;background:#fff;min-width:0}.runtime-stage+ .runtime-stage:before{content:"→";position:absolute;left:-10px;top:38%;color:var(--green);font-weight:900}.runtime-stage small,.runtime-stage strong{display:block}.runtime-stage small{color:#60716b}.runtime-stage code{overflow-wrap:anywhere}.backend-live{color:var(--green);background:#e7f1eb}.backend-fallback{color:var(--warn);background:#fff0d5}.citation-item.used{border-left-color:var(--green);background:#edf8f1}.graph-edge-list{display:grid;gap:4px;margin:7px 0}.graph-edge{font:11px/1.4 ui-monospace,monospace;padding:5px 7px;border-radius:6px;background:#edf3ef;overflow-wrap:anywhere}.runtime-boundary{margin-top:9px;padding:8px;border:1px solid #b9cada;border-radius:8px;background:#f6f9fc;font-size:.73rem}@media(max-width:1100px){.runtime-spine{grid-template-columns:1fr 1fr}}@media(max-width:600px){.runtime-spine{grid-template-columns:1fr}.runtime-stage+ .runtime-stage:before{content:"↓";left:50%;top:-13px}}
"""


RUNTIME_JS = r'''
function renderAgenticGrounding(grounding){
  if(!grounding)return;
  const pkg=grounding.evidence_package||{},answer=grounding.answer||{},trace=grounding.trace||{},runtime=grounding.runtime_contract||{};
  if(runtime.schema!=="nma.runtime-baseline/0.32")throw new Error("missing v0.32 runtime baseline contract");
  const resolution=runtime.resolution||{},graphRuntime=runtime.graph||{},backend=graphRuntime.backend||{},validation=runtime.answer_validation||{},safety=runtime.safety||{};
  const isLive=backend.active_backend==="live-neo4j"&&backend.fallback_used===false&&backend.graph_identity_verified===true;
  const backendClass=isLive?"backend-live":"backend-fallback";
  const events=(trace.events||[]).map(event=>`<div class="trace-step"><strong>${escapeAgentHtml(event.stage)} · ${escapeAgentHtml(event.status)}</strong><small>${escapeAgentHtml(event.detail)}</small>${event.latency_ms!==undefined?`<small>${escapeAgentHtml(event.latency_ms)} ms</small>`:""}</div>`).join("");
  document.querySelector("#agent-trace").innerHTML=`<h3>Agent trace · ${escapeAgentHtml(answer.status)}</h3><div class="graph-meta"><span class="badge ${backendClass}">${escapeAgentHtml(backend.active_backend)}</span><span class="badge">${backend.graph_identity_verified?"graph identity verified":"graph identity not verified"}</span><span class="badge">${escapeAgentHtml(resolution.mode)}</span></div><div class="trace-grid">${events}</div>`;
  const usedNodeIds=new Set(validation.evidence_node_ids_used||[]),usedCitationIds=new Set(validation.citation_ids_used||[]);
  const nodes=(pkg.evidence_nodes||[]).slice(0,16).map(node=>`<span class="evidence-node"><strong>${escapeAgentHtml(node.type)}</strong><br>${escapeAgentHtml(node.id)}${usedNodeIds.has(node.id)?'<br><small>used by answer</small>':""}</span>`).join("");
  const edges=(pkg.graph_paths?.edges||[]).slice(0,10).map(edge=>`<div class="graph-edge">${escapeAgentHtml(edge.source)} → <strong>${escapeAgentHtml(edge.type)}</strong> → ${escapeAgentHtml(edge.target)}</div>`).join("");
  const citations=(pkg.citations||[]).slice(0,10).map(citation=>`<div class="citation-item ${usedCitationIds.has(citation.citation_id)?"used":""}"><strong>${escapeAgentHtml(citation.filename||citation.document_id||"Unresolved document")}</strong> · page ${escapeAgentHtml(citation.page??"?")}<br><code>${escapeAgentHtml(citation.citation_id)}</code>${usedCitationIds.has(citation.citation_id)?" · used by answer":" · available evidence"}</div>`).join("");
  const selected=(resolution.selected_node_ids||[]).map(id=>`<code>${escapeAgentHtml(id)}</code>`).join(" · ")||"none";
  const runtimeSpine=`<div class="runtime-spine" aria-label="Verified Agent runtime spine"><div class="runtime-stage"><small>1 · Resolve</small><strong>${escapeAgentHtml(resolution.mode)}</strong><small>${selected}</small></div><div class="runtime-stage"><small>2 · Traverse</small><strong>${escapeAgentHtml(backend.active_backend)}</strong><small>${escapeAgentHtml(backend.neo4j_database||backend.graph_revision||"no database")}</small></div><div class="runtime-stage"><small>3 · Evidence</small><strong>${escapeAgentHtml(graphRuntime.evidence_node_count)} nodes · ${escapeAgentHtml(graphRuntime.citation_count)} citations</strong><small>typed graph expansion</small></div><div class="runtime-stage"><small>4 · Answer</small><strong>${escapeAgentHtml(validation.status)}</strong><small>${escapeAgentHtml(validation.citation_ids_used?.length||0)} citations used</small></div></div>`;
  document.querySelector("#knowledge-graph").innerHTML=`<h2><span>Canonical GraphRAG result</span><span class="badge ${backendClass}">${isLive?"live Neo4j verified":"fallback visible"}</span></h2>${runtimeSpine}<div class="governance-note"><strong>LLM answer:</strong> ${escapeAgentHtml(answer.answer)}<br><strong>Selected canonical entities:</strong> ${selected}</div><h3>Bounded graph evidence</h3><div class="evidence-node-list">${nodes||'<span class="muted">No reviewed nodes retrieved.</span>'}</div><h3>Typed graph relations</h3><div class="graph-edge-list">${edges||'<div class="result-empty">No relation path was returned.</div>'}</div><h3>Source citations</h3><div class="citation-list">${citations||'<div class="result-empty">No source citation; the Agent must abstain or ask for clarification.</div>'}</div><div class="runtime-boundary"><strong>Runtime boundary</strong> · ${escapeAgentHtml(backend.graph_revision)} · graph identity ${backend.graph_identity_verified?"verified":"not verified"} · fallback ${escapeAgentHtml(backend.fallback_used)} · typed tool ${safety.typed_tool_only?"only":"not verified"} · arbitrary Cypher disabled · no automatic acceptance, execution, or map mutation.</div>`;
}
function renderAgenticEvidenceSummary(grounding){
  if(!grounding)return;
  const pkg=grounding.evidence_package||{},answer=grounding.answer||{},runtime=grounding.runtime_contract||{},graph=runtime.graph||{},backend=graph.backend||{},validation=runtime.answer_validation||{};
  const answered=answer.status==="answered",statusClass=answered?"selected":"abstain",usedCitations=validation.citation_ids_used||[],selected=runtime.resolution?.selected_node_ids||[];
  document.querySelector("#answer").innerHTML=`<span class="status ${statusClass}">${escapeAgentHtml(answer.status||"unknown")}</span><div class="value">${escapeAgentHtml(answer.answer||"No grounded answer was produced.")}</div><p>GraphRAG result: <code>${escapeAgentHtml(backend.active_backend||"unavailable")}</code> · validation <code>${escapeAgentHtml(validation.status||"not-run")}</code> · no automatic portrayal or map action.</p>`;
  document.querySelector("#evidence").innerHTML=`<dl class="facts"><dt>Schema</dt><dd>${escapeAgentHtml(runtime.schema||"nma.runtime-baseline/0.32")}</dd><dt>Graph</dt><dd>${escapeAgentHtml(backend.active_backend||"unavailable")} · identity ${backend.graph_identity_verified?"verified":"not verified"}</dd><dt>Resolved</dt><dd>${escapeAgentHtml(selected.length)} canonical entities</dd><dt>Evidence</dt><dd>${escapeAgentHtml(graph.evidence_node_count??(pkg.evidence_nodes||[]).length)} nodes</dd><dt>Citations</dt><dd>${escapeAgentHtml(usedCitations.length)} used · ${escapeAgentHtml(graph.citation_count??(pkg.citations||[]).length)} available</dd><dt>Validation</dt><dd>${escapeAgentHtml(validation.status||"not-run")}</dd></dl><p>${answered?"The answer is grounded in the canonical evidence package shown at right.":"The Agent stopped without activating a portrayal rule."}</p><div class="path">${usedCitations.map(escapeAgentHtml).join(" → ")||"No citation used"}</div><p><strong>Execution boundary:</strong> informational GraphRAG answers do not create symbols, layers, or map mutations.</p>`;
}
'''.strip()


EXECUTE_AGENT_ROUTE_V031 = r'''async function executeAgentRoute(args,rawMessage){
  let result={intent:args.intent,outcome:"rejected",reason:"state gate rejected the proposed action"};
  if(args.intent==="inspect_feature"){
    const item=findCatalogCapability(args.feature_query||rawMessage,args.feature_code);
    if(item){
      openCapability(item);
      result={intent:args.intent,outcome:"executed",feature_code:item.code,evidence_available:item.evidence_available};
    }else if(lastAgentGrounding){
      const answerStatus=lastAgentGrounding.answer?.status||"abstained";
      result={intent:args.intent,outcome:answerStatus==="answered"?"answered-non-executable":answerStatus,feature_code:null,evidence_available:(lastAgentGrounding.evidence_package?.evidence_nodes||[]).length>0};
    }else{
      currentRequest={question:args.feature_query||rawMessage};
      const decision=executeRequest(currentRequest);
      renderDecision(decision);
      applyDecisionToMap(decision);
      result={intent:args.intent,outcome:decision.status,feature_code:decision.feature?.code||null};
    }
  }else if(args.intent==="propose_style_revision"){
    if(activeWorkshopDecision){const input=document.querySelector("#style-request"),state=ensureWorkshopState(activeWorkshopDecision);if(input&&!state.draft){input.value=rawMessage;proposeStyleRevision(args.style_plan);result={intent:args.intent,outcome:state.draft?"previewed":"rejected",pending_revision:Boolean(state.draft),plan_source:state.draft?.plan.source||null}}}
  }else if(args.intent==="approve_revision"){
    const state=activeWorkshopDecision&&ensureWorkshopState(activeWorkshopDecision);if(state?.draft&&isExplicitApproval(rawMessage)){approveStyleRevision();result={intent:args.intent,outcome:"approved",approved_version:state.approvedVersion}}else result.reason="explicit approval and a pending revision are required";
  }else if(args.intent==="discard_revision"){
    const state=activeWorkshopDecision&&ensureWorkshopState(activeWorkshopDecision);if(state?.draft&&isExplicitDiscard(rawMessage)){discardStyleRevision();result={intent:args.intent,outcome:"discarded",approved_version:state.approvedVersion}}else result.reason="explicit rejection and a pending revision are required";
  }else if(args.intent==="finish_revisions"){
    const state=activeWorkshopDecision&&ensureWorkshopState(activeWorkshopDecision);if(state&&!state.draft&&isExplicitFinish(rawMessage))result=await prepareLayerProposal();else result.reason="finish must be explicit and no revision may be pending";
  }else if(args.intent==="request_layer_confirmation"){
    const state=activeWorkshopDecision&&ensureWorkshopState(activeWorkshopDecision);if(state&&!state.draft&&layerProposal?.status==="proposed"&&isExplicitLayerApproval(rawMessage))result=await createApprovedLayer("natural-language-explicit-approval");else result={intent:args.intent,outcome:"rejected",reason:"an inspected proposal and explicit layer approval are required"};
  }else if(args.intent==="reset_session"){
    lastAgentToolResult=null;result={intent:args.intent,outcome:"reset"};
  }else if(args.intent==="abstain"){
    result={intent:args.intent,outcome:"abstained"};
  }
  return result;
}'''.strip()


REQUEST_AGENT_ROUTE_V031 = r'''async function requestAgentRoute(message){
  lastAgentGrounding=null;
  const response=await fetch(AGENT_API,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({session_id:agentSessionId,message,context:agentContext(),tool_result:lastAgentToolResult})});
  if(!response.ok){
    let failure={};
    try{failure=await response.json()}catch(parseError){}
    const code=String(failure?.error?.code||`http_${response.status}`).slice(0,80);
    const safeMessage=String(failure?.error?.message||"Agent runtime request failed.").slice(0,240);
    const error=new Error(safeMessage);
    error.code=code;
    error.httpStatus=response.status;
    throw error;
  }
  const payload=await response.json();
  if(payload.schema!=="nma.agent-route/1.0"||payload.mode!=="responses-api")throw new Error("invalid agent response");
  lastAgentGrounding=payload.grounding||null;
  if(lastAgentGrounding&&lastAgentGrounding.runtime_contract?.schema!=="nma.runtime-baseline/0.32")throw new Error("invalid runtime contract");
  const backend=lastAgentGrounding?.runtime_contract?.graph?.backend;
  const live=backend?.active_backend==="live-neo4j"&&backend?.fallback_used===false&&backend?.graph_identity_verified===true;
  setAgentMode(lastAgentGrounding&&live?"agentic-vs1":"responses-api-fallback",`${payload.model} · ${backend?.active_backend||"routing"} · ${payload.turn}/${payload.max_turns}`);
  return validateAgentRoute(payload.tool);
}'''.strip()


ASK_V031 = r'''async function ask(){
  const input=document.querySelector("#question"),button=document.querySelector("#ask"),message=input.value.trim();
  if(!message||button.disabled)return;
  document.querySelectorAll("[data-scene-id]").forEach(item=>item.setAttribute("aria-pressed","false"));
  appendAgentMessage("user",message);
  button.disabled=true;
  let args,runtimeError=null;
  try{args=await requestAgentRoute(message)}catch(error){
    runtimeError=error;
    const code=String(error?.code||"client_validation_error").slice(0,80);
    args={intent:"abstain",feature_query:null,feature_code:null,style_request:null,style_plan:null,reply:"Agent runtime failed closed; no GraphRAG answer or map action was produced."};
    setAgentMode("runtime-error",`failed closed · ${code}`);
  }
  const result=await executeAgentRoute(args,message);
  lastAgentToolResult=result;
  if(lastAgentGrounding){renderAgenticGrounding(lastAgentGrounding);renderAgenticEvidenceSummary(lastAgentGrounding)}
  if(runtimeError){
    const code=String(runtimeError?.code||"client_validation_error").slice(0,80);
    const detail=String(runtimeError?.message||"Agent runtime request failed.").slice(0,240);
    appendAgentMessage("agent",`Agent runtime failed closed (${code}): ${detail}\nNo GraphRAG answer, tool execution, or map mutation was accepted.`);
  }else{
    const visibleReply=lastAgentGrounding?.answer?.answer||args.reply;
    appendAgentMessage("agent",`${visibleReply}\nTool: ${args.intent} · ${result.outcome}`);
  }
  button.disabled=false;
  input.focus();
}'''.strip()


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one source marker, found {count}: {old[:100]!r}")
    return text.replace(old, new, 1)


def replace_function(text: str, start: str, following: str, replacement: str) -> str:
    if text.count(start) != 1 or text.count(following) != 1:
        raise RuntimeError(f"Could not uniquely locate function boundary: {start!r}")
    prefix, remainder = text.split(start, 1)
    _, suffix = remainder.split(following, 1)
    return prefix + replacement + "\n" + following + suffix


def build(source: str) -> str:
    text = source
    text = replace_once(
        text,
        "<title>NMA Agentic Demo v0.4 — GraphRAG + LLM + Agent</title>",
        "<title>NMA Agentic Demo v0.31 — verified runtime spine</title>",
    )
    text = replace_once(
        text,
        "    a{color:var(--green)} @media(max-width:1100px)",
        RUNTIME_CSS + "    a{color:var(--green)} @media(max-width:1100px)",
    )
    text = replace_once(
        text,
        '<div class="eyebrow">National Map Agent · Agentic Demo v0.4</div>',
        '<div class="eyebrow">National Map Agent · Agentic Demo v0.31</div>',
    )
    text = replace_once(
        text,
        'register("nmaDemoWorkerV04.js"',
        'register("nmaDemoWorkerV031.js"',
    )
    text = replace_once(
        text,
        "<strong>Query boundary:</strong> this runs against the checked-in portable graph. Neo4j adapter is not connected; no database credential is exposed.",
        "<strong>Portable fallback:</strong> this local deterministic panel uses the checked-in graph. A live Agent answer replaces it with an audited backend identity; no database credential is exposed.",
    )
    text = replace_function(
        text,
        "function renderAgenticGrounding(grounding){",
        "function agentContext()",
        RUNTIME_JS,
    )
    text = replace_function(
        text,
        "async function requestAgentRoute(message){",
        "async function submitSymbolEdit()",
        REQUEST_AGENT_ROUTE_V031,
    )
    text = replace_function(
        text,
        "async function executeAgentRoute(args,rawMessage){",
        "function deterministicRoute(message)",
        EXECUTE_AGENT_ROUTE_V031,
    )
    text = replace_function(
        text,
        "async function ask(){",
        "async function checkAgentStatus()",
        ASK_V031,
    )
    text = replace_once(
        text,
        'async function checkAgentStatus(){try{const response=await fetch(AGENT_STATUS_API,{cache:"no-store"});if(!response.ok)throw new Error("unavailable");const status=await response.json();setAgentMode(status.mode,status.available?`${status.model} · max ${status.max_turns}`:"bounded fallback")}catch(error){setAgentMode("deterministic-fallback","bounded fallback")}}',
        'async function checkAgentStatus(){try{const response=await fetch(AGENT_STATUS_API,{cache:"no-store"});if(!response.ok)throw new Error("unavailable");const status=await response.json(),backend=status.graph_backend||{},live=backend.active_backend==="live-neo4j"&&backend.fallback_used===false&&backend.graph_identity_verified===true;setAgentMode(status.available&&live?"agentic-vs1":"agentic-vs1-fallback",status.available?`${status.model} · ${backend.active_backend||"backend unavailable"} · max ${status.max_turns}`:"bounded fallback")}catch(error){setAgentMode("deterministic-fallback","bounded fallback")}}',
    )
    return text


def build_worker(source: str) -> str:
    text = replace_once(
        source,
        'const CACHE_NAME = "nma-agentic-v0.4-vs1";',
        'const CACHE_NAME = "nma-agentic-runtime-baseline-0.32-grounding-panels";',
    )
    return replace_once(
        text,
        '  "./nmaAgentDemoV04.html",',
        '  "./nmaAgentDemoV031.html",',
    )


def main() -> None:
    TARGET.write_text(build(SOURCE.read_text(encoding="utf-8")), encoding="utf-8")
    WORKER_TARGET.write_text(
        build_worker(WORKER_SOURCE.read_text(encoding="utf-8")), encoding="utf-8"
    )
    print(f"Wrote {TARGET.relative_to(ROOT)}")
    print(f"Wrote {WORKER_TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
