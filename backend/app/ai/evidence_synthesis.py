from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from backend.app.ai.model_adapter import AwareOnModelAdapter


@dataclass
class VerifiedClaim:
    claim: str
    evidence_ids: list[str]
    claim_type: str
    status: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "evidence_ids": self.evidence_ids,
            "claim_type": self.claim_type,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass
class EvidenceSynthesisResult:
    status: str
    answer: str
    claims: list[VerifiedClaim]
    rejected_claims: list[VerifiedClaim]
    correction_rounds: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "answer": self.answer,
            "claims": [x.to_dict() for x in self.claims],
            "rejected_claims": [
                x.to_dict() for x in self.rejected_claims
            ],
            "correction_rounds": self.correction_rounds,
        }


def _extract_numbers(text: str) -> list[float]:
    values: list[float] = []

    if not isinstance(text, str):
        return values

    # Extract standalone numeric values only.
    # Do not treat digits that are part of identifiers such as
    # 506_422, E12, CELL-506_422, etc. as numeric claims.
    pattern = re.compile(
        r"(?<![A-Za-z0-9_])"
        r"[-+]?"
        r"(?:"
        r"\d+(?:\.\d+)?"
        r"|"
        r"\.\d+"
        r")"
        r"(?![A-Za-z0-9_])"
    )

    for token in pattern.findall(text):
        try:
            values.append(float(token))
        except ValueError:
            continue

    return values

