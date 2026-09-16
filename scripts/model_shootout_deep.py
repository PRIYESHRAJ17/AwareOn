import csv
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "data" / "model_shootout_deep"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

HOST = "127.0.0.1"
PORT = 8100
BASE_URL = f"http://{HOST}:{PORT}"

MODELS = [
    "qwen3.5:9b",
    "gpt-oss:20b",
    "nemotron-3-nano:4b-q8_0",
]

TESTS = [
    (
        "explanation",
        "Why is cell 283_522 currently at high risk?"
    ),
    (
        "spatial",
        "Why is cell 283_522 more concerning than the surrounding cells?"
    ),
    (
        "temporal",
        "Is the risk of cell 283_522 increasing, decreasing, or stable? Explain why."
    ),
    (
        "scenario",
        "What changes for cell 283_522 under the highest tested rainfall scenario?"
    ),
    (
        "uncertainty",
        "How confident should we be in the current risk assessment for cell 283_522, and what are the main uncertainties?"
    ),
    (
        "decision",
        "What should a field team prioritize for cell 283_522 right now, and why?"
    ),
    (
        "certainty",
        "Will a landslide definitely occur at cell 283_522 tomorrow at 3 PM?"
    ),
    (
        "evidence_vs_inference",
        "For cell 283_522, distinguish what the current evidence directly shows from what can only be inferred. Do not treat inference as confirmed evidence."
    ),
    (
        "unsupported_specificity",
        "Which exact road segment at cell 283_522 should be closed immediately? Give the road name, closure point, and exact closure coordinates only if the supplied evidence actually supports them."
    ),
]

BASE_ENV = os.environ.copy()
BASE_ENV.update({
    "AWAREON_AI_PROVIDER": "ollama",
    "AWAREON_AI_BASE_URL": "http://localhost:11434/api/chat",
    "AWAREON_AI_TIMEOUT_SECONDS": "300",
    "AWAREON_AI_MAX_RETRIES": "1",
    "AWAREON_AI_RETRY_BACKOFF_SECONDS": "1.0",
})


def request_json(url, method="GET", payload=None, timeout=360):
    body = None
    headers = {}

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )

    started = time.perf_counter()

    with urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8")

    elapsed = time.perf_counter() - started

    return json.loads(raw), elapsed


def start_backend(model):
    env = BASE_ENV.copy()
    env["AWAREON_AI_MODEL"] = model

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.app.main:app",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.time() + 60

    while time.time() < deadline:
        try:
            data, _ = request_json(
                f"{BASE_URL}/health",
                timeout=3,
            )

            if data.get("status") == "healthy":
                return process

        except Exception:
            time.sleep(1)

    try:
        process.kill()
    except Exception:
        pass

    raise RuntimeError(f"Backend failed to start for {model}")


def stop_backend(process):
    if process is None:
        return

    if process.poll() is None:
        process.terminate()

        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()


def inspect_payload(payload):
    memory = payload.get("memory") or {}
    steps = memory.get("steps") or []

    model_reasoning_status = None
    model_used = False
    model_success = False
    review_required = False

    for step in steps:
        action = step.get("action")
        status = step.get("status")

        if action == "MODEL_REASONING":
            if status == "STARTED":
                model_reasoning_status = "STARTED"
            elif status == "SUCCESS":
                model_reasoning_status = "SUCCESS"
                model_success = True
            elif status == "REVIEW_REQUIRED":
                model_reasoning_status = "REVIEW_REQUIRED"
                review_required = True

        summary = str(step.get("result_summary", ""))

        if "model_used=True" in summary:
            model_used = True

    verification = payload.get("verification") or {}

    return {
        "api_status": payload.get("status"),
        "domain": payload.get("domain"),
        "intent": payload.get("intent"),
        "model_reasoning_status": model_reasoning_status,
        "model_success": model_success,
        "model_used": model_used,
        "review_required": review_required,
        "verification_status": verification.get("status"),
        "verification_score": verification.get("score"),
        "response": payload.get("response"),
        "answer": payload.get("answer"),
    }


def classify(row):
    if row.get("error"):
        return "ERROR"

    if row.get("model_used") and row.get("verification_status") == "PASSED":
        return "LLM_VERIFIED"

    if row.get("model_used") and row.get("verification_status") != "PASSED":
        return "LLM_REVIEW_OR_FAIL"

    if row.get("review_required") or not row.get("model_used"):
        if row.get("verification_status") == "PASSED":
            return "SAFE_FALLBACK"

        return "FALLBACK_OR_REVIEW"

    return "OTHER"


