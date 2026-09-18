#!/usr/bin/env python3

from __future__ import annotations

import ast
import csv
import difflib
import hashlib
import json
import os
import platform
import re
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ============================================================
# LOCKED AWAREON AI
# ============================================================

PRIMARY_PROVIDER = "ollama"
PRIMARY_MODEL = "qwen3.5:9b"

BACKUP_PROVIDER = "ollama"
BACKUP_MODEL = "nemotron-3-nano:4b-q8_0"


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

AUDIT_DOCS = ROOT / "docs" / "audit"
OUTPUT_DIR = ROOT / "artifacts" / "baseline_audit"

FEATURE_SCOPE = AUDIT_DOCS / "feature_scope_177.yaml"
INTELLIGENCE_SPEC = AUDIT_DOCS / "intelligence_spec.yaml"
LINEAGE_SPEC = AUDIT_DOCS / "data_lineage.yaml"


# ============================================================
# IGNORE RULES
# ============================================================

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".html",
    ".css",
    ".toml",
    ".ini",
    ".env",
    ".txt",
}


# ============================================================
# KNOWN BAD PRIMARY LABELS
# ============================================================

STALE_PRIMARY_LABELS = [
    "REAL NEMOTRON",
    "VERIFIED NEMOTRON",
    "NEMOTRON SYNTHESIS",
    "NEMOTRON AGENT",
    "NEMOTRON DECISION",
    "NEMOTRON REASONING",
    "NEMOTRON RESPONSE",
]


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class FileRecord:
    path: str
    extension: str
    size_bytes: int
    line_count: int
    sha256: str


@dataclass
class ComponentRecord:
    path: str
    category: str
    classes: list[str]
    functions: list[str]
    imports: list[str]
    routes: list[str]


@dataclass
class SuspiciousFinding:
    path: str
    line: int
    category: str
    matched: str
    severity: str
    reason: str


@dataclass
class DuplicateFinding:
    left: str
    right: str
    similarity: float
    reason: str


@dataclass
class EndpointResult:
    url: str
    status: int | None
    latency_ms: float | None
    ok: bool
    error: str | None


# ============================================================
# BASIC UTILITIES
# ============================================================

def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except Exception:
        return ""


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        value,
        encoding="utf-8",
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()

    try:
        with path.open("rb") as fh:
            while True:
                chunk = fh.read(1024 * 1024)

                if not chunk:
                    break

                digest.update(chunk)

        return digest.hexdigest()

    except Exception:
        return ""


AUDIT_ONLY_PATHS = {
    "scripts/baseline_audit.py",
}

GENERATED_DATA_PATH_PREFIXES = (
    "artifacts/baseline_audit/",
    "data/model_shootout_deep/",
)

NON_PRODUCTION_DOCUMENTS = {
    "README.md",
    "LEVEL20_E2E_QA.md",
}

def is_audit_or_generated(path: Path) -> bool:
    relative_path = rel(path)

    if relative_path in AUDIT_ONLY_PATHS:
        return True

    if any(
        relative_path.startswith(prefix)
        for prefix in GENERATED_DATA_PATH_PREFIXES
    ):
        return True

    return False


def all_source_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        if any(
            part in IGNORED_DIRS
            for part in path.parts
        ):
            continue

        if is_audit_or_generated(path):
            continue

        if (
            path.suffix.lower()
            in SOURCE_EXTENSIONS
        ):
            yield path


def git(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        return result.stdout.strip()

    except Exception:
        return ""


def line_of(text: str, offset: int) -> int:
    return (
        text.count("\n", 0, offset)
        + 1
    )


def production_code_files():
    """
    Files whose executable contents can affect deployed AwareOn behavior.

    Excludes:
      - audit tooling
      - generated benchmark data
      - generated audit artifacts
      - pure documentation
    """

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        if any(
            part in IGNORED_DIRS
            for part in path.parts
        ):
            continue

        relative_path = rel(path)

        if relative_path in AUDIT_ONLY_PATHS:
            continue

        if any(
            relative_path.startswith(prefix)
            for prefix in GENERATED_DATA_PATH_PREFIXES
        ):
            continue

        if relative_path in NON_PRODUCTION_DOCUMENTS:
            continue

        if path.suffix.lower() not in {
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".html",
            ".css",
        }:
            continue

        yield path


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML missing. Run: pip install pyyaml"
        ) from exc

    if not path.exists():
        raise FileNotFoundError(
            str(path)
        )

    data = yaml.safe_load(
        read_text(path)
    )

    if not isinstance(data, dict):
        raise ValueError(
            f"{path} must contain a YAML object."
        )

    return data