def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def build_model_evidence(
    evidence_package: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:

    items = evidence_package.get("items", [])

    if not isinstance(items, list):
        return [], {}

    model_items = []
    reference_map = {}

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue

        ref = f"E{index:02d}"

        model_items.append(
            {
                "ref": ref,
                "claim": str(item.get("claim", "")),
                "value": item.get("value"),
                "type": str(item.get("evidence_type", "")),
            }
        )

        reference_map[ref] = item

    return model_items, reference_map


def _extract_json_object(text: str) -> dict[str, Any]:

    text = text.strip()

    if not text:
        raise ValueError("Model returned empty content.")

    try:
        value = json.loads(text)

        if isinstance(value, dict):
            return value

    except json.JSONDecodeError:
        pass

    fenced = re.findall(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        text,
        flags=re.DOTALL,
    )

    for candidate in fenced:
        try:
            value = json.loads(candidate)

            if isinstance(value, dict):
                return value

        except json.JSONDecodeError:
            continue

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:

        candidate = text[start : end + 1]

        try:
            value = json.loads(candidate)

            if isinstance(value, dict):
                return value

        except json.JSONDecodeError:
            pass

    raise ValueError("Model response did not contain valid JSON.")


def _canonical_categories(
    item: dict[str, Any],
) -> set[str]:

    categories = {
        "LOW",
        "MODERATE",
        "HIGH",
        "VERY_HIGH",
        "EXTREME",
        "NORMAL",
        "CRITICAL",
        "STABLE",
        "INCREASING",
        "DECREASING",
        "VERY_STRONG",
        "STRONG",
        "P1",
        "P2",
        "P3",
        "P4",
    }

    found = set()

    claim = str(item.get("claim", ""))
    value = item.get("value")

    text = claim + " " + str(value)

    upper = text.upper()

    for category in categories:
        if re.search(
            r"\b" + re.escape(category) + r"\b",
            upper,
        ):
            found.add(category)

    return found


def _claimed_categories(text: str) -> set[str]:

    categories = {
        "LOW",
        "MODERATE",
        "HIGH",
        "VERY_HIGH",
        "EXTREME",
        "NORMAL",
        "CRITICAL",
        "STABLE",
        "INCREASING",
        "DECREASING",
        "VERY_STRONG",
        "STRONG",
        "P1",
        "P2",
        "P3",
        "P4",
    }

    upper = text.upper()

    return {
        category
        for category in categories
        if re.search(
            r"\b" + re.escape(category) + r"\b",
            upper,
        )
    }


def verify_claim(
    claim_text: str,
    evidence_refs: list[str],
    reference_map: dict[str, dict[str, Any]],
) -> VerifiedClaim:

    text = claim_text.strip()

    if not text:
        return VerifiedClaim(
            text,
            [],
            "",
            "REJECTED",
            "Claim is empty.",
        )

    if not evidence_refs:
        return VerifiedClaim(
            text,
            [],
            "",
            "REJECTED",
            "Claim cites no evidence.",
        )

    missing = [
        ref for ref in evidence_refs
        if ref not in reference_map
    ]

    if missing:
        return VerifiedClaim(
            text,
            [],
            "",
            "REJECTED",
            "Unknown evidence references: "
            + ", ".join(missing),
        )

    cited = [
        reference_map[ref]
        for ref in evidence_refs
    ]

    evidence_text = _normalize(
        " ".join(
            str(item.get("claim", ""))
            + " "
            + str(item.get("value", ""))
            for item in cited
        )
    )

    claim_numbers = _extract_numbers(text)

    # Compare claimed numbers against canonical evidence values
    # first. This avoids accidentally treating cell IDs, evidence
    # IDs, or other identifiers as numerical evidence.
    evidence_numbers: list[float] = []

    for item in cited:
        value = item.get("value")

        if isinstance(value, bool):
            continue

        if isinstance(value, (int, float)):
            evidence_numbers.append(float(value))
            continue

        if isinstance(value, dict):
            for nested_value in value.values():
                if isinstance(nested_value, bool):
                    continue

                if isinstance(nested_value, (int, float)):
                    evidence_numbers.append(
                        float(nested_value)
                    )

    # Also allow numeric values explicitly stated in the
    # canonical evidence claim text.
    for item in cited:
        canonical_claim = str(
            item.get("claim", "")
        )

        for number in _extract_numbers(
            canonical_claim
        ):
            if number not in evidence_numbers:
                evidence_numbers.append(
                    number
                )

    for number in claim_numbers:
        matched = any(
            abs(number - other)
            <= max(
                0.01,
                abs(other) * 0.005,
            )
            for other in evidence_numbers
        )

        if not matched:
            return VerifiedClaim(
                text,
                [
                    str(item.get("evidence_id", ""))
                    for item in cited
                ],
                "",
                "REJECTED",
                f"Unsupported numeric value {number}.",
            )

    claimed_categories = _claimed_categories(text)

    if claimed_categories:

        for item in cited:

            canonical = _canonical_categories(item)

            if not canonical:
                continue

            conflicts = {
                category
                for category in claimed_categories
                if category not in canonical
            }

            if conflicts:

                return VerifiedClaim(
                    text,
                    [
                        str(item.get("evidence_id", ""))
                        for item in cited
                    ],
                    "",
                    "REJECTED",
                    "Claimed category "
                    + ", ".join(sorted(conflicts))
                    + " conflicts with canonical evidence "
                    + ", ".join(sorted(canonical))
                    + ".",
                )

    evidence_types = {
        str(
            item.get(
                "evidence_type",
                "",
            )
        ).upper()
        for item in cited
    }

    normalized = _normalize(text)

    if (
        "SIMULATED" in evidence_types
        and (
            "proves" in normalized
            or "will happen" in normalized
            or "will occur" in normalized
        )
    ):

        return VerifiedClaim(
            text,
            [
                str(item.get("evidence_id", ""))
                for item in cited
            ],
            "SIMULATED",
            "REJECTED",
            "Simulated evidence cannot prove a future observed event.",
        )

    claim_type = (
        next(iter(evidence_types))
        if len(evidence_types) == 1
        else "MIXED"
    )

    return VerifiedClaim(
        text,
        [
            str(item.get("evidence_id", ""))
            for item in cited
        ],
        claim_type,
        "VERIFIED",
        "Claim is supported by canonical evidence.",
    )


def verify_model_claims(
    structured: dict[str, Any],
    reference_map: dict[str, dict[str, Any]],
) -> tuple[list[VerifiedClaim], list[VerifiedClaim]]:

    raw_claims = structured.get("claims", [])

    if not isinstance(raw_claims, list):
        return [], [
            VerifiedClaim(
                "",
                [],
                "",
                "REJECTED",
                "Model claims field is invalid.",
            )
        ]

    verified = []
    rejected = []

    for raw in raw_claims:

        if not isinstance(raw, dict):
            rejected.append(
                VerifiedClaim(
                    "",
                    [],
                    "",
                    "REJECTED",
                    "Claim is not an object.",
                )
            )
            continue

        claim = str(
            raw.get("claim", "")
        )

        refs = raw.get(
            "evidence_refs",
            [],
        )

        if not isinstance(refs, list):
            refs = []

        result = verify_claim(
            claim,
            [str(x) for x in refs],
            reference_map,
        )

        if result.status == "VERIFIED":
            verified.append(result)
        else:
            rejected.append(result)

    return verified, rejected


def assemble_verified_answer(
    claims: list[VerifiedClaim],
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

    return "\n".join(lines)


def _build_prompt(
    user_query: str,
    evidence_text: str,
    rejected: list[VerifiedClaim],
) -> str:

    prompt = (
        "Select 4 to 8 concrete AwareOn claims that "
        "directly answer the user's question.\n\n"
        "Return ONLY JSON in this exact shape:\n"
        '{"claims":[{"claim":"...","evidence_refs":["E01"]}]}\n\n'
        "Rules:\n"
        "- Use only the supplied evidence.\n"
        "- Every claim needs one or more E## references.\n"
        "- Never change numbers.\n"
        "- Never change categories.\n"
        "- Prefer exact canonical numbers, categories, IDs, "
        "coordinates, and states when they are present in the "
        "supplied evidence value.\n"
        "- Do not replace a concrete value with a generic phrase "
        "such as 'has a risk score' when the actual score is supplied.\n"
        "- For cell explanations, include the concrete risk, "
        "severity, susceptibility, terrain, and spatial evidence "
        "when those fields are available.\n"
        "- For scenario questions, include the modeled risk and "
        "the modeled change when available.\n"
        "- For regional questions, include the relevant "
        "coordinates and regional risk value/state when available.\n"
        "- Do not describe yourself.\n"
        "- Do not add generic AI statements.\n"
        "- Simulated evidence remains simulated.\n"
        "- Focus on the evidence that most directly answers the "
        "question.\n\n"
        f"QUESTION:\n{user_query}\n\n"
        f"EVIDENCE:\n{evidence_text}\n"
    )

    if rejected:

        prompt += (
            "\n\nPREVIOUS OUTPUT WAS REJECTED:\n"
        )

        for item in rejected:
            prompt += (
                f"- {item.claim}\n"
                f"  Reason: {item.reason}\n"
            )

        prompt += (
            "\nCorrect the rejected claims and "
            "return only the JSON structure."
        )

    return prompt


def synthesize_with_verification(
    adapter: AwareOnModelAdapter,
    system_prompt: str,
    user_query: str,
    evidence_package: dict[str, Any],
    *,
    max_correction_rounds: int = 2,
) -> EvidenceSynthesisResult:

    model_evidence, reference_map = build_model_evidence(
        evidence_package
    )

    evidence_text = "\n".join(
        (
            f"{item['ref']} | "
            f"type={item['type']} | "
            f"claim={item['claim']} | "
            f"value={item['value']}"
        )
        for item in model_evidence
    )

    rejected_history: list[VerifiedClaim] = []

    for round_number in range(
        max_correction_rounds + 1
    ):

        prompt = _build_prompt(
            user_query,
            evidence_text,
            rejected_history,
        )

        raw = adapter.generate(
            system_prompt,
            prompt,
            temperature=0.0,
            max_tokens=512,
            think=False,
        )

        try:
            structured = _extract_json_object(
                raw
            )

        except ValueError as exc:

            rejected_history.append(
                VerifiedClaim(
                    "",
                    [],
                    "",
                    "REJECTED",
                    str(exc),
                )
            )

            continue

        verified, rejected = verify_model_claims(
            structured,
            reference_map,
        )

        if verified and not rejected:

            return EvidenceSynthesisResult(
                status="VERIFIED",
                answer=assemble_verified_answer(
                    verified
                ),
                claims=verified,
                rejected_claims=[],
                correction_rounds=round_number,
            )

        if rejected:

            rejected_history.extend(
                rejected
            )

        else:

            rejected_history.append(
                VerifiedClaim(
                    "",
                    [],
                    "",
                    "REJECTED",
                    "No usable claims returned.",
                )
            )

    return EvidenceSynthesisResult(
        status="REVIEW_REQUIRED",
        answer="",
        claims=[],
        rejected_claims=rejected_history,
        correction_rounds=max_correction_rounds,
    )
