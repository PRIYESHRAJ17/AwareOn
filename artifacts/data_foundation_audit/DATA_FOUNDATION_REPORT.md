# AwareOn Data Foundation Audit

Source files inspected: `262`

Status:
`DISCOVERY_ONLY`

## Classification counts

- `cleaning`: `40`
- `features`: `71`
- `ingestion`: `57`
- `provenance`: `74`
- `spatial`: `198`
- `temporal`: `169`
- `validation`: `66`

## Suspicious input candidates

- `backend/app/ai/adversarial_benchmark.py`
- `backend/app/ai/autonomous_master.py`
- `backend/app/ai/decision_orchestrator.py`
- `backend/app/ai/domain_knowledge.py`
- `backend/app/ai/domain_retrieval.py`
- `backend/app/ai/domain_router.py`
- `backend/app/ai/evidence_builder.py`
- `data/model_shootout_deep/deep_results.csv`
- `data/model_shootout_deep/deep_results.json`
- `data/model_shootout_deep/leaderboard.json`
- `data/processed/engines/confidence_uncertainty_engine_output.csv`
- `data/processed/grid/aspect.tif`
- `data/processed/grid/sikkim_dem_clipped.tif`
- `data/processed/grid/sikkim_dem_mosaic.tif`
- `data/processed/grid/sikkim_dem_utm45.tif`
- `data/processed/grid/slope.tif`
- `data/processed/landslides/gsi_inventory_extracted.csv`
- `docs/audit/beast_spec.yaml`
- `docs/audit/data_quality_contract.yaml`
- `scripts/baseline_audit.py`
- `scripts/build_feature_dataset.py`
- `scripts/confidence_uncertainty_engine.py`
- `scripts/data_foundation_audit.py`
- `scripts/model_shootout_deep.py`

## Important

Static discovery is candidate evidence only.
It does not prove that a dataset is authoritative, live,
correctly transformed, or safe for production use.
