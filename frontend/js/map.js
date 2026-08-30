import { api } from "./api.js";
import { state } from "./state.js";
import { switchView } from "./views.js";

const INITIAL_CENTER = [27.55, 88.45];
const INITIAL_ZOOM = 9;
const DETAIL_ZOOM = 11;
const INITIAL_MAX_ZOOM = 12;
const MAX_FOCUS_ZOOM = 15;

export const map = L.map("map", {
  zoomControl: false,
  attributionControl: true,
  preferCanvas: false,
  zoomAnimation: true,
  fadeAnimation: true,
  markerZoomAnimation: true
}).setView(INITIAL_CENTER, INITIAL_ZOOM);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  opacity: 0.90,
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

createPane("awareonRiskPolygonPane", 620, "auto");
createPane("awareonRiskPointPane", 660, "auto");
createPane("awareonIncidentPane", 680, "auto");
createPane("awareonBoundaryPane", 610, "none");

let riskPointLayer = null;
let riskPolygonLayer = null;
let mapToolsBound = false;
let secondaryLayersStarted = false;
let pendingIncidentId = null;
const desiredLayers = new Set(["risk"]);

const n = (v, d = 1) => {
  const number = Number(v);
  return Number.isFinite(number) ? number.toFixed(d) : "—";
};

