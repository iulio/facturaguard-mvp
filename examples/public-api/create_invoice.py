import os
import requests

API_BASE = os.getenv("FACTURAGUARD_API_BASE", "http://localhost:8000")
API_KEY = os.getenv("FACTURAGUARD_API_KEY", "fg_your_api_key_here")

payload = {
    "invoice_number": "ERP-1001",
    "issue_date": "2026-04-27",
    "customer_name": "Client ERP SRL",
    "customer_cui": "RO12345678",
    "total_amount": 1234.56,
    "currency": "RON",
    "anaf_status": "pending",
}

response = requests.post(
    f"{API_BASE}/public-api/v1/invoices",
    headers={"X-API-Key": API_KEY},
    json=payload,
    timeout=10,
)

response.raise_for_status()
print(response.json())