# ============================================================
# 1. COMPLETE COMPONENT INVENTORY
# ============================================================

def classify_component(path: Path) -> str:
    p = rel(path).lower()

    if "/api/" in p:
        return "API"

    if "/ai/" in p:

        if "learning" in p:
            return "Learning"

        if "memory" in p:
            return "Memory"

        if "benchmark" in p:
            return "AI Evaluation"

        if (
            "evidence" in p
            or "grounding" in p
            or "verification" in p
        ):
            return "Evidence / Verification"

        if (
            "orchestr" in p
            or "master" in p
        ):
            return "Orchestrator"

        if "investigat" in p:
            return "Investigator"

        if "tool" in p:
            return "AI Tool"

        return "AI"

    if (
        "engine" in p
        or "/engines/" in p
    ):
        return "Risk Engine"

    if "scenario" in p:
        return "Simulation / Scenario"

    if any(
        token in p
        for token in [
            "cell",
            "cluster",
            "neighborhood",
            "cross_engine",
            "cross_cell",
            "propagation",
            "temporal",
        ]
    ):
        return "Derived Intelligence"

    if any(
        token in p
        for token in [
            "feature",
            "preprocess",
            "processor",
            "transform",
            "ingest",
            "build_",
        ]
    ):
        return "Processor / Feature Generator"

    if "/data/" in p:
        return "Data Layer"

    if p.endswith("main.py"):
        return "Application Entry Point"

    if (
        p.endswith(".html")
        or "/frontend/" in p
    ):
        return "Frontend"

    return "Backend Module"


def analyze_python(path: Path):
    text = read_text(path)

    try:
        tree = ast.parse(text)

    except SyntaxError as exc:
        return {
            "classes": [],
            "functions": [],
            "imports": [],
            "routes": [],
            "error": str(exc),
        }

    classes = []
    functions = []
    imports = []
    routes = []

    for node in ast.walk(tree):

        if isinstance(
            node,
            ast.ClassDef,
        ):
            classes.append(node.name)

        elif isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            functions.append(node.name)

        elif isinstance(
            node,
            ast.Import,
        ):
            imports.extend(
                alias.name
                for alias in node.names
            )

        elif isinstance(
            node,
            ast.ImportFrom,
        ):
            if node.module:
                imports.append(
                    node.module
                )

        elif isinstance(
            node,
            ast.Call,
        ):
            func = node.func

            if isinstance(
                func,
                ast.Attribute,
            ):
                if func.attr in {
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "options",
                }:
                    if node.args:
                        first = node.args[0]

                        if isinstance(
                            first,
                            ast.Constant,
                        ):
                            if isinstance(
                                first.value,
                                str,
                            ):
                                routes.append(
                                    first.value
                                )

    return {
        "classes": sorted(set(classes)),
        "functions": sorted(set(functions)),
        "imports": sorted(set(imports)),
        "routes": sorted(set(routes)),
        "error": None,
    }


