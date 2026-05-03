"""Basic API smoke test.

Usage:
    cd backend
    python scripts/smoke_test.py http://localhost:8000
"""
import sys
import time
import urllib.request
import urllib.error

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"

def get_json(path: str):
    url = f"{BASE_URL}{path}"
    with urllib.request.urlopen(url, timeout=10) as response:
        status = response.status
        body = response.read().decode("utf-8")
    return status, body

def main():
    checks = ["/health", "/ready", "/billing/plans"]

    for path in checks:
        try:
            status, body = get_json(path)
            print(f"[OK] {path} -> {status}")
            if status >= 400:
                raise SystemExit(f"Smoke test failed for {path}: {body}")
        except urllib.error.HTTPError as exc:
            raise SystemExit(f"[FAIL] {path} -> {exc.code}: {exc.read().decode('utf-8')}")
        except Exception as exc:
            raise SystemExit(f"[FAIL] {path}: {exc}")

    print("Smoke test passed.")

if __name__ == "__main__":
    main()
