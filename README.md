AwareOn

AI-Powered Landslide Intelligence & Early-Warning Platform

AwareOn is an AI-powered geospatial intelligence platform for landslide-risk analysis, environmental monitoring, spatial investigation, scenario exploration, historical intelligence, incident investigation, and operational decision support.

It combines spatial risk data, environmental signals, historical intelligence, evidence grounding, deterministic investigation pipelines, confidence-aware reasoning, and agentic interaction into a single map-first operational workspace.

The product is designed around a simple flow:

Question → Investigation → Evidence → Spatial Context → Understanding → Decision Support

What AwareOn Does

AwareOn helps users answer questions such as:

Which areas currently have the highest modeled landslide risk?

Which locations should be reviewed or inspected first?

Why is a particular area high risk?

What evidence supports the assessment?

What changes under a supported rainfall scenario?

What historical patterns are relevant to current risk?

Which spatial cells or incidents require closer attention?

What does the system know, and how confident is it?

The system keeps the map as the primary spatial interface while allowing deeper intelligence to be opened progressively when required.

Key Capabilities

🗺️ Spatial Risk Intelligence

Map-first landslide risk exploration

Cell-level and regional risk analysis

Risk states: Low / Moderate / High / Extreme

Spatial aggregation and clustering

Exact-cell investigation

Regional intelligence around selected locations

AI-driven map focus for relevant cells, regions, and incidents

Interactive scale-aware map navigation

🚨 Incident & Operational Intelligence

Incident-focused spatial investigation

Incident Command workspace

Prioritized areas for further review

Exposure and impact context

Decision-oriented regional analysis

Operational investigation without leaving the map context

🤖 AwareOn Intelligence (AO Intel)

AwareOn provides a natural-language intelligence layer over the platform.

It supports:

Natural-language interaction with AwareOn

Domain-aware routing

Intent classification

Conversational context

Evidence-grounded answer synthesis

Confidence and uncertainty context

Spatially aware investigation

Explainable findings

Verification and limitation reporting

Out-of-domain handling

Primary AI model:

ollama / qwen3.5:9b

Backup model:

ollama / nemotron-3-nano:4b-q8_0

The AI is not treated as the source of truth. Canonical evidence and deterministic investigation pipelines remain authoritative.

🌧️ Scenario Lab

AwareOn supports validated rainfall counterfactuals:

Baseline — 0%

Moderate shock — +25%

Strong shock — +50%

Extreme shock — +100%

Scenario outputs can expose modeled changes such as:

Mean risk

Mean risk change

Escalating cells

Newly elevated cells

Newly extreme cells

Maximum risk

Rainfall trigger response

Unsupported intermediate rainfall states are intentionally not presented as validated model outputs.

🔎 Evidence & Verification

AwareOn uses an evidence-oriented architecture so that:

Evidence is collected from investigation pipelines

Model-generated reasoning is grounded against supplied evidence

Observed, derived, historical, and simulated information remain conceptually distinct

Verification is performed before evidence-backed answers are accepted

Conflicting or insufficient evidence can be surfaced

Unsupported claims are rejected instead of silently invented

🧠 Confidence & Uncertainty

Confidence is treated as a separate concept from risk.

AwareOn can expose:

Confidence associated with findings

Evidence quality and support

Limitations in available intelligence

Uncertainty where the system cannot justify a stronger claim

A high-risk result does not automatically mean high confidence, and an AI-generated explanation does not automatically become observed truth.

💬 Conversational Intelligence

Users can interact with AwareOn without learning internal APIs or GIS terminology.

Examples:

Which areas should be reviewed first?

Why is this cell high risk?

What happens if rainfall increases by 50%?

Which historical landslides are relevant to this region?

Explain the evidence behind this result.

Tell me only the important findings.

Architecture

                    ┌──────────────────────────┐
                    │        AwareOn UI        │
                    │ Map • Risk • AI •        │
                    │ Scenarios • Incidents    │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │     Intelligence API     │
                    │ Natural-language entry   │
                    │ Spatial + AI workflows   │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │       Domain Router       │
                    │    Domain + Intent        │
                    └────────────┬─────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │ Cell         │     │ Regional     │     │ Scenario     │
    │ Intelligence │     │ Intelligence │     │ Investigation│
    └──────────────┘     └──────────────┘     └──────────────┘
            │                    │                    │
            ├────────────────────┼────────────────────┤
            ▼                    ▼                    ▼
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │ Temporal     │     │ Historical   │     │ Exposure &   │
    │ Intelligence │     │ Intelligence │     │ Decision     │
    └──────────────┘     └──────────────┘     └──────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Evidence / Grounding     │
                    │ Verification / Confidence│
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │     Answer Synthesis     │
                    │   + Decision Support     │
                    └──────────────────────────┘

Core Intelligence Engines

AwareOn is built around a set of specialized intelligence engines:

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

These engines feed deterministic investigation workflows and the higher-level intelligence layer.

Major AI Investigation Paths

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

Analyze infrastructure and settlement exposure

DECISION

Produce operational prioritization

EXPLANATION

Explain evidence, findings, and risk drivers

GENERAL_AWAREON

Answer supported AwareOn-domain questions

Repository Structure

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
│       ├── state.js
│       └── views.js
│
├── data/
├── gis/
├── ml/
├── simulation/
├── scripts/
├── docs/
│
├── DATA_PRESERVATION.md
├── LEVEL20_E2E_QA.md
├── START_AWAREON.ps1
├── START_FRONTEND.ps1
└── README.md

Local Setup

