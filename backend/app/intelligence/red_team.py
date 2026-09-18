from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .alert_lifecycle import AlertLedger, AlertTransitionError
from .contracts import EvidenceRecord, utc_now
from .knowledge_manager import propose_lesson, validate_lesson


def _check(name: str, fn: Callable[[], Any]) -> dict[str, Any]:
    try:
        result = fn()
        return {"name": name, "status": "PASS", "details": result}
    except Exception as exc:
        return {"name": name, "status": "FAIL", "details": str(exc)}


def run_red_team(root: Path) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    def invalid_transition():
        ledger = AlertLedger()
        cell_id = "RT_INVALID_1"
        # NORMAL -> CRITICAL is deliberately forbidden: high-severity alerts
        # require the explicit transition lifecycle.
        try:
            ledger.transition(cell_id, "CRITICAL", actor="RED_TEAM", reason="invalid jump")
        except AlertTransitionError:
            return "invalid transition rejected"
        raise AssertionError("invalid transition was accepted")

    def evidence_collision():
        from .provenance import ProvenanceStore
        import tempfile
        with tempfile.TemporaryDirectory(prefix="awareon_rt_") as tmp:
            store = ProvenanceStore(str(Path(tmp) / "red_team.db"))
            first = EvidenceRecord(
                evidence_id="RT-EVIDENCE-1",
                evidence_type="CURRENT",
                source="RED_TEAM",
                source_id="x",
                source_timestamp=None,
                ingestion_timestamp=utc_now(),
                freshness_seconds=None,
                geographic_scope="Sikkim",
                dataset_version="rt",
                provenance={"test": True},
                quality=90.0,
                conflict_state="NONE",
                claim="first",
                value=1,
            )
            store.register_evidence(first)
            second = EvidenceRecord(**{**first.to_dict(), "claim": "tampered"})
            try:
                store.register_evidence(second)
            except ValueError:
                return "evidence collision rejected"
            raise AssertionError("evidence collision was accepted")

    def prohibited_learning_mutation():
        candidate = propose_lesson(
            "change threshold based on this single event",
            ["E1", "E2", "E3"],
            0.95,
        )
        try:
            validate_lesson(candidate)
        except ValueError:
            return "policy mutation rejected"
        raise AssertionError("policy mutation learning was accepted")

    def unsupported_claim_safety():
        import importlib.util
        response_path = root / "backend" / "app" / "ai" / "response_contract.py"
        spec = importlib.util.spec_from_file_location("awareon_response_contract_rt", response_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Could not load response contract for red-team test")
        import sys
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        response = module.build_out_of_domain_response("Explain stock options", confidence=0.0)
        response.validate()
        assert response.domain == "OUTSIDE_DOMAIN"
        return "out-of-domain refusal passed"

    results.extend(
        [
            _check("invalid_alert_transition", invalid_transition),
            _check("evidence_collision", evidence_collision),
            _check("learning_policy_mutation", prohibited_learning_mutation),
            _check("out_of_domain_guardrail", unsupported_claim_safety),
        ]
    )

    failed = [item for item in results if item["status"] != "PASS"]
    return {
        "status": "PASS" if not failed else "FAIL",
        "total": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "tests": results,
    }
