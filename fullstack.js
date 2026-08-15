const DEFAULT_API = localStorage.getItem('noiop_api_base') || '';
let API_BASE = DEFAULT_API.replace(/\/$/,'');
let selectedOpportunityId = null;

function apiUrl(path){ return API_BASE ? API_BASE + path : path; }
function actor(){ return document.getElementById('actorName')?.value || 'demo-decision-owner'; }
function apiHeaders(){ return {'Content-Type':'application/json','X-NOIOP-Actor':actor()}; }
async function api(path, options={}){
  const response = await fetch(apiUrl(path), {...options, headers:{...apiHeaders(), ...(options.headers||{})}});
  const text = await response.text(); let data={}; try{data=text?JSON.parse(text):{}}catch{data={raw:text}};
  if(!response.ok) throw new Error(data.error || data.message || `HTTP ${response.status}`);
  return data;
}
function setConn(text, ok=false){ const e=document.getElementById('backendStatus'); if(e){e.textContent=text;e.style.color=ok?'#5ad39a':'#efc45d';} }
function setOutput(id,data){document.getElementById(id).textContent=typeof data==='string'?data:JSON.stringify(data,null,2);}

async function connectBackend(){
  const field=document.getElementById('apiBase'); API_BASE=(field.value||'').trim().replace(/\/$/,''); localStorage.setItem('noiop_api_base',API_BASE);
  setConn('Connecting...');
  try{const h=await api('/health'); setConn(`CONNECTED | ${h.service} | ${h.version} | persistent store: ${h.persistent_store} | opportunities: ${h.opportunity_count}`,true); await loadOpportunities();}
  catch(e){setConn(`OFFLINE: ${e.message}`);}
}

function formPayload(){
  return {
    tenant_id:document.getElementById('fsTenant').value,
    title:document.getElementById('fsTitle').value,
    description:document.getElementById('fsDescription').value,
    demand:Number(document.getElementById('fsDemand').value), strategic_alignment:Number(document.getElementById('fsAlignment').value),
    readiness:Number(document.getElementById('fsReadiness').value), risk_inverse:Number(document.getElementById('fsRisk').value),
    evidence_quality:Number(document.getElementById('fsEvidence').value), timing:Number(document.getElementById('fsTiming').value)
  };
}

async function createOpportunity(){
  try{const r=await api('/api/v1/opportunities',{method:'POST',body:JSON.stringify(formPayload())}); selectedOpportunityId=r.id; setOutput('workspaceOutput',r); await loadOpportunities();}
  catch(e){setOutput('workspaceOutput','Create failed: '+e.message);}
}

async function loadOpportunities(){
  try{
    const r=await api('/api/v1/opportunities'); const body=document.getElementById('liveRows');
    body.innerHTML=r.items.map(x=>`<tr onclick="selectOpportunity('${x.id}')"><td>${x.title}</td><td>${x.tenant_id}</td><td>${x.status}</td><td>${new Date(x.updated_at).toLocaleString()}</td><td><button onclick="event.stopPropagation();selectOpportunity('${x.id}')">Open</button></td></tr>`).join('');
    document.getElementById('liveCount').textContent=r.count;
  }catch(e){setOutput('workspaceOutput','Load failed: '+e.message);}
}

async function selectOpportunity(id){
  selectedOpportunityId=id;
  try{const r=await api(`/api/v1/opportunities/${id}`); setOutput('workspaceOutput',r); document.getElementById('selectedId').textContent=id;}
  catch(e){setOutput('workspaceOutput','Open failed: '+e.message);}
}

async function assessSelected(){
  if(!selectedOpportunityId) return setOutput('workspaceOutput','Select an opportunity first.');
  try{setOutput('workspaceOutput',await api(`/api/v1/opportunities/${selectedOpportunityId}/assess`,{method:'POST',body:'{}'}));}
  catch(e){setOutput('workspaceOutput','Assessment failed: '+e.message);}
}

async function recordDecision(){
  if(!selectedOpportunityId) return setOutput('workspaceOutput','Select an opportunity first.');
  const payload={actor:actor(),decision:document.getElementById('decisionType').value,rationale:document.getElementById('decisionRationale').value};
  try{setOutput('workspaceOutput',await api(`/api/v1/opportunities/${selectedOpportunityId}/decisions`,{method:'POST',body:JSON.stringify(payload)})); await loadOpportunities();}
  catch(e){setOutput('workspaceOutput','Decision failed: '+e.message);}
}

async function recordValue(){
  if(!selectedOpportunityId) return setOutput('workspaceOutput','Select an opportunity first.');
  const payload={expected_value:Number(document.getElementById('fsExpected').value),realized_value:Number(document.getElementById('fsRealized').value),currency:'SAR'};
  try{setOutput('workspaceOutput',await api(`/api/v1/opportunities/${selectedOpportunityId}/value-events`,{method:'POST',body:JSON.stringify(payload)}));}
  catch(e){setOutput('workspaceOutput','Value event failed: '+e.message);}
}

async function showAudit(){
  if(!selectedOpportunityId) return setOutput('workspaceOutput','Select an opportunity first.');
  try{setOutput('workspaceOutput',await api(`/api/v1/opportunities/${selectedOpportunityId}/audit`));}
  catch(e){setOutput('workspaceOutput','Audit failed: '+e.message);}
}

async function livePortfolio(){
  try{setOutput('workspaceOutput',await api('/api/v1/portfolio/live'));}
  catch(e){setOutput('workspaceOutput','Portfolio failed: '+e.message);}
}

window.addEventListener('DOMContentLoaded',()=>{
  document.getElementById('apiBase').value=API_BASE;
  if(API_BASE || location.protocol.startsWith('http')) connectBackend();
});
