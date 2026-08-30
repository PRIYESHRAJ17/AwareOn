import { state } from "./state.js";
import { switchView } from "./views.js";
import { focusIncident, focusHighestRisk } from "./map.js";

const n=(v,d=1)=>Number.isFinite(Number(v))?Number(v).toFixed(d):"—";
const esc=v=>String(v??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");

export function initIntelligence(){
  const input=document.getElementById("intelligence-query"),send=document.getElementById("intelligence-submit");
  const submit=()=>{const q=input.value.trim();if(!q)return;append("user",q);input.value="";answer(q);};
  send.onclick=submit;input.onkeydown=e=>{if(e.key==="Enter")submit()};document.querySelectorAll(".prompt-card").forEach(b=>b.onclick=()=>{input.value=b.dataset.prompt;submit()});
  append("assistant","I can currently navigate the strongest risk, incident, and scenario signals available in AwareOn. Deeper evidence orchestration will plug into this same workspace.");
}
function append(role,text){const thread=document.getElementById("chat-thread"),wrap=document.createElement("div");wrap.className=`chat-message ${role}`;wrap.innerHTML=role==="assistant"?`<div class="chat-avatar">AO</div><div class="chat-bubble"><strong>AwareOn</strong><p>${esc(text)}</p></div>`:`<div class="chat-bubble"><strong>You</strong><p>${esc(text)}</p></div>`;thread.appendChild(wrap);thread.scrollTop=thread.scrollHeight;}
function answer(q){
  const lower=q.toLowerCase();
  if(lower.includes("priority")||lower.includes("first")||lower.includes("review")){const x=state.incidents[0];if(x){append("assistant",`${x.incident_id} is priority #${x.priority_rank} with a score of ${n(x.priority_score)} and maximum risk of ${n(x.max_risk_score)}.`);focusIncident(x.incident_id);return;}}
  if(lower.includes("why")||lower.includes("high risk")||lower.includes("highest")){let top=state.riskRecords[0];if(top){append("assistant",`The strongest current unified risk is ${n(top.unified_risk_score)} at ${top.cell_id}. The leading drivers are ${top.driver_1}, ${top.driver_2}, and ${top.driver_3}.`);focusHighestRisk();return;}}
  if(lower.includes("50%")||lower.includes("rainfall")){const s=state.scenarioSummary?.scenarios?.find(x=>Number(x.rainfall_change_percent)===50);if(s){append("assistant",`At +50% rainfall, mean risk moves to ${n(s.mean_risk_score)}, with ${s.escalating_cells} cells escalating. New extreme cells: ${s.new_extreme_cells}.`);switchView("scenarios");return;}}
  append("assistant","That question is ready for the next intelligence layer. For now I can surface top priority, strongest risk, and generated rainfall scenario outcomes without inventing unsupported evidence.");
}
