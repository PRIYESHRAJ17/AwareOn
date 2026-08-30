import { api } from "./api.js";
import { state } from "./state.js";
import { switchView } from "./views.js";
import { initMap, initializeMapTools, focusIncident, clearIncidentFocus, clearCellSelection, focusHighestRisk, map } from "./map.js";
import { initIncidents } from "./incidents.js";
import { initScenarios } from "./scenarios.js";
import { initIntelligence } from "./intelligence.js";

const n=(v,d=1)=>Number.isFinite(Number(v))?Number(v).toFixed(d):"—";
const esc=v=>String(v??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");

function toast(title,message){const stack=document.getElementById("toast-stack"),node=document.createElement("div");node.className="toast";node.innerHTML=`<strong>${esc(title)}</strong><span>${esc(message)}</span>`;stack.appendChild(node);setTimeout(()=>node.remove(),3400);}

async function loadOverview(){
  const [risk,alerts]=await Promise.all([api.risk(),api.alerts()]);
  state.riskRecords=risk.data||[];state.alerts=alerts.data||[];
  const c={LOW:0,MODERATE:0,HIGH:0,EXTREME:0};state.riskRecords.forEach(x=>{if(c[x.severity]!=null)c[x.severity]++});
  const active=state.alerts.filter(x=>Number(x.should_alert)===1).length;
  const zones=state.incidents.length;
  document.getElementById("hero-extreme").textContent=c.EXTREME.toLocaleString();
  document.getElementById("overview-cells").textContent=state.riskRecords.length.toLocaleString();
  document.getElementById("overview-high").textContent=c.HIGH.toLocaleString();
  document.getElementById("overview-zones").textContent=zones.toLocaleString();
  document.getElementById("overview-alerts").textContent=active.toLocaleString();
  document.getElementById("map-kpi-risk").textContent=c.EXTREME.toLocaleString();
  document.getElementById("map-kpi-high").textContent=(c.HIGH+c.EXTREME).toLocaleString();
  const badge=document.getElementById("overview-state");badge.textContent=c.EXTREME>0?"EXTREME AREAS":c.HIGH>0?"ELEVATED":"STABLE";
  document.getElementById("freshness-text").textContent=`${new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})} local snapshot`;
  const top=[...state.riskRecords].sort((a,b)=>Number(b.unified_risk_score)-Number(a.unified_risk_score))[0];
  document.getElementById("signal-title").textContent=top?`Strongest signal at ${top.cell_id}`:"Current risk landscape";
  document.getElementById("signal-text").textContent=top?`Unified risk ${n(top.unified_risk_score,1)} is ${top.severity.toLowerCase()} with ${top.driver_1}, ${top.driver_2}, and ${top.driver_3} as the leading drivers.`:"Live intelligence loaded from AwareOn.";
  document.getElementById("signal-driver").textContent=top?`Lead driver · ${top.driver_1}`:"Lead driver · —";
  document.getElementById("signal-confidence").textContent=top?`Confidence · ${n(top.confidence_score)}%`:"Confidence · —";
  document.getElementById("distribution").innerHTML=["LOW","MODERATE","HIGH","EXTREME"].map(k=>`<div class="distribution-row"><span class="dist-name"><i class="risk-dot ${k.toLowerCase()}"></i>${k}</span><b>${c[k].toLocaleString()}</b></div><div class="bar"><span class="${k.toLowerCase()}" style="width:${state.riskRecords.length?c[k]/state.riskRecords.length*100:0}%"></span></div>`).join("");
}

function renderCellAssessment(data){
  const p=document.getElementById("assessment");document.getElementById("selection-title").textContent=data.cell_id;p.classList.remove("empty");
  p.innerHTML=`<div class="assessment-row"><span class="assessment-label">Unified risk</span><b class="assessment-value">${n(data.unified_risk_score,2)}</b></div><div class="assessment-row"><span class="assessment-label">Severity</span><b class="assessment-value">${esc(data.severity)}</b></div><div class="assessment-row"><span class="assessment-label">Warning state</span><b class="assessment-value">${esc(data.warning_state)}</b></div><div class="assessment-row"><span class="assessment-label">Confidence</span><b class="assessment-value">${n(data.confidence_score)}%</b></div><div class="driver"><strong>Decision drivers</strong><div>${esc(data.driver_1)} · ${n(data.driver_1_score)}</div><div>${esc(data.driver_2)} · ${n(data.driver_2_score)}</div><div>${esc(data.driver_3)} · ${n(data.driver_3_score)}</div></div><button class="primary-button" id="full-assessment" style="margin-top:10px">Open full assessment</button>`;
  document.getElementById("full-assessment").onclick=async()=>{try{const x=await api.assessment(data.cell_id);renderFullAssessment(x);}catch(e){toast("Assessment unavailable",e.message)}};
}

function renderFullAssessment(x){const p=document.getElementById("assessment");p.innerHTML=`<div class="assessment-row"><span class="assessment-label">Unified risk</span><b class="assessment-value">${n(x.unified_risk_score,2)}</b></div><div class="assessment-row"><span class="assessment-label">Severity</span><b class="assessment-value">${esc(x.severity)}</b></div><div class="assessment-row"><span class="assessment-label">Warning</span><b class="assessment-value">${esc(x.warning_state)}</b></div><div class="assessment-row"><span class="assessment-label">Susceptibility</span><b class="assessment-value">${(Number(x.susceptibility_probability)*100).toFixed(1)}%</b></div><div class="assessment-row"><span class="assessment-label">Terrain</span><b class="assessment-value">${n(x.terrain_instability_score)}</b></div><div class="assessment-row"><span class="assessment-label">Exposure</span><b class="assessment-value">${n(x.exposure_score)}</b></div><div class="assessment-row"><span class="assessment-label">Spatial pressure</span><b class="assessment-value">${n(x.spatial_pressure_score)}</b></div><div class="assessment-row"><span class="assessment-label">Confidence</span><b class="assessment-value">${n(x.confidence_score)}%</b></div><div class="assessment-row"><span class="assessment-label">Uncertainty</span><b class="assessment-value">${n(x.uncertainty_score)}%</b></div><div class="driver"><strong>Top drivers</strong><div>${esc(x.driver_1)} · ${n(x.driver_1_score)}</div><div>${esc(x.driver_2)} · ${n(x.driver_2_score)}</div><div>${esc(x.driver_3)} · ${n(x.driver_3_score)}</div></div><div class="recommendation"><strong>Recommendation</strong><p>${esc(x.recommendation)}</p></div>`;}

function renderIncidentAssessment(p){document.getElementById("selection-title").textContent=p.incident_id;const el=document.getElementById("assessment");el.classList.remove("empty");el.innerHTML=`<div class="assessment-row"><span class="assessment-label">Priority level</span><b class="assessment-value">${esc(p.priority_level)}</b></div><div class="assessment-row"><span class="assessment-label">Priority score</span><b class="assessment-value">${n(p.priority_score)}</b></div><div class="assessment-row"><span class="assessment-label">Priority rank</span><b class="assessment-value">#${p.priority_rank}</b></div><div class="assessment-row"><span class="assessment-label">Maximum risk</span><b class="assessment-value">${n(p.max_risk_score)}</b></div><div class="assessment-row"><span class="assessment-label">Mean risk</span><b class="assessment-value">${n(p.mean_risk_score)}</b></div><div class="assessment-row"><span class="assessment-label">Affected cells</span><b class="assessment-value">${p.cell_count}</b></div><div class="driver"><strong>Category</strong><div>${esc(p.incident_category)}</div></div><div class="driver"><strong>Affected cells</strong><div>${esc(p.affected_cells)}</div></div><div class="recommendation"><strong>Priority recommendation</strong><p>${esc(p.priority_recommendation)}</p></div>`;}

function initSelection(){
  window.addEventListener("awareon:cell",e=>renderCellAssessment(e.detail));
  window.addEventListener("awareon:incident",e=>renderIncidentAssessment(e.detail));
  window.addEventListener("awareon:clear-selection",()=>resetAssessment());
  document.getElementById("clear-selection").onclick=()=>{clearIncidentFocus();clearCellSelection();resetAssessment()};
  document.getElementById("clear-focus").onclick=clearIncidentFocus;
}
function resetAssessment(){document.getElementById("selection-title").textContent="Nothing selected";const p=document.getElementById("assessment");p.className="assessment empty";p.innerHTML=`<div class="empty-symbol">◈</div><p>Select a risk cell or incident marker to investigate its decision state.</p>`;}

function initNav(){
  document.querySelectorAll(".rail-item").forEach(b=>b.onclick=()=>switchView(b.dataset.view));
  document.querySelectorAll("[data-view]").forEach(b=>{if(!b.classList.contains("rail-item"))b.onclick=()=>switchView(b.dataset.view)});
  document.getElementById("brand-home").onclick=()=>switchView("overview");
}

function initCommandPalette(){
  const overlay=document.getElementById("command-overlay"),input=document.getElementById("global-search"),results=document.getElementById("command-results");
  const open=()=>{overlay.hidden=false;input.value="";renderResults("");setTimeout(()=>input.focus(),30)};
  const close=()=>overlay.hidden=true;
  document.getElementById("search-trigger").onclick=open;document.getElementById("search-trigger").onkeydown=e=>{if(e.key==="Enter"||e.key===" ")open()};document.getElementById("mobile-search").onclick=open;document.getElementById("command-palette-button").onclick=open;document.getElementById("command-close").onclick=close;overlay.addEventListener("click",e=>{if(e.target===overlay)close});document.addEventListener("keydown",e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();open()}if(e.key==="Escape")close()});input.oninput=()=>renderResults(input.value.trim().toLowerCase());
  function renderResults(q){
    const commands=[{title:"Open Command Center",sub:"System overview",tag:"WORKSPACE",go:()=>switchView("overview")},{title:"Open Risk Explorer",sub:"Spatial investigation",tag:"WORKSPACE",go:()=>switchView("risk-map")},{title:"Open Incident Command",sub:"Priority queue",tag:"WORKSPACE",go:()=>switchView("incidents")},{title:"Open Scenario Lab",sub:"Counterfactual analysis",tag:"WORKSPACE",go:()=>switchView("scenarios")},{title:"Open Intelligence",sub:"Investigation workspace",tag:"WORKSPACE",go:()=>switchView("intelligence")}];
    const cells=state.riskRecords.filter(x=>String(x.cell_id).toLowerCase().includes(q)).slice(0,6).map(x=>({title:x.cell_id,sub:`Risk ${n(x.unified_risk_score)} · ${x.severity}`,tag:"CELL",go:()=>{switchView("risk-map");focusCellById(x.cell_id)}}));
    const incidents=state.incidents.filter(x=>String(x.incident_id).toLowerCase().includes(q)).slice(0,6).map(x=>({title:x.incident_id,sub:`${x.priority_level} · priority ${n(x.priority_score)}`,tag:"INCIDENT",go:()=>focusIncident(x.incident_id)}));
    const all=q?[...cells,...incidents]:commands;results.innerHTML=all.length?all.map((r,i)=>`<button class="command-result" data-i="${i}"><div><strong>${esc(r.title)}</strong><span>${esc(r.sub)}</span></div><span class="result-tag">${r.tag}</span></button>`).join(""):`<div class="muted">No matching AwareOn result.</div>`;results.querySelectorAll(".command-result").forEach((b,i)=>b.onclick=()=>{all[i].go();close()});
  }
  window.awareonOpenSearch=open;
}
function focusCellById(id){let target=null;state.riskLayer?.eachLayer(l=>{if(String(l.feature.properties.cell_id)===String(id))target=l});if(target){target.fire("click");}}