const esc = v => String(v ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

const riskColor = score => {
  const n = Number(score);
  if (n >= 75) return "#7e2023";
  if (n >= 50) return "#de403e";
  if (n >= 25) return "#d69318";
  return "#19a463";
};

const riskLabel = score => {
  const n = Number(score);
  if (n >= 75) return "EXTREME";
  if (n >= 50) return "HIGH";
  if (n >= 25) return "MODERATE";
  return "LOW";
};

const normal = f => ({
  color: "#0d1b2a",
  weight: 1.1,
  opacity: 0.78,
  fillColor: riskColor(f?.properties?.unified_risk_score),
  fillOpacity: 0.60
});

const hover = f => ({
  color: "#081320",
  weight: 3,
  opacity: 1,
  fillColor: riskColor(f?.properties?.unified_risk_score),
  fillOpacity: 0.88
});

const selected = f => ({
  color: "#2563eb",
  weight: 4.5,
  opacity: 1,
  fillColor: riskColor(f?.properties?.unified_risk_score),
  fillOpacity: 0.94
});

const dim = f => ({
  color: "#93a1b2",
  weight: 0.5,
  opacity: 0.18,
  fillColor: riskColor(f?.properties?.unified_risk_score),
  fillOpacity: 0.06
});

const focus = f => ({
  color: "#00bcd4",
  weight: 4.5,
  opacity: 1,
  fillColor: riskColor(f?.properties?.unified_risk_score),
  fillOpacity: 0.90,
  dashArray: "7 4"
});

function cellTooltip(p) {
  return `<strong>AwareOn cell ${esc(p?.cell_id)}</strong><br>Risk ${n(p?.unified_risk_score)} · ${esc(riskLabel(p?.unified_risk_score))}<br>Warning ${esc(p?.warning_state)}<br>Confidence ${n(p?.confidence_score)}<br><span style="color:#2563eb;font-weight:800">Click to investigate</span>`;
}

function featureCenter(feature) {
  const geometry = feature?.geometry;
  if (!geometry) return null;

  if (geometry.type === "Point") {
    const [lon, lat] = geometry.coordinates || [];
    if (!Number.isFinite(Number(lat)) || !Number.isFinite(Number(lon))) return null;
    return [Number(lat), Number(lon)];
  }

  if (geometry.type === "Polygon") {
    const ring = geometry?.coordinates?.[0];
    if (!Array.isArray(ring) || ring.length === 0) return null;

    let minLon = Infinity, maxLon = -Infinity;
    let minLat = Infinity, maxLat = -Infinity;

    for (const coordinate of ring) {
      if (!Array.isArray(coordinate) || coordinate.length < 2) continue;
      const lon = Number(coordinate[0]);
      const lat = Number(coordinate[1]);
      if (!Number.isFinite(lon) || !Number.isFinite(lat)) continue;
      minLon = Math.min(minLon, lon);
      maxLon = Math.max(maxLon, lon);
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
    }

    if (!Number.isFinite(minLon) || !Number.isFinite(maxLon) || !Number.isFinite(minLat) || !Number.isFinite(maxLat)) return null;
    return [(minLat + maxLat) / 2, (minLon + maxLon) / 2];
  }

  if (geometry.type === "MultiPolygon") {
    const first = geometry?.coordinates?.[0];
    if (first) return featureCenter({ geometry: { type: "Polygon", coordinates: first } });
  }

  return null;
}

function riskPointIcon() {
  return L.divIcon({
    className: "awareon-risk-point-icon",
    html: `<span class="awareon-risk-point" style="display:block;width:5px;height:5px;background:#111827;border:1px solid rgba(255,255,255,.96);border-radius:50%;box-shadow:0 0 0 1px rgba(15,23,42,.40);transform:translate(-50%,-50%);cursor:pointer;pointer-events:auto;transition:transform 120ms ease,box-shadow 120ms ease,background 120ms ease"></span>`,
    iconSize: [5, 5],
    iconAnchor: [2.5, 2.5]
  });
}

function buildRiskPointLayer(geojson) {
  const group = L.layerGroup();
  const features = geojson?.features || [];
  let created = 0;

  for (const feature of features) {
    const properties = feature?.properties || {};
    const center = featureCenter(feature);
    if (!center) continue;

    const marker = L.marker(center, {
      icon: riskPointIcon(),
      pane: "awareonRiskPointPane",
      keyboard: true,
      title: `AwareOn risk cell ${properties.cell_id ?? ""}`
    });

    marker.feature = feature;
    marker.cellId = String(properties.cell_id ?? "");

    marker.bindTooltip(cellTooltip(properties), {
      sticky: true,
      direction: "top",
      opacity: 0.98,
      className: "awareon-risk-tooltip"
    });

    marker.on("mouseover", () => {
      const element = marker.getElement();
      const dot = element?.querySelector(".awareon-risk-point");
      if (dot) {
        dot.style.transform = "translate(-50%,-50%) scale(2.1)";
        dot.style.background = "#020617";
        dot.style.boxShadow = "0 0 0 3px rgba(37,99,235,.16),0 0 10px rgba(15,23,42,.42)";
      }
    });

    marker.on("mouseout", () => {
      const element = marker.getElement();
      const dot = element?.querySelector(".awareon-risk-point");
      if (dot) {
        dot.style.transform = "translate(-50%,-50%)";
        dot.style.background = "#111827";
        dot.style.boxShadow = "0 0 0 1px rgba(15,23,42,.40)";
      }
    });

    marker.on("click", () => selectCellById(marker.cellId));
    group.addLayer(marker);
    created += 1;
  }

  console.log("AwareOn risk points created:", created);
  return group;
}

function loadRiskLayer(geojson) {
  state.riskGeoJson = geojson;

  riskPolygonLayer = L.geoJSON(geojson, {
    pane: "awareonRiskPolygonPane",
    style: normal,
    onEachFeature(feature, layer) {
      const p = feature?.properties || {};
      layer.bindTooltip(cellTooltip(p), {
        sticky: true,
        direction: "top",
        opacity: 0.97,
        className: "awareon-risk-tooltip"
      });

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

      layer.on("click", () => selectCell(layer));
      layer.on("add", () => {
        const element = layer.getElement();
        if (element) element.style.cursor = "pointer";
      });
    }
  });

  state.riskLayer = riskPolygonLayer;
  state.mapInitialBounds = riskPolygonLayer.getBounds();

  riskPointLayer = buildRiskPointLayer(geojson);
  riskPointLayer.addTo(map);

  if (state.mapInitialBounds.isValid()) {
    map.fitBounds(state.mapInitialBounds, { padding: [45, 45], maxZoom: INITIAL_MAX_ZOOM });
  }

  syncRiskDisplay();
}

async function loadRisk() {
  const riskGeo = await api.riskLayer();
  if (!riskGeo || riskGeo.type !== "FeatureCollection" || !riskGeo.features?.length) {
    throw new Error("AwareOn risk layer returned no features.");
  }
  loadRiskLayer(riskGeo);
  console.log("AwareOn risk layer loaded:", riskGeo.features.length);
}

function syncRiskDisplay() {
  if (!riskPointLayer || !riskPolygonLayer) return;

  if (state.incidentFocusActive) {
    if (!map.hasLayer(riskPolygonLayer)) riskPolygonLayer.addTo(map);
    if (map.hasLayer(riskPointLayer)) map.removeLayer(riskPointLayer);
    return;
  }

  const zoom = map.getZoom();

  if (zoom < DETAIL_ZOOM) {
    if (!map.hasLayer(riskPolygonLayer)) {
      // keep polygons available for programmatic selection but don't render them regionally
    } else {
      map.removeLayer(riskPolygonLayer);
    }

    if (!map.hasLayer(riskPointLayer) && desiredLayers.has("risk")) riskPointLayer.addTo(map);
  } else {
    if (!map.hasLayer(riskPolygonLayer) && desiredLayers.has("risk")) riskPolygonLayer.addTo(map);
    if (!map.hasLayer(riskPointLayer) && desiredLayers.has("risk")) riskPointLayer.addTo(map);
  }
}

function selectCellById(cellId) {
  if (!riskPolygonLayer) {
    console.warn("Risk polygon layer is not ready.");
    return;
  }

  let target = null;
  riskPolygonLayer.eachLayer(layer => {
    if (String(layer?.feature?.properties?.cell_id) === String(cellId)) target = layer;
  });

  if (target) selectCell(target);
  else console.warn("AwareOn risk cell not found:", cellId);
}

function selectCell(layer) {
  if (!layer) return;

  clearIncidentFocus();

  if (state.selectedRiskLayer && state.selectedRiskLayer !== layer) {
    state.selectedRiskLayer.setStyle(normal(state.selectedRiskLayer.feature));
  }

  state.selectedRiskLayer = layer;
  state.selectedCell = layer.feature.properties;

  if (!map.hasLayer(riskPolygonLayer)) riskPolygonLayer.addTo(map);
  layer.setStyle(selected(layer.feature));
  layer.bringToFront();

  const bounds = layer.getBounds();
  if (bounds?.isValid()) {
    map.flyToBounds(bounds, { padding: [90, 90], maxZoom: MAX_FOCUS_ZOOM, duration: 0.55 });
  }

  switchView("risk-map");
  window.dispatchEvent(new CustomEvent("awareon:cell", { detail: layer.feature.properties }));
}

export function focusIncident(id) {
  if (!state.incidentLayer) {
    pendingIncidentId = String(id);
    console.log("Incident focus queued until spatial incident layer is ready:", id);
    return;
  }

  let target = null;
  state.incidentLayer.eachLayer(layer => {
    if (String(layer.incidentId) === String(id)) target = layer;
  });

  if (!target) {
    console.warn("AwareOn incident not found:", id);
    return;
  }

  const p = target.feature.properties;
  const affected = String(p.affected_cells || "").split(",").map(v => v.trim()).filter(Boolean);

  state.incidentFocusActive = true;
  state.selectedIncident = p;
  state.highlightedIncidentCells = [];

  if (riskPointLayer && map.hasLayer(riskPointLayer)) map.removeLayer(riskPointLayer);
  if (riskPolygonLayer && !map.hasLayer(riskPolygonLayer)) riskPolygonLayer.addTo(map);

  riskPolygonLayer.eachLayer(layer => {
    const hit = affected.includes(String(layer?.feature?.properties?.cell_id));
    layer.setStyle(hit ? focus(layer.feature) : dim(layer.feature));
    if (hit) {
      layer.bringToFront();
      state.highlightedIncidentCells.push(layer);
    }
  });

  if (state.highlightedIncidentCells.length) {
    const bounds = L.featureGroup(state.highlightedIncidentCells).getBounds();
    if (bounds.isValid()) map.fitBounds(bounds, { padding: [70, 70], maxZoom: MAX_FOCUS_ZOOM });
  } else {
    map.flyTo(target.getLatLng(), 13, { duration: 0.6 });
  }

  target.bringToFront();
  target.openTooltip();

  const focusBar = document.getElementById("focus-bar");
  const title = document.getElementById("focus-bar-title");
  const cells = document.getElementById("focus-bar-cells");

  focusBar?.classList.add("active");
  if (title) title.textContent = `${p.incident_id} · ${p.priority_level}`;
  if (cells) cells.textContent = `${p.cell_count} affected cells`;

  switchView("risk-map");
  window.dispatchEvent(new CustomEvent("awareon:incident", { detail: p }));
}

export function clearIncidentFocus() {
  state.incidentFocusActive = false;
  state.selectedIncident = null;
  state.highlightedIncidentCells = [];

  if (riskPolygonLayer) {
    riskPolygonLayer.eachLayer(layer => {
      layer.setStyle(layer === state.selectedRiskLayer ? selected(layer.feature) : normal(layer.feature));
    });
  }

  document.getElementById("focus-bar")?.classList.remove("active");
  syncRiskDisplay();
}

export function clearCellSelection() {
  if (state.selectedRiskLayer) {
    state.selectedRiskLayer.setStyle(normal(state.selectedRiskLayer.feature));
  }
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
    case "risk": return riskPointLayer;
    case "incidents": return state.incidentLayer;
    case "history": return state.historicalLayer;
    case "exposure": return state.exposureLayer;
    default: return null;
  }
}

