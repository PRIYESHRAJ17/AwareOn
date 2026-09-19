AwareOn

AI-Powered Geospatial Landslide Intelligence & Early-Warning Decision Support

AwareOn is a map-first spatial intelligence platform built to help investigate landslide risk, understand environmental and historical signals, explore supported rainfall scenarios, examine evidence, and turn spatial intelligence into operational priorities.

It brings risk analytics, GIS context, incidents, scenarios, evidence, verification, and conversational AI into one focused workspace.

AwareOn is a decision-support system. It is not a replacement for official emergency warnings, field inspection, or government authorities.

What AwareOn Is

AwareOn is designed around a simple workflow:

ASK → INVESTIGATE → VERIFY → UNDERSTAND → LOCATE → DECIDE

Instead of forcing users to navigate raw datasets, APIs, model outputs, and GIS internals, AwareOn presents the useful intelligence first and progressively reveals deeper evidence and analysis when required.

The product is designed around a Sikkim / Himalayan landslide-risk study context, while keeping the architecture extensible to broader spatial-risk applications.

Core Product Experiences

🗺️ Map-First Spatial Intelligence

The map is the primary workspace rather than a background visualization.

AwareOn supports:

Interactive Leaflet-based spatial exploration

Cell-level risk visualization

Risk polygons, points, and zoom-aware clustering

Smooth map focus and repositioning

Exact-cell selection and investigation

Regional spatial context

Historical and exposure layers

Incident highlighting and affected-cell focus

Highest-risk focus and map reset

Adaptive GIS scale display based on the real map scale

The interface uses progressive disclosure so the map remains readable while deeper intelligence appears only when needed.

📊 Risk Explorer

Risk Explorer turns the spatial risk surface into an investigation workflow.

Users can:

Explore modeled risk across the study area

Select individual cells

Inspect risk severity and warning state

Review confidence and uncertainty

Understand dominant risk drivers

Open deeper cell intelligence

Move from spatial context into evidence-backed investigation

Risk semantics remain consistent across the map and analytical interfaces:

LOW · MODERATE · HIGH · EXTREME

🚨 Incident Command

AwareOn converts spatially related risk and alert information into ranked incidents.

Users can:

Review prioritized incidents

Inspect incident priority and affected cells

Focus an incident directly on the map

Understand the surrounding risk context

Move from incident overview into deeper investigation

The map remains central throughout the incident workflow.

🌧️ Scenario Lab

AwareOn exposes only validated rainfall counterfactual states:

Scenario

State

Baseline

0%

Moderate shock

+25%

Strong shock

+50%

Extreme shock

+100%

Scenario exploration can surface modeled changes including:

Mean risk

Mean risk change

Escalating cells

Newly elevated cells

Newly extreme cells

Maximum risk

Rainfall-trigger response

Scenario interpretation and decision context

AwareOn intentionally does not invent unsupported intermediate rainfall simulations.

🤖 AO Intel — Conversational Intelligence

AO Intel provides natural-language access to AwareOn's spatial intelligence.

Users can ask questions such as:

Which areas should be reviewed first?

Why is this cell high risk?

What happens if rainfall increases by 50%?

Which historical events are relevant here?

What is the historical trajectory of this region?

AO Intel can route supported questions into specialized investigation paths for:

Cell risk

Regional risk

Scenarios

Historical intelligence

Temporal intelligence

Early warning

Exposure

Decision support

Risk explanation

General AwareOn-domain questions

The goal is not generic chatbot behavior.

AO Intel is designed around:

ASK → INVESTIGATE → SHOW → ACT

Where supported, responses can connect back to the map, investigations, scenarios, and evidence.

Evidence-First Intelligence

AwareOn treats evidence as a first-class part of the product.

The intelligence workflow is designed to:

Gather evidence from investigation pipelines

Ground model-generated reasoning against supplied evidence

Distinguish observed, derived, historical, and simulated information

Preserve source and evidence context

Perform verification before accepting supported answers

Surface limitations and uncertainty

Reject unsupported claims rather than silently inventing them

Detailed evidence can be opened through the intelligence interface without forcing raw backend schemas into the initial view.

Confidence & Uncertainty

Risk and confidence are intentionally separate concepts.

For example:

HIGH RISK + HIGH CONFIDENCE

and

HIGH RISK + LOW CONFIDENCE

represent meaningfully different situations.

AwareOn therefore exposes confidence, uncertainty, evidence quality, and limitations alongside risk where the underlying intelligence supports them.

AI Architecture

AwareOn uses a layered intelligence architecture rather than treating the language model as the system of truth.

Intelligence flow

User
  ↓
AwareOn UI / Map / AO Intel
  ↓
Intelligence API
  ↓
Domain + Intent Routing
  ↓
Specialized Investigation
  ├── Cell Intelligence
  ├── Regional Intelligence
  ├── Scenario Investigation
  ├── Historical Intelligence
  ├── Temporal Intelligence
  ├── Early Warning
  ├── Exposure
  └── Decision Support
  ↓
Evidence / Grounding
  ↓
Verification
  ↓
Answer + Confidence + Limitations
  ↓
Spatial / Decision Actions

Model policy

AwareOn's AI layer is designed so that:

Canonical evidence remains the source of truth

AI reasoning is grounded rather than treated as authoritative data

Validated memory and learning signals remain evidence-linked

Unsupported claims are rejected

Critical deterministic paths remain deterministic where appropriate

The production model architecture uses a primary Qwen-based model with a lightweight Nemotron backup path.

12 Core Intelligence Engines

