import { state } from "./state.js";

const config = {
  overview: ["SITUATION ROOM", "Command Center", "See what matters now, then move directly to the map."],
  "risk-map": ["GEOINT WORKSPACE", "Risk Explorer", "Inspect spatial risk, evidence, and decision context."],
  incidents: ["INCIDENT COMMAND", "Priority Incidents", "Move from ranked zones to focused spatial action."],
  scenarios: ["DECISION SUPPORT", "Scenario Lab", "Explore supported rainfall counterfactuals and their spatial effects."],
  intelligence: ["AWAREON INTELLIGENCE", "Ask the landscape", "Investigate risk, evidence, scenarios, history, and decisions in natural language."]
};

function setDrawer(open = true){
  const panel = document.getElementById("context-panel");
  if (!panel) return;
  panel.classList.toggle("collapsed", !open);
  document.body.classList.toggle("drawer-open", open);
}

export function openContextDrawer(){ setDrawer(true); }
export function closeContextDrawer(){ setDrawer(false); }
export function isContextDrawerOpen(){ return !document.getElementById("context-panel")?.classList.contains("collapsed"); }

export function switchView(name, options = {}) {
  if (!config[name]) return;
  state.activeView = name;
  document.querySelectorAll(".rail-item").forEach(b => b.classList.toggle("active", b.dataset.view === name));
  document.querySelectorAll(".workspace").forEach(v => v.classList.toggle("active", v.id === `view-${name}`));
  const [eyebrow, title, subtitle] = config[name];
  document.getElementById("workspace-eyebrow")?.replaceChildren(document.createTextNode(eyebrow));
  document.getElementById("workspace-title")?.replaceChildren(document.createTextNode(title));
  document.getElementById("workspace-subtitle")?.replaceChildren(document.createTextNode(subtitle));
  const stageMode = document.getElementById("stage-mode");
  if (stageMode) stageMode.textContent = title.toUpperCase();
  if (options.openDrawer !== false) setDrawer(true);
  window.setTimeout(() => window.dispatchEvent(new Event("resize")), 120);
}
