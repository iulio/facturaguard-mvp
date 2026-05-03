"use client";

import Link from "next/link";

const curlExample = `curl -X POST http://localhost:8000/public-api/v1/invoices \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: fg_your_api_key_here" \\
  -d '{
    "invoice_number": "ERP-1001",
    "issue_date": "2026-04-27",
    "customer_name": "Client ERP SRL",
    "customer_cui": "RO12345678",
    "total_amount": 1234.56,
    "currency": "RON",
    "anaf_status": "pending"
  }'`;

const jsExample = `async function createInvoice(apiKey) {
  const response = await fetch("http://localhost:8000/public-api/v1/invoices", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey,
    },
    body: JSON.stringify({
      invoice_number: "ERP-1001",
      issue_date: "2026-04-27",
      customer_name: "Client ERP SRL",
      customer_cui: "RO12345678",
      total_amount: 1234.56,
      currency: "RON",
      anaf_status: "pending",
    }),
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}`;

const pythonExample = `import requests

api_key = "fg_your_api_key_here"

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
    "http://localhost:8000/public-api/v1/invoices",
    headers={"X-API-Key": api_key},
    json=payload,
    timeout=10,
)

response.raise_for_status()
print(response.json())`;

export default function DeveloperPage() {
  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>Developer portal</h1>
          <p>Exemple rapide pentru integrarea ERP-urilor cu FacturaGuard Public API.</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <Link className="btn secondary" href="/api-keys">API keys</Link>
          <Link className="btn secondary" href="/">Dashboard</Link>
        </div>
      </div>

      <section className="grid grid-3">
        <div className="card">
          <h2>1. Creează API key</h2>
          <p>Din pagina API keys, creează o cheie cu scope:</p>
          <pre>invoices:write</pre>
        </div>
        <div className="card">
          <h2>2. Trimite factura</h2>
          <p>Folosește endpointul public pentru facturi:</p>
          <pre>POST /public-api/v1/invoices</pre>
        </div>
        <div className="card">
          <h2>3. Verifică dashboard</h2>
          <p>Factura apare în dashboard, work queue și audit log.</p>
        </div>
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>Endpoint</h2>
        <table className="table">
          <tbody>
            <tr><td><b>Method</b></td><td>POST</td></tr>
            <tr><td><b>URL</b></td><td>/public-api/v1/invoices</td></tr>
            <tr><td><b>Header</b></td><td>X-API-Key: fg_...</td></tr>
            <tr><td><b>Scope</b></td><td>invoices:write</td></tr>
          </tbody>
        </table>
      </section>

      <section className="grid grid-2" style={{ marginTop: 18 }}>
        <CodeCard title="cURL" code={curlExample} />
        <CodeCard title="JavaScript" code={jsExample} />
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <CodeCard title="Python" code={pythonExample} />
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>Payload fields</h2>
        <table className="table">
          <thead>
            <tr><th>Câmp</th><th>Tip</th><th>Obligatoriu</th><th>Descriere</th></tr>
          </thead>
          <tbody>
            <tr><td>invoice_number</td><td>string</td><td>da</td><td>Numărul facturii din ERP</td></tr>
            <tr><td>issue_date</td><td>date</td><td>da</td><td>Format ISO: YYYY-MM-DD</td></tr>
            <tr><td>customer_name</td><td>string</td><td>da</td><td>Numele clientului</td></tr>
            <tr><td>customer_cui</td><td>string</td><td>da</td><td>CUI client</td></tr>
            <tr><td>total_amount</td><td>number</td><td>da</td><td>Total factură</td></tr>
            <tr><td>currency</td><td>string</td><td>nu</td><td>Default: RON</td></tr>
            <tr><td>anaf_status</td><td>string</td><td>nu</td><td>Default: pending</td></tr>
            <tr><td>anaf_message</td><td>string</td><td>nu</td><td>Mesaj eroare/status, dacă există</td></tr>
          </tbody>
        </table>
      </section>
    </main>
  );
}

function CodeCard({ title, code }: { title: string; code: string }) {
  async function copyCode() {
    await navigator.clipboard.writeText(code);
  }

  return (
    <div className="card" style={{ boxShadow: "none" }}>
      <div className="header">
        <h2>{title}</h2>
        <button className="btn secondary" onClick={copyCode}>Copiază</button>
      </div>
      <pre style={{ whiteSpace: "pre-wrap", overflowX: "auto" }}>{code}</pre>
    </div>
  );
}
