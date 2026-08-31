import { api } from "./api.js";
import { state } from "./state.js";
import { switchView, openContextDrawer, closeContextDrawer } from "./views.js";
import { initMap, initializeMapTools, focusIncident, clearIncidentFocus, clearCellSelection, focusHighestRisk, focusCellById, map } from "./map.js";
import { initIncidents } from "./incidents.js";
import { initScenarios } from "./scenarios.js";
import { initIntelligence } from "./intelligence.js";

const n=(v,d=1)=>Number.isFinite(Number(v))?Number(v).toFixed(d):"—";
const esc=v=>String(v??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");

function toast(title,message){
  const stack=document.getElementById("toast-stack");
  if(!stack)return;
  const node=document.createElement("div");
  node.className="toast";
  node.innerHTML=`<strong>${esc(title)}</strong><span>${esc(message)}</span>`;
  stack.appendChild(node);
  setTimeout(()=>node.remove(),3400);
}

async function loadOverview(){
  const [risk,alerts]=await Promise.all([api.risk(),api.alerts()]);
  state.riskRecords=risk.data||[];
  state.alerts=alerts.data||[];
  const counts={LOW:0,MODERATE:0,HIGH:0,EXTREME:0};
  state.riskRecords.forEach(x=>{if(counts[x.severity]!=null)counts[x.severity]++;});
  const active=state.alerts.filter(x=>Number(x.should_alert)===1).length;
  const zones=state.incidents.length;
  document.getElementById("hero-extreme").textContent=counts.EXTREME.toLocaleString();
  document.getElementById("overview-cells").textContent=state.riskRecords.length.toLocaleString();
  document.getElementById("overview-high").textContent=counts.HIGH.toLocaleString();
  document.getElementById("overview-zones").textContent=zones.toLocaleString();
  document.getElementById("overview-alerts").textContent=active.toLocaleString();
  document.getElementById("map-kpi-risk").textContent=counts.EXTREME.toLocaleString();
  document.getElementById("map-kpi-high").textContent=(counts.HIGH+counts.EXTREME).toLocaleString();
  document.getElementById("map-kpi-incidents").textContent=zones.toLocaleString();
  const badge=document.getElementById("overview-state");
  badge.textContent=counts.EXTREME>0?"EXTREME AREAS":counts.HIGH>0?"ELEVATED":"STABLE";
  document.getElementById("freshness-text").textContent=`${new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})} local snapshot`;
  const top=[...state.riskRecords].sort((a,b)=>Number(b.unified_risk_score)-Number(a.unified_risk_score))[0];
  document.getElementById("signal-title").textContent=top?`Strongest signal at ${top.cell_id}`:"Current risk landscape";
  document.getElementById("signal-text").textContent=top?`Risk ${n(top.unified_risk_score,1)} is ${String(top.severity||"").toLowerCase()} with ${top.driver_1}, ${top.driver_2}, and ${top.driver_3} leading the current assessment.`:"Live intelligence loaded from AwareOn.";
  document.getElementById("signal-driver").textContent=top?`Lead driver · ${top.driver_1}`:"Lead driver · —";
  document.getElementById("signal-confidence").textContent=top?`Confidence · ${n(top.confidence_score)}%`:"Confidence · —";
  document.getElementById("distribution").innerHTML=["LOW","MODERATE","HIGH","EXTREME"].map(level=>{
    const total=state.riskRecords.length||1;
    const pct=(counts[level]/total)*100;
    return `<div class="distribution-row"><span>${level}</span><div class="distribution-track"><div class="distribution-fill risk-${level.toLowerCase()}" style="width:${pct.toFixed(1)}%"></div></div><b>${counts[level].toLocaleString()}</b></div>`;
  }).join("");
}

function renderCellAssessment(data){
  const p=document.getElementById("assessment");
  if(!p)return;
  document.getElementById("selection-title").textContent=data.cell_id||"Selected cell";
  p.classList.remove("empty");
  p.innerHTML=`<div class="assessment-row"><span class="assessment-label">Unified risk</span><b class="assessment-value">${n(data.unified_risk_score,2)}</b></div><div class="assessment-row"><span class="assessment-label">Severity</span><b class="assessment-value">${esc(data.severity)}</b></div><div class="assessment-row"><span class="assessment-label">Warning</span><b class="assessment-value">${esc(data.warning_state)}</b></div><div class="assessment-row"><span class="assessment-label">Confidence</span><b class="assessment-value">${n(data.confidence_score)}%</b></div><div class="driver"><strong>Decision drivers</strong><div>${esc(data.driver_1)} · ${n(data.driver_1_score)}</div><div>${esc(data.driver_2)} · ${n(data.driver_2_score)}</div><div>${esc(data.driver_3)} · ${n(data.driver_3_score)}</div></div><button class="primary-button" id="full-assessment" type="button">Open full assessment</button>`;
  document.getElementById("full-assessment").onclick=async()=>{
    try{
      const x=await api.assessment(data.cell_id);
      p.innerHTML=`<div class="assessment-row"><span class="assessment-label">Unified risk</span><b class="assessment-value">${n(x.unified_risk_score,2)}</b></div><div class="assessment-row"><span class="assessment-label">Severity</span><b class="assessment-value">${esc(x.severity)}</b></div><div class="assessment-row"><span class="assessment-label">Warning</span><b class="assessment-value">${esc(x.warning_state)}</b></div><div class="assessment-row"><span class="assessment-label">Susceptibility</span><b class="assessment-value">${n(Number(x.susceptibility_probability)*100,1)}%</b></div><div class="assessment-row"><span class="assessment-label">Terrain</span><b class="assessment-value">${n(x.terrain_instability_score)}</b></div><div class="assessment-row"><span class="assessment-label">Exposure</span><b class="assessment-value">${n(x.exposure_score)}</b></div><div class="assessment-row"><span class="assessment-label">Spatial pressure</span><b class="assessment-value">${n(x.spatial_pressure_score)}</b></div><div class="assessment-row"><span class="assessment-label">Confidence</span><b class="assessment-value">${n(x.confidence_score)}%</b></div><div class="recommendation"><strong>Recommendation</strong><p>${esc(x.recommendation)}</p></div>`;
    }catch(e){toast("Assessment unavailable",e.message);}
  };
}
function renderIncidentAssessment(p){
  document.getElementById("selection-title").textContent=p.incident_id||"Incident";
  const el=document.getElementById("assessment");
  el.classList.remove("empty");
  el.innerHTML=`<div class="assessment-row"><span class="assessment-label">Priority</span><b class="assessment-value">${esc(p.priority_level)}</b></div><div class="assessment-row"><span class="assessment-label">Priority score</span><b class="assessment-value">${n(p.priority_score)}</b></div><div class="assessment-row"><span class="assessment-label">Rank</span><b class="assessment-value">#${p.priority_rank}</b></div><div class="assessment-row"><span class="assessment-label">Maximum risk</span><b class="assessment-value">${n(p.max_risk_score)}</b></div><div class="assessment-row"><span class="assessment-label">Affected cells</span><b class="assessment-value">${p.cell_count}</b></div><div class="recommendation"><strong>Priority recommendation</strong><p>${esc(p.priority_recommendation)}</p></div>`;
}
function resetAssessment(){
  document.getElementById("selection-title").textContent="Select a location";
  const p=document.getElementById("assessment");
  p.className="assessment empty";
  p.innerHTML=`<div class="empty-symbol">◈</div><p>Click a risk cell or incident on the map to investigate it.</p>`;
}
function initSelection(){
  window.addEventListener("awareon:cell",e=>{renderCellAssessment(e.detail);openContextDrawer();});
  window.addEventListener("awareon:incident",e=>{renderIncidentAssessment(e.detail);openContextDrawer();});
  window.addEventListener("awareon:clear-selection",resetAssessment);
  window.addEventListener("awareon:cell-quick",e=>{renderCellAssessment(e.detail);switchView("risk-map",{openDrawer:true});});
  document.getElementById("clear-selection")?.addEventListener("click",()=>{clearIncidentFocus();clearCellSelection();resetAssessment();});
}
function initDrawer(){
  document.getElementById("drawer-toggle")?.addEventListener("click",()=>{
    const panel=document.getElementById("context-panel");
    panel?.classList.toggle("collapsed");
  });
  document.getElementById("drawer-close")?.addEventListener("click",closeContextDrawer);
  document.addEventListener("keydown",e=>{
    if(e.key==="Escape" && !document.getElementById("command-overlay")?.hidden) return;
    if(e.key==="Escape") closeContextDrawer();
  });
}
function initNav(){
  document.querySelectorAll(".rail-item,[data-view]").forEach(b=>{
    if(b.classList.contains("prompt-card"))return;
    b.addEventListener("click",()=>{
      const view=b.dataset.view;
      if(view)switchView(view,{openDrawer:true});
    });
  });
  document.getElementById("brand-home")?.addEventListener("click",()=>switchView("overview",{openDrawer:true}));
}
function searchResultRows(query){
  const q=query.trim().toLowerCase();
  if(!q)return [];
  const cells=state.riskRecords.filter(x=>String(x.cell_id).toLowerCase().includes(q)).slice(0,8).map(x=>({title:x.cell_id,sub:`Risk ${n(x.unified_risk_score)} · ${x.severity}`,tag:"CELL",go:()=>{switchView("risk-map");focusCellById(x.cell_id);}}));
  const incidents=state.incidents.filter(x=>String(x.incident_id).toLowerCase().includes(q)).slice(0,6).map(x=>({title:x.incident_id,sub:`${x.priority_level} · priority ${n(x.priority_score)}`,tag:"INCIDENT",go:()=>focusIncident(x.incident_id)}));
  return [...cells,...incidents];
}
function initSearch(){
  const input=document.getElementById("global-search");
  const results=document.getElementById("command-results");
  const overlay=document.getElementById("command-overlay");
  const modalInput=document.getElementById("command-modal-input");
  const modalResults=document.getElementById("command-modal-results");
  const render=(target,q)=>{
    const rows=searchResultRows(q);
    if(!rows.length){target.innerHTML=q?`<div class="search-empty">No matching AwareOn object.</div>`:"";target.hidden=!q;return;}
    target.innerHTML=rows.map((r,i)=>`<button class="command-result" data-i="${i}" type="button"><div><strong>${esc(r.title)}</strong><span>${esc(r.sub)}</span></div><span class="result-tag">${esc(r.tag)}</span></button>`).join("");
    target.hidden=false;
    target.querySelectorAll(".command-result").forEach((b,i)=>b.onclick=()=>{rows[i].go();target.hidden=true;input.value="";});
  };
  input?.addEventListener("input",()=>render(results,input.value));
  input?.addEventListener("keydown",e=>{if(e.key==="Enter"){const rows=searchResultRows(input.value);if(rows[0]){rows[0].go();results.hidden=true;input.value="";}}if(e.key==="Escape"){results.hidden=true;input.blur();}});
  const openOverlay=()=>{overlay.hidden=false;modalInput.value=input?.value||"";modalInput.focus();render(modalResults,modalInput.value);};
  document.getElementById("command-palette-button")?.addEventListener("click",openOverlay);
  modalInput?.addEventListener("input",()=>render(modalResults,modalInput.value));
  modalInput?.addEventListener("keydown",e=>{if(e.key==="Enter"){const rows=searchResultRows(modalInput.value);if(rows[0]){rows[0].go();overlay.hidden=true;}}});
  document.getElementById("command-close")?.addEventListener("click",()=>overlay.hidden=true);
  overlay?.addEventListener("click",e=>{if(e.target===overlay)overlay.hidden=true;});
  document.addEventListener("keydown",e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();input?.focus();}if(e.key==="Escape"){overlay.hidden=true;}});
}
function initPresentation(){
  document.getElementById("theme-button")?.addEventListener("click",()=>{
    const shell=document.getElementById("app");
    state.presentationMode=!state.presentationMode;
    shell.classList.toggle("map-focus",state.presentationMode);
    if(state.presentationMode)closeContextDrawer();else openContextDrawer();
  });
  document.getElementById("refresh-data")?.addEventListener("click",()=>location.reload());
}
function initScenarioEvents(){window.addEventListener("awareon:scenario",e=>{const {pct,result}=e.detail;if(result?.supported)toast("Scenario ready",`${pct===0?"Baseline":`+${pct}% rainfall`} · ${result.escalating_cells} escalating cells.`);});}
async function boot(){
  initNav();initDrawer();initSelection();initSearch();initPresentation();initScenarioEvents();initIntelligence();initializeMapTools();
  try{
    await api.health();
    document.getElementById("rail-status-text").textContent="Operational";
    document.getElementById("rail-status-orb").style.background="#1fa86b";
    document.getElementById("map-status-text").textContent="Live intelligence";
    document.getElementById("map-status-meta").textContent="Backend connected";
    document.getElementById("map-status-orb").style.background="#1fa86b";
  }catch(e){
    document.getElementById("rail-status-text").textContent="Offline";
    document.getElementById("map-status-text").textContent="Backend unavailable";
    document.getElementById("map-status-meta").textContent=e.message;
    toast("Backend unavailable",e.message);
  }
  try{
    const incidentsPromise=initIncidents();
    const mapPromise=initMap();
    const scenarioPromise=initScenarios();
    await Promise.all([loadOverview(),incidentsPromise,mapPromise]);
    scenarioPromise.catch(e=>console.error("Scenario initialization failed:",e));
    state.ready=true;
    toast("AwareOn ready","Spatial decision intelligence is online.");
  }catch(e){console.error(e);toast("Some intelligence failed to load",e.message);}
}
boot();
