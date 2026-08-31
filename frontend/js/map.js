import { api } from "./api.js";
import { state } from "./state.js";
import { switchView, openContextDrawer } from "./views.js";

const INITIAL_CENTER = [27.55, 88.45];
const INITIAL_ZOOM = 9;
const POLYGON_ZOOM = 13;
const MAX_FOCUS_ZOOM = 15;

export const map = L.map("map", {
  zoomControl: false,
  attributionControl: true,
  preferCanvas: true,
  zoomAnimation: true,
  fadeAnimation: true,
  markerZoomAnimation: true,
  wheelDebounceTime: 25,
  wheelPxPerZoomLevel: 110
}).setView(INITIAL_CENTER, INITIAL_ZOOM);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  opacity: 0.92,
  attribution: "&copy; OpenStreetMap contributors"
}).addTo(map);

L.control.zoom({ position: "bottomright" }).addTo(map);

function createPane(name, zIndex, pointerEvents = "none") {
  let pane = map.getPane(name);
  if (!pane) pane = map.createPane(name);
  pane.style.zIndex = String(zIndex);
  pane.style.pointerEvents = pointerEvents;
  return pane;
}

createPane("awareonRiskClusterPane", 640, "auto");
createPane("awareonRiskPointPane", 660, "auto");
createPane("awareonRiskPolygonPane", 650, "auto");
createPane("awareonIncidentPane", 680, "auto");
createPane("awareonBoundaryPane", 610, "none");

let riskPointLayer = null;
let riskPolygonLayer = null;
let riskClusterLayer = null;
let mapToolsBound = false;
let secondaryLayersStarted = false;
let pendingIncidentId = null;
const desiredLayers = new Set(["risk"]);