def run_component_inventory() -> dict[str, Any]:
    files = []
    components = []

    for path in all_source_files():

        text = read_text(path)

        files.append(
            asdict(
                FileRecord(
                    path=rel(path),
                    extension=path.suffix.lower(),
                    size_bytes=path.stat().st_size,
                    line_count=len(
                        text.splitlines()
                    ),
                    sha256=file_sha256(path),
                )
            )
        )

        if path.suffix.lower() != ".py":
            continue

        analysis = analyze_python(path)

        components.append(
            asdict(
                ComponentRecord(
                    path=rel(path),
                    category=classify_component(path),
                    classes=analysis["classes"],
                    functions=analysis["functions"],
                    imports=analysis["imports"],
                    routes=analysis["routes"],
                )
            )
        )

    category_counts = Counter(
        item["category"]
        for item in components
    )

    result = {
        "git": {
            "branch": git(
                ["branch", "--show-current"]
            ),
            "commit": git(
                ["rev-parse", "HEAD"]
            ),
            "status": git(
                ["status", "--short"]
            ),
        },
        "file_count": len(files),
        "python_component_count": len(
            components
        ),
        "category_counts": dict(
            category_counts
        ),
        "files": files,
        "components": components,
    }

    write_json(
        OUTPUT_DIR
        / "component_inventory.json",
        result,
    )

    return result


# ============================================================
# 2. 177 FEATURE GAP AUDIT
# ============================================================

def run_feature_audit() -> dict[str, Any]:

    scope = load_yaml(
        FEATURE_SCOPE
    )

    features = scope.get(
        "features",
        [],
    )

    expected = int(
        scope.get(
            "expected_count",
            177,
        )
    )

    ids = [
        item.get("id")
        for item in features
        if isinstance(item, dict)
    ]

    duplicate_ids = [
        item
        for item, count in Counter(ids).items()
        if count > 1
    ]

    missing_ids = sorted(
        set(range(1, expected + 1))
        - set(
            item
            for item in ids
            if isinstance(item, int)
        )
    )

    repo_text = {
        rel(path): read_text(path)
        for path in all_source_files()
    }

    results = []

    for feature in features:

        feature_id = feature.get("id")

        feature_name = feature.get(
            "feature",
            "",
        )

        keywords = feature.get(
            "keywords",
            [],
        )

        evidence = []

        for path, text in repo_text.items():

            lower = text.lower()

            hits = [
                str(keyword)
                for keyword in keywords
                if str(keyword).lower()
                in lower
            ]

            if hits:
                evidence.append(
                    {
                        "path": path,
                        "keywords": hits,
                    }
                )

        results.append(
            {
                "id": feature_id,
                "feature": feature_name,
                "category": feature.get(
                    "category"
                ),
                "required_state": feature.get(
                    "required_state",
                    "REAL",
                ),
                "evidence": evidence[:30],
                "audit_status": (
                    "CANDIDATE_EVIDENCE"
                    if evidence
                    else "NO_CODE_EVIDENCE"
                ),
            }
        )

    status = "PASS"

    # The authoritative 177-item scope is not present in the
    # repository or recoverable from Git history. Do not fabricate it.
    # This is a documented scope-provenance gap, not evidence that
    # AwareOn itself is missing 177 implemented capabilities.
    scope_unavailable = len(features) == 0 and expected == 177

    if scope_unavailable:
        status = "SCOPE_UNAVAILABLE"
    elif len(features) != expected:
        status = "BLOCKED"

    if duplicate_ids:
        status = "BLOCKED"

    if missing_ids and not scope_unavailable:
        status = "BLOCKED"

    result = {
        "status": status,
        "expected_count": expected,
        "actual_count": len(features),
        "duplicate_ids": duplicate_ids,
        "missing_ids": missing_ids,
        "features": results,
        "scope_provenance": (
            "The authoritative 177-item feature scope was not found "
            "in repository files or Git history. The audit therefore "
            "refuses to fabricate feature entries."
        ),
        "important_note": (
            "Code keyword matches are candidate evidence only. "
            "They do not prove feature completion."
        ),
    }

    write_json(
        OUTPUT_DIR
        / "feature_gap_audit.json",
        result,
    )

    with (
        OUTPUT_DIR
        / "feature_gap_audit.csv"
    ).open(
        "w",
        newline="",
        encoding="utf-8",
    ) as fh:

        writer = csv.writer(fh)

        writer.writerow(
            [
                "id",
                "category",
                "feature",
                "required_state",
                "audit_status",
                "evidence_count",
                "evidence_paths",
            ]
        )

        for item in results:

            writer.writerow(
                [
                    item["id"],
                    item["category"],
                    item["feature"],
                    item["required_state"],
                    item["audit_status"],
                    len(
                        item["evidence"]
                    ),
                    ";".join(
                        x["path"]
                        for x in item["evidence"]
                    ),
                ]
            )

    return result


