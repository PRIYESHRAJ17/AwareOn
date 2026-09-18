# AwareOn Baseline Audit

Generated: 2026-09-16 19:06:20

## Locked AI

Primary:
`ollama / qwen3.5:9b`

Backup:
`ollama / nemotron-3-nano:4b-q8_0`

## Component inventory

Source files:
`187`

Python components:
`160`

## Feature audit

Expected:
`177`

Actual:
`0`

Status:
`SCOPE_UNAVAILABLE`

Duplicate IDs:
`[]`

Missing IDs:
`[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177]`

## Placeholder / fake / proxy audit

Total findings:
`109`

Critical:
`0`

High:
`0`

## Architecture overlap audit

High-similarity pairs:
`0`

## Data lineage

Required stages:
`SOURCE -> RAW -> CLEAN -> FEATURES -> ENGINE -> DERIVED_INTELLIGENCE -> AI_EVIDENCE -> DECISION`

## Performance

Base URL:
`http://127.0.0.1:8000`

## Intelligence specification

Status:
`PASS`

Primary AI valid:
`True`

Backup AI valid:
`True`

## Qwen primary lock

Status:
`PASS`

Stale primary labels:
`0`

## Important

This document is an audit result.

It must not be interpreted as proof that every future capability
already exists.

A feature only becomes complete after implementation, integration,
positive testing, adversarial testing, failure testing, improvement,
retesting and validation.
