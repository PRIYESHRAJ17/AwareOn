# AwareOn

### AI-Powered Landslide Intelligence & Early-Warning Platform

AwareOn is an AI-powered geospatial intelligence platform for landslide-risk analysis, environmental monitoring, spatial investigation, scenario exploration, and operational decision support.

It combines spatial risk data, environmental signals, historical intelligence, evidence grounding, deterministic investigation pipelines, and agentic reasoning into a single map-first operational workspace.

---

## What AwareOn Does

AwareOn helps users answer questions such as:

- Which areas currently have the highest modeled landslide risk?
- Which locations should be reviewed or inspected first?
- Why is a particular area high risk?
- What evidence supports the assessment?
- What happens under a supported rainfall counterfactual?
- What historical patterns are relevant to current risk?
- Which spatial cells require closer attention?

The system is designed to move from **question → investigation → evidence → spatial context → decision support**.

---

## Key Capabilities

### 🗺️ Spatial Risk Intelligence

- Interactive map-first risk exploration
- Cell-level and regional risk analysis
- High / Extreme risk identification
- Spatial clustering and priority detection
- Exact-cell investigation
- Regional intelligence around study-area coordinates

### 🤖 AI Intelligence Agent

- Natural-language interaction with AwareOn
- Domain-aware query routing
- Intent classification
- Conversational memory
- Evidence-grounded answer synthesis
- Specialized investigation paths for:
  - Cell risk
  - Regional risk
  - Scenarios
  - Historical intelligence
  - Temporal intelligence
  - Early warning
  - Exposure
  - Decision support

### 🌧️ Scenario Lab
AwareOn supports tested rainfall counterfactuals:

- Baseline — 0%
- Moderate shock — +25%
- Strong shock — +50%
- Extreme shock — +100%

Scenario results expose modeled changes such as:

- Mean risk
- Mean risk change
- Escalating cells
- Newly elevated cells
- Newly extreme cells
- Maximum risk
- Rainfall trigger response

Unsupported intermediate simulations are intentionally not presented as validated model outputs.

### 🔎 Evidence & Verification
AwareOn maintains an evidence-oriented architecture so that:

- Evidence is collected from investigation pipelines
- Model-generated reasoning is grounded against supplied evidence
- Observed, derived, historical, and simulated information are kept conceptually separate
- Verification is performed before validated answers are returned
- Unsupported claims are rejected rather than silently invented

### 🧠 Decision Intelligence
The platform can transform regional intelligence into an operational priority order, allowing users to identify the highest-risk areas for further review.

### 💬 Conversational Intelligence
Users can interact using natural language rather than learning internal API or GIS terminology.

Examples:

> Which areas should be reviewed first?

> Which area is most affected by landslides in Sikkim?

> What happens if rainfall increases by 50%?

> Why is this area high risk?

> Tell this in short.

---

## Architecture

```text
                    ┌─────────────────────┐
                    │     AwareOn UI      │
                    │ Map • Risk • AI •   │
                    │ Scenario • Incidents│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Intelligence API    │
                    │ Natural-language    │
                    │ investigation entry │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Domain Router       │
                    │ Domain + Intent     │
                    └──────────┬──────────┘
                               │
┌─────────────────┼──────────────────┐ ▼                 ▼                  ▼ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │ Cell         │  │ Regional     │  │ Scenario     │ │ Intelligence │  │ Intelligence │  │ Investigation│ └──────────────┘  └──────────────┘  └──────────────┘ │                 │                  │ └─────────────────┼──────────────────┘ ▼ ┌─────────────────────┐ │ Evidence / Grounding│ │ Verification        │ └──────────┬──────────┘ │ ▼ ┌─────────────────────┐ │ Answer Synthesis    │ │ + Decision Support  │ └─────────────────────┘

---

## Major AI Investigation Paths

| Intent | Purpose |
| --- | --- |
| `CELL_RISK` | Investigate an exact spatial risk cell |
| `REGIONAL_RISK` | Analyze regional risk and high-risk clusters |
| `SCENARIO` | Evaluate supported rainfall counterfactuals |
| `TEMPORAL` | Analyze environmental trends over time |
| `HISTORICAL_EVENT` | Investigate historical events |
| `HISTORICAL_RECURRENCE` | Identify repeated historical patterns |
| `HISTORICAL_CURRENT` | Connect historical context to current intelligence |
| `EARLY_WARNING` | Generate warning-oriented intelligence |
| `EXPOSURE` | Analyze infrastructure / settlement exposure |
| `DECISION` | Produce operational prioritization |
| `EXPLANATION` | Explain evidence and risk drivers |
| `GENERAL_AWAREON` | Answer supported AwareOn-domain questions |

---

## Repository Structure

```text
AwareOn/
├── backend/
│   └── app/
│       ├── ai/
│       │   ├── autonomous_master.py
│       │   ├── domain_router.py
│       │   ├── domain_knowledge.py
│       │   ├── domain_retrieval.py
│       │   ├── cell_investigator.py
│       │   ├── regional_investigator.py
│       │   ├── scenario_investigator.py
│       │   ├── decision_orchestrator.py
│       │   ├── temporal_orchestrator.py
│       │   ├── evidence_synthesis.py
│       │   ├── grounding.py
│       │   ├── verification.py
│       │   └── ...
│       ├── intelligence_api.py
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
│       ├── scenarios.js
│       ├── map.js
│       └── views.js
│
├── data/
├── gis/
├── ml/
├── simulation/
├── scripts/
├── docs/
├── cv/
│
├── DATA_PRESERVATION.md
├── LEVEL20_E2E_QA.md
├── INSTALL_FROM_BACKUP.ps1
├── INSTALL_FROM_BACKUP.sh
├── START_AWAREON.ps1
├── START_FRONTEND.ps1
└── README.md