const n = (v, d = 1) => {
  const value = Number(v);
  return Number.isFinite(value) ? value.toFixed(d) : "—";
};
const esc = v => String(v ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");

const riskColor = score => {
  const value = Number(score);
  if (value >= 75) return "#7f282b";
  if (value >= 50) return "#df4945";
  if (value >= 25) return "#d99619";
  return "#1fa86b";
};
const riskLabel = score => {
  const value = Number(score);
  if (value >= 75) return "EXTREME";
  if (value >= 50) return "HIGH";
  if (value >= 25) return "MODERATE";
  return "LOW";
};

function rgbaFromHex(hex, alpha) {
  const clean = String(hex).replace('#','');
  const value = clean.length === 3 ? clean.split('').map(ch => ch + ch).join('') : clean;
  const int = Number.parseInt(value, 16);
  if (!Number.isFinite(int)) return `rgba(255,255,255,${alpha})`;
  return `rgba(${(int >> 16) & 255},${(int >> 8) & 255},${int & 255},${alpha})`;
}

const normal = f => ({
  color: "#5f7487",
  weight: 0.8,
  opacity: 0.55,
  fillColor: riskColor(f?.properties?.unified_risk_score),
  fillOpacity: 0.16
});
const hover = f => ({
  color: "#18283b",
  weight: 1.8,
  opacity: 0.86,
  fillColor: riskColor(f?.properties?.unified_risk_score),
  fillOpacity: 0.30
});
const selected = f => ({
  color: "#2563eb",
  weight: 3,
  opacity: 1,
  fillColor: riskColor(f?.properties?.unified_risk_score),
  fillOpacity: 0.42
});
const dim = f => ({
  color: "#90a0b0",
  weight: 0.5,
  opacity: 0.12,
  fillColor: riskColor(f?.properties?.unified_risk_score),
  fillOpacity: 0.035
});
const focus = f => ({
  color: "#08a4ba",
  weight: 2.8,
  opacity: 1,
  fillColor: riskColor(f?.properties?.unified_risk_score),
  fillOpacity: 0.36,
  dashArray: "6 4"
});

function featureCenter(feature) {
  const geometry = feature?.geometry;
  if (!geometry) return null;
  if (geometry.type === "Point") {
    const [lon, lat] = geometry.coordinates || [];
    return Number.isFinite(Number(lat)) && Number.isFinite(Number(lon)) ? [Number(lat), Number(lon)] : null;
  }
  const coordinates = geometry.type === "Polygon" ? geometry.coordinates?.[0] : geometry.type === "MultiPolygon" ? geometry.coordinates?.[0]?.[0] : null;
  if (!Array.isArray(coordinates) || !coordinates.length) return null;
  let minLon = Infinity, maxLon = -Infinity, minLat = Infinity, maxLat = -Infinity;
  for (const pair of coordinates) {
    if (!Array.isArray(pair) || pair.length < 2) continue;
    const lon = Number(pair[0]), lat = Number(pair[1]);
    if (!Number.isFinite(lon) || !Number.isFinite(lat)) continue;
    minLon = Math.min(minLon, lon); maxLon = Math.max(maxLon, lon);
    minLat = Math.min(minLat, lat); maxLat = Math.max(maxLat, lat);
  }
  if (!Number.isFinite(minLon) || !Number.isFinite(maxLon) || !Number.isFinite(minLat) || !Number.isFinite(maxLat)) return null;
  return [(minLat + maxLat) / 2, (minLon + maxLon) / 2];
}

function cellTooltip(p) {
  return `<strong>Cell ${esc(p?.cell_id)}</strong><br>Risk ${n(p?.unified_risk_score,1)} · ${esc(riskLabel(p?.unified_risk_score))}<br>Warning ${esc(p?.warning_state || "—")} · Confidence ${n(p?.confidence_score,0)}`;
}

function popupHtml(p) {
  const cell = esc(p?.cell_id || "Unknown");
  const risk = n(p?.unified_risk_score, 1);
  const category = esc(riskLabel(p?.unified_risk_score));
  return `<div class="awareon-map-popup" data-cell-id="${cell}"><span class="popup-kicker">SPATIAL RISK CELL</span><h4>${cell}</h4><div class="popup-score"><strong>${risk}</strong><span>${category}</span></div><div class="popup-grid"><div class="popup-stat"><span>Warning</span><b>${esc(p?.warning_state || "—")}</b></div><div class="popup-stat"><span>Confidence</span><b>${n(p?.confidence_score,0)}%</b></div></div><button class="popup-open" data-ao-action="open-cell" data-cell-id="${cell}" type="button">Open intelligence</button></div>`;
}

function pointIcon(color, size = 8) {
  return L.divIcon({
    className: "awareon-risk-point-icon",
    html: `<span class="risk-point" style="display:block;width:${size}px;height:${size}px;background:${color}"></span>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2]
  });
}

function buildRiskPointLayer(geojson) {
  const group = L.layerGroup();
  for (const feature of geojson?.features || []) {
    const p = feature?.properties || {};
    const center = featureCenter(feature);
    if (!center) continue;
    const marker = L.marker(center, {
      icon: pointIcon(riskColor(p.unified_risk_score), 8),
      pane: "awareonRiskPointPane",
      keyboard: true,
      title: `AwareOn risk cell ${p.cell_id ?? ""}`
    });
    marker.feature = feature;
    marker.cellId = String(p.cell_id ?? "");
    marker.bindTooltip(cellTooltip(p), { sticky: true, direction: "top", className: "awareon-risk-tooltip" });
    marker.on("click", () => openCellQuick(marker.cellId));
    group.addLayer(marker);
  }
  return group;
}

function clusterStepForZoom(zoom) {
  if (zoom <= 8) return 0.65;
  if (zoom <= 9) return 0.42;
  if (zoom <= 10) return 0.26;
  return 0.14;
}

function clusterRisk(features) {
  let weighted = 0;
  let weight = 0;
  let counts = { low: 0, moderate: 0, high: 0, extreme: 0 };
  for (const feature of features) {
    const score = Number(feature?.properties?.unified_risk_score);
    if (!Number.isFinite(score)) continue;
    weighted += score;
    weight += 1;
    if (score >= 75) counts.extreme += 1;
    else if (score >= 50) counts.high += 1;
    else if (score >= 25) counts.moderate += 1;
    else counts.low += 1;
  }
  return { mean: weight ? weighted / weight : 0, counts };
}

function buildRiskClusters() {
  const layer = L.layerGroup();
  const features = state.riskGeoJson?.features || [];
  if (!features.length) return layer;
  const zoom = map.getZoom();
  const step = clusterStepForZoom(zoom);
  const buckets = new Map();
  for (const feature of features) {
    const center = featureCenter(feature);
    if (!center) continue;
    const key = `${Math.floor(center[0] / step)}:${Math.floor(center[1] / step)}`;
    if (!buckets.has(key)) buckets.set(key, { latSum: 0, lonSum: 0, items: [] });
    const bucket = buckets.get(key);
    bucket.latSum += center[0]; bucket.lonSum += center[1]; bucket.items.push(feature);
  }
  for (const bucket of buckets.values()) {
    const count = bucket.items.length;
    const center = [bucket.latSum / count, bucket.lonSum / count];
    const stats = clusterRisk(bucket.items);
    const radius = Math.min(30, 11 + Math.sqrt(count) * 2.4);
    const color = riskColor(stats.mean);
    const marker = L.marker(center, {
      pane: "awareonRiskClusterPane",
      icon: L.divIcon({
        className: "awareon-risk-cluster",
        html: `<span class="risk-cluster" style="width:${radius}px;height:${radius}px;background:${rgbaFromHex(color,.20)};border-color:${color}">${count}</span>`,
        iconSize: [radius, radius],
        iconAnchor: [radius / 2, radius / 2]
      }),
      keyboard: true,
      title: `${count} AwareOn risk cells`
    });
    const bounds = L.latLngBounds(bucket.items.map(f => featureCenter(f)).filter(Boolean));
    marker.bindTooltip(`<strong>${count} cells</strong><br>Average risk ${n(stats.mean,1)} · ${esc(riskLabel(stats.mean))}`, { direction: "top", className: "awareon-risk-tooltip" });
    marker.on("click", () => {
      if (bounds.isValid()) {
        map.flyToBounds(bounds, { padding: [80, 80], maxZoom: Math.min(POLYGON_ZOOM, zoom + 2), duration: 0.55 });
      }
    });
    layer.addLayer(marker);
  }
  return layer;
}

function rebuildRiskClusters() {
  if (riskClusterLayer && map.hasLayer(riskClusterLayer)) map.removeLayer(riskClusterLayer);
  riskClusterLayer = buildRiskClusters();
  if (desiredLayers.has("risk") && map.getZoom() < POLYGON_ZOOM && !state.incidentFocusActive) riskClusterLayer.addTo(map);
}

function loadRiskLayer(geojson) {
  state.riskGeoJson = geojson;
  riskPolygonLayer = L.geoJSON(geojson, {
    pane: "awareonRiskPolygonPane",
    style: normal,
    onEachFeature(feature, layer) {
      const p = feature?.properties || {};
      layer.feature = feature;
      layer.bindTooltip(cellTooltip(p), { sticky: true, direction: "top", className: "awareon-risk-tooltip" });
      layer.on("mouseover", () => {
        if (state.selectedRiskLayer === layer) return;
        if (state.incidentFocusActive && !state.highlightedIncidentCells.includes(layer)) return;
        layer.setStyle(hover(feature));
        layer.bringToFront();
      });
      layer.on("mouseout", () => {
        if (state.selectedRiskLayer === layer) return;
        if (state.incidentFocusActive && !state.highlightedIncidentCells.includes(layer)) layer.setStyle(dim(feature));
        else if (state.highlightedIncidentCells.includes(layer)) layer.setStyle(focus(feature));
        else layer.setStyle(normal(feature));
      });
      layer.on("click", () => openCellQuick(String(p.cell_id || "")));
    }
  });
  state.riskLayer = riskPolygonLayer;
  state.mapInitialBounds = riskPolygonLayer.getBounds();
  riskPointLayer = buildRiskPointLayer(geojson);
  rebuildRiskClusters();
  if (state.mapInitialBounds.isValid()) map.fitBounds(state.mapInitialBounds, { padding: [80, 90], maxZoom: INITIAL_ZOOM });
  syncRiskDisplay();
}

async function loadRisk() {
  const geo = await api.riskLayer();
  if (!geo || geo.type !== "FeatureCollection" || !geo.features?.length) throw new Error("AwareOn risk layer returned no features.");
  loadRiskLayer(geo);
}

function syncRiskDisplay() {
  if (!riskPolygonLayer || !riskPointLayer) return;
  const zoom = map.getZoom();
  if (state.incidentFocusActive) {
    if (riskClusterLayer && map.hasLayer(riskClusterLayer)) map.removeLayer(riskClusterLayer);
    if (map.hasLayer(riskPointLayer)) map.removeLayer(riskPointLayer);
    if (desiredLayers.has("risk") && !map.hasLayer(riskPolygonLayer)) riskPolygonLayer.addTo(map);
    return;
  }
  if (!desiredLayers.has("risk")) {
    if (riskClusterLayer && map.hasLayer(riskClusterLayer)) map.removeLayer(riskClusterLayer);
    if (map.hasLayer(riskPointLayer)) map.removeLayer(riskPointLayer);
    if (map.hasLayer(riskPolygonLayer)) map.removeLayer(riskPolygonLayer);
    return;
  }
  if (zoom < POLYGON_ZOOM) {
    if (map.hasLayer(riskPolygonLayer)) map.removeLayer(riskPolygonLayer);
    if (map.hasLayer(riskPointLayer)) map.removeLayer(riskPointLayer);
    rebuildRiskClusters();
  } else {
    if (riskClusterLayer && map.hasLayer(riskClusterLayer)) map.removeLayer(riskClusterLayer);
    if (map.hasLayer(riskPointLayer)) map.removeLayer(riskPointLayer);
    if (!map.hasLayer(riskPolygonLayer)) riskPolygonLayer.addTo(map);
  }
}

function openCellQuick(cellId) {
  if (!cellId) return;
  let p = null;
  if (riskPolygonLayer) riskPolygonLayer.eachLayer(layer => { if (String(layer?.feature?.properties?.cell_id) === String(cellId)) p = layer.feature.properties; });
  if (!p && state.riskGeoJson) {
    const feature = state.riskGeoJson.features.find(f => String(f?.properties?.cell_id) === String(cellId));
    p = feature?.properties;
  }
  if (!p) return;
  const center = featureCenter(state.riskGeoJson.features.find(f => String(f?.properties?.cell_id) === String(cellId)));
  const popup = L.popup({ closeButton: true, offset: [0, -6], maxWidth: 300 });
  popup.setLatLng(center || map.getCenter()).setContent(popupHtml(p)).openOn(map);
  window.dispatchEvent(new CustomEvent("awareon:cell-quick", { detail: p }));
}

document.addEventListener("click", event => {
  const button = event.target.closest("[data-ao-action='open-cell']");
  if (!button) return;
  const id = button.dataset.cellId;
  if (id) {
    event.preventDefault();
    selectCellById(id);
    openContextDrawer();
  }
});

export function focusCellById(cellId) {
  if (!riskPolygonLayer) return;
  let target = null;
  riskPolygonLayer.eachLayer(layer => { if (String(layer?.feature?.properties?.cell_id) === String(cellId)) target = layer; });
  if (target) {
    if (map.getZoom() < POLYGON_ZOOM) map.flyTo(featureCenter(target.feature), Math.min(POLYGON_ZOOM, map.getZoom() + 3), { duration: 0.55 });
    selectCell(target);
  } else {
    openCellQuick(cellId);
  }
}

function selectCellById(cellId) { focusCellById(cellId); }

function selectCell(layer) {
  if (!layer) return;
  clearIncidentFocus();
  if (state.selectedRiskLayer && state.selectedRiskLayer !== layer) state.selectedRiskLayer.setStyle(normal(state.selectedRiskLayer.feature));
  state.selectedRiskLayer = layer;
  state.selectedCell = layer.feature.properties;
  if (!map.hasLayer(riskPolygonLayer)) riskPolygonLayer.addTo(map);
  layer.setStyle(selected(layer.feature));
  layer.bringToFront();
  const bounds = layer.getBounds?.();
  if (bounds?.isValid()) map.flyToBounds(bounds, { padding: [90, 90], maxZoom: MAX_FOCUS_ZOOM, duration: 0.5 });
  switchView("risk-map", { openDrawer: true });
  window.dispatchEvent(new CustomEvent("awareon:cell", { detail: layer.feature.properties }));
}

export function focusHighestRisk() {
  if (!riskPolygonLayer) return;
  let top = null;
  riskPolygonLayer.eachLayer(layer => {
    const score = Number(layer?.feature?.properties?.unified_risk_score);
    if (Number.isFinite(score) && (!top || score > Number(top.feature.properties.unified_risk_score))) top = layer;
  });
  if (top) selectCell(top);
}

export function focusIncident(id) {
  if (!state.incidentLayer) { pendingIncidentId = String(id); return; }
  let target = null;
  state.incidentLayer.eachLayer(layer => { if (String(layer.incidentId) === String(id)) target = layer; });
  if (!target) return;
  const p = target.feature.properties;
  const affected = String(p.affected_cells || "").split(",").map(v => v.trim()).filter(Boolean);
  state.incidentFocusActive = true;
  state.selectedIncident = p;
  state.highlightedIncidentCells = [];
  if (riskClusterLayer && map.hasLayer(riskClusterLayer)) map.removeLayer(riskClusterLayer);
  if (riskPointLayer && map.hasLayer(riskPointLayer)) map.removeLayer(riskPointLayer);
  if (riskPolygonLayer && !map.hasLayer(riskPolygonLayer) && desiredLayers.has("risk")) riskPolygonLayer.addTo(map);
  riskPolygonLayer?.eachLayer(layer => {
    const hit = affected.includes(String(layer?.feature?.properties?.cell_id));
    layer.setStyle(hit ? focus(layer.feature) : dim(layer.feature));
    if (hit) state.highlightedIncidentCells.push(layer);
  });
  if (state.highlightedIncidentCells.length) {
    const bounds = L.featureGroup(state.highlightedIncidentCells).getBounds();
    if (bounds.isValid()) map.flyToBounds(bounds, { padding: [80,80], maxZoom: MAX_FOCUS_ZOOM, duration: 0.55 });
  } else map.flyTo(target.getLatLng(), 13, { duration: 0.55 });
  target.bringToFront();
  target.openTooltip();
  const focusBar = document.getElementById("focus-bar");
  focusBar.hidden = false;
  document.getElementById("focus-bar-title").textContent = `${p.incident_id} · ${p.priority_level}`;
  document.getElementById("focus-bar-cells").textContent = `${p.cell_count} affected cells`;
  switchView("risk-map", { openDrawer: true });
  window.dispatchEvent(new CustomEvent("awareon:incident", { detail: p }));
}

export function clearIncidentFocus() {
  state.incidentFocusActive = false;
  state.selectedIncident = null;
  state.highlightedIncidentCells = [];
  if (riskPolygonLayer) riskPolygonLayer.eachLayer(layer => layer.setStyle(layer === state.selectedRiskLayer ? selected(layer.feature) : normal(layer.feature)));
  const focusBar = document.getElementById("focus-bar");
  if (focusBar) focusBar.hidden = true;
  syncRiskDisplay();
}

export function clearCellSelection() {
  if (state.selectedRiskLayer) state.selectedRiskLayer.setStyle(normal(state.selectedRiskLayer.feature));
  state.selectedRiskLayer = null;
  state.selectedCell = null;
  window.dispatchEvent(new CustomEvent("awareon:clear-selection"));
}

function setButtonActive(button, active) {
  if (!button) return;
  button.classList.toggle("is-active", active);
  button.setAttribute("aria-pressed", active ? "true" : "false");
}
function resolveLayer(key) {
  switch (key) {
    case "risk": return riskPolygonLayer && map.getZoom() >= POLYGON_ZOOM ? riskPolygonLayer : riskClusterLayer;
    case "incidents": return state.incidentLayer;
    case "history": return state.historicalLayer;
    case "exposure": return state.exposureLayer;
    default: return null;
  }
}
export function initializeMapTools() {
  if (mapToolsBound) return;
  mapToolsBound = true;
  document.querySelectorAll("[data-layer-toggle]").forEach(button => {
    setButtonActive(button, desiredLayers.has(button.dataset.layerToggle));
    button.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      const key = button.dataset.layerToggle;
      if (!key) return;
      if (desiredLayers.has(key)) desiredLayers.delete(key); else desiredLayers.add(key);
      setButtonActive(button, desiredLayers.has(key));
      if (key === "risk") syncRiskDisplay(); else {
        const layer = resolveLayer(key);
        if (layer) { if (desiredLayers.has(key)) layer.addTo(map); else map.removeLayer(layer); }
      }
    });
  });
  document.getElementById("map-reset")?.addEventListener("click", e => { e.preventDefault(); clearIncidentFocus(); clearCellSelection(); map.closePopup(); desiredLayers.add("risk"); setButtonActive(document.querySelector('[data-layer-toggle="risk"]'), true); if (state.mapInitialBounds?.isValid()) map.flyToBounds(state.mapInitialBounds, { padding:[80,90], maxZoom:INITIAL_ZOOM, duration:.55 }); syncRiskDisplay(); });
  document.getElementById("map-focus-risk")?.addEventListener("click", e => { e.preventDefault(); focusHighestRisk(); });
  document.getElementById("clear-focus")?.addEventListener("click", e => { e.preventDefault(); clearIncidentFocus(); });
}

async function loadSecondaryLayers() {
  if (secondaryLayersStarted) return;
  secondaryLayersStarted = true;
  const boundaryPromise = api.boundary().then(geojson => {
    state.boundaryLayer=L.geoJSON(geojson,{pane:"awareonBoundaryPane",style:()=>({color:"#657588",weight:1.3,opacity:.48,fillOpacity:0,interactive:false})}).addTo(map);
  }).catch(err=>console.error("Boundary layer failed:",err));
  const historyPromise = api.historicalLayer().then(geojson => {
    state.historicalLayer=L.geoJSON(geojson,{pointToLayer:(f,ll)=>L.circleMarker(ll,{radius:Number(f?.properties?.hotspot_score)>=75?8:Number(f?.properties?.hotspot_score)>=50?6:4,color:"#163b64",weight:1,fillColor:"#2563eb",fillOpacity:.74}),onEachFeature:(f,l)=>{const p=f?.properties||{};l.bindTooltip(`<strong>Historical hotspot</strong><br>${esc(p.hotspot_id)}<br>${p.event_count??0} events · score ${n(p.hotspot_score)}`,{sticky:true});l.on("click",()=>{switchView("risk-map");openContextDrawer();})}});
    if(desiredLayers.has("history"))state.historicalLayer.addTo(map);
  }).catch(err=>console.error("History layer failed:",err));
  const exposurePromise = api.exposureLayer().then(geojson => {
    state.exposureLayer=L.geoJSON(geojson,{style:()=>({color:"#7656d6",weight:1,opacity:.58,fillColor:"#a28bea",fillOpacity:.14}),onEachFeature:(f,l)=>{const p=f?.properties||{};l.bindTooltip(`<strong>Exposure</strong><br>Cell ${esc(p.cell_id)}<br>Score ${n(p.exposure_score)} · ${esc(p.exposure_category)}`,{sticky:true});l.on("click",()=>{switchView("risk-map");openContextDrawer();})}});
    if(desiredLayers.has("exposure"))state.exposureLayer.addTo(map);
  }).catch(err=>console.error("Exposure layer failed:",err));
  const incidentsPromise = api.incidents().then(geojson => {
    state.incidentLayer=L.geoJSON(geojson,{pane:"awareonIncidentPane",pointToLayer:(f,ll)=>{const p=f?.properties||{};const radius=p.priority_level==="P1_CRITICAL"?10:p.priority_level==="P2_HIGH"?8:7;return L.circleMarker(ll,{radius,color:"#583113",weight:1.6,fillColor:"#ef7b33",fillOpacity:.94})},onEachFeature:(f,l)=>{const p=f?.properties||{};l.incidentId=String(p.incident_id??"");l.bindTooltip(`<strong>${esc(p.priority_level)}</strong><br>${esc(p.incident_id)} · rank #${p.priority_rank}<br>Priority ${n(p.priority_score)} · ${p.cell_count??0} cells`,{sticky:true});l.on("click",()=>focusIncident(p.incident_id));}});
    if(desiredLayers.has("incidents"))state.incidentLayer.addTo(map);
    if(pendingIncidentId){const id=pendingIncidentId;pendingIncidentId=null;setTimeout(()=>focusIncident(id),0);}
  }).catch(err=>console.error("Incident layer failed:",err));
  await Promise.allSettled([boundaryPromise,historyPromise,exposurePromise,incidentsPromise]);
}

export async function initMap() {
  map.invalidateSize(true);
  initializeMapTools();
  await loadRisk();
  loadSecondaryLayers();
  setTimeout(()=>{map.invalidateSize(true);syncRiskDisplay();},120);
}

map.on("zoomend",()=>{rebuildRiskClusters();syncRiskDisplay();});
map.on("moveend",()=>{if(map.getZoom()<POLYGON_ZOOM)rebuildRiskClusters();});
window.addEventListener("resize",()=>setTimeout(()=>map.invalidateSize(true),80));

window.awareonMapDebug=()=>({zoom:map.getZoom(),mapWidth:map.getContainer().getBoundingClientRect().width,mapHeight:map.getContainer().getBoundingClientRect().height,riskFeatures:state.riskGeoJson?.features?.length||0,riskPolygons:riskPolygonLayer?.getLayers()?.length||0,riskPoints:riskPointLayer?.getLayers()?.length||0,riskClusters:riskClusterLayer?.getLayers()?.length||0,riskIncidents:state.incidentLayer?.getLayers()?.length||0,selectedCell:state.selectedCell?.cell_id||null});
