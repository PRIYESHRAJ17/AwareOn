from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from backend.app.ai.evidence_synthesis import (
    build_model_evidence,
    verify_model_claims,
)
from backend.app.ai.model_adapter import (
    AwareOnModelAdapter,
)


# ============================================================
# RESULT
# ============================================================

@dataclass
class CorrectionResult:
    status: str
    initial_claims: list[Any]
    rejected_claims: list[Any]
    corrected_claims: list[Any]
    correction_rounds: int
    final_answer: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "initial_claims": [
                item.to_dict()
                for item in self.initial_claims
            ],
            "rejected_claims": [
                item.to_dict()
                for item in self.rejected_claims
            ],
            "corrected_claims": [
                item.to_dict()
                for item in self.corrected_claims
            ],
            "correction_rounds":
                self.correction_rounds,
            "final_answer":
                self.final_answer,
        }


# ============================================================
# JSON EXTRACTION
# ============================================================

def _extract_json(
    text: str,
) -> dict[str, Any]:

    text = text.strip()

    if not text:
        raise ValueError(
            "Model returned empty content."
        )

    try:
        value = json.loads(text)

        if isinstance(value, dict):
            return value

    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:

        candidate = text[
            start:end + 1
        ]

        try:
            value = json.loads(
                candidate
            )

            if isinstance(value, dict):
                return value

        except json.JSONDecodeError:
            pass

    raise ValueError(
        "Model response did not contain valid JSON."
    )


# ============================================================
# MODEL-FACING EVIDENCE
# ============================================================

def _evidence_text(
    evidence_package: dict[str, Any],
) -> tuple[
    str,
    dict[str, dict[str, Any]],
]:

    items, reference_map = build_model_evidence(
        evidence_package
    )

    lines = []

    for item in items:

        lines.append(
            (
                f"{item['ref']} | "
                f"type={item['type']} | "
                f"claim={item['claim']} | "
                f"value={item['value']}"
            )
        )

    return (
        "\n".join(lines),
        reference_map,
    )


# ============================================================
# ANSWER ASSEMBLY
# ============================================================

def _assemble_answer(
    claims: list[Any],
) -> str:

    if not claims:

        return (
            "AwareOn could not produce a verified "
            "evidence-backed answer."
        )

    lines = [
        "AwareOn verified findings:"
    ]

    for claim in claims:

        refs = ", ".join(
            claim.evidence_ids
        )

        lines.append(
            f"- {claim.claim} [{refs}]"
        )

    return "\n".join(
        lines
    )


# ============================================================
# CONTROLLED CORRECTION
# ============================================================

def run_controlled_correction(
    adapter: AwareOnModelAdapter,
    system_prompt: str,
    user_query: str,
    evidence_package: dict[str, Any],
    bad_claims: dict[str, Any],
    *,
    max_rounds: int = 2,
) -> CorrectionResult:

    evidence_text, reference_map = _evidence_text(
        evidence_package
    )

    initial_verified, rejected = verify_model_claims(
        bad_claims,
        reference_map,
    )

    if not rejected:

        return CorrectionResult(
            status="NO_CORRECTION_NEEDED",
            initial_claims=initial_verified,
            rejected_claims=[],
            corrected_claims=[],
            correction_rounds=0,
            final_answer=_assemble_answer(
                initial_verified
            ),
        )

    correction_history = list(
        rejected
    )

    for round_number in range(
        1,
        max_rounds + 1,
    ):

        rejected_text = "\n".join(
            (
                f"Rejected claim: {item.claim}\n"
                f"Reason: {item.reason}"
            )
            for item in correction_history
        )

        prompt = (
            "You are the AwareOn evidence correction engine.\n\n"
            "Correct ONLY the rejected claims below.\n"
            "Return ONLY JSON in exactly this shape:\n"
            '{"claims":[{"claim":"...","evidence_refs":["E08"]}]}\n\n'
            "Rules:\n"
            "- Use only supplied evidence.\n"
            "- Every claim must cite E## evidence refs.\n"
            "- Never alter numbers.\n"
            "- Never strengthen categories.\n"
            "- Do not create unrelated claims.\n"
            "- Do not describe yourself.\n"
            "- Preserve SIMULATED evidence as simulated.\n\n"
            f"QUESTION:\n{user_query}\n\n"
            f"EVIDENCE:\n{evidence_text}\n\n"
            f"REJECTED:\n{rejected_text}"
        )

        raw = adapter.generate(
            system_prompt,
            prompt,
            temperature=0.0,
            max_tokens=512,
            think=False,
        )

        try:
            structured = _extract_json(
                raw
            )

        except ValueError as exc:

            correction_history = [
                type(
                    "CorrectionIssue",
                    (),
                    {
                        "claim": "",
                        "evidence_ids": [],
                        "claim_type": "",
                        "status": "REJECTED",
                        "reason": str(exc),
                        "to_dict": lambda self: {
                            "claim": self.claim,
                            "evidence_ids":
                                self.evidence_ids,
                            "claim_type":
                                self.claim_type,
                            "status":
                                self.status,
                            "reason":
                                self.reason,
                        },
                    },
                )()
            ]

            continue

        verified, still_rejected = verify_model_claims(
            structured,
            reference_map,
        )

        if verified and not still_rejected:

            return CorrectionResult(
                status="CORRECTED",
                initial_claims=initial_verified,
                rejected_claims=rejected,
                corrected_claims=verified,
                correction_rounds=round_number,
                final_answer=_assemble_answer(
                    verified
                ),
            )

        if still_rejected:
            correction_history = still_rejected
        else:
            correction_history = [
                type(
                    "CorrectionIssue",
                    (),
                    {
                        "claim": "",
                        "evidence_ids": [],
                        "claim_type": "",
                        "status": "REJECTED",
                        "reason":
                            "No valid corrected claims returned.",
                        "to_dict": lambda self: {
                            "claim": self.claim,
                            "evidence_ids":
                                self.evidence_ids,
                            "claim_type":
                                self.claim_type,
                            "status":
                                self.status,
                            "reason":
                                self.reason,
                        },
                    },
                )()
            ]

    return CorrectionResult(
        status="REVIEW_REQUIRED",
        initial_claims=initial_verified,
        rejected_claims=rejected,
        corrected_claims=[],
        correction_rounds=max_rounds,
        final_answer="",
    )