Requirements

Python 3.11+ recommended

Git

A modern web browser

Required AwareOn project data under data/

Ollama for local AI functionality

Backend

From the repository root:

python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

The backend API is available at:

http://127.0.0.1:8000

Frontend

Serve the frontend using the project's normal frontend startup method.

The repository also contains:

START_AWAREON.ps1
START_FRONTEND.ps1

for local Windows startup.

AI

The current model policy is:

Primary:
ollama / qwen3.5:9b

Backup:
ollama / nemotron-3-nano:4b-q8_0

The AI layer is designed as an intelligence and reasoning layer over AwareOn's evidence and deterministic pipelines, not as a replacement for them.

Validation

AwareOn includes automated validation and a documented end-to-end QA process.

Level 20 End-to-End QA

python scripts/level20_e2e.py

The documented smoke suite covers:

health
risk
regional
scenario
ood

The previously recorded smoke-suite result was:

health       | PASS
risk         | PASS
regional     | PASS
scenario     | PASS
ood          | PASS

RESULT: 5/5

Run the suite locally again when making a new release or deployment.

AI Agent Benchmark

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

These are documented project validation results and should be treated as historical validation records until the benchmarks are rerun.

Model Honesty

AwareOn is intentionally designed not to represent unsupported simulations or fabricated observations as real-world facts.

The platform follows several rules:

Supported rainfall scenario states are explicitly bounded

Simulated outputs remain identified as simulated

AI inference is not automatically treated as observed truth

Evidence and verification remain part of the intelligence workflow

Confidence and uncertainty are surfaced separately from risk

Out-of-domain questions can be rejected

Missing or insufficient evidence should produce limitations rather than invented answers

Learning or improvement must remain evidence-linked, validated, auditable, and reversible

The canonical evidence layer remains authoritative over generated AI reasoning.

Product Experience

AwareOn is designed as a focused spatial intelligence workspace rather than a conventional dashboard.

Command Center

The map provides the primary operational context for:

Current regional situation

Risk distribution

Incidents

Spatial focus

Contextual investigation

Risk Explorer

Users can move from regional patterns into exact-cell investigation without losing spatial context.

Incident Command

Incidents can become spatial investigation anchors, allowing operational analysis to remain connected to the map.

Scenario Lab

Scenario investigation exposes supported rainfall counterfactuals and their modeled spatial effects.

AO Intel

The intelligence workspace provides:

Natural-language investigation

Evidence-backed explanations

Confidence context

Findings and limitations

Relevant tools and verification information

AI reasoning grounded in AwareOn intelligence

The interface uses progressive disclosure so deeper intelligence appears when it is needed rather than keeping every technical detail visible at once.

Example Queries

Regional intelligence

Which areas currently deserve the most attention?

Operational prioritization

Which areas should a field team review first?

Scenario analysis

What happens if rainfall increases by 50%?

Cell investigation

Why is cell 506_422 high risk?

Historical intelligence

Which historical landslides are relevant to this region?

Temporal intelligence

What is the historical trajectory of this area?

Evidence investigation

What evidence supports this risk assessment?

Limitation-aware explanation

How confident is this finding and what are its limitations?

Current Study Context

AwareOn is designed around a Sikkim / Himalayan landslide intelligence study context, where terrain, rainfall, environmental conditions, historical activity, infrastructure exposure, and spatial risk interact.

The current product is designed to support investigation across:

Spatial risk

Environmental conditions

Historical activity

Temporal changes

Rainfall scenarios

Exposure

Incidents

Evidence

Confidence

Operational decisions

The system is a decision-support platform, not a replacement for official emergency management, field inspection, or government warning systems.

Design Principles

AwareOn follows several core principles:

Map-first intelligence
Spatial context remains central to investigation and decision making.

Evidence before assertion
Answers should be grounded in supported evidence.

Deterministic where possible
Critical intelligence paths use validated deterministic pipelines wherever practical.

Natural language access
Users should be able to investigate AwareOn without learning internal system terminology.

Model honesty
Simulated information is explicitly treated as simulated.

Confidence-aware intelligence
Uncertainty and confidence are distinct from the risk result itself.

Progressive disclosure
The interface should expose deeper detail when it becomes useful.

Spatial continuity
Moving from regional analysis to a cell, incident, or investigation should preserve geographic context.

Operational usefulness
The objective is not only to describe risk, but to help determine what deserves attention next.

Human oversight
Critical interpretation and operational decisions remain with the responsible human teams and authorities.

Product Status

AwareOn — Final Product Build

The current build includes:

Map-first spatial risk intelligence

Cell and regional investigation

Incident investigation

Supported rainfall Scenario Lab

Evidence and verification workflows

Confidence and uncertainty context

Historical and temporal intelligence

Exposure and decision support

Conversational AI intelligence

AI ↔ map integration

Progressive disclosure

Responsive product UX

Performance and reliability improvements

API validation and error handling

Repository security and hygiene

Product documentation

End-to-end QA definition and validation tooling

The immediate final validation checkpoint is Level 20 E2E QA, followed by any future roadmap work that is explicitly defined and validated rather than assumed from the roadmap numbering.

Disclaimer

AwareOn is a research and decision-support platform.

Risk scores, scenario outputs, historical interpretations, exposure analyses, confidence estimates, and AI-generated responses should be interpreted within the system's available data, model assumptions, evidence quality, and stated limitations.

AwareOn should not be treated as an independent source of emergency warnings or as a substitute for official authorities, field teams, or on-ground verification.

Author

Priyesh Raj