# ============================================================
# 3. PLACEHOLDER / FAKE / STATIC / PROXY AUDIT
# ============================================================

SUSPICIOUS_PATTERNS = [
    (
        "PLACEHOLDER",
        r"\b(TODO|FIXME|XXX|HACK|PLACEHOLDER|NOT_IMPLEMENTED|COMING_SOON)\b",
        "MEDIUM",
        "Possible unfinished implementation.",
    ),
    (
        "SIMULATION",
        r"\b(simulat(?:e|ed|ion)|synthetic|mock|dummy|fake|demo[_ -]?data|sample[_ -]?data)\b",
        "MEDIUM",
        "Possible simulated or non-production data path.",
    ),
    (
        "RANDOM_GENERATION",
        r"\b(random\.(random|uniform|randint|choice)|np\.random\.)",
        "HIGH",
        "Random generation can indicate synthetic runtime output.",
    ),
    (
        "STATIC_NUMERIC_RISK",
        r"\b(risk_score\s*=\s*[0-9]+(?:\.[0-9]+)?)\b",
        "HIGH",
        "Potential hard-coded risk result.",
    ),
    (
        "STATIC_CONFIDENCE",
        r"\b(confidence\s*=\s*[0-9]+(?:\.[0-9]+)?)\b",
        "HIGH",
        "Potential hard-coded confidence value.",
    ),
    (
        "STATIC_UNCERTAINTY",
        r"\b(uncertainty\s*=\s*[0-9]+(?:\.[0-9]+)?)\b",
        "HIGH",
        "Potential hard-coded uncertainty value.",
    ),
    (
        "FAKE_DELAY",
        r"\btime\.sleep\s*\(",
        "LOW",
        "Artificial timing may indicate demo behavior.",
    ),
    (
        "LIVE_CLAIM",
        r"\b(live|real[- ]time|realtime|real time|continuous|nowcasting)\b",
        "MEDIUM",
        "Live/realtime claim requires actual freshness semantics.",
    ),
    (
        "STALE_PRIMARY_MODEL",
        "|".join(
            re.escape(item)
            for item in STALE_PRIMARY_LABELS
        ),
        "CRITICAL",
        (
            "Nemotron wording is inconsistent with the locked "
            "production primary Qwen 3.5 9B."
        ),
    ),
]


def run_placeholder_audit() -> dict[str, Any]:

    findings: list[dict[str, Any]] = []

    compiled = [
        (
            category,
            re.compile(
                pattern,
                re.IGNORECASE,
            ),
            severity,
            reason,
        )
        for (
            category,
            pattern,
            severity,
            reason,
        ) in SUSPICIOUS_PATTERNS
    ]

    for path in production_code_files():

        text = read_text(path)

        for (
            category,
            pattern,
            severity,
            reason,
        ) in compiled:

            for match in pattern.finditer(
                text
            ):

                matched_text = match.group(0)

                # ------------------------------------------------
                # Context-aware static-confidence handling.
                #
                # The scanner must distinguish:
                #   1. production hard-coded certainty,
                #   2. explicit zero-confidence safety boundaries,
                #   3. deterministic test fixtures.
                # ------------------------------------------------
                if category == "STATIC_CONFIDENCE":

                    rel_path = rel(path).replace(
                        "\\",
                        "/",
                    )

                    # Deterministic confidence values used only
                    # by the confidence integrity test are not
                    # production implementation.
                    if rel_path == (
                        "scripts/confidence_integrity_test.py"
                    ):
                        continue

                    # Zero confidence is a conservative boundary
                    # state, not a claim of certainty. It may still
                    # deserve review elsewhere, but it must not be
                    # classified as HIGH hard-coded confidence.
                    numeric_match = re.search(
                        r"confidence\s*=\s*"
                        r"([0-9]+(?:\.[0-9]+)?)",
                        matched_text,
                    )

                    if (
                        numeric_match is not None
                        and float(
                            numeric_match.group(1)
                        ) == 0.0
                    ):
                        continue

                findings.append(
                    asdict(
                        SuspiciousFinding(
                            path=rel(path),
                            line=line_of(
                                text,
                                match.start(),
                            ),
                            category=category,
                            matched=matched_text[:300],
                            severity=severity,
                            reason=reason,
                        )
                    )
                )

    result = {
        "total": len(findings),
        "critical": sum(
            item["severity"]
            == "CRITICAL"
            for item in findings
        ),
        "high": sum(
            item["severity"]
            == "HIGH"
            for item in findings
        ),
        "medium": sum(
            item["severity"]
            == "MEDIUM"
            for item in findings
        ),
        "findings": findings,
    }

    write_json(
        OUTPUT_DIR
        / "placeholder_fake_proxy_audit.json",
        result,
    )

    return result