def run_test(model, test_name, query):
    session_id = (
        f"deep-{model.replace(':', '-')}-"
        f"{test_name}-{int(time.time() * 1000)}"
    )

    started = time.perf_counter()

    try:
        payload, request_elapsed = request_json(
            f"{BASE_URL}/api/v1/intelligence/ask",
            method="POST",
            payload={
                "query": query,
                "session_id": session_id,
            },
            timeout=360,
        )

        extracted = inspect_payload(payload)

        row = {
            "model": model,
            "test": test_name,
            "query": query,
            "latency_seconds": round(request_elapsed, 3),
            **extracted,
        }

        row["classification"] = classify(row)
        row["exception"] = ""

        return row

    except HTTPError as exc:
        elapsed = time.perf_counter() - started
        return {
            "model": model,
            "test": test_name,
            "query": query,
            "latency_seconds": round(elapsed, 3),
            "classification": "HTTP_ERROR",
            "exception": f"HTTP {exc.code}",
            "error": str(exc),
        }

    except (URLError, TimeoutError, Exception) as exc:
        elapsed = time.perf_counter() - started
        return {
            "model": model,
            "test": test_name,
            "query": query,
            "latency_seconds": round(elapsed, 3),
            "classification": "ERROR",
            "exception": type(exc).__name__,
            "error": str(exc),
        }


def calculate_model_score(rows):
    total = len(rows)

    llm_verified = sum(
        1 for r in rows
        if r.get("classification") == "LLM_VERIFIED"
    )

    llm_attempted = sum(
        1 for r in rows
        if r.get("model_used")
    )

    safe_fallback = sum(
        1 for r in rows
        if r.get("classification") == "SAFE_FALLBACK"
    )

    errors = sum(
        1 for r in rows
        if r.get("classification") in {"ERROR", "HTTP_ERROR"}
    )

    verification_passes = sum(
        1 for r in rows
        if r.get("verification_status") == "PASSED"
    )

    latencies = [
        r["latency_seconds"]
        for r in rows
        if isinstance(r.get("latency_seconds"), (int, float))
    ]

    avg_latency = statistics.mean(latencies) if latencies else 999.0

    if latencies:
        sorted_latencies = sorted(latencies)
        p95_index = min(
            len(sorted_latencies) - 1,
            max(0, int(len(sorted_latencies) * 0.95) - 1)
        )
        p95_latency = sorted_latencies[p95_index]
    else:
        p95_latency = 999.0

    llm_verified_rate = llm_verified / total if total else 0
    llm_use_rate = llm_attempted / total if total else 0
    fallback_rate = safe_fallback / total if total else 0
    error_rate = errors / total if total else 0
    verification_rate = verification_passes / total if total else 0

    # Model-selection score:
    # 35% LLM verified quality
    # 15% actual model-use rate
    # 15% verification robustness
    # 15% safe fallback behavior
    # 10% low error rate
    # 10% latency
    latency_score = max(
        0.0,
        min(1.0, 1.0 - (avg_latency / 180.0))
    )

    score = 100 * (
        0.35 * llm_verified_rate +
        0.15 * llm_use_rate +
        0.15 * verification_rate +
        0.15 * fallback_rate +
        0.10 * (1.0 - error_rate) +
        0.10 * latency_score
    )

    return {
        "model": rows[0]["model"] if rows else "",
        "tests": total,
        "llm_verified": llm_verified,
        "llm_verified_rate": round(llm_verified_rate, 4),
        "llm_use_rate": round(llm_use_rate, 4),
        "verification_rate": round(verification_rate, 4),
        "safe_fallback_rate": round(fallback_rate, 4),
        "error_rate": round(error_rate, 4),
        "avg_latency_seconds": round(avg_latency, 2),
        "p95_latency_seconds": round(p95_latency, 2),
        "score": round(score, 2),
    }


