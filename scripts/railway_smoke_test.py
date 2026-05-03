#!/usr/bin/env python3
"""Post-deploy smoke test for FacturaGuard on Railway.

Usage:

    python scripts/railway_smoke_test.py \
      --backend https://your-backend.up.railway.app \
      --frontend https://your-frontend.up.railway.app

Optional deeper test that writes demo data:

    python scripts/railway_smoke_test.py \
      --backend https://your-backend.up.railway.app \
      --frontend https://your-frontend.up.railway.app \
      --include-auth-flow

This script uses only Python stdlib.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

@dataclass
class SmokeContext:
    backend: str
    frontend: str | None
    timeout: int
    token: str | None = None

def normalize_url(value: str | None) -> str | None:
    if not value:
        return None
    return value.rstrip("/")

def request(
    method: str,
    url: str,
    *,
    timeout: int,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
) -> tuple[int, str, dict]:
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read().decode("utf-8", errors="replace")
            return response.status, content, dict(response.headers)
    except urllib.error.HTTPError as exc:
        content = exc.read().decode("utf-8", errors="replace")
        return exc.code, content, dict(exc.headers)

def json_request(
    ctx: SmokeContext,
    method: str,
    path: str,
    payload: dict | None = None,
    *,
    auth: bool = False,
) -> tuple[int, dict | str]:
    headers = {"Content-Type": "application/json"}
    if auth:
        if not ctx.token:
            raise RuntimeError("Auth token missing.")
        headers["Authorization"] = f"Bearer {ctx.token}"

    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    status, text, _ = request(method, f"{ctx.backend}{path}", timeout=ctx.timeout, headers=headers, body=body)

    try:
        return status, json.loads(text)
    except Exception:
        return status, text

def multipart_upload(
    ctx: SmokeContext,
    path: str,
    field_name: str,
    filename: str,
    content: bytes,
    content_type: str = "text/csv",
) -> tuple[int, dict | str]:
    if not ctx.token:
        raise RuntimeError("Auth token missing.")

    boundary = f"----FacturaGuardSmoke{secrets.token_hex(12)}"
    parts = [
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode(),
        f"Content-Type: {content_type}\r\n\r\n".encode(),
        content,
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    body = b"".join(parts)

    headers = {
        "Authorization": f"Bearer {ctx.token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    status, text, _ = request("POST", f"{ctx.backend}{path}", timeout=ctx.timeout, headers=headers, body=body)

    try:
        return status, json.loads(text)
    except Exception:
        return status, text

def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"[OK] {name}{': ' + detail if detail else ''}")
    else:
        print(f"[FAIL] {name}{': ' + detail if detail else ''}")
        raise SystemExit(1)

def check_backend_basic(ctx: SmokeContext) -> None:
    print("\n== Backend basic checks ==")
    for path in ["/health", "/ready", "/templates/invoices.csv", "/templates/invoices.xml"]:
        status, text, _ = request("GET", f"{ctx.backend}{path}", timeout=ctx.timeout)
        check(path, status == 200, f"status={status}")

    status, text, _ = request("GET", f"{ctx.backend}/docs", timeout=ctx.timeout)
    check("/docs", status in {200, 307, 308}, f"status={status}")

def check_frontend_basic(ctx: SmokeContext) -> None:
    if not ctx.frontend:
        return

    print("\n== Frontend basic checks ==")
    for path in ["/", "/landing", "/pricing", "/roi", "/help", "/templates"]:
        status, text, _ = request("GET", f"{ctx.frontend}{path}", timeout=ctx.timeout)
        check(path, status == 200, f"status={status}")

def check_auth_flow(ctx: SmokeContext) -> None:
    print("\n== Auth/org/upload smoke flow ==")

    stamp = int(time.time())
    email = f"smoke-{stamp}@facturaguard.local"
    password = f"SmokePassword{stamp}!"

    status, payload = json_request(
        ctx,
        "POST",
        "/auth/register",
        {
            "name": "Railway Smoke User",
            "email": email,
            "password": password,
        },
    )
    check("register", status == 200, f"status={status}")

    status, payload = json_request(
        ctx,
        "POST",
        "/auth/login",
        {
            "email": email,
            "password": password,
        },
    )
    check("login", status == 200 and isinstance(payload, dict) and "access_token" in payload, f"status={status}")
    ctx.token = payload["access_token"]

    cui = f"RO{stamp % 100000000:08d}"
    status, org = json_request(
        ctx,
        "POST",
        "/organizations",
        {
            "name": f"Railway Smoke SRL {stamp}",
            "cui": cui,
            "address": "Railway Smoke Street 1",
        },
        auth=True,
    )
    check("create organization", status == 200 and isinstance(org, dict) and "id" in org, f"status={status}")
    org_id = org["id"]

    csv_content = (
        "invoice_number,issue_date,customer_name,customer_cui,total_amount,currency,anaf_status,anaf_message\n"
        f"SMOKE-{stamp},2026-04-27,Client Smoke SRL,RO12345678,123.45,RON,pending,\n"
    ).encode("utf-8")

    status, invoices = multipart_upload(
        ctx,
        f"/organizations/{org_id}/invoices/upload",
        "file",
        "railway-smoke.csv",
        csv_content,
        "text/csv",
    )
    check("upload CSV", status == 200 and isinstance(invoices, list) and len(invoices) >= 1, f"status={status}")
    invoice_id = invoices[0]["id"]

    status, dashboard = json_request(ctx, "GET", f"/organizations/{org_id}/dashboard", auth=True)
    check("dashboard", status == 200 and isinstance(dashboard, dict), f"status={status}")

    status, ubl = json_request(ctx, "GET", f"/organizations/{org_id}/invoices/{invoice_id}/ubl-preview", auth=True)
    check("UBL preview", status == 200 and isinstance(ubl, dict) and "xml" in ubl, f"status={status}")

    status, system = json_request(ctx, "GET", "/system/status", auth=True)
    check("system status", status == 200 and isinstance(system, dict), f"status={status}")

    print(f"\nCreated smoke test user: {email}")
    print("You can delete this user/org later from the database if needed.")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", required=True, help="Railway backend URL, e.g. https://api.up.railway.app")
    parser.add_argument("--frontend", default=None, help="Railway frontend URL, e.g. https://app.up.railway.app")
    parser.add_argument("--timeout", default=20, type=int)
    parser.add_argument("--include-auth-flow", action="store_true", help="Create smoke user/org and upload sample CSV")
    args = parser.parse_args()

    ctx = SmokeContext(
        backend=normalize_url(args.backend) or "",
        frontend=normalize_url(args.frontend),
        timeout=args.timeout,
    )

    print("FacturaGuard Railway smoke test")
    print(f"Backend:  {ctx.backend}")
    print(f"Frontend: {ctx.frontend or '-'}")

    check_backend_basic(ctx)
    check_frontend_basic(ctx)

    if args.include_auth_flow:
        check_auth_flow(ctx)

    print("\nAll selected smoke checks passed.")

if __name__ == "__main__":
    main()