function initPresentation(){document.getElementById("theme-button").onclick=()=>{state.presentationMode=!state.presentationMode;document.body.classList.toggle("presentation",state.presentationMode);toast("Presentation mode",state.presentationMode?"Reduced chrome for a cleaner map view.":"Full workspace restored.")};document.getElementById("refresh-data").onclick=()=>location.reload()}

function initScenarioEvents(){window.addEventListener("awareon:scenario",e=>{const {pct,result}=e.detail;if(!result?.supported)return;toast("Scenario ready",`${pct===0?"Baseline":`+${pct}% rainfall`} · ${result.escalating_cells} escalating cells.`);state.scenarioRecords=result.records||[];updateTimelineFromScenario(result)})}
function updateTimelineFromScenario(result){const mean=Number(result.mean_risk_score);const pos=Math.max(0,Math.min(100,mean));const fill=document.getElementById("timeline-fill");const now=document.getElementById("timeline-now");if(fill)fill.style.width=`${pos}%`;if(now)now.style.left=`${pos}%`}

function updateTimelineFromRisk(){const scores=state.riskRecords.map(x=>Number(x.unified_risk_score)).filter(Number.isFinite);const value=scores.length?Math.max(...scores):0;const fill=document.getElementById("timeline-fill");const now=document.getElementById("timeline-now");if(fill)fill.style.width=`${Math.max(0,Math.min(100,value))}%`;if(now)now.style.left=`${Math.max(0,Math.min(100,value))}%`}

