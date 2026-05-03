"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../api";

export default function WorkQueuePage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [activeOrg, setActiveOrg] = useState<number | null>(null);
  const [queue, setQueue] = useState<any>(null);
  const [filters, setFilters] = useState({ status: "", priority: "", tag: "" });
  const [error, setError] = useState("");

  useEffect(() => { loadOrganizations(); }, []);
  useEffect(() => { if (activeOrg) loadQueue(activeOrg); }, [activeOrg]);

  async function loadOrganizations() {
    try {
      const data = await apiFetch("/organizations");
      setOrgs(data);
      if (data.length > 0) setActiveOrg(data[0].id);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function loadQueue(orgId = activeOrg) {
    if (!orgId) return;
    const params = new URLSearchParams();
    if (filters.status) params.set("status", filters.status);
    if (filters.priority) params.set("priority", filters.priority);
    if (filters.tag) params.set("tag", filters.tag);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    setQueue(await apiFetch(`/organizations/${orgId}/work-queue${suffix}`));
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>Work queue</h1>
          <p>Facturi operaționale care necesită atenție.</p>
        </div>
        <a className="btn secondary" href="/">Dashboard</a>
      </div>

      {error && <p className="error">{error}</p>}

      <section className="card">
        <h2>Firmă</h2>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {orgs.map((org) => (
            <button key={org.id} className={org.id === activeOrg ? "btn" : "btn secondary"} onClick={() => setActiveOrg(org.id)}>
              {org.name}
            </button>
          ))}
        </div>
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <div className="header">
          <h2>Filtre</h2>
          <button className="btn secondary" onClick={() => loadQueue()}>Aplică</button>
        </div>
        <div className="grid grid-3">
          <select className="input" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <option value="">Statusuri de lucru</option>
            <option value="rejected">rejected</option>
            <option value="overdue">overdue</option>
            <option value="near_deadline">near_deadline</option>
            <option value="unsent">unsent</option>
            <option value="pending">pending</option>
          </select>
          <select className="input" value={filters.priority} onChange={(e) => setFilters({ ...filters, priority: e.target.value })}>
            <option value="">Toate prioritățile</option>
            <option value="urgent">urgent</option>
            <option value="high">high</option>
            <option value="normal">normal</option>
            <option value="low">low</option>
          </select>
          <input className="input" placeholder="tag, ex: urgent" value={filters.tag} onChange={(e) => setFilters({ ...filters, tag: e.target.value })} />
        </div>
      </section>

      {queue && (
        <>
          <section className="grid grid-4" style={{ marginTop: 18 }}>
            <Metric label="În queue" value={queue.total} />
            <Metric label="Urgent" value={queue.urgent} />
            <Metric label="Respinse" value={queue.rejected} />
            <Metric label="Depășite" value={queue.overdue} />
          </section>

          <section className="card" style={{ marginTop: 18 }}>
            <h2>Facturi</h2>
            <div style={{ overflowX: "auto" }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Factură</th>
                    <th>Client</th>
                    <th>Status</th>
                    <th>Prioritate</th>
                    <th>Taguri</th>
                    <th>Deadline</th>
                  </tr>
                </thead>
                <tbody>
                  {queue.invoices.map((invoice: any) => (
                    <tr key={invoice.id}>
                      <td>{invoice.invoice_number}</td>
                      <td>{invoice.customer_name}</td>
                      <td><span className={`badge ${invoice.internal_status}`}>{invoice.internal_status}</span></td>
                      <td><span className={`badge ${invoice.priority === "urgent" ? "high" : invoice.priority === "high" ? "medium" : "validated"}`}>{invoice.priority}</span></td>
                      <td>{invoice.tags || "-"}</td>
                      <td>{invoice.due_submission_date}</td>
                    </tr>
                  ))}
                  {queue.invoices.length === 0 && <tr><td colSpan={6}>Nu există facturi în queue.</td></tr>}
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
