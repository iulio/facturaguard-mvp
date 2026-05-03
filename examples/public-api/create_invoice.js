const API_BASE = process.env.FACTURAGUARD_API_BASE || "http://localhost:8000";
const API_KEY = process.env.FACTURAGUARD_API_KEY || "fg_your_api_key_here";

async function main() {
  const payload = {
    invoice_number: "ERP-1001",
    issue_date: "2026-04-27",
    customer_name: "Client ERP SRL",
    customer_cui: "RO12345678",
    total_amount: 1234.56,
    currency: "RON",
    anaf_status: "pending",
  };

  const response = await fetch(`${API_BASE}/public-api/v1/invoices`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  console.log(await response.json());
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
