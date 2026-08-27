#!/usr/bin/env python3
"""Build the v0.32 school Hero flow while preserving v0.31."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "nmaAgentDemoV031.html"
TARGET = ROOT / "nmaAgentDemoV032.html"
WORKER_SOURCE = ROOT / "nmaDemoWorkerV031.js"
WORKER_TARGET = ROOT / "nmaDemoWorkerV032.js"


HERO_CSS = """
    .hero-contract{margin:8px 0;padding:10px;border:1px solid #91b8a2;border-radius:9px;background:#f4faf6}.hero-contract strong{display:block}.hero-contract small{color:#53655f}.hero-stage.pending{border-top-color:#a7b1ac}.hero-stage.completed{border-top-color:var(--green)}.hero-stage.failed{border-top-color:#b42318}.server-result{margin-top:8px;padding:9px;border:1px solid #b9cada;border-radius:8px;background:#fff}.server-result code{overflow-wrap:anywhere}.hero-actions{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.hero-actions button.secondary{background:#64756d}.qa-checks{display:grid;gap:4px;margin-top:8px}.qa-check{display:flex;justify-content:space-between;gap:8px;padding:5px 7px;border-radius:6px;background:#edf3ef;font-size:.72rem}.qa-check.failed{background:#fff1f0;color:#8a2018}
"""


HERO_JS = r'''
const PORTRAYAL_API="/api/portrayal-review",PORTRAYAL_DECISION_API="/api/portrayal-review/decision",PORTRAYAL_PREVIEW_API="/api/portrayal-review/preview",REAL_LAYER_API="/api/real-layer",REAL_LAYER_EXECUTE_API="/api/real-layer/execute",SCHOOL_HERO_EVIDENCE_API="/api/hero/school/evidence",REQUIRED_F03_SERVER_REVISION="f03-school-hero-centered-edit-2026-08-12.4";
const HERO_STAGE_ORDER=["resolve","retrieve","explain","propose","validate","approve","execute","observe","qa","cite"];
const heroState={featureCode:"9920103",featureName:"小學",portrayalProposalId:null,approvedPortrayalProposalId:null,portrayalResult:null,portrayalPreview:null,layerProposalId:null,layerResult:null,stages:Object.fromEntries(HERO_STAGE_ORDER.map(stage=>[stage,{status:"pending",detail:"Waiting for the supervised Agent."}]))};

async function postHeroJson(url,body){
  const response=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  let payload={};try{payload=await response.json()}catch(error){}
  if(!response.ok){const failure=new Error(payload?.error?.message||`Hero API failed (${response.status}).`);failure.code=payload?.error?.code||`http_${response.status}`;throw failure}
  return payload;
}
function isSchoolHeroEvidenceQuestion(message){return /小學|9920103/.test(message)&&/圖式|規則|哪一頁|呈現/.test(message)}
function withSchoolCenterOperation(message,plan){if(!plan||!/中間|中央|置中/.test(message)||plan.operations?.some(item=>item.action==="center"))return plan;return {...plan,operations:[...(plan.operations||[]),{action:"center",target:"flagpole-bottom",value:null,reference:"support",relation:"centered"}].slice(0,8)}}
async function requestSchoolHeroEvidence(){const response=await fetch(SCHOOL_HERO_EVIDENCE_API,{cache:"no-store"});let payload={};try{payload=await response.json()}catch(error){}if(!response.ok)throw new Error(payload?.error?.message||"Reviewed school evidence is unavailable.");if(payload.server_revision!==REQUIRED_F03_SERVER_REVISION||payload.schema!=="nma.agentic-vs1/1.0")throw new Error("incompatible F03 school evidence response");lastAgentGrounding=payload;setAgentMode("agentic-vs1",`reviewed school GraphRAG · ${payload.server_revision}`);return payload}
function setHeroStage(stage,status,detail){if(heroState.stages[stage])heroState.stages[stage]={status,detail}}
function ingestHeroEvents(events){for(const event of events||[]){const aliases={plan:"propose",reason:"explain",inspection:"observe",approval:"approve"},stage=aliases[event.stage]||event.stage;if(heroState.stages[stage])setHeroStage(stage,event.status==="passed"||event.status==="verified"||event.status==="completed"||event.status==="approved"||String(event.status).startsWith("executed")||event.status==="available"?"completed":event.status==="pending"?"pending":"completed",event.detail||event.status)}}
function renderHeroTrace(){
  const cards=HERO_STAGE_ORDER.map((stage,index)=>{const item=heroState.stages[stage];return `<div class="trace-step hero-stage ${escapeAgentHtml(item.status)}"><strong>${index+1} · ${escapeAgentHtml(stage)}</strong><small>${escapeAgentHtml(item.status)}</small><small>${escapeAgentHtml(item.detail)}</small></div>`}).join("");
  document.querySelector("#agent-trace").innerHTML=`<h3>School Hero Agent trace · ${heroState.layerResult?"verified real layer":heroState.layerProposalId?"layer approval pending":heroState.portrayalProposalId?"symbol review active":"evidence review"}</h3><div class="trace-grid">${cards}</div>`;
}
function schoolHeroStructure(operations=[],compiled=null){const structure=compiled?JSON.parse(JSON.stringify(compiled)):{flag_top_alignment:"offset",support:{enabled:false,shape:null,width_relation:"independent"},flagpole_attachment:"detached",flagpole_horizontal_alignment:"edge"};for(const item of operations){if(item.action==="align")structure.flag_top_alignment=item.value?.relation||"offset";else if(item.action==="add_shape")structure.support={...structure.support,enabled:true,shape:item.value?.shape||"rectangle"};else if(item.action==="remove_shape")structure.support={...structure.support,enabled:false,shape:null};else if(item.action==="match_dimension")structure.support={...structure.support,width_relation:item.value?.relation||"independent"};else if(item.action==="attach")structure.flagpole_attachment=item.value?.relation||"inserted-into-top";else if(item.action==="detach")structure.flagpole_attachment="detached";else if(item.action==="center")structure.flagpole_horizontal_alignment=item.value?.relation||"centered"}return structure}
function schoolHeroSvg(color="#111111",label="school portrayal preview",structure=null){const state=structure||schoolHeroStructure(),support=state.support?.enabled===true,supportWidth=state.support?.width_relation==="same-width"?38:state.support?.width_relation==="proportional-width"?28:24,supportX=14,supportY=37,supportHeight=16,poleX=support&&state.flagpole_horizontal_alignment==="centered"?supportX+supportWidth/2:14,poleEnd=state.flagpole_attachment==="inserted-into-top"&&support?supportY+7:57,flagTop=state.flag_top_alignment==="aligned"?7:9,flagRight=poleX+38;return `<svg viewBox="0 0 64 64" role="img" aria-label="${escapeAgentHtml(label)}"><g fill="${escapeAgentHtml(color)}" stroke="${escapeAgentHtml(color)}" stroke-linecap="round" stroke-linejoin="round">${support?`<rect x="${supportX}" y="${supportY}" width="${supportWidth}" height="${supportHeight}" rx="1" stroke-width="1"/>`:""}<path d="M${poleX} ${poleEnd}V7" fill="none" stroke-width="4"/><path d="M${poleX} ${flagTop}L${flagRight} 24L${poleX} 30Z" stroke-width="1"/></g></svg>`}
function portrayalColor(result){const channels=result?.observation?.render_ir?.channels||{};return channels.marker?.color||channels.stroke?.color||"#111111"}
function serverCitations(result){return result?.evidence_package?.citations||result?.proposal?.evidence?.citations||[]}
function renderServerPortrayal(result,preview=null){
  const proposal=result?.proposal,baseline=proposal?.official_baseline;if(!proposal||!baseline)return;
  const asset=baseline.review_asset?.path||"assets/symbols/nlsc112v5.4/review-candidates/school-flag-v1.svg",operations=proposal.derived_preview_ir?.overrides||[],proposedColor=operations.find(item=>item.action==="set_color"&&item.target==="marker")?.value?.color||"#111111",color=preview?portrayalColor(preview):proposedColor,structure=schoolHeroStructure(operations,preview?.observation?.render_ir?.structure||null),citations=serverCitations(result);
  document.querySelector("#symbol-workshop").innerHTML=`<h2><span>School symbol review</span><span class="badge ${preview?"approved":"pending"}">${preview?"approved preview":"approval required"}</span></h2><div class="symbol-compare"><div class="symbol-version"><div class="version-header"><strong>Specification baseline</strong><span class="badge">immutable · black</span></div><div class="symbol-preview"><img src="${escapeAgentHtml(asset)}" alt="School specification-derived baseline"></div><div class="style-summary">Document 01 · page ${escapeAgentHtml(baseline.page)} · source rule <code>${escapeAgentHtml(baseline.source_rule_id)}</code></div></div><div class="symbol-version ${preview?"approved":"pending"}"><div class="version-header"><strong>Derived user preference</strong><span class="badge ${preview?"approved":"pending"}">${preview?"compiled after approval":"unapproved proposal"}</span></div><div class="symbol-preview">${schoolHeroSvg(color,"school derived user-preference preview",structure)}</div><div class="style-summary">${operations.map(item=>`${escapeAgentHtml(item.action)} ${escapeAgentHtml(item.target)}`).join(" · ")||"No approved override"}</div></div></div><div class="server-result"><strong>Authority boundary</strong><br>V0 remains immutable. The derived preview is a user preference and does not activate the official rule.<br><code>${escapeAgentHtml(heroState.portrayalProposalId||"")}</code></div><div class="citation-list">${citations.slice(0,4).map(item=>`<div class="citation-item"><strong>${escapeAgentHtml(item.filename||"Reviewed specification")}</strong> · page ${escapeAgentHtml(item.page??"?")}<br><code>${escapeAgentHtml(item.citation_id)}</code></div>`).join("")}</div>${!preview?'<div class="hero-actions"><button id="hero-approve-symbol">Approve derived preview</button><button id="hero-discard-symbol" class="secondary">Discard</button></div>':`<div class="workflow-next"><strong>Symbol preview approved</strong><p>Continue in the supervised conversation: say「不用再修改，請準備真實小學圖層」.</p></div>`}`;
  document.querySelector("#hero-approve-symbol")?.addEventListener("click",()=>approveHeroPortrayal("button-explicit-approval"));
  document.querySelector("#hero-discard-symbol")?.addEventListener("click",()=>discardHeroPortrayal("button-explicit-discard"));
}
async function proposeHeroPortrayal(message,symbolEditPlan){
  const payload={feature_code:heroState.featureCode,message,symbol_edit_plan:symbolEditPlan};if(heroState.approvedPortrayalProposalId)payload.parent_proposal_id=heroState.approvedPortrayalProposalId;
  const result=await postHeroJson(PORTRAYAL_API,payload);heroState.portrayalResult=result;heroState.portrayalProposalId=result.proposal_state?.proposal_id||null;heroState.portrayalPreview=null;
  ingestHeroEvents(result.trace?.events);setHeroStage("propose","completed","LLM returned a bounded evidence-bound portrayal plan.");setHeroStage("validate","completed","Server validated geometry, operations, evidence IDs and citations.");setHeroStage("approve","pending","Derived preview awaits explicit human approval.");renderServerPortrayal(result);renderHeroTrace();return {intent:"propose_style_revision",outcome:"proposal-pending-approval",proposal_id:heroState.portrayalProposalId};
}
async function approveHeroPortrayal(source="natural-language-explicit-approval"){
  if(!heroState.portrayalProposalId)throw new Error("No portrayal proposal awaits approval.");
  await postHeroJson(PORTRAYAL_DECISION_API,{proposal_id:heroState.portrayalProposalId,decision:"approve"});
  const preview=await postHeroJson(PORTRAYAL_PREVIEW_API,{proposal_id:heroState.portrayalProposalId});heroState.approvedPortrayalProposalId=heroState.portrayalProposalId;heroState.portrayalPreview=preview;
  setHeroStage("approve","completed",`Derived symbol explicitly approved via ${source}.`);setHeroStage("execute","completed","Deterministic portrayal compiler produced safe render IR.");setHeroStage("observe","completed","Compiled preview returned to the Agent; no map layer created.");renderServerPortrayal(heroState.portrayalResult,preview);renderHeroTrace();return {intent:"approve_revision",outcome:"approved-preview-observed",proposal_id:heroState.portrayalProposalId};
}
async function discardHeroPortrayal(source="natural-language-explicit-discard"){
  if(!heroState.portrayalProposalId)throw new Error("No portrayal proposal awaits a decision.");
  await postHeroJson(PORTRAYAL_DECISION_API,{proposal_id:heroState.portrayalProposalId,decision:"discard"});setHeroStage("approve","completed",`Derived proposal discarded via ${source}; V0 unchanged.`);heroState.portrayalProposalId=null;heroState.portrayalResult=null;heroState.portrayalPreview=null;renderHeroTrace();document.querySelector("#symbol-workshop").innerHTML='<h2><span>School symbol review</span><span class="badge">V0 retained</span></h2><div class="result-empty">The derived proposal was discarded. The immutable black baseline remains selected.</div>';return {intent:"discard_revision",outcome:"discarded"};
}
function renderServerLayerProposal(result){
  const plan=result.plan,inspections=plan?.source_inspections||[],citations=plan?.citation_ids||[];document.querySelector("#layer-workshop").innerHTML=`<h2><span>Real school layer</span><span class="badge pending">approval required</span></h2><div class="layer-proposal"><strong>Read-only inspection complete; conversion has not run.</strong></div><dl class="facts"><dt>Source</dt><dd>${escapeAgentHtml(plan.source_layers.join(", "))}</dd><dt>Filter</dt><dd><code>${escapeAgentHtml(plan.source_filter.field)} = ${escapeAgentHtml(plan.source_filter.value)}</code></dd><dt>Geometry</dt><dd>${escapeAgentHtml(plan.geometry_role)}</dd><dt>Expected</dt><dd>${escapeAgentHtml(plan.expected_feature_count)} real features</dd><dt>Inspected files</dt><dd>${escapeAgentHtml(inspections.length)}</dd></dl><div class="server-result"><strong>Immutable inspected plan</strong><br><code>${escapeAgentHtml(plan.plan_id)}</code><br>${escapeAgentHtml(citations.length)} reviewed citation(s) bound.</div><div class="hero-actions"><button id="hero-approve-layer">Approve and create real layer</button></div>`;document.querySelector("#hero-approve-layer")?.addEventListener("click",()=>executeHeroLayer("button-explicit-approval"));
}
async function proposeHeroLayer(){
  if(!heroState.approvedPortrayalProposalId)throw new Error("Approve a derived preview before layer planning.");
  const result=await postHeroJson(REAL_LAYER_API,{profile_id:"school-point",message:"使用已審核的真實 MARK Shapefiles 建立小學 9920103 圖層"});heroState.layerProposalId=result.proposal_state?.proposal_id||null;
  ingestHeroEvents(result.trace?.events);setHeroStage("propose","completed","Agent proposed the reviewed school-point mapping.");setHeroStage("validate","completed","Read-only GDAL inspection matched the reviewed mapping and 15-feature expectation.");setHeroStage("approve","pending","Real-layer execution awaits separate explicit approval.");renderServerLayerProposal(result);renderHeroTrace();return {intent:"finish_revisions",outcome:"real-layer-proposal-pending",proposal_id:heroState.layerProposalId};
}
function ensureHeroSchoolIcon(color,structure){const support=structure?.support?.enabled===true,attached=structure?.flagpole_attachment==="inserted-into-top",centered=support&&structure?.flagpole_horizontal_alignment==="centered",poleX=centered ? .42 : .18,id=`nma-v032-school-${String(color).replace(/[^0-9a-f]/gi,"")}-${support?"support":"plain"}-${attached?"attached":"detached"}-${centered?"centered":"edge"}`;if(map.hasImage(id))return id;canvasIcon(map,id,24,32,(g,w,h,d)=>{g.strokeStyle=color;g.fillStyle=color;g.lineWidth=d;if(support)g.fillRect(w*.18,h*.58,w*.48,h*.26);g.beginPath();g.moveTo(w*poleX,h*.04);g.lineTo(w*poleX,attached&&support?h*.7:h*.96);g.stroke();g.beginPath();g.moveTo(w*poleX,h*.07);g.lineTo(w*.96,h*.35);g.lineTo(w*poleX,h*.39);g.closePath();g.fill()});return id}
function fitHeroFeatures(collection){const coords=(collection.features||[]).map(item=>item.geometry?.coordinates).filter(item=>Array.isArray(item)&&Number.isFinite(item[0])&&Number.isFinite(item[1]));if(!coords.length)return;const bounds=coords.reduce((b,c)=>b.extend(c),new maplibregl.LngLatBounds(coords[0],coords[0]));map.fitBounds(bounds,{padding:70,maxZoom:15})}
async function addVerifiedHeroLayer(result){
  if(result.qa?.status!=="passed"||result.observation?.provenance?.random_coordinates!==false)throw new Error("Real-layer QA did not pass.");
  const response=await fetch(result.output_url,{cache:"no-store"});if(!response.ok)throw new Error("Verified GeoJSON could not be loaded.");const collection=await response.json();if(collection.features?.length!==15)throw new Error("Verified GeoJSON feature count changed.");
  for(const id of ["nma-v032-school-label","nma-v032-school-symbol"]){if(map.getLayer(id))map.removeLayer(id)}if(map.getSource("nma-v032-school-real"))map.removeSource("nma-v032-school-real");
  map.addSource("nma-v032-school-real",{type:"geojson",data:collection});const structure=heroState.portrayalPreview?.observation?.render_ir?.structure||null,icon=ensureHeroSchoolIcon(portrayalColor(heroState.portrayalPreview),structure);map.addLayer({id:"nma-v032-school-symbol",type:"symbol",source:"nma-v032-school-real",layout:{"icon-image":icon,"icon-size":1.15,"icon-allow-overlap":true}});map.addLayer({id:"nma-v032-school-label",type:"symbol",source:"nma-v032-school-real",layout:{"text-field":["get","MARKNAME1"],"text-size":11,"text-offset":[0,1.5],"text-anchor":"top"},paint:{"text-color":"#111111","text-halo-color":"#ffffff","text-halo-width":1.2}});fitHeroFeatures(collection);
}
function renderExecutedHeroLayer(result){const checks=result.qa?.checks||[];document.querySelector("#layer-workshop").innerHTML=`<h2><span>Real school layer</span><span class="badge approved">verified on map</span></h2><div class="layer-created"><strong>${escapeAgentHtml(result.observation.feature_count)} real school Points created after approval.</strong></div><dl class="facts"><dt>GeoJSON</dt><dd><code>${escapeAgentHtml(result.output_url)}</code></dd><dt>Output SHA-256</dt><dd><code>${escapeAgentHtml(result.observation.output_sha256)}</code></dd><dt>Source</dt><dd>${escapeAgentHtml(result.observation.provenance.source_archive)}</dd><dt>Random coordinates</dt><dd>${escapeAgentHtml(result.observation.provenance.random_coordinates)}</dd></dl><div class="qa-checks">${checks.map(item=>`<div class="qa-check ${escapeAgentHtml(item.status)}"><span>${escapeAgentHtml(item.id)}</span><strong>${escapeAgentHtml(item.status)}</strong></div>`).join("")}</div><div class="citation-list">${(result.citation_ids||[]).map(id=>`<div class="citation-item used"><code>${escapeAgentHtml(id)}</code> · bound to executed plan</div>`).join("")}</div>`}
async function executeHeroLayer(source="natural-language-explicit-approval"){
  if(!heroState.layerProposalId)throw new Error("No inspected real-layer proposal awaits approval.");
  const result=await postHeroJson(REAL_LAYER_EXECUTE_API,{proposal_id:heroState.layerProposalId,decision:"approve"});await addVerifiedHeroLayer(result);heroState.layerResult=result;ingestHeroEvents(result.trace?.events);setHeroStage("approve","completed",`Layer plan explicitly approved via ${source}.`);setHeroStage("execute","completed","GDAL executed the checksum-bound Shapefile plan.");setHeroStage("observe","completed",`${result.observation.feature_count} real Point features and output checksum observed.`);setHeroStage("qa",result.qa.status==="passed"?"completed":"failed","Feature count, geometry, filter and non-random coordinates checked.");setHeroStage("cite",(result.citation_ids||[]).length?"completed":"failed",`${(result.citation_ids||[]).length} reviewed citation(s) remain bound.`);renderExecutedHeroLayer(result);renderHeroTrace();return {intent:"request_layer_confirmation",outcome:"verified-real-layer-on-map",feature_count:result.observation.feature_count,output_sha256:result.observation.output_sha256};
}
'''.strip()


EXECUTE_ROUTE = r'''async function executeAgentRoute(args,rawMessage){
  let result={intent:args.intent,outcome:"rejected",reason:"state gate rejected the proposed action"};
  if(args.intent==="inspect_feature"){
    const item=findCatalogCapability(args.feature_query||rawMessage,args.feature_code);
    if(item&&item.code===heroState.featureCode){openCapability(item);setHeroStage("resolve","completed","小學 resolved to canonical code 9920103.");setHeroStage("retrieve","completed","Canonical GraphRAG returned reviewed Document 01 evidence.");setHeroStage("explain","completed","Grounded answer and source citations were validated.");renderHeroTrace();result={intent:args.intent,outcome:"executed",feature_code:item.code,evidence_available:item.evidence_available}}
    else if(lastAgentGrounding){const answerStatus=lastAgentGrounding.answer?.status||"abstained";result={intent:args.intent,outcome:answerStatus==="answered"?"answered-non-executable":answerStatus,feature_code:null,evidence_available:(lastAgentGrounding.evidence_package?.evidence_nodes||[]).length>0}}
    else result={intent:args.intent,outcome:"abstained",reason:"The v0.32 Hero flow is bounded to school 9920103."};
  }else if(args.intent==="propose_style_revision"){
    if(activeWorkshopDecision?.feature.code===heroState.featureCode)result=await proposeHeroPortrayal(rawMessage,args.style_plan);else result.reason="Select school 9920103 before requesting a derived revision";
  }else if(args.intent==="approve_revision"){
    if(heroState.portrayalProposalId&&isExplicitApproval(rawMessage))result=await approveHeroPortrayal();else result.reason="explicit approval and a server proposal are required";
  }else if(args.intent==="discard_revision"){
    if(heroState.portrayalProposalId&&isExplicitDiscard(rawMessage))result=await discardHeroPortrayal();else result.reason="explicit rejection and a server proposal are required";
  }else if(args.intent==="finish_revisions"){
    if(heroState.approvedPortrayalProposalId&&isExplicitFinish(rawMessage))result=await proposeHeroLayer();else result.reason="an approved server-side portrayal preview and explicit finish are required";
  }else if(args.intent==="request_layer_confirmation"){
    if(heroState.layerProposalId&&isExplicitLayerApproval(rawMessage))result=await executeHeroLayer();else result.reason="an inspected server proposal and explicit layer approval are required";
  }else if(args.intent==="reset_session"){
    lastAgentToolResult=null;result={intent:args.intent,outcome:"reset"};
  }else if(args.intent==="abstain")result={intent:args.intent,outcome:"abstained"};
  return result;
}'''.strip()


ASK_FUNCTION = r'''async function ask(){
  const input=document.querySelector("#question"),button=document.querySelector("#ask"),message=input.value.trim(),originalLabel=button.textContent;
  if(!message||button.disabled)return;
  document.querySelectorAll("[data-scene-id]").forEach(item=>item.setAttribute("aria-pressed","false"));
  appendAgentMessage("user",message);button.disabled=true;button.textContent="Working…";
  let args=null,result=null,runtimeError=null;
  try{
    try{const localPlan=deterministicRoute(message);if(localPlan.intent==="propose_style_revision")localPlan.style_plan=withSchoolCenterOperation(message,localPlan.style_plan);if(isSchoolHeroEvidenceQuestion(message)){await requestSchoolHeroEvidence();args=localPlan}else{args=await requestAgentRoute(message);if(activeWorkshopDecision?.feature.code===heroState.featureCode&&args.intent==="propose_style_revision")args.style_plan=withSchoolCenterOperation(message,args.style_plan)}}catch(error){
      const fallback=deterministicRoute(message);
      if(fallback.intent==="propose_style_revision"){
        args=fallback;setAgentMode("deterministic-fallback","bounded SymbolEditPlan fallback");
      }else{
        runtimeError=error;args={intent:"abstain",feature_query:null,feature_code:null,style_request:null,style_plan:null,reply:"Agent runtime failed closed; no GraphRAG answer or map action was produced."};setAgentMode("runtime-error",`failed closed · ${String(error?.code||"client_validation_error").slice(0,80)}`);
      }
    }
    if(!runtimeError){
      try{result=await executeAgentRoute(args,message);lastAgentToolResult=result}catch(error){runtimeError=error;result={intent:args.intent,outcome:"failed-closed",reason:String(error?.message||"Tool execution failed.").slice(0,240)};setAgentMode("runtime-error",`failed closed · ${String(error?.code||"tool_execution_error").slice(0,80)}`)}
    }else result=await executeAgentRoute(args,message);
    if(lastAgentGrounding){renderAgenticGrounding(lastAgentGrounding);renderAgenticEvidenceSummary(lastAgentGrounding)}
    renderHeroTrace();
    if(runtimeError){const code=String(runtimeError?.code||"tool_execution_error").slice(0,80),detail=String(runtimeError?.message||"Agent runtime request failed.").slice(0,240);appendAgentMessage("agent",`Agent runtime failed closed (${code}): ${detail}\nNo unverified answer, symbol, or map mutation was accepted.`)}
    else{const visibleReply=lastAgentGrounding?.answer?.answer||args.reply;appendAgentMessage("agent",`${visibleReply}\nTool: ${args.intent} · ${result.outcome}`)}
  }finally{button.disabled=false;button.textContent=originalLabel;input.focus()}
}'''.strip()


CHECK_STATUS_FUNCTION = r'''async function checkAgentStatus(){try{const response=await fetch(AGENT_STATUS_API,{cache:"no-store"});if(!response.ok)throw new Error("unavailable");const status=await response.json();if(status.server_revision!==REQUIRED_F03_SERVER_REVISION){setAgentMode("runtime-error",`incompatible server · ${status.server_revision||"revision missing"}`);return}const backend=status.graph_backend||{},live=backend.active_backend==="live-neo4j"&&backend.fallback_used===false&&backend.graph_identity_verified===true;setAgentMode(status.available&&live?"agentic-vs1":"agentic-vs1-fallback",status.available?`${status.model} · ${backend.active_backend||"backend unavailable"} · ${status.server_revision}`:"bounded fallback")}catch(error){setAgentMode("deterministic-fallback","server unavailable")}}'''.strip()


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
        "<title>NMA Agentic Demo v0.31 — verified runtime spine</title>",
        "<title>NMA Agentic Demo v0.32 — school Hero flow</title>",
    )
    text = replace_once(
        text,
        "    a{color:var(--green)} @media(max-width:1100px)",
        HERO_CSS + "    a{color:var(--green)} @media(max-width:1100px)",
    )
    text = replace_once(
        text,
        '<div class="eyebrow">National Map Agent · Agentic Demo v0.31</div>',
        '<div class="eyebrow">National Map Agent · Agentic Demo v0.32 · School Hero</div>',
    )
    text = replace_once(
        text,
        '<div class="question"><input id="question" value="小學的圖式規則在哪一頁？"><button id="ask">Ask</button></div>',
        '<div class="question"><input id="question" value="小學的圖式規則在哪一頁？"><button id="ask">Ask</button></div><div class="hero-contract"><strong>Live acceptance path · 小學 9920103</strong><small>GraphRAG → supervised symbol revision → explicit approvals → 15 real MARK Shapefile features → QA → citations. No random geometry.</small></div>',
    )
    text = replace_once(
        text,
        'register("nmaDemoWorkerV031.js"',
        'register("nmaDemoWorkerV032.js"',
    )
    text = replace_once(
        text,
        'flag_attachment:"Flag attachment"',
        'flag_attachment:"Flag attachment",flagpole_horizontal_alignment:"Flagpole horizontal alignment"',
    )
    text = replace_once(
        text,
        'flag_attachment:"detached"',
        'flag_attachment:"detached",flagpole_horizontal_alignment:"edge"',
    )
    text = replace_once(
        text,
        'detach:{key:"flag_attachment",target:"flagpole-bottom",reference:"support-top",relations:new Set(["detached"]),map:()=>"detached"}',
        'detach:{key:"flag_attachment",target:"flagpole-bottom",reference:"support-top",relations:new Set(["detached"]),map:()=>"detached"},center:{key:"flagpole_horizontal_alignment",target:"flagpole-bottom",reference:"support",relations:new Set(["centered"]),map:()=>"centered"}',
    )
    text = replace_once(text, "function agentContext()", HERO_JS + "\nfunction agentContext()")
    text = replace_function(
        text,
        "async function executeAgentRoute(args,rawMessage){",
        "function deterministicRoute(message)",
        EXECUTE_ROUTE,
    )
    text = replace_function(
        text,
        "async function ask(){",
        "async function checkAgentStatus()",
        ASK_FUNCTION,
    )
    text = replace_function(
        text,
        "async function checkAgentStatus(){",
        "function setRuntimeStatus(message,degraded=false)",
        CHECK_STATUS_FUNCTION,
    )
    text = replace_once(
        text,
        'if(payload.schema!=="nma.agent-route/1.0"||payload.mode!=="responses-api")throw new Error("invalid agent response");',
        'if(payload.schema!=="nma.agent-route/1.0"||payload.mode!=="responses-api"||payload.server_revision!==REQUIRED_F03_SERVER_REVISION)throw new Error("incompatible F03 agent server revision");',
    )
    text = replace_once(
        text,
        "const citations=(pkg.citations||[]).slice(0,10).map",
        "const citations=(pkg.citations||[]).filter(citation=>usedCitationIds.has(citation.citation_id)).slice(0,10).map",
    )
    text = replace_once(text, "<h3>Source citations</h3>", "<h3>Cited source</h3>")
    text = replace_once(
        text,
        "  if(lastAgentGrounding){renderAgenticGrounding(lastAgentGrounding);renderAgenticEvidenceSummary(lastAgentGrounding)}",
        "  if(lastAgentGrounding){renderAgenticGrounding(lastAgentGrounding);renderAgenticEvidenceSummary(lastAgentGrounding)}\n  renderHeroTrace();",
    )
    return text


def build_worker(source: str) -> str:
    text = replace_once(
        source,
        'const CACHE_NAME = "nma-agentic-runtime-baseline-0.32-grounding-panels";',
        'const CACHE_NAME = "nma-agentic-v0.32.4-school-hero-centered-edit";',
    )
    return replace_once(
        text,
        '  "./nmaAgentDemoV031.html",',
        '  "./nmaAgentDemoV032.html",',
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