# ============================================================
# 4. DUPLICATE / OVERLAP AUDIT
# ============================================================

def normalize_python(text: str) -> str:

    text = re.sub(
        r"#.*",
        "",
        text,
    )

    text = re.sub(
        r'""".*?"""',
        "",
        text,
        flags=re.DOTALL,
    )

    text = re.sub(
        r"'''.*?'''",
        "",
        text,
        flags=re.DOTALL,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def run_duplicate_audit() -> dict[str, Any]:

    python_files = []

    for path in ROOT.rglob("*.py"):

        if any(
            part in IGNORED_DIRS
            for part in path.parts
        ):
            continue

        text = normalize_python(
            read_text(path)
        )

        if len(text) >= 500:
            python_files.append(
                (
                    rel(path),
                    text,
                )
            )

    findings = []

    for i in range(
        len(python_files)
    ):

        left_path, left_text = (
            python_files[i]
        )

        for j in range(
            i + 1,
            len(python_files),
        ):

            right_path, right_text = (
                python_files[j]
            )

            score = (
                difflib.SequenceMatcher(
                    None,
                    left_text[:25000],
                    right_text[:25000],
                ).ratio()
            )

            if score >= 0.78:

                findings.append(
                    asdict(
                        DuplicateFinding(
                            left=left_path,
                            right=right_path,
                            similarity=round(
                                score,
                                4,
                            ),
                            reason=(
                                "High code similarity. "
                                "Review for duplicated "
                                "responsibility."
                            ),
                        )
                    )
                )

    domains = {
        "AI_ORCHESTRATION": [
            "orchestr",
            "master",
            "decision",
            "agent_loop",
        ],
        "INVESTIGATION": [
            "investigator",
            "investigation",
            "cell_intelligence",
        ],
        "RISK": [
            "risk",
            "engine",
            "unified",
        ],
        "SCENARIO": [
            "scenario",
            "counterfactual",
        ],
        "LEARNING": [
            "learning",
            "memory",
            "feedback",
        ],
        "EVIDENCE": [
            "evidence",
            "grounding",
            "verification",
        ],
    }

    clusters = defaultdict(list)

    for path, _ in python_files:

        lower = path.lower()

        for domain, terms in domains.items():

            if any(
                term in lower
                for term in terms
            ):
                clusters[domain].append(
                    path
                )

    result = {
        "high_similarity_pairs": findings,
        "responsibility_clusters": dict(
            clusters
        ),
        "warning": (
            "Similarity and filename clusters are candidates "
            "for review; they are not proof of duplicate logic."
        ),
    }

    write_json(
        OUTPUT_DIR
        / "duplicate_architecture_audit.json",
        result,
    )

    return result


# ============================================================
# 5. DATA LINEAGE AUDIT
# ============================================================

LINEAGE_STAGES = [
    "SOURCE",
    "RAW",
    "CLEAN",
    "FEATURES",
    "ENGINE",
    "DERIVED_INTELLIGENCE",
    "AI_EVIDENCE",
    "DECISION",
]


def run_lineage_audit() -> dict[str, Any]:

    specification = load_yaml(
        LINEAGE_SPEC
    )

    repo_text = {
        rel(path): read_text(path).lower()
        for path in all_source_files()
    }

    keywords = {
        "SOURCE": [
            "source",
            "sentinel",
            "rainfall",
            "weather",
            "sar",
            "gsi",
            "dem",
            "gis",
        ],
        "RAW": [
            "raw",
            "download",
            "ingest",
        ],
        "CLEAN": [
            "clean",
            "normalize",
            "sanitize",
            "validation",
        ],
        "FEATURES": [
            "feature",
            "transform",
        ],
        "ENGINE": [
            "engine",
            "predict",
            "risk_score",
        ],
        "DERIVED_INTELLIGENCE": [
            "cell",
            "cluster",
            "neighborhood",
            "propagation",
            "cross_engine",
            "temporal",
        ],
        "AI_EVIDENCE": [
            "evidence",
            "grounding",
            "verification",
        ],
        "DECISION": [
            "decision",
            "recommend",
            "alert",
            "warning",
            "priority",
        ],
    }

    stage_results = {}

    for stage in LINEAGE_STAGES:

        matches = []

        for path, text in repo_text.items():

            hits = [
                keyword
                for keyword in keywords[stage]
                if keyword in text
            ]

            if hits:
                matches.append(
                    {
                        "path": path,
                        "keywords": hits[:20],
                    }
                )

        stage_results[stage] = {
            "candidate_count": len(
                matches
            ),
            "files": matches[:50],
        }

    explicit_requirements = (
        specification.get(
            "artifact_contract",
            {},
        ).get(
            "required_fields",
            [],
        )
    )

    result = {
        "required_stages": LINEAGE_STAGES,
        "stage_results": stage_results,
        "required_artifact_fields": explicit_requirements,
        "warning": (
            "Keyword discovery does not prove runtime lineage. "
            "Runtime lineage still requires actual producer/consumer "
            "IDs, timestamps, versions, freshness and provenance."
        ),
    }

    write_json(
        OUTPUT_DIR
        / "data_lineage_audit.json",
        result,
    )

    return result


# ============================================================
# 6. PERFORMANCE BASELINE
# ============================================================

ENDPOINTS = [
    "/health",
    "/api/v1/engines",
    "/api/v1/risk",
    "/api/v1/alerts",
    "/api/v1/incidents",
    "/api/v1/scenario/summary",
]


def request_get(
    base_url: str,
    path: str,
) -> EndpointResult:

    url = (
        base_url.rstrip("/")
        + path
    )

    request = Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "AwareOn-Baseline-Audit/1.0"
            ),
        },
    )

    start = time.perf_counter()

    try:

        with urlopen(
            request,
            timeout=30,
        ) as response:

            response.read()

            elapsed = (
                time.perf_counter()
                - start
            ) * 1000

            return EndpointResult(
                url=url,
                status=response.status,
                latency_ms=round(
                    elapsed,
                    2,
                ),
                ok=(
                    200
                    <= response.status
                    < 400
                ),
                error=None,
            )

    except HTTPError as exc:

        elapsed = (
            time.perf_counter()
            - start
        ) * 1000

        return EndpointResult(
            url=url,
            status=exc.code,
            latency_ms=round(
                elapsed,
                2,
            ),
            ok=False,
            error=str(exc),
        )

    except (
        URLError,
        TimeoutError,
        Exception,
    ) as exc:

        elapsed = (
            time.perf_counter()
            - start
        ) * 1000

        return EndpointResult(
            url=url,
            status=None,
            latency_ms=round(
                elapsed,
                2,
            ),
            ok=False,
            error=str(exc),
        )