function applyDesiredLayer(key) {
  const layer = resolveLayer(key);
  if (!layer) return;

  const shouldShow = desiredLayers.has(key);
  const visible = map.hasLayer(layer);

  if (shouldShow && !visible) layer.addTo(map);
  if (!shouldShow && visible) map.removeLayer(layer);

  const button = document.querySelector(`[data-layer-toggle="${key}"]`);
  setButtonActive(button, shouldShow);
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

      if (desiredLayers.has(key)) desiredLayers.delete(key);
      else desiredLayers.add(key);

      setButtonActive(button, desiredLayers.has(key));
      applyDesiredLayer(key);
      syncRiskDisplay();
    });
  });

  document.getElementById("map-reset")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    desiredLayers.add("risk");
    setButtonActive(document.querySelector('[data-layer-toggle="risk"]'), true);
    clearIncidentFocus();
    clearCellSelection();
    if (state.mapInitialBounds?.isValid()) map.fitBounds(state.mapInitialBounds, { padding: [45, 45], maxZoom: INITIAL_MAX_ZOOM });
    window.setTimeout(syncRiskDisplay, 350);
  });

  document.getElementById("map-focus-risk")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    focusHighestRisk();
  });

  document.getElementById("clear-focus")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    clearIncidentFocus();
  });
}

