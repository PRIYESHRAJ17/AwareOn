# AwareOn Intelligence Build — Levels 2–15

Generated: 2026-09-18T03:52:43.426652+00:00

## Scope

Coordinated implementation of the remaining Level 2/3 hardening plus Levels 5–15. Level 4 is a frozen regression dependency because its final trust validation already passed.

## Truth boundaries

The Intelligence layer does not promote modeled counterfactuals to observations, does not automatically change engine formulas/thresholds/policy, and does not invent exact infrastructure dependencies where the underlying data only provide exposure proxies.

## Validation snapshot

```json
{
  "backups": [
    {
      "backup": "artifacts\\intelligence_upgrade_2_15\\backup\\20260918_092224\\backend\\app\\ai\\response_contract.py",
      "original": "backend\\app\\ai\\response_contract.py"
    },
    {
      "backup": "artifacts\\intelligence_upgrade_2_15\\backup\\20260918_092224\\backend\\app\\ai\\model_adapter.py",
      "original": "backend\\app\\ai\\model_adapter.py"
    },
    {
      "backup": "artifacts\\intelligence_upgrade_2_15\\backup\\20260918_092224\\backend\\app\\main.py",
      "original": "backend\\app\\main.py"
    },
    {
      "backup": "artifacts\\intelligence_upgrade_2_15\\backup\\20260918_092224\\backend\\app\\services\\gis_service.py",
      "original": "backend\\app\\services\\gis_service.py"
    },
    {
      "backup": "artifacts\\intelligence_upgrade_2_15\\backup\\20260918_092224\\.gitignore",
      "original": ".gitignore"
    }
  ],
  "changed_files": [
    "backend/app/intelligence/__init__.py",
    "backend/app/intelligence/alert_lifecycle.py",
    "backend/app/intelligence/api.py",
    "backend/app/intelligence/cascade_intelligence.py",
    "backend/app/intelligence/contracts.py",
    "backend/app/intelligence/field_feedback.py",
    "backend/app/intelligence/knowledge_manager.py",
    "backend/app/intelligence/provenance.py",
    "backend/app/intelligence/red_team.py",
    "backend/app/intelligence/reliability.py",
    "backend/app/intelligence/scenario_resilience.py",
    "backend/app/intelligence/validation.py",
    "backend\\app\\ai\\model_adapter.py",
    "backend\\app\\ai\\response_contract.py",
    "backend\\app\\main.py",
    "backend\\app\\services\\gis_service.py"
  ],
  "compile": {
    "command": [
      "C:\\Users\\Priyesh Raj\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\\python.exe",
      "-m",
      "compileall",
      "-q",
      "backend",
      "scripts"
    ],
    "completed_at": "2026-09-18T03:52:25.217768+00:00",
    "returncode": 0,
    "started_at": "2026-09-18T03:52:24.459396+00:00",
    "status": "PASS",
    "stderr": "",
    "stdout": ""
  },
  "completed_at": "2026-09-18T03:52:43.424585+00:00",
  "overall_status": "DEGRADED_RASTER_VERIFICATION",
  "preflight": {
    "max_confidence_uncertainty_error": 1.4210854715202004e-14,
    "protected_names": [
      "AwareOn_source_snapshot_20260918.tar.gz",
      "master_grid_100m.geojson.tar.gz"
    ],
    "state_rows": 1298,
    "status": "PASS"
  },
  "project": "AwareOn",
  "protected": [
    "AwareOn_source_snapshot_20260918.tar.gz",
    "master_grid_100m.geojson.tar.gz"
  ],
  "regressions": [
    {
      "command": [
        "C:\\Users\\Priyesh Raj\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\\python.exe",
        "-m",
        "py_compile",
        "backend/app/main.py"
      ],
      "completed_at": "2026-09-18T03:52:25.387854+00:00",
      "returncode": 0,
      "started_at": "2026-09-18T03:52:25.217815+00:00",
      "status": "PASS",
      "stderr": "",
      "stdout": ""
    },
    {
      "command": [
        "C:\\Users\\Priyesh Raj\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\\python.exe",
        "-c",
        "import runpy; runpy.run_path('scripts/confidence_integrity_test.py', run_name='__main__')"
      ],
      "completed_at": "2026-09-18T03:52:28.254358+00:00",
      "returncode": 0,
      "started_at": "2026-09-18T03:52:25.387863+00:00",
      "status": "PASS",
      "stderr": "",
      "stdout": "CONFIDENCE INTEGRITY: PASS\n"
    },
    {
      "command": [
        "C:\\Users\\Priyesh Raj\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\\python.exe",
        "scripts/validate_intelligence_state.py"
      ],
      "completed_at": "2026-09-18T03:52:29.039457+00:00",
      "returncode": 1,
      "started_at": "2026-09-18T03:52:28.254374+00:00",
      "status": "FAIL",
      "stderr": "Traceback (most recent call last):\n  File \"C:\\Users\\Priyesh Raj\\Documents\\AwareOn\\scripts\\validate_intelligence_state.py\", line 216, in <module>\n    print(\"\\nSTEP 21.2 COMPLETE \\u2705\")\n    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Program Files\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_3.13.3824.0_x64__qbz5n2kfra8p0\\Lib\\encodings\\cp1252.py\", line 19, in encode\n    return codecs.charmap_encode(input,self.errors,encoding_table)[0]\n           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nUnicodeEncodeError: 'charmap' codec can't encode character '\\u2705' in position 21: character maps to <undefined>\n",
      "stdout": "\n========================================\nSTEP 21.2 INTELLIGENCE STATE QA\n========================================\n\nEngine consistency:\n        engine status  rows  missing_from_state  extra_cells\nsusceptibility     OK  1298                   0            0\n       terrain     OK  1298                   0            0\n      exposure     OK  1298                   0            0\n       spatial     OK  1298                   0            0\n    confidence     OK  1298                   0            0\n   explanation     OK  1298                   0            0\n\nState rows: 1298\nUnique cell IDs: 1298\nMissing state values: 0\nAll state values present: YES\n\nUnified risk range: 8.622 to 84.458\n\nConfidence range: 47.156 to 91.281\n\nValidation output:\nC:\\Users\\Priyesh Raj\\Documents\\AwareOn\\data\\processed\\intelligence\\intelligence_state_validation.csv\n"
    },
    {
      "command": [
        "C:\\Users\\Priyesh Raj\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\\python.exe",
        "scripts/data_quality_audit.py"
      ],
      "completed_at": "2026-09-18T03:52:38.682508+00:00",
      "returncode": 0,
      "started_at": "2026-09-18T03:52:29.039474+00:00",
      "status": "PASS",
      "stderr": "",
      "stdout": "========================================================================\nAWAREON DATA QUALITY AUDIT\n========================================================================\nOverall: PASS\n\nPASS           CSV     gsi_clean\nPASS           CSV     static_features\nPASS           CSV     static_features_validated\nPASS           CSV     ground_truth_train\nPASS           CSV     ground_truth_validation\nPASS           CSV     ground_truth_test\nPASS           CSV     positive_cells\nPASS           CSV     negative_cells\nPASS           CSV     era5_environment\nPASS           CSV     current_risk\nPASS           CSV     intelligence_state\nUNVERIFIED     RASTER  dem_clipped\nUNVERIFIED     RASTER  dem_utm45\nUNVERIFIED     RASTER  slope\nUNVERIFIED     RASTER  aspect\n\nJSON : C:\\Users\\Priyesh Raj\\Documents\\AwareOn\\artifacts\\data_foundation_audit\\data_quality_results.json\nREPORT: C:\\Users\\Priyesh Raj\\Documents\\AwareOn\\artifacts\\data_foundation_audit\\DATA_QUALITY_REPORT.md\n========================================================================\n"
    },
    {
      "command": [
        "C:\\Users\\Priyesh Raj\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\\python.exe",
        "scripts/final_intelligence_audit.py"
      ],
      "completed_at": "2026-09-18T03:52:39.314260+00:00",
      "returncode": 1,
      "started_at": "2026-09-18T03:52:38.682527+00:00",
      "status": "FAIL",
      "stderr": "Traceback (most recent call last):\n  File \"C:\\Users\\Priyesh Raj\\Documents\\AwareOn\\scripts\\final_intelligence_audit.py\", line 376, in <module>\n    print(\"AUDIT PASSED \\u2705\")\n    ~~~~~^^^^^^^^^^^^^^^^^^^\n  File \"C:\\Program Files\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_3.13.3824.0_x64__qbz5n2kfra8p0\\Lib\\encodings\\cp1252.py\", line 19, in encode\n    return codecs.charmap_encode(input,self.errors,encoding_table)[0]\n           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nUnicodeEncodeError: 'charmap' codec can't encode character '\\u2705' in position 13: character maps to <undefined>\n",
      "stdout": "\n========================================\nSTEP 29\nAWAREON INTELLIGENCE FINAL AUDIT\n========================================\nengine_01_susceptibility     OK\nengine_02_rainfall           OK\nengine_03_soil               OK\nengine_04_terrain            OK\nengine_05_sar                OK\nengine_06_history            OK\nengine_07_anomaly            OK\nengine_08_exposure           OK\nengine_09_spatial            OK\nengine_10_temporal           OK\nengine_11_confidence         OK\nengine_12_explanation        OK\nintelligence_state           OK\nstate_validation             OK\nrisk_decisions               OK\nalerts                       OK\nincidents                    OK\nprioritized_incidents        OK\nhistorical_current           OK\nscenario_analysis            OK\n\nIntegrity checks:\nintelligence_state_rows          PASS\nrisk_decision_rows               PASS\nalert_rows                       PASS\nscenario_rows                    PASS\nhistorical_current_rows          PASS\nincident_rows                    PASS\npriority_rows                    PASS\nunique_state_cells               PASS\nunique_decision_cells            PASS\nunique_alert_cells               PASS\nstate_no_missing                 PASS\ndecisions_no_missing             PASS\nalerts_no_missing                PASS\nscenario_no_missing              PASS\nsusceptibility_0_1               PASS\nrisk_score_0_100                 PASS\nconfidence_0_100                 PASS\nscenario_risk_0_100              PASS\nall_four_scenarios               PASS\nunique_priority_ranks            PASS\n\n========================================\n"
    },
    {
      "command": [
        "C:\\Users\\Priyesh Raj\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\\python.exe",
        "-c",
        "from backend.app.main import app; print('API_IMPORT_OK', len(app.routes))"
      ],
      "completed_at": "2026-09-18T03:52:40.426798+00:00",
      "returncode": 0,
      "started_at": "2026-09-18T03:52:39.314268+00:00",
      "status": "PASS",
      "stderr": "",
      "stdout": "API_IMPORT_OK 27\n"
    }
  ],
  "scope": "Level 2 partial + Level 3 partial + Level 5-15",
  "script": "AwareOn_INTELLIGENCE_Upgrade_2_15.py",
  "started_at": "2026-09-18T03:52:23.717361+00:00",
  "validation": {
    "level_10_field": {
      "human_observation_ledger": true,
      "status": "PASS"
    },
    "level_11_learning": {
      "evidence_linked": true,
      "policy_mutation_forbidden": true,
      "status": "PASS"
    },
    "level_12_reliability": {
      "status": "PASS"
    },
    "level_13_integration": {
      "api_router": true,
      "status": "PASS"
    },
    "level_14_red_team": {
      "failed": 1,
      "passed": 3,
      "status": "FAIL",
      "tests": [
        {
          "details": "invalid transition rejected",
          "name": "invalid_alert_transition",
          "status": "PASS"
        },
        {
          "details": "[WinError 32] The process cannot access the file because it is being used by another process: 'C:\\\\Users\\\\PRIYES~1\\\\AppData\\\\Local\\\\Temp\\\\awareon_rt_euucb8da\\\\red_team.db'",
          "name": "evidence_collision",
          "status": "FAIL"
        },
        {
          "details": "policy mutation rejected",
          "name": "learning_policy_mutation",
          "status": "PASS"
        },
        {
          "details": "out-of-domain refusal passed",
          "name": "out_of_domain_guardrail",
          "status": "PASS"
        }
      ],
      "total": 4
    },
    "level_15_full_validation": {
      "status": "PENDING_COMPLETION_GATE"
    },
    "level_2_raster": {
      "checks": [
        {
          "file": "sikkim_dem_clipped.tif",
          "reason": "Rasterio unavailable and gdalinfo not found. Target-machine raster verification is still required.",
          "status": "UNVERIFIED"
        },
        {
          "file": "sikkim_dem_utm45.tif",
          "reason": "Rasterio unavailable and gdalinfo not found. Target-machine r
```

## Git

No automatic Git commit is created. Review the report and diff before committing.