def run_performance_baseline(
    base_url: str,
) -> dict[str, Any]:

    results = []

    for path in ENDPOINTS:

        samples = []

        for _ in range(3):

            result = request_get(
                base_url,
                path,
            )

            samples.append(
                result
            )

        valid = [
            item.latency_ms
            for item in samples
            if item.latency_ms
            is not None
        ]

        result = samples[-1]

        results.append(
            {
                "path": path,
                "status": result.status,
                "ok": all(
                    item.ok
                    for item in samples
                ),
                "samples_ms": valid,
                "median_ms": (
                    statistics.median(valid)
                    if valid
                    else None
                ),
                "max_ms": (
                    max(valid)
                    if valid
                    else None
                ),
                "errors": [
                    item.error
                    for item in samples
                    if item.error
                ],
            }
        )

    result = {
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "git_commit": git(
                ["rev-parse", "HEAD"]
            ),
            "git_branch": git(
                ["branch", "--show-current"]
            ),
        },
        "ai": {
            "primary_provider": PRIMARY_PROVIDER,
            "primary_model": PRIMARY_MODEL,
            "backup_provider": BACKUP_PROVIDER,
            "backup_model": BACKUP_MODEL,
            "configured_provider": os.getenv(
                "AWAREON_AI_PROVIDER",
                "",
            ),
            "configured_model": os.getenv(
                "AWAREON_AI_MODEL",
                "",
            ),
        },
        "base_url": base_url,
        "endpoints": results,
    }

    write_json(
        OUTPUT_DIR
        / "performance_baseline.json",
        result,
    )

    return result