export function focusHighestRisk() {
  if (!riskPolygonLayer) {
    console.warn("AwareOn risk layer is still loading.");
    return;
  }

  let top = null;
  riskPolygonLayer.eachLayer(layer => {
    const score = Number(layer?.feature?.properties?.unified_risk_score);
    if (Number.isFinite(score) && (!top || score > Number(top.feature.properties.unified_risk_score))) top = layer;
  });

  if (top) selectCell(top);
}

async function loadSecondaryLayers() {
  if (secondaryLayersStarted) return;
  secondaryLayersStarted = true;

  const boundaryPromise = api.boundary().then(geojson => {
    state.boundaryLayer = L.geoJSON(geojson, {
      pane: "awareonBoundaryPane",
      style: () => ({ color: "#536273", weight: 1.4, opacity: 0.55, fillOpacity: 0, interactive: false })
    }).addTo(map);
    state.boundaryLayer.bringToFront();
    console.log("Boundary loaded.");
  }).catch(err => console.error("Boundary layer failed:", err));

  const historyPromise = api.historicalLayer().then(geojson => {
    state.historicalLayer = L.geoJSON(geojson, {
      pointToLayer: (f, ll) => L.circleMarker(ll, {
        radius: Number(f?.properties?.hotspot_score) >= 75 ? 9 : Number(f?.properties?.hotspot_score) >= 50 ? 7 : 5,
        color: "#12314e",
        weight: 1.2,
        fillColor: "#2563eb",
        fillOpacity: 0.77
      }),
      onEachFeature: (f, l) => l.bindTooltip(`<strong>Historical hotspot</strong><br>${esc(f?.properties?.hotspot_id)}<br>${f?.properties?.event_count ?? 0} events · score ${n(f?.properties?.hotspot_score)}`, { sticky: true })
    });
    console.log("Historical layer loaded:", geojson?.features?.length || 0);
    applyDesiredLayer("history");
  }).catch(err => console.error("Historical layer failed:", err));

  const exposurePromise = api.exposureLayer().then(geojson => {
    state.exposureLayer = L.geoJSON(geojson, {
      style: () => ({ color: "#7656d6", weight: 1, opacity: 0.65, fillColor: "#a28bea", fillOpacity: 0.19 }),
      onEachFeature: (f, l) => l.bindTooltip(`<strong>Exposure</strong><br>Cell ${esc(f?.properties?.cell_id)}<br>Score ${n(f?.properties?.exposure_score)}<br>${esc(f?.properties?.exposure_category)}`, { sticky: true })
    });
    console.log("Exposure layer loaded:", geojson?.features?.length || 0);
    applyDesiredLayer("exposure");
  }).catch(err => console.error("Exposure layer failed:", err));

  const incidentsPromise = api.incidents().then(geojson => {
    state.incidentLayer = L.geoJSON(geojson, {
      pane: "awareonIncidentPane",
      pointToLayer: (f, ll) => {
        const p = f?.properties || {};
        const radius = p.priority_level === "P1_CRITICAL" ? 12 : p.priority_level === "P2_HIGH" ? 10 : 8;
        return L.circleMarker(ll, { radius, color: "#332010", weight: 2, fillColor: "#ef7b33", fillOpacity: 0.94 });
      },
      onEachFeature: (f, l) => {
        const p = f?.properties || {};
        l.incidentId = String(p.incident_id ?? "");
        l.bindTooltip(`<strong>Priority ${esc(p.priority_level)}</strong><br>${esc(p.incident_id)} · rank #${p.priority_rank}<br>Priority ${n(p.priority_score)} · max risk ${n(p.max_risk_score)}<br>${p.cell_count ?? 0} affected cells`, { sticky: true });
        l.on("click", () => focusIncident(p.incident_id));
      }
    });
    console.log("Incident layer loaded:", geojson?.features?.length || 0);
    applyDesiredLayer("incidents");

    if (pendingIncidentId) {
      const id = pendingIncidentId;
      pendingIncidentId = null;
      window.setTimeout(() => focusIncident(id), 0);
    }
  }).catch(err => console.error("Incident layer failed:", err));

  await Promise.allSettled([boundaryPromise, historyPromise, exposurePromise, incidentsPromise]);
}

