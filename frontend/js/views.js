import { state } from "./state.js";

const config = {
  overview: ["SITUATION ROOM", "Command Center", "Understand the current risk landscape before you act."],
  "risk-map": ["GEOINT WORKSPACE", "Risk Explorer", "Inspect a location, evidence chain, and decision state."],
  incidents: ["INCIDENT COMMAND", "Priority Incidents", "Move from ranked risk zones to spatial action."],
  scenarios: ["DECISION SUPPORT", "Scenario Lab", "Test the actual counterfactual states available to AwareOn."],
  intelligence: ["AWAREON INTELLIGENCE", "Investigation Workspace", "Ask grounded questions and jump directly to spatial context."]
};

export function switchView(name) {
  if (!config[name]) return;
  state.activeView = name;
  document.querySelectorAll(".rail-item").forEach(b => b.classList.toggle("active", b.dataset.view === name));
  document.querySelectorAll(".workspace").forEach(v => v.classList.toggle("active", v.id === `view-${name}`));
  const [eyebrow, title, subtitle] = config[name];
  document.getElementById("workspace-eyebrow").textContent = eyebrow;
  document.getElementById("workspace-title").textContent = title;
  document.getElementById("workspace-subtitle").textContent = subtitle;
  document.getElementById("stage-mode").textContent = title.toUpperCase();
  window.setTimeout(() => window.dispatchEvent(new Event("resize")), 80);
}