# ============================================================
# 7. INTELLIGENCE SPEC VALIDATION
# ============================================================

def run_spec_validation() -> dict[str, Any]:

    spec = load_yaml(
        INTELLIGENCE_SPEC
    )

    required_sections = {
        "project",
        "ai",
        "truth_model",
        "learning",
        "evidence",
        "performance",
        "reliability",
        "validation",
        "completion_rule",
    }

    missing_sections = sorted(
        required_sections
        - set(spec.keys())
    )

    primary = (
        spec
        .get("ai", {})
        .get("primary", {})
    )

    backup = (
        spec
        .get("ai", {})
        .get("backup", {})
    )

    primary_ok = (
        primary.get("provider")
        == PRIMARY_PROVIDER
        and primary.get("model")
        == PRIMARY_MODEL
        and primary.get("role")
        == "production_primary"
    )

    backup_ok = (
        backup.get("provider")
        == BACKUP_PROVIDER
        and backup.get("model")
        == BACKUP_MODEL
        and backup.get("role")
        == "fallback_only"
    )

    result = {
        "status": (
            "PASS"
            if (
                not missing_sections
                and primary_ok
                and backup_ok
            )
            else "FAIL"
        ),
        "missing_sections": missing_sections,
        "primary_ai_ok": primary_ok,
        "backup_ai_ok": backup_ok,
        "primary": primary,
        "backup": backup,
    }

    write_json(
        OUTPUT_DIR
        / "intelligence_spec_validation.json",
        result,
    )

    return result


# ============================================================
# QWEN PRIMARY LOCK AUDIT
# ============================================================

def run_qwen_lock_audit() -> dict[str, Any]:

    findings = []

    configured_provider = (
        os.getenv(
            "AWAREON_AI_PROVIDER",
            "",
        )
        .strip()
        .lower()
    )

    configured_model = (
        os.getenv(
            "AWAREON_AI_MODEL",
            "",
        )
        .strip()
    )

    for path in production_code_files():

        text = read_text(path)

        for label in STALE_PRIMARY_LABELS:

            pattern = re.compile(
                re.escape(label),
                re.IGNORECASE,
            )

            for match in pattern.finditer(
                text
            ):

                findings.append(
                    {
                        "path": rel(path),
                        "line": line_of(
                            text,
                            match.start(),
                        ),
                        "matched": match.group(
                            0
                        ),
                        "reason": (
                            "Production code still names "
                            "Nemotron as the agent/model. "
                            "Qwen 3.5 9B is the locked primary."
                        ),
                    }
                )

    environment_ok = (
        configured_model
        in {
            "",
            PRIMARY_MODEL,
            BACKUP_MODEL,
        }
    )

    result = {
        "status": (
            "PASS"
            if (
                not findings
                and environment_ok
            )
            else "FAIL"
        ),
        "locked_primary": {
            "provider": PRIMARY_PROVIDER,
            "model": PRIMARY_MODEL,
        },
        "locked_backup": {
            "provider": BACKUP_PROVIDER,
            "model": BACKUP_MODEL,
        },
        "configured_provider": configured_provider,
        "configured_model": configured_model,
        "stale_primary_labels": findings,
    }

    write_json(
        OUTPUT_DIR
        / "qwen_primary_lock_audit.json",
        result,
    )

    return result