export async function initMap() {
  map.invalidateSize(true);
  initializeMapTools();

  await loadRisk();
  loadSecondaryLayers();

  window.setTimeout(() => {
    map.invalidateSize(true);
    syncRiskDisplay();
  }, 150);

  window.setTimeout(() => map.invalidateSize(true), 600);
}

map.on("zoomend", syncRiskDisplay);

window.addEventListener("resize", () => {
  window.setTimeout(() => map.invalidateSize(true), 80);
});

window.awareonMapDebug = () => ({
  zoom: map.getZoom(),
  mapWidth: map.getContainer().getBoundingClientRect().width,
  mapHeight: map.getContainer().getBoundingClientRect().height,
  riskFeatures: state.riskGeoJson?.features?.length || 0,
  riskPolygons: riskPolygonLayer?.getLayers()?.length || 0,
  riskPoints: riskPointLayer?.getLayers()?.length || 0,
  riskPointsVisible: Boolean(riskPointLayer && map.hasLayer(riskPointLayer)),
  riskPolygonsVisible: Boolean(riskPolygonLayer && map.hasLayer(riskPolygonLayer)),
  incidents: state.incidentLayer?.getLayers()?.length || 0,
  historical: state.historicalLayer?.getLayers()?.length || 0,
  exposureReady: Boolean(state.exposureLayer),
  boundaryReady: Boolean(state.boundaryLayer),
  pendingIncidentId
});
