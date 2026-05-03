"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../api";

export default function InvoiceNotesPage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [activeOrg, setActiveOrg] = useState<number | null>(null);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [activeInvoice, setActiveInvoice] = useState<number | null>(null);
  const [notes, setNotes] = useState<any[]>([]);
  const [body, setBody] = useState("");
  const [isInternal, setIsInternal] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    if (activeOrg) loadInvoices(activeOrg);
  }, [activeOrg]);

  useEffect(() => {
    if (activeOrg && activeInvoice) loadNotes(activeOrg, activeInvoice);
  }, [activeOrg, activeInvoice]);

  async function loadOrganizations() {
    try {
      const data = await apiFetch("/organizations");
      setOrgs(data);
      if (data.length > 0) setActiveOrg(data[0].id);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function loadInvoices(orgId: number) {
    const data = await apiFetch(`/organizations/${orgId}/invoices`);
    setInvoices(data);
    if (data.length > 0) setActiveInvoice(data[0].id);
  }

  async function loadNotes(orgId: number, invoiceId: number) {
    setNotes(await apiFetch(`/organizations/${orgId}/invoices/${invoiceId}/notes`));
  }

  async function submitNote() {
    if (!activeOrg || !activeInvoice) return;
    setError("");
    setMessage("");

    try {
      await apiFetch(`/organizations/${activeOrg}/invoices/${activeInvoice}/notes`, {
        method: "POST",
        body: JSON.stringify({ body, is_internal: isInternal }),
      });
      setBody("");
      setIsInternal(false);
      setMessage("Nota a fost adăugată.");
      await loadNotes(activeOrg, activeInvoice);
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>Note facturi</h1>
          <p>Comentarii și colaborare pe facturi problematice.</p>
        </div>
        <a className="btn secondary" href="/">Dashboard</a>
      </div>

      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}

      <section className="grid grid-2">
        <div className="card">
          <h2>Firmă</h2>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {orgs.map((org) => (
              <button key={org.id} className={org.id === activeOrg ? "btn" : "btn secondary"} onClick={() => setActiveOrg(org.id)}>
                {org.name}
              </button>
            ))}
          </div>
        </div>

        <div className="card">
          <h2>Factură</h2>
          <select className="input" value={activeInvoice || ""} onChange={(e) => setActiveInvoice(Number(e.target.value))}>
            {invoices.map((invoice) => (
              <option key={invoice.id} value={invoice.id}>
                {invoice.invoice_number} · {invoice.customer_name} · {invoice.internal_status}
              </option>
            ))}
          </select>
        </div>
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>Adaugă notă</h2>
        <textarea className="input" rows={5} placeholder="Scrie o notă..." value={body} onChange={(e) => setBody(e.target.value)} />
        <label className="setting-row">
          <span>Notă internă</span>
          <input type="checkbox" checked={isInternal} onChange={(e) => setIsInternal(e.target.checked)} />
        </label>
        <button className="btn" onClick={submitNote}>Adaugă notă</button>
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>Note existente</h2>
        {notes.map((note) => (
          <div className="card" style={{ boxShadow: "none", marginBottom: 12 }} key={note.id}>
            <span className={`badge ${note.is_internal ? "medium" : "validated"}`}>{note.is_internal ? "internă" : "client-visible"}</span>
            <p>{note.body}</p>
            <small>{new Date(note.created_at).toLocaleString()} · user #{note.author_user_id || "system"}</small>
          </div>
        ))}
        {notes.length === 0 && <p>Nu există note pentru această factură.</p>}
      </section>
    </main>
  );
}
