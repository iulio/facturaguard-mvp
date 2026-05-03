"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../api";

export default function InvoiceMetadataPage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [activeOrg, setActiveOrg] = useState<number | null>(null);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [activeInvoice, setActiveInvoice] = useState<any>(null);
  const [tags, setTags] = useState("");
  const [priority, setPriority] = useState("normal");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { loadOrganizations(); }, []);
  useEffect(() => { if (activeOrg) loadInvoices(activeOrg); }, [activeOrg]);

  async function loadOrganizations() {
    try {
      const data = await apiFetch("/organizations");
      setOrgs(data);
      if (data.length > 0) setActiveOrg(data[0].id);
    } catch (err: any) { setError(err.message); }
  }

  async function loadInvoices(orgId: number) {
    const data = await apiFetch(`/organizations/${orgId}/invoices`);
    setInvoices(data);
    if (data.length > 0) selectInvoice(data[0]);
  }

  function selectInvoice(invoice: any) {
    setActiveInvoice(invoice);
    setTags(invoice.tags || "");
    setPriority(invoice.priority || "normal");
  }

  async function saveMetadata() {
    if (!activeOrg || !activeInvoice) return;
    setError("");
    setMessage("");

    try {
      await apiFetch(`/organizations/${activeOrg}/invoices/${activeInvoice.id}/metadata`, {
        method: "PUT",
        body: JSON.stringify({ tags, priority }),
      });
      setMessage("Metadata salvată.");
      await loadInvoices(activeOrg);
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>Invoice tags & priority</h1>
          <p>Etichetează și prioritizează facturile pentru lucru operațional.</p>
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
          <select className="input" value={activeInvoice?.id || ""} onChange={(e) => selectInvoice(invoices.find((invoice) => invoice.id === Number(e.target.value)))}>
            {invoices.map((invoice) => (
              <option key={invoice.id} value={invoice.id}>
                {invoice.invoice_number} · {invoice.customer_name} · {invoice.priority || "normal"}
              </option>
            ))}
          </select>
        </div>
      </section>

      {activeInvoice && (
        <section className="card" style={{ marginTop: 18 }}>
          <h2>{activeInvoice.invoice_number}</h2>
          <label>
            Taguri, separate prin virgulă
            <input className="input" value={tags} onChange={(e) => setTags(e.target.value)} placeholder="urgent, client-important, verificare" />
          </label>
          <label>
            Prioritate
            <select className="input" value={priority} onChange={(e) => setPriority(e.target.value)}>
              <option value="low">low</option>
              <option value="normal">normal</option>
              <option value="high">high</option>
              <option value="urgent">urgent</option>
            </select>
          </label>
          <button className="btn" style={{ marginTop: 18 }} onClick={saveMetadata}>Salvează</button>
        </section>
      )}
    </main>
  );
}
