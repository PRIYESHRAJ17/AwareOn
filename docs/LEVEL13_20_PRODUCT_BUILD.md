# AwareOn Levels 13–20 Product Build

## Product direction

AwareOn is a map-first spatial decision-intelligence workspace. The interface intentionally uses progressive disclosure: the map remains the dominant canvas and context appears when the user asks for it or selects a spatial object.

The interaction language is inspired by the current Atlas product direction: conversational entry, live map as the primary workspace, contextual analysis, clean surfaces, restrained motion, and reusable workspaces/templates. AwareOn keeps its own disaster-intelligence identity and risk semantics.

## Level 13 — UI/UX

- Light workspace with dark navigation rail.
- Adaptive contextual drawer; the map remains visible and dominant.
- Larger readable type instead of shrinking content to create density.
- Calm white/cool-gray surfaces, restrained navy/blue accents, semantic risk colors.
- Smooth panel and message transitions.
- ChatGPT-like AwareOn thinking indicator using `AO` branding.
- Progressive disclosure replaces permanently visible dashboard clutter.

## Level 14 — AI ↔ Map

- Risk cells aggregate into numbered visual clusters at lower zoom.
- Clusters expand progressively as zoom increases.
- High-detail view uses interactive cells rather than a wall of tiny dots.
- Hover shows a quiet spatial tooltip.
- Click opens a quick popup.
- `Open intelligence` moves into the contextual drawer.
- Incident focus highlights affected risk cells and recenters the map.
- Search can locate risk cells and incidents.

## Level 15 — Performance / reliability

- Leaflet canvas rendering is enabled for spatial efficiency.
- Risk markers are progressively represented by zoom-dependent aggregation.
- Map camera transitions use bounded fly-to/fly-to-bounds animations.
- Frontend loading states are explicit and non-blocking.
- Intelligence requests have clean error handling and session identifiers.

## Level 16 — API hardening

- Intelligence requests accept a bounded session identifier.
- Server-side conversation memory is bounded by session count and turn count.
- Generic 500 responses no longer expose raw internal exception text to clients.
- Existing exact-cell and spatial APIs are preserved.

## Level 17 — Security / repository hygiene

- Environment files and credentials stay ignored.
- Runtime caches, bytecode, model binaries, and generated geospatial artifacts remain excluded from source delivery.
- No client-side secrets were introduced.

## Level 18 — Documentation

This document plus `LEVEL20_E2E_QA.md` define the final product and local QA contract for Levels 13–20.

## Level 19 — Demo readiness

The final demo should demonstrate:

1. Sikkim current regional situation → regional intelligence.
2. Exact cell investigation → quick popup → deep drawer.
3. Incident focus → affected cells on map.
4. Rainfall scenario → scenario readout and map effect.
5. Evidence-backed AI explanation.
6. Out-of-domain safety boundary.

## Level 20 — Final E2E QA

Run the E2E helper locally after the user's original `data/` assets have been restored. The browser acceptance checklist is included in `LEVEL20_E2E_QA.md`.
