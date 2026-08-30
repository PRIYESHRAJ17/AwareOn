AWAREON — ULTIMATE FRONTEND FOUNDATION
======================================

Purpose
-------
This is the permanent frontend foundation for AwareOn Steps 36–50.
It is designed as an AI-native geospatial decision-intelligence interface rather than a generic dashboard.

Included
--------
- Command Center
- Risk Explorer
- Incident Command
- Scenario Lab
- Intelligence workspace
- Immersive Leaflet map
- Risk / Incident / History / Exposure map controls
- Incident focus with affected-cell highlighting
- Contextual assessment panel
- Global command/search palette (Cmd/Ctrl+K)
- Scenario outcome cards
- Trust-boundary labels: Observed / Derived / Modelled / Simulated
- Responsive layouts
- Loading/empty/degraded interaction states
- Premium visual hierarchy, motion and glass surfaces

Backend APIs expected
---------------------
http://127.0.0.1:8000

At minimum:
/health
/api/v1/risk
/api/v1/alerts
/api/v1/assessment/{cell_id}
/api/v1/gis/risk-layer
/api/v1/gis/exposure-layer
/api/v1/gis/historical-hotspots
/api/v1/gis/priority-incidents
/api/v1/gis/boundary
/api/v1/scenario/summary
/api/v1/scenario/simulate

Run
---
From the AwareOn repository:

python -m http.server 5500 --directory frontend

Keep FastAPI running on port 8000.
Open:
http://127.0.0.1:5500

IMPORTANT
---------
The files in this package are meant to replace the contents of your existing frontend folder as a single permanent baseline.
Do not keep applying whole-file app.js replacements for every future step. Later work should extend the existing modules.
