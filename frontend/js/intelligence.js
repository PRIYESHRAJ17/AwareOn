import { switchView } from "./views.js";
import { focusCellById } from "./map.js";

const API_BASE =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "https://awareon-backend.onrender.com";
const esc = value => String(value ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
const get = id => document.getElementById(id);
let busy = false;
const SESSION_KEY = "awareon.ai.session.v1";

function sessionId(){
  let value = null;
  try { value = localStorage.getItem(SESSION_KEY); } catch {}
  if(!value){
    value = globalThis.crypto?.randomUUID?.() || `ao-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
    try { localStorage.setItem(SESSION_KEY,value); } catch {}
  }
  return value;
}

export function initIntelligence(){
  const input=get("intelligence-query");
  const send=get("intelligence-submit");
  const topBar=get("search-wrap");
  const topInput=get("global-search");
  if(!input||!send)return;
  send.onclick=submitQuery;
  input.onkeydown=e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();submitQuery();}};
  document.querySelectorAll(".prompt-card").forEach(button=>button.onclick=()=>{input.value=button.dataset.prompt||button.querySelector("strong")?.textContent||"";submitQuery();});

  // AwareOn Intel top bar: make the interaction feel alive without changing
  // the search bar's core behavior or affecting other application views.
  if(topBar && !topBar.dataset.aoLivelyBound){
    topBar.dataset.aoLivelyBound="true";
    const phrases=[
      "Ask AwareOn about the landscape…",
      "Ask about a cell, incident, or scenario…",
      "Try: what happens at +50% rainfall?",
      "Investigate risk, evidence, history, or decisions…"
    ];
    let phraseIndex=0;
    let phraseTimer=null;

    const updatePhrase=()=>{
      if(!topInput)return;
      const intelActive=document.getElementById("view-intelligence")?.classList.contains("active");
      if(!intelActive || topInput.value.trim() || document.activeElement===topInput)return;
      topInput.classList.add("ao-placeholder-shift");
      window.setTimeout(()=>{
        if(!topInput)return;
        phraseIndex=(phraseIndex+1)%phrases.length;
        topInput.placeholder=phrases[phraseIndex];
        topInput.classList.remove("ao-placeholder-shift");
      },180);
    };

    const startPhraseLoop=()=>{
      if(phraseTimer)window.clearInterval(phraseTimer);
      phraseTimer=window.setInterval(updatePhrase,3600);
    };
    startPhraseLoop();

    topBar.addEventListener("pointermove",event=>{
      const rect=topBar.getBoundingClientRect();
      const x=Math.max(0,Math.min(100,((event.clientX-rect.left)/rect.width)*100));
      const y=Math.max(0,Math.min(100,((event.clientY-rect.top)/rect.height)*100));
      topBar.style.setProperty("--ao-mx",`${x}%`);
      topBar.style.setProperty("--ao-my",`${y}%`);
    });
    topBar.addEventListener("mouseenter",()=>topBar.classList.add("ao-pointer-live"));
    topBar.addEventListener("mouseleave",()=>topBar.classList.remove("ao-pointer-live"));
    topInput?.addEventListener("focus",()=>topBar.classList.add("ao-focus-live"));
    topInput?.addEventListener("blur",()=>topBar.classList.remove("ao-focus-live"));
    topInput?.addEventListener("input",()=>{
      topBar.classList.toggle("ao-has-query",Boolean(topInput.value.trim()));
    });
  }

  appendAssistant("Ask AwareOn about the landscape, a location, a scenario, or a decision. I’ll investigate the current intelligence and show the useful evidence with it.");
}

export async function submitQuery(queryOverride = ""){
  if(busy)return;
  const input=get("intelligence-query");
  if(!input)return;
  const query=String(queryOverride || input.value || "").trim();
  if(!query)return;
  append("user",query);
  input.value="";
  busy=true;
  document.body.classList.add("ao-ai-busy");
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
  }finally{busy=false;document.body.classList.remove("ao-ai-busy");setBusy(false);}
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
  const evidence=Array.isArray(payload?.response?.evidence)?payload.response.evidence:[];
  if(!evidence.length)return;
  const status=String(payload?.status||"").toUpperCase();
  const canGround=status!=="OUTSIDE_DOMAIN" && status!=="CLARIFICATION_REQUIRED" && status!=="REVIEW_REQUIRED";
  const card=document.createElement("div");
  card.className="ao-evidence-card ao-evidence-expandable";
  const items=evidence.map(item=>{
    const claim=String(item?.claim||item?.value||"").trim();
    if(!claim)return "";
    const source=String(item?.source_tool||item?.evidence_type||"AwareOn intelligence").replaceAll("_"," ");
    return `<div class="ao-evidence-item"><span>${esc(source)}</span><div>${esc(claim)}</div></div>`;
  }).filter(Boolean).join("");
  if(!items)return;
  card.innerHTML=`<div class="ao-evidence-head"><strong>Supporting evidence</strong><span class="ao-verified ${canGround?"":"is-caution"}">${canGround?"GROUNDED":"REVIEW"}</span></div><div class="ao-evidence-preview">${evidence.slice(0,2).map(item=>`<div class="ao-evidence-item"><span>${esc(String(item?.source_tool||item?.evidence_type||"AwareOn evidence").replaceAll("_"," "))}</span><div>${esc(String(item?.claim||item?.value||""))}</div></div>`).join("")}</div><button class="ao-evidence-toggle" type="button" aria-haspopup="dialog" aria-label="View all detailed evidence">View detailed evidence · ${evidence.length} items <b>↗</b></button>`;
  const toggle=card.querySelector(".ao-evidence-toggle");
  toggle?.addEventListener("click",event=>openDetailedEvidence(payload,event));
  bubble.appendChild(card);
}

function formatDetailValue(value){
  if(value===null || value===undefined || value==="")return "—";
  if(typeof value === "object"){
    const keys=Object.keys(value);
    if(!keys.length)return "No additional details";
    const labels=keys.slice(0,4).map(key=>key.replaceAll("_"," ").replace(/\b\w/g,char=>char.toUpperCase()));
    const remainder=keys.length-labels.length;
    return esc(labels.join(" · ") + (remainder>0 ? ` · +${remainder} more` : ""));
  }
  const text=String(value).trim();
  if(text.length>260)return esc(`${text.slice(0,257)}…`);
  return esc(text);
}

function evidenceDetailItem(item,index){
  const entries=[
    ["Evidence type",item?.evidence_type],
    ["Source tool",item?.source_tool],
    ["Source ID",item?.source_id],
    ["Confidence",item?.confidence!=null ? `${item.confidence}${Number(item.confidence)<=1 ? "" : "%"}` : null],
    ["Claim",item?.claim],
    ["Value",item?.value],
    ["Metadata",item?.metadata],
  ].filter(([,value])=>value!==undefined && value!==null && value!=="");

  return `<article class="ao-detail-evidence-item"><div class="ao-detail-evidence-index">Evidence ${index+1}</div>${entries.map(([label,value])=>`<div class="ao-detail-row"><span>${esc(label)}</span><div>${formatDetailValue(value)}</div></div>`).join("")}</article>`;
}

function openDetailedEvidence(payload,event){
  let panel=document.getElementById("ao-detailed-evidence");
  if(!panel){
    panel=document.createElement("section");
    panel.id="ao-detailed-evidence";
    panel.className="ao-detailed-evidence";
    panel.setAttribute("role","dialog");
    panel.setAttribute("aria-modal","false");
    panel.innerHTML=`<div class="ao-detailed-evidence-head"><div><span class="eyebrow">AWAREON INTELLIGENCE</span><h3>Detailed evidence</h3><p id="ao-detail-query"></p></div><button id="ao-detail-close" class="ao-detail-close" type="button" aria-label="Close detailed evidence">×</button></div><div id="ao-detail-body" class="ao-detailed-evidence-body"></div><footer class="ao-detailed-evidence-foot"><div class="ao-model-badge">AO Intel</div><div><strong>Built with dual local models</strong><p>Primary: Ollama · <b>qwen3.5:9b</b><br>Backup: Ollama · <b>nemotron-3-nano:4b-q8_0</b></p><p>AO Intel uses controlled self-learning and validation memory to improve over time. New learning is treated as a validated development signal rather than an unrestricted automatic override of current evidence.</p></div></footer>`;
    document.body.appendChild(panel);
    panel.querySelector("#ao-detail-close")?.addEventListener("click",()=>closeDetailedEvidence());
    panel.addEventListener("pointerdown",e=>{if(e.target===panel)closeDetailedEvidence();});
    document.addEventListener("keydown",e=>{if(e.key==="Escape")closeDetailedEvidence();});
  }

  const body=panel.querySelector("#ao-detail-body");
  const queryEl=panel.querySelector("#ao-detail-query");
  const response=payload?.response||{};
  const evidence=Array.isArray(response?.evidence)?response.evidence:[];
  const verification=payload?.verification||{};
  const tools=Array.isArray(response?.tools_used)?response.tools_used:[];
  const limitations=Array.isArray(response?.limitations)?response.limitations:[];
  const investigations=Array.isArray(payload?.investigations)?payload.investigations:[];
  const facts=investigations.flatMap(item=>Array.isArray(item?.findings)?item.findings:[]).filter(Boolean);

  if(queryEl)queryEl.textContent=String(payload?.query||"Current AwareOn investigation");
  if(body){
    body.innerHTML=`
      <section class="ao-detail-block ao-detail-answer">
        <span class="eyebrow">INVESTIGATION SUMMARY</span>
        <h4>${esc(String(payload?.answer||response?.answer||"AwareOn completed the investigation."))}</h4>
        <div class="ao-detail-meta-grid">
          <div><span>Status</span><b>${esc(payload?.status||"—")}</b></div>
          <div><span>Domain</span><b>${esc(response?.domain||payload?.domain||"—")}</b></div>
          <div><span>Intent</span><b>${esc(response?.intent||payload?.intent||"—")}</b></div>
          <div><span>Confidence</span><b>${response?.confidence!=null?esc(response.confidence+"%"):"—"}</b></div>
        </div>
      </section>

      <section class="ao-detail-block">
        <div class="ao-detail-section-title"><span class="eyebrow">EVIDENCE PACKAGE</span><b>${evidence.length} items</b></div>
        ${evidence.length?evidence.map((item,index)=>evidenceDetailItem(item,index)).join(""):"<div class='ao-detail-empty'>No evidence items were returned for this investigation.</div>"}
      </section>

      <section class="ao-detail-block">
        <div class="ao-detail-section-title"><span class="eyebrow">INVESTIGATION TRACE</span><b>${tools.length} tools</b></div>
        <div class="ao-detail-trace-grid">
          <div><span>Tools used</span><strong>${esc(tools.length?tools.join(" · "):"None reported")}</strong></div>
          <div><span>Verification</span><strong>${esc(verification?.status||"Not reported")} · ${verification?.score!=null?esc(String(verification.score)):"—"}</strong></div>
          <div><span>Verification issues</span><strong>${esc(Array.isArray(verification?.issues)&&verification.issues.length?verification.issues.join(" · "):"None reported")}</strong></div>
        </div>
      </section>

      ${facts.length?`<section class="ao-detail-block"><div class="ao-detail-section-title"><span class="eyebrow">FINDINGS</span><b>${facts.length}</b></div><ul class="ao-detail-list">${facts.map(f=>`<li>${esc(String(f))}</li>`).join("")}</ul></section>`:""}

      ${limitations.length?`<section class="ao-detail-block"><div class="ao-detail-section-title"><span class="eyebrow">LIMITATIONS</span><b>${limitations.length}</b></div><ul class="ao-detail-list">${limitations.map(f=>`<li>${esc(String(f))}</li>`).join("")}</ul></section>`:""}

      <section class="ao-detail-block ao-detail-responsibility">
        <span class="eyebrow">INTERPRETATION</span>
        <p>Observed, derived, historical, and simulated evidence should remain distinguishable. Current evidence should be checked together with confidence, uncertainty, location, scale, data freshness, official guidance, and on-ground conditions before consequential decisions.</p>
      </section>`;
  }

  const clickY=Number(event?.clientY)||120;
  const panelHeight=Math.min(window.innerHeight-120,760);
  const top=Math.max(76,Math.min(clickY-120,window.innerHeight-panelHeight-24));
  panel.style.setProperty("--ao-detail-top",`${top}px`);
  panel.classList.add("is-open");
  window.requestAnimationFrame(()=>body?.scrollTo({top:0,behavior:"instant"}));
}

function closeDetailedEvidence(){
  document.getElementById("ao-detailed-evidence")?.classList.remove("is-open");
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