# ============================================================
# FINAL REPORT
# ============================================================

def generate_report(
    inventory,
    features,
    placeholders,
    duplicates,
    lineage,
    performance,
    intelligence,
    qwen,
) -> str:

    return f"""# AwareOn Baseline Audit

Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}

## Locked AI

Primary:
`{PRIMARY_PROVIDER} / {PRIMARY_MODEL}`

Backup:
`{BACKUP_PROVIDER} / {BACKUP_MODEL}`

## Component inventory

Source files:
`{inventory["file_count"]}`

Python components:
`{inventory["python_component_count"]}`

## Feature audit

Expected:
`{features["expected_count"]}`

Actual:
`{features["actual_count"]}`

Status:
`{features["status"]}`

Duplicate IDs:
`{features["duplicate_ids"]}`

Missing IDs:
`{features["missing_ids"]}`

## Placeholder / fake / proxy audit

Total findings:
`{placeholders["total"]}`

Critical:
`{placeholders["critical"]}`

High:
`{placeholders["high"]}`

## Architecture overlap audit

High-similarity pairs:
`{len(duplicates["high_similarity_pairs"])}`

## Data lineage

Required stages:
`{" -> ".join(lineage["required_stages"])}`

## Performance

Base URL:
`{performance.get("base_url", "not run")}`

## Intelligence specification

Status:
`{intelligence["status"]}`

Primary AI valid:
`{intelligence["primary_ai_ok"]}`

Backup AI valid:
`{intelligence["backup_ai_ok"]}`

## Qwen primary lock

Status:
`{qwen["status"]}`

Stale primary labels:
`{len(qwen["stale_primary_labels"])}`

## Important

This document is an audit result.

It must not be interpreted as proof that every future capability
already exists.

A feature only becomes complete after implementation, integration,
positive testing, adversarial testing, failure testing, improvement,
retesting and validation.
"""


# ============================================================
# MAIN
# ============================================================

def main():

    ensure_output_dir()

    print()
    print("=" * 72)
    print("AWAREON BASELINE AUDIT")
    print("=" * 72)
    print()
    print(
        "PRIMARY :",
        PRIMARY_PROVIDER,
        PRIMARY_MODEL,
    )
    print(
        "BACKUP  :",
        BACKUP_PROVIDER,
        BACKUP_MODEL,
    )
    print()

    print("[1/7] Component inventory...")
    inventory = run_component_inventory()

    print("[2/7] 177-feature audit...")
    try:
        features = run_feature_audit()
    except Exception as exc:
        features = {
            "status": "BLOCKED",
            "expected_count": 177,
            "actual_count": 0,
            "duplicate_ids": [],
            "missing_ids": [],
            "error": str(exc),
        }

        write_json(
            OUTPUT_DIR
            / "feature_gap_audit_error.json",
            features,
        )

    print("[3/7] Placeholder/fake/proxy audit...")
    placeholders = run_placeholder_audit()

    print("[4/7] Architecture overlap audit...")
    duplicates = run_duplicate_audit()

    print("[5/7] Data lineage audit...")
    lineage = run_lineage_audit()

    print("[6/7] Performance baseline...")

    base_url = os.getenv(
        "AWAREON_BASE_URL",
        "http://127.0.0.1:8000",
    )

    performance = run_performance_baseline(
        base_url
    )

    print("[7/7] Specification + Qwen lock...")
    intelligence = run_spec_validation()
    qwen = run_qwen_lock_audit()

    report = generate_report(
        inventory,
        features,
        placeholders,
        duplicates,
        lineage,
        performance,
        intelligence,
        qwen,
    )

    write_text(
        OUTPUT_DIR
        / "AUDIT_REPORT.md",
        report,
    )

    print()
    print("=" * 72)
    print("AUDIT FINISHED")
    print("=" * 72)
    print()
    print(
        "Output:",
        OUTPUT_DIR,
    )
    print()
    print(
        "Read:",
        OUTPUT_DIR
        / "AUDIT_REPORT.md",
    )
    print()


if __name__ == "__main__":
    main()
