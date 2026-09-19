import { api } from "./api.js";
import { state } from "./state.js";
import { switchView, openContextDrawer, closeContextDrawer } from "./views.js";
import { initMap, initializeMapTools, focusIncident, clearIncidentFocus, clearCellSelection, focusHighestRisk, focusCellById, map } from "./map.js";
import { initIncidents } from "./incidents.js";
import { initScenarios, refreshScenarioContext } from "./scenarios.js";
import { initIntelligence, submitQuery } from "./intelligence.js";

const n=(v,d=1)=>Number.isFinite(Number(v))?Number(v).toFixed(d):"—";
const esc=v=>String(v??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");

function toast(title,message){const stack=document.getElementById("toast-stack");if(!stack)return;const node=document.createElement("div");node.className="toast";node.innerHTML=`<strong>${esc(title)}</strong><span>${esc(message)}</span>`;stack.appendChild(node);setTimeout(()=>node.remove(),3400);}

const aboutContent={
 overview:{
   kicker:"OVERVIEW",
   title:"What AwareOn is",
   lead:"AwareOn is a research and decision-support platform for spatial landslide-risk intelligence. It brings modeled risk, environmental signals, historical context, scenario analysis, evidence, confidence, uncertainty, and AI-assisted investigation into one map-first workspace.",
   sections:[
     {title:"What it is designed to do",items:[
       "Help users understand changing landslide-risk conditions across cells and regions.",
       "Connect multiple evidence layers instead of relying on a single risk signal.",
       "Make modelled outputs easier to inspect, compare, explain, and verify."
     ]},
     {title:"What it is not",items:[
       "It is not a replacement for official emergency authorities, evacuation orders, engineering assessments, or field verification.",
       "A scenario result is a modelled counterfactual, not an observation of what is happening on the ground."
     ]},
     {title:"Intended users",items:[
       "Government of India ministries, departments, agencies, and central disaster-management or infrastructure bodies.",
       "State governments and state departments/agencies across India, including disaster-management and public-works teams.",
       "District administrations, local authorities, emergency-response, inspection, monitoring, and field coordination teams.",
       "Roads, transport, utilities, water, environment, and other infrastructure teams responsible for exposed assets or corridors.",
       "Farmers, farm owners, orchards, plantations, agricultural land managers, large landowners, estate owners, and property managers.",
       "Infrastructure and utility operators, private developers, and project planners who need spatial risk context, subject to professional verification.",
       "Universities, researchers, geospatial analysts, academics, and authorized NGOs or resilience organizations."
     ]}
   ]
 },
 how:{
   kicker:"HOW AWAREON WORKS",
   title:"From map to evidence to decision context",
   lead:"AwareOn is designed around a spatial workflow: discover an area, inspect a cell or region, understand the evidence, compare supported scenarios, and review confidence and uncertainty before acting.",
   sections:[
     {title:"Core workflow",items:[
       "Map-first discovery and spatial selection.",
       "Deterministic risk and intelligence engines combine environmental and contextual signals.",
       "Evidence grounding keeps observed, derived, historical, and simulated information distinguishable.",
       "AI-assisted investigation turns supported evidence into understandable explanations and spatial context."
     ]},
     {title:"Human verification remains important",items:[
       "Critical operational decisions should be cross-checked against current official information, professional assessment, and field conditions."
     ]}
   ]
 },
 data:{
   kicker:"DATA & SOURCES",
   title:"Multiple evidence layers with provenance",
   lead:"AwareOn works with available project datasets and publicly available geospatial/environmental information. The system is designed to keep source class and known limitations visible rather than treating every value as equally certain.",
   sections:[
     {title:"Representative intelligence layers",items:[
       "Terrain and topographic characteristics.",
       "Rainfall and triggering conditions.",
       "Soil wetness and related environmental signals.",
       "Historical landslide and disaster context.",
       "SAR / InSAR-derived evidence where available.",
       "Exposure, infrastructure, incidents, and spatial context."
     ]},
     {title:"Evidence classes",items:[
       "Observed — information supplied by a source or observation.",
       "Derived — values calculated by AwareOn intelligence engines.",
       "Historical — past-event/source-backed context.",
       "Simulated — modelled scenario or counterfactual output."
     ]}
   ]
 },
 method:{
   kicker:"METHODOLOGY",
   title:"Multi-signal, confidence-aware analysis",
   lead:"AwareOn combines multiple modeled signals including susceptibility, terrain instability, rainfall triggers, soil wetness, exposure, spatial pressure, temporal signals, anomaly evidence, and confidence/uncertainty information.",
   sections:[
     {title:"Scenario methodology",items:[
       "Supported rainfall states are limited to 0%, +25%, +50%, and +100%.",
       "Scenario views compare supported precomputed/modelled states against the baseline.",
       "Unsupported intermediate states are not presented as if they were simulated."
     ]},
     {title:"Interpretation principle",items:[
       "Risk, confidence, and uncertainty are separate dimensions; a high-risk result with lower confidence should be treated differently from a high-risk result with strong evidence support."
     ]}
   ]
 },
 evidence:{
   kicker:"EVIDENCE & VERIFICATION",
   title:"Grounded outputs with visible limitations",
   lead:"AwareOn is built around evidence traceability. AI responses are intended to stay tied to the current evidence package and to distinguish supported findings from uncertainty or limitations.",
   sections:[
     {title:"Verification principles",items:[
       "Claims should be supportable by the evidence used in the investigation.",
       "Observed and simulated information must remain clearly labelled.",
       "Confidence and uncertainty should not be confused with the risk score itself.",
       "Historical learning does not override newer canonical evidence."
     ]},
     {title:"What users should check",items:[
       "Data freshness and coverage.",
       "Location and scale of the result.",
       "Confidence / uncertainty indicators.",
       "Current official alerts and on-ground conditions before consequential action."
     ]}
   ]
 },
 disclaimer:{
   kicker:"DISCLAIMER & RESPONSIBLE USE",
   title:"Use AwareOn responsibly",
   lead:"AwareOn is a research and decision-support system. Its outputs depend on available data, model assumptions, processing quality, spatial coverage, and the limitations shown by the system. AwareOn does not present itself as an independent emergency authority.",
   sections:[
     {title:"Important limitations",items:[
       "Do not treat an AwareOn result as a guaranteed prediction, official warning, evacuation order, or professional engineering conclusion.",
       "Do not rely on the platform alone for decisions involving life safety, infrastructure safety, land acquisition, emergency response, or financial exposure.",
       "Independent verification with relevant authorities, professionals, and current field conditions remains the user's responsibility."
     ]},
     {title:"Responsible and lawful use",items:[
       "AwareOn does not recommend, endorse, or suggest using the platform for harmful, unlawful, deceptive, unauthorized, or otherwise abusive purposes.",
       "Do not use outputs to intentionally create danger, interfere with emergency response, exploit vulnerable locations, or bypass applicable laws, regulations, or official instructions.",
       "Users are responsible for how they interpret, communicate, and act on information produced by the system."
     ]},
     {title:"Liability and decision responsibility",items:[
       "To the extent permitted by applicable law, AwareOn and its developers/operators are not responsible for losses, damages, or adverse outcomes resulting from misuse, unsupported interpretation, or decisions made solely from model outputs without appropriate verification.",
       "References to intended users do not imply government adoption, certification, endorsement, or operational authorization."
     ]}
   ]
 },
};

function renderAbout(section="overview"){
  state.aboutSection=section;
  const box=document.getElementById("about-content"); if(!box)return;
  const item=aboutContent[section]||aboutContent.overview;
  const sectionMarkup=(item.sections||[]).map(group=>`
    <section class="ao-about-section16">
      <h4>${esc(group.title)}</h4>
      <ul>${group.items.map(text=>`<li>${esc(text)}</li>`).join("")}</ul>
    </section>`).join("");
  box.innerHTML=`
    <article class="ao-about-card16">
      <span class="eyebrow">${esc(item.kicker)}</span>
      <h3>${esc(item.title)}</h3>
      <p class="ao-about-lead16">${esc(item.lead)}</p>
      <div class="ao-about-sections16">${sectionMarkup}</div>
    </article>
    <article class="ao-about-note16">
      <strong>Model honesty</strong>
      <p>AwareOn does not invent unsupported spatial states, scenario values, evidence, or certainty. Users should review the supporting context and applicable limitations before making consequential decisions.</p>
    </article>`;
  document.querySelectorAll("[data-about]").forEach(btn=>{const active=btn.dataset.about===section;btn.classList.toggle("active",active);btn.setAttribute("aria-selected",active?"true":"false");});
}


function renderRiskAnalytics(counts){
  const total=state.riskRecords.length||1;
  const levels=["LOW","MODERATE","HIGH","EXTREME"];
  const donut=document.getElementById("risk-donut-static");
  const totalEl=document.getElementById("donut-total");
  const stops=[]; let cursor=0;
  const colors={LOW:"#2fb47c",MODERATE:"#d8a12a",HIGH:"#e2574c",EXTREME:"#7f282b"};
  levels.forEach(level=>{const start=cursor;cursor+=(counts[level]/total)*360;stops.push(`${colors[level]} ${start}deg ${cursor}deg`);});
  if(donut){donut.style.background=`conic-gradient(${stops.join(",")})`;donut.setAttribute("aria-label",`Risk distribution: ${levels.map(l=>`${l} ${counts[l]}`).join(", ")}`);}
  if(totalEl) totalEl.textContent=state.riskRecords.length.toLocaleString();
  const bars=levels.map(level=>{const pct=(counts[level]/total)*100;return `<div class="ao-static-line16"><span>${level}</span><i><em class="risk-${level.toLowerCase()}" style="width:${pct.toFixed(1)}%"></em></i><b>${counts[level].toLocaleString()}</b></div>`;}).join("");
  const dist=document.getElementById("distribution"); if(dist) dist.innerHTML=bars;
  const riskExplorer=[...levels].map(level=>`<div class="ao-static-line16"><span>${level}</span><i><em class="risk-${level.toLowerCase()}" style="width:${((counts[level]/total)*100).toFixed(1)}%"></em></i><b>${counts[level].toLocaleString()}</b></div>`).join("");
  const a=document.getElementById("risk-explorer-bars"); const b=document.getElementById("risk-explorer-bars-panel"); if(a)a.innerHTML=riskExplorer; if(b)b.innerHTML=riskExplorer;
}

async function loadOverview(){
  const [risk,alerts]=await Promise.all([api.risk(),api.alerts()]);
  state.riskRecords=risk.data||[]; state.alerts=alerts.data||[];
  const counts={LOW:0,MODERATE:0,HIGH:0,EXTREME:0}; state.riskRecords.forEach(x=>{if(counts[x.severity]!=null)counts[x.severity]++;});
  const active=state.alerts.filter(x=>Number(x.should_alert)===1).length; const zones=state.incidents.length;
  const set=(id,v)=>{const el=document.getElementById(id);if(el)el.textContent=v;};
  set("hero-extreme",counts.EXTREME.toLocaleString()); set("overview-cells",state.riskRecords.length.toLocaleString()); set("overview-high",counts.HIGH.toLocaleString()); set("overview-zones",zones.toLocaleString()); set("overview-alerts",active.toLocaleString());
  set("map-kpi-risk",counts.EXTREME.toLocaleString()); set("map-kpi-high",(counts.HIGH+counts.EXTREME).toLocaleString()); set("map-kpi-incidents",zones.toLocaleString());
  set("overview-state",counts.EXTREME>0?"EXTREME AREAS":counts.HIGH>0?"ELEVATED":"STABLE"); set("freshness-text",`${new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})} local snapshot`);
  const top=[...state.riskRecords].sort((a,b)=>Number(b.unified_risk_score)-Number(a.unified_risk_score))[0];
  set("signal-title",top?`Strongest signal at ${top.cell_id}`:"Current risk landscape"); set("signal-text",top?`Risk ${n(top.unified_risk_score,1)} is ${String(top.severity||"").toLowerCase()} with ${top.driver_1}, ${top.driver_2}, and ${top.driver_3} leading the current assessment.`:"Live intelligence loaded from AwareOn."); set("signal-driver",top?`Lead driver · ${top.driver_1}`:"Lead driver · —"); set("signal-confidence",top?`Confidence · ${n(top.confidence_score)}%`:"Confidence · —");
  renderRiskAnalytics(counts);
}

function updateTrustBars(data){
  const root=document.getElementById("cell-trust-bars"); if(!root)return;
  const c=Math.max(0,Math.min(100,Number(data?.confidence_score)||0)); const u=Math.max(0,Math.min(100,Number(data?.uncertainty_score)||0));
  const heads=root.querySelectorAll(":scope > div");
  if(heads[0])heads[0].innerHTML=`<span>Confidence</span><b>${n(c,0)}%</b>`;
  if(heads[1])heads[1].innerHTML=`<span>Uncertainty</span><b>${n(u,0)}%</b>`;
  const em=root.querySelectorAll(":scope > i > em");
  if(em[0])em[0].style.width=`${c}%`;
  if(em[1])em[1].style.width=`${u}%`;
}

function renderCellAssessment(data){
  const p=document.getElementById("assessment"); if(!p)return;
  document.getElementById("selection-title").textContent=data.cell_id||"Selected cell";
  const banner=document.getElementById("selected-context-banner"); if(banner){banner.hidden=false;banner.textContent=`Selected cell · ${data.cell_id} · exact intelligence context`;}
  updateTrustBars(data);
  p.classList.remove("empty");
  p.innerHTML=`<div class="ao-assessment-hero16"><span>UNIFIED RISK</span><strong>${n(data.unified_risk_score,1)}</strong><em>${esc(data.severity)}</em></div><div class="assessment-row"><span class="assessment-label">Warning</span><b class="assessment-value">${esc(data.warning_state)}</b></div><div class="driver"><strong>Decision drivers</strong><div><span>${esc(data.driver_1)}</span><b>${n(data.driver_1_score)}</b></div><div><span>${esc(data.driver_2)}</span><b>${n(data.driver_2_score)}</b></div><div><span>${esc(data.driver_3)}</span><b>${n(data.driver_3_score)}</b></div></div><button class="primary-button" id="full-assessment" type="button">Open full assessment</button><button class="ao-secondary-btn16" id="cell-scenario-open" type="button">Analyze this cell in Scenario Lab</button>`;
  document.getElementById("full-assessment").onclick=async()=>{
    try{const x=await api.assessment(data.cell_id); renderFullAssessment(x); refreshScenarioContext();}
    catch(e){toast("Assessment unavailable",e.message);}
  };
  document.getElementById("cell-scenario-open")?.addEventListener("click",()=>{switchView("scenarios",{openDrawer:true});refreshScenarioContext();});
}
function renderFullAssessment(x){
  const p=document.getElementById("assessment"); if(!p)return; updateTrustBars(x);
  p.innerHTML=`<div class="ao-assessment-hero16"><span>FULL ASSESSMENT · ${esc(x.cell_id)}</span><strong>${n(x.unified_risk_score,1)}</strong><em>${esc(x.severity)}</em></div><div class="assessment-row"><span class="assessment-label">Warning</span><b class="assessment-value">${esc(x.warning_state)}</b></div><div class="assessment-row"><span class="assessment-label">Susceptibility</span><b class="assessment-value">${n(Number(x.susceptibility_probability)*100,1)}%</b></div><div class="assessment-row"><span class="assessment-label">Terrain</span><b class="assessment-value">${n(x.terrain_instability_score)}</b></div><div class="assessment-row"><span class="assessment-label">Exposure</span><b class="assessment-value">${n(x.exposure_score)}</b></div><div class="assessment-row"><span class="assessment-label">Spatial pressure</span><b class="assessment-value">${n(x.spatial_pressure_score)}</b></div><div class="assessment-row"><span class="assessment-label">Confidence</span><b class="assessment-value">${n(x.confidence_score)}%</b></div><div class="recommendation"><strong>Recommendation</strong><p>${esc(x.recommendation)}</p></div><button class="ao-secondary-btn16" type="button" id="full-to-scenario">Analyze tested scenarios</button>`;
  document.getElementById("full-to-scenario")?.addEventListener("click",()=>{state.selectedCell=x;switchView("scenarios",{openDrawer:true});refreshScenarioContext();});
}
function renderIncidentAssessment(p){document.getElementById("selection-title").textContent=p.incident_id||"Incident";const banner=document.getElementById("selected-context-banner");if(banner){banner.hidden=false;banner.textContent=`Incident · ${p.incident_id} · ${p.cell_count} affected cells`;}const el=document.getElementById("assessment");el.classList.remove("empty");el.innerHTML=`<div class="ao-assessment-hero16"><span>INCIDENT PRIORITY</span><strong>#${p.priority_rank}</strong><em>${esc(p.priority_level)}</em></div><div class="assessment-row"><span class="assessment-label">Priority score</span><b class="assessment-value">${n(p.priority_score)}</b></div><div class="assessment-row"><span class="assessment-label">Maximum risk</span><b class="assessment-value">${n(p.max_risk_score)}</b></div><div class="assessment-row"><span class="assessment-label">Affected cells</span><b class="assessment-value">${p.cell_count}</b></div><div class="recommendation"><strong>Priority recommendation</strong><p>${esc(p.priority_recommendation)}</p></div>`;}
function resetAssessment(){document.getElementById("selection-title").textContent="Select a location";const b=document.getElementById("selected-context-banner");if(b){b.hidden=true;b.textContent="";}const p=document.getElementById("assessment");p.className="assessment empty";p.innerHTML=`<div class="empty-symbol">◈</div><p>Select a cell or priority incident to open its dedicated analysis workspace.</p>`;updateTrustBars({confidence_score:0,uncertainty_score:0});}

function initSelection(){
  window.addEventListener("awareon:cell",e=>{state.selectedCell=e.detail||null;renderCellAssessment(e.detail);openContextDrawer();switchView("risk-map",{openDrawer:true});refreshScenarioContext();});
  window.addEventListener("awareon:incident",e=>{renderIncidentAssessment(e.detail);openContextDrawer();switchView("incidents",{openDrawer:true});});
  window.addEventListener("awareon:clear-selection",()=>{state.selectedCell=null;state.scenarioScopeCellId=null;resetAssessment();});
  window.addEventListener("awareon:cell-quick",e=>{state.selectedCell=e.detail||null;renderCellAssessment(e.detail);switchView("risk-map",{openDrawer:true});refreshScenarioContext();});
  document.getElementById("clear-selection")?.addEventListener("click",()=>{clearIncidentFocus();clearCellSelection();resetAssessment();});
}
function initDrawer(){document.getElementById("drawer-toggle")?.addEventListener("click",()=>document.getElementById("context-panel")?.classList.toggle("collapsed"));document.getElementById("drawer-close")?.addEventListener("click",closeContextDrawer);document.addEventListener("keydown",e=>{if(e.key==="Escape")closeContextDrawer();});}
function initNav(){
  document.querySelectorAll(".rail-item,[data-view]").forEach(b=>{
    if(b.classList.contains("prompt-card"))return;
    b.addEventListener("click",()=>{
      const view=b.dataset.view;
      if(view){switchView(view,{openDrawer:true}); if(view==="scenarios")refreshScenarioContext(); if(view==="about")renderAbout(state.aboutSection);}
    });
  });
  document.getElementById("brand-home")?.addEventListener("click",()=>switchView("overview",{openDrawer:true}));
  document.getElementById("about-button")?.addEventListener("click",()=>{switchView("about",{openDrawer:true});renderAbout(state.aboutSection);});
  document.querySelectorAll("[data-about]").forEach(btn=>{
    btn.addEventListener("click",()=>renderAbout(btn.dataset.about));
    btn.addEventListener("keydown",e=>{
      if(!["ArrowRight","ArrowLeft","Home","End"].includes(e.key)) return;
      const tabs=[...document.querySelectorAll("[data-about]")];
      const idx=tabs.indexOf(btn);
      let next=idx;
      if(e.key==="ArrowRight") next=(idx+1)%tabs.length;
      if(e.key==="ArrowLeft") next=(idx-1+tabs.length)%tabs.length;
      if(e.key==="Home") next=0;
      if(e.key==="End") next=tabs.length-1;
      e.preventDefault(); tabs[next].focus(); renderAbout(tabs[next].dataset.about);
    });
  });
  renderAbout("overview");
}
function searchResultRows(query){const q=query.trim().toLowerCase();if(!q)return [];const cells=state.riskRecords.filter(x=>String(x.cell_id).toLowerCase().includes(q)).slice(0,8).map(x=>({title:x.cell_id,sub:`Risk ${n(x.unified_risk_score)} · ${x.severity}`,tag:"CELL",go:()=>{switchView("risk-map",{openDrawer:true});focusCellById(x.cell_id);}}));const incidents=state.incidents.filter(x=>String(x.incident_id).toLowerCase().includes(q)).slice(0,6).map(x=>({title:x.incident_id,sub:`${x.priority_level} · priority ${n(x.priority_score)}`,tag:"INCIDENT",go:()=>focusIncident(x.incident_id)}));return [...cells,...incidents];}
function initSearch(){const input=document.getElementById("global-search"),results=document.getElementById("command-results"),overlay=document.getElementById("command-overlay"),modalInput=document.getElementById("command-modal-input"),modalResults=document.getElementById("command-modal-results");const render=(target,q)=>{const rows=searchResultRows(q);if(!rows.length){target.innerHTML=q?`<div class="search-empty">No exact cell or incident match. Press Ask to investigate naturally.</div>`:"";target.hidden=!q;return;}target.innerHTML=rows.map((r,i)=>`<button class="command-result" data-i="${i}" type="button"><div><strong>${esc(r.title)}</strong><span>${esc(r.sub)}</span></div><span class="result-tag">${esc(r.tag)}</span></button>`).join("");target.hidden=false;target.querySelectorAll(".command-result").forEach((b,i)=>b.onclick=()=>{rows[i].go();target.hidden=true;input.value="";});};input?.addEventListener("input",()=>render(results,input.value));input?.addEventListener("keydown",e=>{if(e.key==="Enter"){const rows=searchResultRows(input.value);if(rows[0]){rows[0].go();results.hidden=true;input.value="";}else if(input.value.trim()){goAI(input.value.trim());}}if(e.key==="Escape"){results.hidden=true;input.blur();}});document.getElementById("top-ai-send")?.addEventListener("click",()=>{const q=input?.value.trim();if(q)goAI(q);});const openOverlay=()=>{overlay.hidden=false;modalInput.value=input?.value||"";modalInput.focus();render(modalResults,modalInput.value);};document.getElementById("command-palette-button")?.addEventListener("click",openOverlay);modalInput?.addEventListener("input",()=>render(modalResults,modalInput.value));modalInput?.addEventListener("keydown",e=>{if(e.key==="Enter"){const rows=searchResultRows(modalInput.value);if(rows[0]){rows[0].go();overlay.hidden=true;}else if(modalInput.value.trim()){goAI(modalInput.value.trim());overlay.hidden=true;}}});document.getElementById("command-close")?.addEventListener("click",()=>overlay.hidden=true);overlay?.addEventListener("click",e=>{if(e.target===overlay)overlay.hidden=true;});}
async function goAI(query){switchView("intelligence",{openDrawer:true});const input=document.getElementById("intelligence-query");if(input){input.value=query;await submitQuery(query);}}
function initPresentation(){document.getElementById("theme-button")?.addEventListener("click",()=>{const shell=document.getElementById("app");state.presentationMode=!state.presentationMode;shell.classList.toggle("map-focus",state.presentationMode);if(state.presentationMode)closeContextDrawer();else openContextDrawer();});document.getElementById("refresh-data")?.addEventListener("click",()=>location.reload());}
function initScenarioEvents(){window.addEventListener("awareon:scenario",e=>{const {pct,result}=e.detail||{};if(result?.supported)toast("Scenario ready",`${pct===0?"Baseline":`+${pct}% rainfall`}${result.cell_specific?" · selected cell":""}`);});}
async function boot(){initNav();initDrawer();initSelection();initSearch();initPresentation();initScenarioEvents();initIntelligence();initializeMapTools();try{await api.health();const ro=document.getElementById("rail-status-orb");if(ro)ro.style.background="#1fa86b";const rt=document.getElementById("rail-status-text");if(rt)rt.textContent="Operational";const ms=document.getElementById("map-status-text");if(ms)ms.textContent="Live intelligence";const mm=document.getElementById("map-status-meta");if(mm)mm.textContent="Backend connected";const mo=document.getElementById("map-status-orb");if(mo)mo.style.background="#1fa86b";}catch(e){toast("Backend unavailable",e.message);}try{const incidentsPromise=initIncidents();const mapPromise=initMap();const scenarioPromise=initScenarios();await Promise.all([loadOverview(),incidentsPromise,mapPromise]);scenarioPromise.catch(e=>console.error("Scenario initialization failed:",e));state.ready=true;}catch(e){console.error(e);toast("Some intelligence failed to load",e.message);}}
boot();
