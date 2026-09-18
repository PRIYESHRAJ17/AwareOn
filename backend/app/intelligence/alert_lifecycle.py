from __future__ import annotations

import hashlib
from typing import Any

from .contracts import AlertDecision, ALERT_STATES, clamp, utc_now, validate_alert_state
from .provenance import provenance_store


ORDER = {
    "NORMAL": 0,
    "WATCH": 1,
    "ADVISORY": 2,
    "WARNING": 3,
    "CRITICAL": 4,
}

TRANSITIONS = {
    "NORMAL": {"NORMAL", "WATCH", "RESOLVED", "EXPIRED"},
    "WATCH": {"WATCH", "ADVISORY", "NORMAL", "RESOLVED", "EXPIRED"},
    "ADVISORY": {"ADVISORY", "WARNING", "WATCH", "RESOLVED", "EXPIRED"},
    "WARNING": {"WARNING", "CRITICAL", "ADVISORY", "RESOLVED", "EXPIRED"},
    "CRITICAL": {"CRITICAL", "WARNING", "RESOLVED", "EXPIRED"},
    "RESOLVED": {"RESOLVED", "WATCH", "ADVISORY"},
    "EXPIRED": {"EXPIRED", "WATCH", "ADVISORY"},
}


class AlertTransitionError(ValueError):
    pass


def derive_operational_state(
    risk_score: float,
    confidence_score: float,
    dynamic_signal: float,
    current_state: str = "NORMAL",
    persistence_count: int = 1,
) -> AlertDecision:
    """Derive a reversible operational posture with hysteresis.

    This is an AwareOn operational state, not an official government warning.
    Thresholds are deliberately kept separate from deterministic hazard-engine formulas.
    """
    risk = clamp(risk_score)
    confidence = clamp(confidence_score)
    dynamic = clamp(dynamic_signal)
    current = current_state if current_state in ORDER else "NORMAL"
    persistence = max(1, int(persistence_count))

    # Upward activation thresholds are intentionally harder to clear than routine states.
    target = "NORMAL"
    if risk >= 85 and confidence >= 60:
        target = "CRITICAL"
    elif risk >= 70 and confidence >= 55:
        target = "WARNING"
    elif risk >= 55 and confidence >= 50:
        target = "ADVISORY"
    elif risk >= 40:
        target = "WATCH"

    if dynamic >= 75 and risk >= 65 and confidence >= 55:
        if ORDER[target] < ORDER["WARNING"]:
            target = "WARNING"
        if dynamic >= 90 and risk >= 80 and confidence >= 70:
            target = "CRITICAL"

    # Hysteresis prevents alert flapping around boundaries.
    down_thresholds = {
        "CRITICAL": 80.0,
        "WARNING": 65.0,
        "ADVISORY": 50.0,
        "WATCH": 35.0,
    }
    if current in down_thresholds and risk < down_thresholds[current] and dynamic < 55:
        target = min(target, current, key=lambda x: ORDER.get(x, 0))

    if persistence < 2 and ORDER.get(target, 0) >= ORDER["WARNING"]:
        target = "ADVISORY" if target == "WARNING" else "WARNING"
        if target == "WARNING" and risk < 85:
            target = "ADVISORY"

    reason_parts = [f"risk={risk:.2f}", f"confidence={confidence:.2f}", f"dynamic={dynamic:.2f}"]
    if current != target:
        reason_parts.append(f"transition={current}->{target}")
    else:
        reason_parts.append("state_persisted")

    return AlertDecision(
        cell_id="",
        state=target,
        risk_score=risk,
        confidence_score=confidence,
        uncertainty_score=100.0 - confidence,
        dynamic_signal=dynamic,
        reason="; ".join(reason_parts),
        generated_at=utc_now(),
    )


class AlertLedger:
    """Persistent alert state/event ledger with explicit transitions."""

    def __init__(self, store=provenance_store) -> None:
        self.store = store

    def current_state(self, cell_id: str) -> str:
        events = self.store.list_alert_events(cell_id, limit=1)
        return events[0]["to_state"] if events else "NORMAL"

    def transition(
        self,
        cell_id: str,
        target_state: str,
        *,
        actor: str,
        reason: str,
        evidence_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        validate_alert_state(target_state)
        current = self.current_state(cell_id)
        allowed = TRANSITIONS[current]
        if target_state not in allowed:
            raise AlertTransitionError(
                f"Invalid alert transition {current}->{target_state} for {cell_id}."
            )

        event_id = "ALT-" + hashlib.sha256(
            f"{cell_id}|{current}|{target_state}|{actor}|{reason}".encode("utf-8")
        ).hexdigest()[:20].upper()
        evidence = sorted(set(evidence_ids or []))
        self.store.record_alert_event(
            event_id,
            cell_id,
            current,
            target_state,
            actor,
            reason,
            evidence,
        )
        return {
            "event_id": event_id,
            "cell_id": cell_id,
            "from_state": current,
            "to_state": target_state,
            "actor": actor,
            "reason": reason,
            "evidence_ids": evidence,
            "created_at": utc_now(),
        }


alert_ledger = AlertLedger()
