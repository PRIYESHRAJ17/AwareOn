import { api } from "./api.js";
import { state } from "./state.js";
import { focusIncident } from "./map.js";

const n=(v,d=1)=>Number.isFinite(Number(v))?Number(v).toFixed(d):"—";
const esc=v=>String(v??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");

function requestFocus(id){
  if(state.incidentLayer){ focusIncident(id); return; }
  state.pendingIncidentId = String(id);
  const started = Date.now();
  const timer = setInterval(()=>{
    if(state.incidentLayer){ clearInterval(timer); focusIncident(id); return; }
    if(Date.now()-started>15000){ clearInterval(timer); console.warn("Incident focus timeout:",id); }
  },100);
}

export async function initIncidents(){
  const data=await api.incidents();
  state.incidents=(data.features||[]).map(f=>f.properties).sort((a,b)=>Number(a.priority_rank||999999)-Number(b.priority_rank||999999));
  const dot=document.getElementById("rail-incident-dot"); if(dot) dot.style.display=state.incidents.length?"block":"none";
  const total=document.getElementById("incident-total"); if(total) total.textContent=state.incidents.length.toLocaleString();
  const mapTotal=document.getElementById("map-kpi-incidents"); if(mapTotal) mapTotal.textContent=state.incidents.length.toLocaleString();
  renderPriorityList();
  renderIncidentQueue();
}

function renderPriorityList(){
  const el=document.getElementById("priority-list"); if(!el)return;
  el.innerHTML=state.incidents.slice(0,5).map(x=>`<button class="priority-item" type="button" data-id="${esc(x.incident_id)}"><div class="priority-rank">#${x.priority_rank}</div><div><div class="priority-id">${esc(x.incident_id)}</div><div class="priority-meta">${x.cell_count} cells · max risk ${n(x.max_risk_score)}</div><span class="priority-level">${esc(x.priority_level)}</span></div><div class="priority-score">${n(x.priority_score)}</div></button>`).join("")||`<div class="muted">No prioritized zones.</div>`;
  el.querySelectorAll(".priority-item").forEach(row=>row.addEventListener("click",()=>requestFocus(row.dataset.id)));
}

function renderIncidentQueue(){
  const el=document.getElementById("incident-list"); if(!el)return;
  el.innerHTML=state.incidents.slice(0,100).map(x=>`<article class="incident-card" data-id="${esc(x.incident_id)}" tabindex="0" role="button"><div class="incident-card-head"><span class="incident-id">${esc(x.incident_id)}</span><span class="priority-level">${esc(x.priority_level)}</span></div><div class="incident-grid"><div class="incident-metric"><span>Rank</span><b>#${x.priority_rank}</b></div><div class="incident-metric"><span>Priority</span><b>${n(x.priority_score)}</b></div><div class="incident-metric"><span>Max risk</span><b>${n(x.max_risk_score)}</b></div><div class="incident-metric"><span>Cells</span><b>${x.cell_count}</b></div></div></article>`).join("")||`<div class="muted">No incidents available.</div>`;
  el.querySelectorAll(".incident-card").forEach(card=>{
    const open=()=>requestFocus(card.dataset.id);
    card.addEventListener("click",open);
    card.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();open();}});
  });
}
