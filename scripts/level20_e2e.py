from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8000"


def get(path: str) -> object:
    with urlopen(f"{BASE}{path}", timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def post(path: str, payload: dict) -> object:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        f"{BASE}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def check(label: str, fn) -> bool:
    try:
        value = fn()
        ok = isinstance(value, dict)
        if label == "health":
            ok = ok and value.get("status") == "healthy"
        elif label == "risk":
            ok = ok and isinstance(value.get("data"), list) and len(value["data"]) > 0
        elif label == "regional":
            ok = ok and value.get("success") is True and value.get("status") == "READY"
        elif label == "scenario":
            ok = ok and value.get("success") is True and value.get("status") == "READY"
        elif label == "ood":
            ok = ok and value.get("success") is True and value.get("status") == "OUTSIDE_DOMAIN"
        print(f"{label:12} | {'PASS' if ok else 'FAIL'}")
        return ok
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        print(f"{label:12} | FAIL | {exc}")
        return False


def main() -> int:
    print("=" * 72)
    print("AWAREON LEVEL 20 E2E QA")
    print("=" * 72)
    tests = [
        ("health", lambda: get("/health")),
        ("risk", lambda: get("/api/v1/risk")),
        ("regional", lambda: post("/api/v1/intelligence/ask", {"query": "What is the current situation of landslides in Sikkim?", "session_id": "level20"})),
        ("scenario", lambda: post("/api/v1/intelligence/ask", {"query": "What happens under +100% rainfall?", "session_id": "level20"})),
        ("ood", lambda: post("/api/v1/intelligence/ask", {"query": "Give me a recipe for chocolate cake", "session_id": "level20"})),
    ]
    passed = sum(check(label, fn) for label, fn in tests)
    print("-" * 72)
    print(f"RESULT: {passed}/{len(tests)}")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
