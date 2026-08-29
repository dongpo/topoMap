const stageNames={intent:'Intent',knowledge_retrieval:'Graph retrieval',evidence:'Evidence projection',constraint_resolution:'Constraints',plan:'LLM planner',proposal:'Proposal validation',authorization:'Authorization',gis_execution:'GIS execution',verification:'Verification',provenance:'Provenance',map_result:'Map result'};
let runId=null,poller=null,map=null,currentMode=null,config=null;
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const compact=s=>{const v=String(s??'—');return v.length>30?`${v.slice(0,14)}…${v.slice(-12)}`:v};
const relationPalette=['#087255','#1769d2','#7c4db4','#b45b0a','#a52f52','#137c8b','#566b2f','#8a5b22','#3d5a80'];
async function api(path,options){const response=await fetch(path,options);let value;try{value=await response.json()}catch{value={error:`HTTP ${response.status}`}}if(!response.ok)throw new Error(value.error||`HTTP ${response.status}`);return value}
function pill(el,status){el.textContent=status;el.className=`pill ${String(status).toLowerCase().replaceAll(' ','-')}`}
function ms(value){return value===undefined||value===null?'—':value<1000?`${Number(value).toFixed(1)} ms`:`${(value/1000).toFixed(2)} s`}
function setMode(mode,identity=''){
  currentMode=mode;const bar=$('mode-bar');bar.className=`mode-bar ${mode==='LIVE'?'live':mode==='REPLAY'?'replay':'idle'}`;
  $('mode-dot').textContent=mode==='LIVE'?'●':mode==='REPLAY'?'▶':'○';
  $('mode-label').textContent=mode==='LIVE'?'LIVE CLOUD RUN':mode==='REPLAY'?'VERIFIED REPLAY':'NO RUN SELECTED';
  $('mode-run').textContent=identity;
}
function relationKey(type){return String(type||'RELATED_TO').toLowerCase().replace(/[^a-z0-9]+/g,'-')}
function relationColor(type){let hash=0;for(const char of String(type||''))hash=(hash*31+char.charCodeAt(0))>>>0;return relationPalette[hash%relationPalette.length]}
function renderRelationLegend(id,edges=[],emptyText='No relations in this view.'){
  const host=$(id);if(!host)return;
  const counts=new Map();edges.forEach(edge=>counts.set(edge.type||'RELATED_TO',(counts.get(edge.type||'RELATED_TO')||0)+1));
  if(!counts.size){host.className='relation-legend empty';host.textContent=emptyText;return}
  host.className='relation-legend';host.innerHTML=`<b>DIRECTED RELATIONS</b>${[...counts.entries()].sort(([a],[b])=>a.localeCompare(b)).map(([type,count])=>`<span style="--relation-color:${relationColor(type)}"><i></i>${esc(type)} <small>×${count}</small></span>`).join('')}`;
}
function markerDefinitions(prefix,edges){
  const types=[...new Set(edges.map(edge=>edge.type||'RELATED_TO'))];
  return `<defs>${types.map(type=>`<marker id="${prefix}-${relationKey(type)}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L8,4 L0,8 z" fill="${relationColor(type)}"></path></marker>`).join('')}</defs>`;
}
function edgePoints(source,target,padding=15){
  const dx=target.x-source.x,dy=target.y-source.y,length=Math.hypot(dx,dy)||1,ux=dx/length,uy=dy/length;
  return {x1:source.x+ux*padding,y1:source.y+uy*padding,x2:target.x-ux*padding,y2:target.y-uy*padding};
}
function relationEdge(edge,pos,prefix,showLabel=false,padding=15){
  const points=edgePoints(pos[edge.source],pos[edge.target],padding),type=edge.type||'RELATED_TO',color=relationColor(type);
  const label=showLabel?`<text class="edge-label" x="${(points.x1+points.x2)/2}" y="${(points.y1+points.y2)/2-4}" text-anchor="middle">${esc(type)}</text>`:'';
  return `<g class="relation-edge" style="--relation-color:${color}"><line x1="${points.x1}" y1="${points.y1}" x2="${points.x2}" y2="${points.y2}" stroke="${color}" marker-end="url(#${prefix}-${relationKey(type)})"><title>${esc(edge.source)} —${esc(type)}→ ${esc(edge.target)}</title></line>${label}</g>`;
}
function renderGraph(id,data){
  const host=$(id),nodes=(data?.nodes||[]).slice(0,32),edges=data?.edges||[];
  const legendId=id==='domain-graph'?'domain-relations':'retrieved-relations';
  if(!nodes.length){host.className='graph empty';host.textContent='No runtime graph selected.';renderRelationLegend(legendId,[],'Select LIVE or VERIFIED REPLAY to load graph relations.');return}
  const w=700,h=340,cx=w/2,cy=h/2,r=Math.min(w,h)*.36,pos={};
  nodes.forEach((node,index)=>{const angle=(Math.PI*2*index/nodes.length)-Math.PI/2;pos[node.id]={x:cx+Math.cos(angle)*r,y:cy+Math.sin(angle)*r}});
  const visibleEdges=edges.filter(edge=>pos[edge.source]&&pos[edge.target]),showLabels=nodes.length<=10&&visibleEdges.length<=12,prefix=relationKey(id);
  const lines=visibleEdges.map(edge=>relationEdge(edge,pos,prefix,showLabels)).join('');
  const dots=nodes.map(node=>{const point=pos[node.id],props=node.properties||{},label=(props.feature_name||props.name||props.code||node.label||node.id).slice(0,23),projected=node.display_state==='PROJECTED_EVIDENCE';return `<g class="${projected?'projected':''}"><circle cx="${point.x}" cy="${point.y}" r="${projected?15:11}"><title>${esc(node.id)} · ${esc(node.type)}${projected?' · PROJECTED':''}</title></circle><text x="${point.x}" y="${point.y+27}" text-anchor="middle">${esc(label)}</text></g>`}).join('');
  host.className='graph';host.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(data.label||'Knowledge graph')}">${markerDefinitions(prefix,visibleEdges)}${lines}${dots}</svg>`;renderRelationLegend(legendId,visibleEdges);
}
function renderActionGraph(data){
  const host=$('action-graph'),all=data?.nodes||[],nodes=all.slice(0,48),edges=data?.edges||[];
  if(!nodes.length){host.className='graph trace-graph empty';host.textContent='No runtime trace selected.';renderRelationLegend('action-relations',[],'Select LIVE or VERIFIED REPLAY to load action relations.');return}
  const types=['UserRequirement','RetrievedEvidence','Constraint','PlannerDecision','Proposal','Authorization','GISOperation','Verification','Provenance'],w=1180,h=430,pos={};
  types.forEach((type,column)=>{const group=nodes.filter(node=>node.type===type);group.forEach((node,index)=>{pos[node.id]={x:55+column*(1070/(types.length-1)),y:48+(index+1)*(330/(group.length+1))}})});
  const visibleEdges=edges.filter(edge=>pos[edge.source]&&pos[edge.target]),prefix='action-graph';
  const lines=visibleEdges.map(edge=>relationEdge(edge,pos,prefix,false,12)).join('');
  const labels=types.map((type,index)=>`<text class="column-label" x="${55+index*(1070/(types.length-1))}" y="22" text-anchor="middle">${esc(type)}</text>`).join('');
  const dots=nodes.filter(node=>pos[node.id]).map(node=>{const point=pos[node.id],label=compact(node.label||node.id);return `<g><circle cx="${point.x}" cy="${point.y}" r="9"><title>${esc(node.id)} · ${esc(node.type)}</title></circle><text x="${point.x}" y="${point.y+20}" text-anchor="middle">${esc(label)}</text></g>`}).join('');
  host.className='graph trace-graph';host.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Knowledge to constraint to action trace">${markerDefinitions(prefix,visibleEdges)}${labels}${lines}${dots}</svg>`;renderRelationLegend('action-relations',visibleEdges);
}
function renderStages(record){
  $('stages').innerHTML=Object.entries(stageNames).map(([key,label])=>{const status=(record.stages?.[key]?.status||'WAITING').toLowerCase();return `<div class="stage ${status}" title="${esc(label)}: ${esc(status)}"><div class="bar"></div><b>${esc(label)}</b><small>${esc(status.toUpperCase())}</small></div>`}).join('');pill($('overall'),record.status||'WAITING');
}
function renderRQ1(comparison){
  $('rq1-question').textContent=comparison.question;
  $('rq1-cards').innerHTML=comparison.rows.map(row=>{
    const supported=row.claims.supported.length,unsupported=row.claims.unsupported.length,contradicted=row.claims.contradicted.length;
    const presentation=row.answer_presentation||{},translated=presentation.mode==='PRESENTATION_TRANSLATION_FROM_FROZEN_RAW';
    const requirements=row.requirements.map(item=>`<li class="${item.status.toLowerCase()}"><span>${esc(item.label)}</span><b>${esc(item.status)}</b></li>`).join('');
    const claims=[...row.claims.supported,...row.claims.unsupported,...row.claims.contradicted].map(item=>`<li><b>${esc(item.status)}</b> · ${esc(item.text)}</li>`).join('')||'<li>None recorded</li>';
    const displayNote=translated?'<p class="answer-meta">繁體中文展示翻譯 · 凍結回答身分與驗證結果不變</p>':'';
    return `<article class="rq1-item ${esc(row.architecture)}"><div class="rq1-head"><h3>${esc(row.architecture)}</h3><span class="pill ${row.final_validator_result.toLowerCase()}">${esc(row.final_validator_result)}</span></div>${displayNote}<p class="answer" lang="${esc(presentation.display_language||'en')}">${esc(row.answer)}</p><div class="score"><strong>${Math.round(row.requirement_accuracy*6)}/6</strong><span>requirements correct</span></div><ul class="requirements">${requirements}</ul><div class="claim-counts"><span>${supported} supported</span><span>${unsupported} unsupported</span><span>${contradicted} contradicted</span></div><p class="retrieval-summary">${esc(row.retrieval_context_summary.summary)}</p><details><summary>Evidence, claims &amp; controls</summary><dl><dt>Grounding</dt><dd>${esc(row.grounding_status)}</dd><dt>Coverage</dt><dd>${esc(row.coverage_status)}</dd><dt>Retrieved</dt><dd>${esc(row.retrieved_item_count)}</dd><dt>Projected</dt><dd>${esc(row.projected_evidence_count)}</dd><dt>Latency</dt><dd>${ms(row.latency_ms.total)}</dd><dt>Answer display</dt><dd>${esc(presentation.notice||'Exact frozen answer.')}</dd><dt>Frozen answer hash</dt><dd>${esc(presentation.frozen_answer_sha256||row.answer_raw_response_hash)}</dd><dt>Prompt contract</dt><dd>${esc(row.prompt_contract_hash)}</dd></dl><ul class="claim-list">${claims}</ul></details></article>`;
  }).join('');
  $('rq1-controls').textContent=JSON.stringify({question_identity:comparison.question_identity,same_question:comparison.same_question,same_model:comparison.same_model,same_temperature:comparison.same_temperature,same_context_window:comparison.same_context_window,manual_answer_editing:comparison.manual_answer_editing,execution_timestamp_finding:comparison.execution_timestamp_finding},null,2);
}
function renderConstraints(rows=[]){$('constraints').innerHTML=rows.length?rows.map(item=>`<tr><td><code>${esc(item.constraint_id)}</code></td><td>${(item.source_evidence||[]).map(value=>`<code>${esc(value)}</code>`).join('<br>')}</td><td class="status-${item.status.toLowerCase()}">${esc(item.status)}</td><td>${esc(item.resolved_value===null?'UNRESOLVED':typeof item.resolved_value==='object'?JSON.stringify(item.resolved_value):item.resolved_value)}</td><td>${esc(item.planner_consequence)}<br><span class="muted">${esc((item.plan_steps||[]).join(', '))}</span></td></tr>`).join(''):'<tr><td colspan="5" class="muted">No selected run.</td></tr>'}
function dl(rows){return rows.map(([term,value])=>`<dt>${esc(term)}</dt><dd>${esc(value??'—')}</dd>`).join('')}
function renderProposal(record){
  const proposal=record.proposal||{},expected=proposal.expected_final_state?.derived_artifact?.semantic_values||{};
  pill($('proposal-status'),record.proposal_validation?.status||'WAITING');renderConstraints(record.constraints);
  $('proposal-summary').innerHTML=dl([['Proposal ID',proposal.proposal_id],['Proposal hash',proposal.proposal_hash],['Operation',proposal.decision?.execution_status],['Target',`${expected.classification||'—'} · ${expected.geometry||'—'}`],['GIS tools',(proposal.plan||[]).map(step=>step.tool).join(' → ')],['Resolved',(proposal.constraints?.resolved||[]).length],['Bounded unresolved',(proposal.constraints?.unresolved||[]).length],['Contradicted',(proposal.constraints?.contradicted||[]).length],['Validation',record.proposal_validation?.status]]);
  $('proposal-json').textContent=JSON.stringify(proposal,null,2);
}
function renderTrust(record){
  const proposal=record.proposal||{},authorization=record.authorization||{},execution=record.execution||{},provenance=record.provenance||{};
  const hashes=[proposal.proposal_hash,authorization.proposal_hash,provenance.executed_proposal_hash],identity=Boolean(hashes[0])&&new Set(hashes).size===1;
  $('proposal-hash').textContent=compact(hashes[0]);$('proposal-hash').title=hashes[0]||'';$('authorized-hash').textContent=compact(hashes[1]);$('authorized-hash').title=hashes[1]||'';$('executed-hash').textContent=compact(hashes[2]);$('executed-hash').title=hashes[2]||'';pill($('identity-status'),identity?'HASH IDENTITY PASS':'HASH IDENTITY FAIL');
  $('authorization-summary').innerHTML=dl([['Result',authorization.decision],['Authorization ID',authorization.authorization_id],['Authorized proposal',authorization.proposal_hash],['Policy',authorization.policy_reference?.id],['Parameter overrides',authorization.parameter_bounds?.parameter_overrides_allowed]]);
  $('execution-summary').innerHTML=dl([['Result',execution.status],['Execution ID',execution.execution_id],['Executor',execution.executor_version],['Receipt',execution.execution_receipt?.id],['Actual operation',(execution.tool_calls||[]).map(call=>call.tool).join(' → ')]]);
  const scope=authorization.authorized_scope||{};$('mutation-scope').textContent=`${scope.mutation_type||'—'}. Source access: ${scope.source_access||'—'}. Authoritative render: ${String(scope.authoritative_render)}. Output is confined to the run workspace.`;
}
function renderVerification(record){
  const verification=record.verification||{};pill($('verification-status'),verification.status||'WAITING');
  $('verification-checks').innerHTML=(verification.checks||[]).map(check=>`<article class="check ${check.status.toLowerCase()}"><div><b>${esc(check.rule_id)}</b><span>${esc(check.status)}</span></div><dl>${dl([['Expected',typeof check.expected==='object'?JSON.stringify(check.expected):check.expected],['Observed',typeof check.observed==='object'?JSON.stringify(check.observed):check.observed]])}</dl></article>`).join('')||'<p class="muted">No selected run.</p>';
}
function renderProvenance(record){
  const p=record.provenance||{};pill($('provenance-status'),p.result||'WAITING');
  $('trace').innerHTML=dl([['Mode',record.mode],['Run ID',record.run_id],['Retrieval',p.retrieval_id],['Plan',p.plan_id],['Proposal',p.proposal_id],['Authorization',p.authorization_id],['Execution',p.execution_id],['Verification',p.verification_id],['Receipt',p.receipt_id],['Provenance',p.provenance_id],['Timestamp',p.timestamp],['Source before',p.source_sha256_before],['Source after',p.source_sha256_after]]);
  $('provenance-json').textContent=JSON.stringify(p,null,2);
}
function renderTiming(timing={}){$('timing').innerHTML=Object.entries(timing).map(([name,value])=>[`$${name}`.slice(1).replaceAll('_',' '),ms(value)]).map(([a,b])=>`<dt>${esc(a)}</dt><dd>${esc(b)}</dd>`).join('')}
async function renderMap(mode){
  const resultPath=mode==='REPLAY'?'/ama/demo/replay/result':`/ama/run/${runId}/result`;
  const [source,result]=await Promise.all([api('/ama/source'),api(resultPath)]);
  if(!map){map=new maplibregl.Map({container:'map',style:{version:8,sources:{},layers:[{id:'bg',type:'background',paint:{'background-color':'#edf1ed'}}]},center:[121,23.7],zoom:6});await new Promise(resolve=>map.on('load',resolve))}
  for(const id of ['source','result']){if(map.getLayer(id))map.removeLayer(id);if(map.getSource(id))map.removeSource(id)}
  map.addSource('source',{type:'geojson',data:source});map.addLayer({id:'source',type:'circle',source:'source',paint:{'circle-radius':12,'circle-color':'#98a49f','circle-stroke-color':'#fff','circle-stroke-width':2}});map.addSource('result',{type:'geojson',data:result});map.addLayer({id:'result',type:'circle',source:'result',paint:{'circle-radius':7,'circle-color':mode==='REPLAY'?'#8a4dcc':'#1565c0','circle-stroke-color':'#fff','circle-stroke-width':2}});const coords=result.features[0].geometry.coordinates;map.flyTo({center:coords,zoom:15});pill($('map-status'),mode==='LIVE'?'LIVE RESULT':'REPLAY RESULT');
}
async function renderRecord(record,mode){
  record.mode=mode;setMode(mode,mode==='REPLAY'?(record.replay_identity||record.run_id):record.run_id);runId=record.run_id;renderStages(record);$('run-meta').textContent=record.run_id;renderProposal(record);renderTrust(record);renderVerification(record);renderProvenance(record);renderTiming(record.timing_ms);
  $('m-graphrag').textContent=ms(record.timing_ms?.graphrag);$('m-plan').textContent=ms(record.timing_ms?.llm_planning);$('m-auth').textContent=ms(record.timing_ms?.authorization);$('m-gis').textContent=ms(record.timing_ms?.gis_execution);$('m-verify').textContent=ms(record.timing_ms?.verification);$('m-total').textContent=ms(record.timing_ms?.end_to_end);
  if(record.evidence){const views=mode==='REPLAY'?await api('/ama/demo/replay/views'):await api(`/ama/run/${runId}/demo-views`);renderGraph('retrieved-graph',views.retrieved_subgraph);renderActionGraph(views.evidence_action_trace);$('node-count').textContent=`${record.retrieval?.node_count||0} retrieved · ${record.evidence?.projected_node_count||0} projected`}
  await renderMap(mode);
}
function showFailure(error){clearInterval(poller);$('run').disabled=false;$('error').hidden=false;$('error-text').textContent=` ${error.message||error} No replay has been selected.`;$('fallback').hidden=false}
async function begin(){
  try{$('error').hidden=true;$('run').disabled=true;$('tamper').disabled=true;const record=await api('/ama/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({intent:$('intent').value})});runId=record.run_id;setMode('LIVE',runId);renderStages(record);$('run-meta').textContent=runId;poller=setInterval(async()=>{try{const current=await api(`/ama/run/${runId}`);renderStages(current);renderTiming(current.timing_ms);if(current.status==='PASS'){clearInterval(poller);$('run').disabled=false;$('tamper').disabled=false;await renderRecord(current,'LIVE')}else if(current.status==='FAILED'){showFailure(new Error(current.failure?.message||'Live run failed.'))}}catch(error){showFailure(error)}},750)}catch(error){showFailure(error)}
}
async function replay(){try{$('error').hidden=true;$('tamper').disabled=true;const record=await api('/ama/demo/replay');await renderRecord(record,'REPLAY')}catch(error){showFailure(error)}}
async function reset(){
  try{clearInterval(poller);await api('/ama/reset',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});runId=null;currentMode=null;setMode(null);$('tamper').disabled=true;$('tamper-result').hidden=true;$('error').hidden=true;$('run').disabled=false;renderStages({status:'WAITING',stages:{}});for(const id of ['proposal-status','identity-status','map-status','verification-status','provenance-status'])pill($(id),'WAITING');$('run-meta').textContent='Canonical bounded scenario';$('retrieved-graph').className='graph empty';$('retrieved-graph').textContent='Run AMA or choose replay.';renderRelationLegend('retrieved-relations',[],'Select LIVE or VERIFIED REPLAY to load graph relations.');$('action-graph').className='graph trace-graph empty';$('action-graph').textContent='Run AMA or choose replay.';renderRelationLegend('action-relations',[],'Select LIVE or VERIFIED REPLAY to load action relations.');$('constraints').innerHTML='<tr><td colspan="5" class="muted">No selected run.</td></tr>';if(map){for(const id of ['source','result']){if(map.getLayer(id))map.removeLayer(id);if(map.getSource(id))map.removeSource(id)}}}catch(error){showFailure(error)}
}
async function tamper(){try{if(currentMode!=='LIVE')throw new Error('Tamper control is available only for the selected fresh live run.');const value=await api(`/ama/run/${runId}/tamper-test`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});$('tamper-result').hidden=false;$('tamper-result').textContent=JSON.stringify(value,null,2);$('tamper').textContent=value.status==='PASS'?'Tamper denied — no mutation':'Tamper test failed'}catch(error){showFailure(error)}}
async function init(){
  const [loadedConfig,domain,rq1]=await Promise.all([api('/ama/config'),api('/ama/demo/domain-kg'),api('/ama/demo/rq1-comparison')]);config=loadedConfig;$('intent').value=config.canonical_intent;$('intent-forms').innerHTML=dl([['Normalized intent',config.normalized_intent],['Planner input',config.planner_input],['Original substituted',false]]);$('deployment-footer').textContent=`AMA-DEMO-02 · ${config.deployment}`;renderGraph('domain-graph',domain);renderRelationLegend('retrieved-relations',[],'Select LIVE or VERIFIED REPLAY to load graph relations.');renderRelationLegend('action-relations',[],'Select LIVE or VERIFIED REPLAY to load action relations.');renderRQ1(rq1);renderStages({status:'WAITING',stages:{}});setMode(null);
}
$('run').addEventListener('click',begin);$('replay').addEventListener('click',replay);$('fallback').addEventListener('click',replay);$('reset').addEventListener('click',reset);$('tamper').addEventListener('click',tamper);init().catch(showFailure);