AwareOn's intelligence stack is built around twelve registered engines:

Landslide Susceptibility

Rainfall Trigger

Soil Wetness

Terrain Instability

SAR Evidence

Historical Events

Anomaly Detection

Exposure & Impact

Spatial Propagation

Temporal Risk

Confidence & Uncertainty

Explanation & Recommendation

These engines feed the higher-level investigation, evidence, warning, scenario, and decision workflows.

Major Investigation Paths

Intent

Purpose

CELL_RISK

Investigate an exact spatial risk cell

REGIONAL_RISK

Analyze regional risk and high-risk clusters

SCENARIO

Evaluate supported rainfall counterfactuals

TEMPORAL

Analyze environmental trends over time

HISTORICAL_EVENT

Investigate historical events

HISTORICAL_RECURRENCE

Identify repeated historical patterns

HISTORICAL_CURRENT

Connect historical context to current intelligence

EARLY_WARNING

Generate warning-oriented intelligence

EXPOSURE

Analyze infrastructure / settlement exposure

DECISION

Produce operational prioritization

EXPLANATION

Explain evidence and risk drivers

GENERAL_AWAREON

Answer supported AwareOn-domain questions

Product Design Principles

Map-first

Spatial context remains central to investigation and decision making.

Evidence before assertion

Important claims should be traceable to supported evidence.

Progressive disclosure

Users see the most useful information first, then deeper context on demand.

Model honesty

Observed, derived, historical, simulated, uncertain, and unsupported information are not intentionally presented as the same thing.

Deterministic where possible

Critical scenario and intelligence paths use validated deterministic logic where appropriate.

Operational usefulness

The product aims to answer not only:

What is happening?

but also:

What deserves attention next?

Repository Structure

AwareOn/
├── backend/
│   └── app/
│       ├── ai/
│       ├── intelligence/
│       ├── services/
│       ├── exact_cell_intelligence.py
│       ├── regional_intelligence.py
│       └── ...
│
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── app.js
│       ├── intelligence.js
│       ├── map.js
│       ├── scenarios.js
│       ├── state.js
│       └── views.js
│
├── data/
├── gis/
├── ml/
├── simulation/
├── scripts/
├── docs/
├── artifacts/
├── cv/
├── DATA_PRESERVATION.md
├── LEVEL20_E2E_QA.md
├── INSTALL_FROM_BACKUP.ps1
├── INSTALL_FROM_BACKUP.sh
├── START_AWAREON.ps1
├── START_FRONTEND.ps1
└── README.md

Local Setup

Requirements

Python 3.11+ recommended

Git

A modern web browser

The required AwareOn project data under data/

Start the backend

From the repository root:

python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

Backend:

http://127.0.0.1:8000

Start the frontend

Use the project's normal frontend serving method or the provided Windows startup script:

START_FRONTEND.ps1

The repository also includes:

START_AWAREON.ps1

for combined local startup.

Validation

AwareOn includes automated validation and end-to-end QA.

Level 20 E2E

python scripts/level20_e2e.py

The documented smoke suite covers:

Health

Risk

Regional intelligence

Scenario

Out-of-domain handling

The previously recorded validation result is:

health       | PASS
risk         | PASS
regional     | PASS
scenario     | PASS
ood          | PASS

RESULT: 5/5

AI Benchmark

The project also includes dedicated AI benchmark coverage for:

Cell explanation

Rainfall scenarios

Regional intelligence

Historical trajectory

Early warning

Decision support

Evidence conflict handling

Out-of-domain rejection

Previously recorded real-agent benchmark:

TOTAL: 9
PASSED: 9
FAILED: 0
SCORE: 96.83

These figures are documented project validation results; rerun the suites locally when making a new release or deployment.

Model Honesty & Safety

AwareOn intentionally avoids representing unsupported simulations or fabricated observations as real-world facts.

In particular:

Supported rainfall states are explicitly bounded

Simulated outputs remain identified as modeled

AI inference is not automatically treated as observed truth

Evidence and verification remain part of the intelligence workflow

Out-of-domain questions can be rejected

Users are shown limitations where the available intelligence cannot support a reliable answer

AwareOn is intended for research, analysis, and decision support.

It should not be treated as an independent emergency-warning authority or as a substitute for official agencies, field teams, or on-ground verification.

Typical Questions

Regional

Which areas currently deserve the most attention?

Cell investigation

Why is cell 506_422 high risk?

Scenario analysis

What happens if rainfall increases by 50%?

Historical intelligence

Which historical landslides are relevant to this region?

Temporal intelligence

What is the historical trajectory of this area?

Decision support

Which areas should a field team review first?

Current Product Status

AwareOn is a complete map-first spatial intelligence application combining:

Interactive geospatial risk exploration

Cell and regional intelligence

Incident investigation

Supported rainfall scenario analysis

Evidence-backed AI investigation

Confidence and uncertainty context

Historical and temporal intelligence

Operational prioritization

Progressive disclosure and contextual investigation

Responsive map-first product UX

The frontend is designed as a focused spatial intelligence workspace rather than a conventional dashboard, keeping the map central while exposing deeper intelligence on demand.

Responsible Use

AwareOn is a research and decision-support platform.

Risk scores, scenario outputs, historical interpretations, exposure analyses, and AI-generated responses should always be interpreted in the context of:

Available data

Model assumptions

Evidence quality

Confidence and uncertainty

Supported scenario boundaries

Local field conditions

Official guidance

For real-world emergency decisions, official authorities and qualified field professionals remain authoritative.




Author
Priyesh Raj
