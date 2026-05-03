"use client";

import { useEffect, useState } from "react";
import { apiFetch, getToken } from "../api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function AuditPage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [active, setActive] = useState<number | null>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [filters, setFilters] = useState({ action: "", entity_type: "" });
  const [error, setError] = useState("");

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    if (active) {
      loadAudit(active);
      loadSummary(active);
    }
  }, [active]);

  async function loadOrganizations() {
    setError("");
    try {
      const data = await apiFetch("/organizations");
      setOrgs(data);
      if (data.length > 0) setActive(data[0].id);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function loadAudit(orgId = active) {
    if (!orgId) return;
    const params = new URLSearchParams();
    if (filters.action) params.set("action", filters.action);
    if (filters.entity_type) params.set("entity_type", filters.entity_type);
    params.set("limit", "200");
    const data = await apiFetch(`/organizations/${orgId}/audit-logs?${params.toString()}`);
    setLogs(data);
  }

  async function loadSummary(orgId = active) {
    if (!orgId) return;
    setSummary(await apiFetch(`/organizations/${orgId}/audit-summary`));
  }

  async function downloadAuditCsv() {
    if (!active) return;
    const token = getToken();
    const params = new URLSearchParams();
    if (filters.action) params.set("action", filters.action);
    if (filters.entity_type) params.set("entity_type", filters.entity_type);
    params.set("limit", "1000");

    const response = await fetch(`${API_BASE}/organizations/${active}/audit-logs/export.csv?${params.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      setError("Exportul audit nu a putut fi generat.");
      return;
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "facturaguard-audit.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>Audit log</h1>
          <p>Trasabilitate pentru acțiuni, documente, invitații, sync, plăți și exporturi.</p>
        </div>
        <a className="btn secondary" href="/">Dashboard</a>
      </div>

      {error && <p className="error">{error}</p>}

      <section className="card">
        <h2>Firmă</h2>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {orgs.map((org) => (
            <button
              key={org.id}
              className={org.id === active ? "btn" : "btn secondary"}
              onClick={() => setActive(org.id)}
            >
              {org.name}
            </button>
          ))}
        </div>
      </section>

      <section className="grid grid-4" style={{ marginTop: 18 }}>
        <Metric label="Evenimente" value={summary?.total_events ?? 0} />
        <Metric label="Tipuri acțiuni" value={summary?.by_action?.length ?? 0} />
        <Metric label="Tipuri entități" value={summary?.by_entity_type?.length ?? 0} />
        <Metric label="Recente" value={summary?.recent_events?.length ?? 0} />
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <div className="header">
          <h2>Filtre</h2>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn secondary" onClick={() => active && loadAudit(active)}>Aplică</button>
            <button className="btn secondary" onClick={downloadAuditCsv}>Export CSV</button>
          </div>
        </div>
        <div className="grid grid-2">
          <input
            className="input"
            placeholder="Filtru acțiune, ex: payment, document, invitation"
            value={filters.action}
            onChange={(e) => setFilters({ ...filters, action: e.target.value })}
          />
          <input
            className="input"
            placeholder="Entity type, ex: invoice, organization_document"
            value={filters.entity_type}
            onChange={(e) => setFilters({ ...filters, entity_type: e.target.value })}
          />
        </div>
      </section>

      <section className="grid grid-2" style={{ marginTop: 18 }}>
        <div className="card">
          <h2>Top acțiuni</h2>
          <table className="table">
            <tbody>
              {(summary?.by_action ?? []).slice(0, 8).map((item: any) => (
                <tr key={item.action}>
                  <td>{item.action}</td>
                  <td>{item.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h2>Top entități</h2>
          <table className="table">
            <tbody>
              {(summary?.by_entity_type ?? []).slice(0, 8).map((item: any) => (
                <tr key={item.entity_type}>
                  <td>{item.entity_type}</td>
                  <td>{item.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>Evenimente</h2>
        <div style={{ overflowX: "auto" }}>
          <table className="table">
            <thead>
              <tr>
                <th>Data</th>
                <th>Acțiune</th>
                <th>Entitate</th>
                <th>Mesaj</th>
                <th>Actor</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.created_at).toLocaleString()}</td>
                  <td>{log.action}</td>
                  <td>{log.entity_type || "-"}</td>
                  <td>{log.message}</td>
                  <td>{log.actor_user_id || "system"}</td>
                </tr>
              ))}
              {logs.length === 0 && <tr><td colSpan={5}>Nu există evenimente.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
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