## Local Setup

### Requirements

- Python 3.11+ recommended
- Git
- A modern web browser
- Existing AwareOn project data under `data/`

### Backend

From the repository root:

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

The backend API is available at:

[127.0.0.1:8000](http://127.0.0.1:8000)
Frontend

Serve the frontend using the project's normal frontend startup method.

The repository also contains:

START_AWAREON.ps1
START_FRONTEND.ps1

for local startup on Windows.

Validation

AwareOn includes automated checks for core system behavior.

End-to-End QA
python scripts/level20_e2e.py

Verified smoke-suite result:

| health | PASS |
| --- | --- |
| risk | PASS |
| regional | PASS |
| scenario | PASS |
| ood | PASS |

RESULT: 5/5
AI Agent Benchmark

The project also contains dedicated AI benchmark suites covering:

Cell explanation
Rainfall scenarios
Regional intelligence
Historical trajectory
Early warning
Decision support
Evidence conflict handling
Out-of-domain rejection

The previously executed real-agent benchmark completed:

TOTAL: 9
PASSED: 9
FAILED: 0
SCORE: 96.83
Model Honesty

AwareOn is intentionally designed not to represent unsupported simulations or fabricated observations as real-world facts.

Scenario Lab exposes only the supported tested rainfall states.

The intelligence layer distinguishes between evidence types and uses verification before accepting model-generated claims.

When the system cannot reliably answer a question from its supported intelligence, it should state that limitation rather than invent information.

Example Queries
Regional intelligence
Which area is most affected by landslides in Sikkim?
Operational prioritization
Which areas should be reviewed first?
Scenario analysis
What happens if rainfall increases by 50%?
Cell investigation
Why is cell 506_422 high risk?
Historical intelligence
Which historical landslides occurred near Gangtok?
Temporal intelligence
What is the historical trajectory of this region?
Current Study Context

AwareOn is designed around a Sikkim / Himalayan landslide intelligence study context, where terrain, rainfall, environmental conditions, historical activity, infrastructure exposure, and spatial risk interact.

The system is intended as a decision-support platform, not as a replacement for official emergency management, field inspection, or government warning systems.

Design Principles

AwareOn follows several core principles:

Map-first intelligence
Spatial context remains central to investigation and decision making.
Evidence before assertion
Answers should be grounded in supported evidence.
Deterministic where possible
Critical scenario and intelligence paths use validated deterministic pipelines.
Natural language access
Users should be able to ask questions without learning system internals.
Model honesty
Simulated information is explicitly treated as simulated.
Operational usefulness
The objective is not only to describe risk, but to help users determine what deserves attention next.
Status

Submission-ready AwareOn build

Core platform, AI investigation workflows, Scenario Lab, evidence/verification pipeline, conversational intelligence, spatial investigation, and Level 20 end-to-end QA are implemented.



Author
Priyesh Raj