function initTimelineControls(){const track=document.querySelector(".timeline-track");if(!track)return;track.setAttribute("role","slider");track.setAttribute("tabindex","0");track.setAttribute("aria-label","Risk state");const focusAt=(clientX)=>{const rect=track.getBoundingClientRect();const pct=Math.max(0,Math.min(100,((clientX-rect.left)/rect.width)*100));const scores=state.riskRecords.map(x=>({x,score:Number(x.unified_risk_score)})).filter(v=>Number.isFinite(v.score)).sort((a,b)=>Math.abs(a.score-pct)-Math.abs(b.score-pct));if(scores[0]){switchView("risk-map");const id=scores[0].x.cell_id;let target=null;state.riskLayer?.eachLayer(l=>{if(String(l.feature?.properties?.cell_id)===String(id))target=l});if(target)target.fire("click");}};track.addEventListener("click",e=>focusAt(e.clientX));track.addEventListener("keydown",e=>{if(e.key==="ArrowLeft"||e.key==="ArrowRight"){e.preventDefault();const rect=track.getBoundingClientRect();const current=e.key==="ArrowLeft"?rect.left+rect.width*0.45:rect.left+rect.width*0.55;focusAt(current);}})}

async function boot(){
  initNav();initSelection();initCommandPalette();initPresentation();initScenarioEvents();initIntelligence();initializeMapTools();initTimelineControls();
  try{
    await api.health();
    document.getElementById("rail-status-text").textContent="Operational";document.getElementById("rail-status-orb").style.background="#19a463";document.getElementById("rail-status-orb").style.boxShadow="0 0 0 4px rgba(25,164,99,.12)";document.getElementById("map-status-text").textContent="Live intelligence";document.getElementById("map-status-meta").textContent="Backend connected";document.getElementById("map-status-orb").style.background="#19a463";
  }catch(e){document.getElementById("rail-status-text").textContent="Offline";document.getElementById("rail-status-orb").style.background="#de403e";document.getElementById("map-status-text").textContent="Backend unavailable";document.getElementById("map-status-meta").textContent=e.message;document.getElementById("map-status-orb").style.background="#de403e";toast("Backend unavailable",e.message)}
  try{
    const incidentsPromise=initIncidents();
    const mapPromise=initMap();
    const scenarioPromise=initScenarios();
    await Promise.all([loadOverview(),incidentsPromise,mapPromise]);
    scenarioPromise.catch(e=>console.error("Scenario initialization failed:",e));
    state.ready=true;
    document.getElementById("footer-system").textContent=`${state.riskRecords.length.toLocaleString()} cells · ${state.incidents.length.toLocaleString()} zones`;
    updateTimelineFromRisk();
    toast("AwareOn ready","Spatial decision intelligence is online.");
  }catch(e){console.error(e);toast("Some intelligence failed to load",e.message);document.getElementById("map-status-text").textContent="Partial intelligence";document.getElementById("map-status-meta").textContent=e.message}
}
boot();
