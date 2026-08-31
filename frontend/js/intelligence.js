import { switchView } from "./views.js";
import { focusCellById } from "./map.js";

const API_BASE = "http://127.0.0.1:8000";
const esc = value => String(value ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
const get = id => document.getElementById(id);
let busy = false;
const SESSION_KEY = "awareon.ai.session.v1";

function sessionId(){
  let value = localStorage.getItem(SESSION_KEY);
  if(!value){
    value = globalThis.crypto?.randomUUID?.() || `ao-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
    localStorage.setItem(SESSION_KEY,value);
  }
  return value;
}

export function initIntelligence(){
  const input=get("intelligence-query");
  const send=get("intelligence-submit");
  if(!input||!send)return;
  send.onclick=submit;
  input.onkeydown=e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();submit();}};
  document.querySelectorAll(".prompt-card").forEach(button=>button.onclick=()=>{input.value=button.dataset.prompt||button.querySelector("strong")?.textContent||"";submit();});
  appendAssistant("Ask AwareOn about the landscape, a location, a scenario, or a decision. I’ll investigate the current intelligence and show the useful evidence with it.");
}

async function submit(){
  if(busy)return;
  const input=get("intelligence-query");
  if(!input)return;
  const query=input.value.trim();
  if(!query)return;
  append("user",query);
  input.value="";
  busy=true;
  setBusy(true);
  const loading=appendThinking();
  try{
    const response=await fetch(`${API_BASE}/api/v1/intelligence/ask`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query,session_id:sessionId()})});
    let payload=null;
    try{payload=await response.json();}catch{throw new Error("AwareOn returned an unreadable response.");}
    if(!response.ok)throw new Error(payload?.detail||"AwareOn intelligence request failed.");
    if(!payload||payload.success!==true)throw new Error("AwareOn returned an invalid response.");
    loading?.remove();
    renderAgentResult(payload);
  }catch(error){
    loading?.remove();
    appendAssistant(`I couldn’t complete that investigation. ${error?.message||"Please try again."}`);
  }finally{busy=false;setBusy(false);}
}

function setBusy(value){
  const send=get("intelligence-submit"),input=get("intelligence-query");
  if(send){send.disabled=value;send.textContent=value?"":"Ask";send.classList.toggle("is-thinking",value);}
  if(input)input.disabled=value;
}

function renderAgentResult(payload){
  const status=String(payload?.status||"").toUpperCase();
  const answer=String(
    payload?.answer||
    payload?.response?.answer||
    "AwareOn completed the investigation."
  );

  const wrapper=append("assistant",answer);

  if(
    status!=="OUTSIDE_DOMAIN" &&
    status!=="CLARIFICATION_REQUIRED"
  ){
    renderEvidenceCard(wrapper,payload);
  }

  attachSpatialActions(wrapper,payload);
}


function renderEvidenceCard(wrapper,payload){
  const bubble=wrapper?.querySelector(".chat-bubble");
  if(!bubble)return;

  const evidence=
    Array.isArray(payload?.response?.evidence)
      ? payload.response.evidence
      : [];

  if(!evidence.length)return;

  const card=document.createElement("div");
  card.className="ao-evidence-card";

  const items=evidence
    .slice(0,4)
    .map(item=>{
      const claim=
        String(
          item?.claim||
          item?.value||
          ""
        ).trim();

      if(!claim)return "";

      const source=
        String(
          item?.source_tool||
          item?.evidence_type||
          "AwareOn intelligence"
        )
        .replaceAll("_"," ");

      return `
        <div class="ao-evidence-item">
          <span>${esc(source)}</span>
          <div>${esc(claim)}</div>
        </div>
      `;
    })
    .filter(Boolean)
    .join("");

  if(!items)return;

  card.innerHTML=`
    <div class="ao-evidence-head">
      <strong>Supporting evidence</strong>
      <span class="ao-verified">GROUNDED</span>
    </div>

    ${items}

    ${
      evidence.length>4
        ? `<div class="ao-evidence-more">
            ${evidence.length-4} additional supporting signals
           </div>`
        : ""
    }
  `;

  bubble.appendChild(card);
}


function attachSpatialActions(wrapper,payload){
  const bubble=wrapper?.querySelector(".chat-bubble");
  if(!bubble)return;

  const sources=[
    payload?.query||"",
    payload?.answer||"",
    payload?.response?.answer||""
  ];

  for(
    const investigation
    of payload?.investigations||[]
  ){
    if(investigation?.cell_id){
      sources.push(
        String(investigation.cell_id)
      );
    }
  }

  const match=
    sources
      .join(" ")
      .match(/\b(\d{2,4}_\d{2,4})\b/);

  const actions=[];

  if(match){
    actions.push(`
      <button
        class="ao-action"
        type="button"
        data-focus-cell="${esc(match[1])}"
      >
        Locate ${esc(match[1])}
      </button>
    `);
  }

  const query=
    String(
      payload?.query||""
    ).toLowerCase();

  if(
    query.includes("scenario")||
    query.includes("rainfall")||
    query.includes("what happens")||
    payload?.response?.tools_used?.some?.(
      tool=>String(tool).toLowerCase().includes("scenario")
    )
  ){
    actions.push(`
      <button
        class="ao-action"
        type="button"
        data-open-scenario="true"
      >
        Open Scenario Lab
      </button>
    `);
  }

  if(!actions.length)return;

  const row=document.createElement("div");
  row.className="ao-action-row";
  row.innerHTML=actions.join("");

  bubble.appendChild(row);

  row
    .querySelector(
      "[data-focus-cell]"
    )
    ?.addEventListener(
      "click",
      event=>{
        const cell=
          event.currentTarget.dataset.focusCell;

        if(!cell)return;

        switchView(
          "risk-map",
          {openDrawer:true}
        );

        focusCellById(cell);
      }
    );

  row
    .querySelector(
      "[data-open-scenario]"
    )
    ?.addEventListener(
      "click",
      ()=>{
        switchView("scenarios");
      }
    );
}


function renderResultMeta(){
  /*
   * Intentionally hidden from the user.
   *
   * Backend status, intent, turn counts and other
   * execution metadata remain available in the
   * response object but are not rendered as chat content.
   */
}


function appendAssistant(text){return append("assistant",text);}
function appendThinking(){
  const node=append("assistant","");
  const bubble=node?.querySelector(".chat-bubble");
  if(!bubble)return node;
  const p=bubble.querySelector("p");
  if(p)p.remove();
  const thinking=document.createElement("div");
  thinking.className="ao-thinking";
  thinking.innerHTML=`<span class="ao-thinking-label">Investigating</span><i></i><i></i><i></i>`;
  bubble.appendChild(thinking);
  node.classList.add("is-loading");
  return node;
}
function append(role,text){
  const thread=get("chat-thread");
  if(!thread)return null;
  const wrapper=document.createElement("div");
  wrapper.className=`chat-message ${role}`;
  if(role==="assistant")wrapper.innerHTML=`<div class="chat-avatar">AO</div><div class="chat-bubble"><strong>AwareOn</strong><p>${esc(text)}</p></div>`;
  else wrapper.innerHTML=`<div class="chat-bubble"><strong>You</strong><p>${esc(text)}</p></div>`;
  thread.appendChild(wrapper);
  requestAnimationFrame(()=>thread.scrollTo({top:thread.scrollHeight,behavior:"smooth"}));
  return wrapper;
}
