"use client";

import { useEffect, useState } from "react";
import { apiFetch, getToken } from "../api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function ClientPortalPage() {
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [active, setActive] = useState<number | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    loadPortal();
  }, []);

  useEffect(() => {
    if (active) loadDetail(active);
  }, [active]);

  async function loadPortal() {
    setError("");
    try {
      const data = await apiFetch("/client-portal");
      setOrganizations(data.organizations);
      if (data.organizations.length > 0) setActive(data.organizations[0].id);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function loadDetail(orgId: number) {
    try {
      setDetail(await apiFetch(`/client-portal/organizations/${orgId}`));
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function downloadDocument(documentId: number, filename: string) {
    if (!active) return;
    const token = getToken();
    const response = await fetch(`${API_BASE}/organizations/${active}/documents/${documentId}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      setError("Documentul nu a putut fi descărcat.");
      return;
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  if (!getToken()) {
    return (
      <main className="container">
        <div className="card">
          <h1>Portal client</h1>
          <p>Trebuie să fii autentificat.</p>
          <a className="btn" href="/">Login</a>
        </div>
      </main>
    );
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>Portal client</h1>
          <p>Vizualizare read-only pentru facturi, alerte și documente.</p>
        </div>
        <a className="btn secondary" href="/">Dashboard</a>
      </div>

      {error && <p className="error">{error}</p>}

      <section className="card">
        <h2>Firmele mele</h2>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {organizations.map((org) => (
            <button
              key={org.id}
              className={org.id === active ? "btn" : "btn secondary"}
              onClick={() => setActive(org.id)}
            >
              {org.name}
            </button>
          ))}
        </div>
        {organizations.length === 0 && <p>Nu ai acces la nicio firmă încă.</p>}
      </section>

      {detail && (
        <>
          <section className="grid grid-4" style={{ marginTop: 18 }}>
            <Metric label="Facturi" value={detail.organization.total_invoices} />
            <Metric label="Alerte" value={detail.organization.open_alerts} />
            <Metric label="Respinse" value={detail.organization.rejected} />
            <Metric label="Depășite" value={detail.organization.overdue} />
          </section>

          <section className="card" style={{ marginTop: 18 }}>
            <h2>Alerte deschise</h2>
            {detail.open_alerts.map((alert: any) => (
              <div key={alert.id} className="card" style={{ boxShadow: "none", marginBottom: 12 }}>
                <span className={`badge ${alert.severity}`}>{alert.severity}</span>
                <h3>{alert.title}</h3>
                <p>{alert.message}</p>
              </div>
            ))}
            {detail.open_alerts.length === 0 && <p>Nu există alerte deschise.</p>}
          </section>

          <section className="card" style={{ marginTop: 18 }}>
            <h2>Facturi recente</h2>
            <div style={{ overflowX: "auto" }}>
              <table className="table">
                <thead><tr><th>Număr</th><th>Data</th><th>Client</th><th>Total</th><th>Status</th></tr></thead>
                <tbody>
                  {detail.recent_invoices.map((invoice: any) => (
                    <tr key={invoice.id}>
                      <td>{invoice.invoice_number}</td>
                      <td>{invoice.issue_date}</td>
                      <td>{invoice.customer_name}</td>
                      <td>{invoice.total_amount} {invoice.currency}</td>
                      <td><span className={`badge ${invoice.internal_status}`}>{invoice.internal_status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="card" style={{ marginTop: 18 }}>
            <h2>Documente</h2>
            <div style={{ overflowX: "auto" }}>
              <table className="table">
                <thead><tr><th>Fișier</th><th>Tip</th><th>Mărime</th><th>Acțiune</th></tr></thead>
                <tbody>
                  {detail.documents.map((doc: any) => (
                    <tr key={doc.id}>
                      <td>{doc.original_filename}</td>
                      <td>{doc.document_type}</td>
                      <td>{doc.file_size} bytes</td>
                      <td><button className="btn secondary" onClick={() => downloadDocument(doc.id, doc.original_filename)}>Download</button></td>
                    </tr>
                  ))}
                  {detail.documents.length === 0 && <tr><td colSpan={4}>Nu există documente.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="card">
      <p>{label}</p>
      <h2>{value}</h2>
    </div>
  );
}
