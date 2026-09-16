import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]

MODELS = [
    "qwen3.5:9b",
    "gemma4:12b",
    "gpt-oss:20b",
    "mistral-small3.2:24b",
    "nemotron-3-nano:30b",
    "nemotron-3-nano:4b-q8_0",
]

TESTS = {
    "explanation": "Why is cell 283_522 currently at high risk?",
    "scenario": "What changes for cell 283_522 under the highest tested rainfall scenario?",
    "decision": "What should a field team prioritize for cell 283_522 right now, and why?",
}

BASE_ENV = os.environ.copy()
BASE_ENV.update({
    "AWAREON_AI_PROVIDER": "ollama",
    "AWAREON_AI_BASE_URL": "http://localhost:11434/api/chat",
    "AWAREON_AI_TIMEOUT_SECONDS": "240",
    "AWAREON_AI_MAX_RETRIES": "1",
    "AWAREON_AI_RETRY_BACKOFF_SECONDS": "1.0",
})

HOST = "127.0.0.1"
PORT = "8000"
BASE_URL = f"http://{HOST}:{PORT}"


def get_json(url, method="GET", payload=None, timeout=300):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(url, data=data, headers=headers, method=method)

    start = time.perf_counter()
    with urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    elapsed = time.perf_counter() - start

    return json.loads(body), elapsed


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
            PORT,
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.time() + 45

    while time.time() < deadline:
        try:
            data, _ = get_json(f"{BASE_URL}/health", timeout=3)
            if data.get("status") == "healthy":
                return process
        except Exception:
            time.sleep(1)

    process.kill()
    raise RuntimeError(f"Backend failed to start for {model}")


def stop_backend(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def extract_result(payload):
    memory = payload.get("memory", {})
    steps = memory.get("steps", [])

    model_started = False
    model_success = False
    model_used = False
    model_status = "UNKNOWN"

    for step in steps:
        if step.get("action") == "MODEL_REASONING":
            status = step.get("status")
            if status == "STARTED":
                model_started = True
                model_status = step.get("result_summary", status)
            elif status == "SUCCESS":
                model_success = True
            elif status == "REVIEW_REQUIRED":
                model_status = "REVIEW_REQUIRED"

        if (
            step.get("action") == "SYNTHESIS"
            and "model_used=" in step.get("result_summary", "")
        ):
            model_used = "model_used=True" in step["result_summary"]

    verification = payload.get("verification", {})

    return {
        "status": payload.get("status"),
        "model_started": model_started,
        "model_success": model_success,
        "model_used": model_used,
        "model_status": model_status,
        "verification_status": verification.get("status"),
        "verification_score": verification.get("score"),
        "answer": payload.get("answer", ""),
    }


def main():
    results = []

    for model in MODELS:
        print("\n" + "=" * 80)
        print(f"MODEL: {model}")
        print("=" * 80)

        process = None

        try:
            process = start_backend(model)
            print("Backend: READY")

            for test_name, query in TESTS.items():
                print(f"\n[{test_name}] {query}")

                try:
                    payload, latency = get_json(
                        f"{BASE_URL}/api/v1/intelligence/ask",
                        method="POST",
                        payload={
                            "query": query,
                            "session_id": f"fast-{model.replace(':', '-')}-{test_name}",
                        },
                        timeout=300,
                    )

                    extracted = extract_result(payload)

                    row = {
                        "model": model,
                        "test": test_name,
                        "latency_seconds": round(latency, 2),
                        **extracted,
                    }

                    results.append(row)

                    print(
                        f"  latency={latency:.2f}s | "
                        f"model_used={extracted['model_used']} | "
                        f"model_status={extracted['model_status']} | "
                        f"verification={extracted['verification_status']} "
                        f"({extracted['verification_score']})"
                    )

                except Exception as exc:
                    row = {
                        "model": model,
                        "test": test_name,
                        "error": str(exc),
                    }
                    results.append(row)
                    print(f"  ERROR: {exc}")

        except Exception as exc:
            print(f"MODEL ERROR: {exc}")

        finally:
            if process is not None:
                stop_backend(process)

    out = ROOT / "data" / "model_shootout_fast.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("\n" + "=" * 80)
    print("FAST MODEL SHOOTOUT COMPLETE")
    print("=" * 80)
    print(f"Saved: {out}")

    # Simple leaderboard
    leaderboard = []

    for model in MODELS:
        rows = [r for r in results if r.get("model") == model]
        valid = [r for r in rows if "error" not in r]

        if not valid:
            continue

        model_used_count = sum(1 for r in valid if r["model_used"])
        verified_count = sum(
            1 for r in valid
            if r["verification_status"] == "PASSED"
        )

        avg_latency = sum(
            r["latency_seconds"] for r in valid
        ) / len(valid)

        leaderboard.append({
            "model": model,
            "model_use_rate": model_used_count / len(valid),
            "verification_rate": verified_count / len(valid),
            "avg_latency": round(avg_latency, 2),
        })

    leaderboard.sort(
        key=lambda x: (
            x["verification_rate"],
            x["model_use_rate"],
            -x["avg_latency"],
        ),
        reverse=True,
    )

    print("\nLEADERBOARD")
    print("-" * 80)

    for i, row in enumerate(leaderboard, 1):
        print(
            f"{i}. {row['model']:<30} "
            f"verified={row['verification_rate']:.0%} | "
            f"LLM_used={row['model_use_rate']:.0%} | "
            f"avg={row['avg_latency']}s"
        )


if __name__ == "__main__":
    main()