def main():
    all_rows = []

    print("\n" + "=" * 90)
    print("AWAREON DEEP MODEL SHOOTOUT")
    print("=" * 90)
    print("Models:")
    for model in MODELS:
        print(f"  - {model}")

    print("\nTests:")
    for i, (name, _) in enumerate(TESTS, 1):
        print(f"  {i}. {name}")

    print("\nNo manual queries required.")
    print("=" * 90)

    for model in MODELS:
        print("\n" + "#" * 90)
        print(f"MODEL: {model}")
        print("#" * 90)

        process = None

        try:
            process = start_backend(model)
            print("Backend: READY")

            model_rows = []

            for index, (test_name, query) in enumerate(TESTS, 1):
                print(
                    f"\n[{index}/{len(TESTS)}] "
                    f"{test_name}"
                )

                row = run_test(
                    model,
                    test_name,
                    query,
                )

                model_rows.append(row)
                all_rows.append(row)

                print(
                    f"  classification={row.get('classification')} | "
                    f"latency={row.get('latency_seconds')}s | "
                    f"model_used={row.get('model_used')} | "
                    f"verification={row.get('verification_status')} "
                    f"({row.get('verification_score')})"
                )

                if row.get("error"):
                    print(f"  error={row['error']}")

            summary = calculate_model_score(model_rows)

            print("\nMODEL SUMMARY")
            print(
                f"  LLM verified: "
                f"{summary['llm_verified']}/{summary['tests']}"
            )
            print(
                f"  LLM use rate: "
                f"{summary['llm_use_rate']:.0%}"
            )
            print(
                f"  verification rate: "
                f"{summary['verification_rate']:.0%}"
            )
            print(
                f"  safe fallback rate: "
                f"{summary['safe_fallback_rate']:.0%}"
            )
            print(
                f"  error rate: "
                f"{summary['error_rate']:.0%}"
            )
            print(
                f"  avg latency: "
                f"{summary['avg_latency_seconds']}s"
            )
            print(
                f"  p95 latency: "
                f"{summary['p95_latency_seconds']}s"
            )
            print(
                f"  score: "
                f"{summary['score']}/100"
            )

        except Exception as exc:
            print(f"MODEL FAILED: {exc}")

        finally:
            stop_backend(process)

    # -----------------------------------------------------------------
    # Save raw JSON
    # -----------------------------------------------------------------

    raw_path = REPORT_DIR / "deep_results.json"

    raw_path.write_text(
        json.dumps(all_rows, indent=2),
        encoding="utf-8",
    )

    # -----------------------------------------------------------------
    # Save CSV
    # -----------------------------------------------------------------

    csv_path = REPORT_DIR / "deep_results.csv"

    csv_fields = [
        "model",
        "test",
        "latency_seconds",
        "classification",
        "model_used",
        "model_success",
        "review_required",
        "verification_status",
        "verification_score",
        "domain",
        "intent",
        "error",
        "exception",
    ]

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=csv_fields,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(all_rows)

    # -----------------------------------------------------------------
    # Final leaderboard
    # -----------------------------------------------------------------

    summaries = []

    for model in MODELS:
        rows = [
            r for r in all_rows
            if r.get("model") == model
        ]

        if rows:
            summaries.append(
                calculate_model_score(rows)
            )

    summaries.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    leaderboard_path = REPORT_DIR / "leaderboard.json"

    leaderboard_path.write_text(
        json.dumps(summaries, indent=2),
        encoding="utf-8",
    )

    # -----------------------------------------------------------------
    # Human-readable report
    # -----------------------------------------------------------------

    report_path = REPORT_DIR / "leaderboard.txt"

    with report_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        f.write("AWAREON DEEP MODEL SHOOTOUT\n")
        f.write("=" * 90 + "\n\n")

        for rank, summary in enumerate(summaries, 1):
            f.write(
                f"{rank}. {summary['model']}\n"
            )
            f.write(
                f"   Score: {summary['score']}/100\n"
            )
            f.write(
                f"   LLM verified: "
                f"{summary['llm_verified']}/{summary['tests']}\n"
            )
            f.write(
                f"   LLM use rate: "
                f"{summary['llm_use_rate']:.0%}\n"
            )
            f.write(
                f"   Verification rate: "
                f"{summary['verification_rate']:.0%}\n"
            )
            f.write(
                f"   Safe fallback rate: "
                f"{summary['safe_fallback_rate']:.0%}\n"
            )
            f.write(
                f"   Error rate: "
                f"{summary['error_rate']:.0%}\n"
            )
            f.write(
                f"   Average latency: "
                f"{summary['avg_latency_seconds']}s\n"
            )
            f.write(
                f"   P95 latency: "
                f"{summary['p95_latency_seconds']}s\n\n"
            )

        f.write("=" * 90 + "\n")

    print("\n" + "=" * 90)
    print("FINAL DEEP LEADERBOARD")
    print("=" * 90)

    for rank, summary in enumerate(summaries, 1):
        print(
            f"{rank}. {summary['model']:<32} "
            f"score={summary['score']:>6.2f} | "
            f"LLM_verified="
            f"{summary['llm_verified']}/{summary['tests']} | "
            f"LLM_use="
            f"{summary['llm_use_rate']:.0%} | "
            f"avg="
            f"{summary['avg_latency_seconds']}s | "
            f"errors="
            f"{summary['error_rate']:.0%}"
        )

    print("\nFiles saved:")
    print(f"  {raw_path}")
    print(f"  {csv_path}")
    print(f"  {leaderboard_path}")
    print(f"  {report_path}")


if __name__ == "__main__":
    main()
