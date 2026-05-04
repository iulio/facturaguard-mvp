"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../api";

function priorityStyle(priority: string): React.CSSProperties {
  const base: React.CSSProperties = {
    display: "inline-flex",
    borderRadius: 999,
    padding: "4px 10px",
    fontSize: 12,
    fontWeight: 700,
  };
  if (priority === "high") return { ...base, background: "#fee2e2", color: "#991b1b" };
  if (priority === "medium") return { ...base, background: "#fef3c7", color: "#92400e" };
  return { ...base, background: "#e0f2fe", color: "#075985" };
}

function cardStyle(): React.CSSProperties {
  return {
    border: "1px solid #e5e7eb",
    borderRadius: 16,
    padding: 16,
    background: "#fff",
  };
}

export default function PilotPage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [activeOrg, setActiveOrg] = useState<number | null>(null);
  const [workspace, setWorkspace] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    if (activeOrg) loadWorkspace(activeOrg);
  }, [activeOrg]);

  async function loadOrganizations() {
    try {
      const data = await apiFetch("/organizations");
      setOrgs(data);
      if (data.length > 0) setActiveOrg(data[0].id);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function loadWorkspace(orgId = activeOrg) {
    if (!orgId) return;
    setError("");
    try {
      setWorkspace(await apiFetch(`/organizations/${orgId}/pilot-workspace`));
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>Pilot workspace</h1>
          <p>Rezumat rapid pentru pregătirea unui pilot FacturaGuard: date, integrări, deployment și următorii pași.</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn secondary" onClick={() => loadWorkspace()}>Refresh</button>
          <a className="btn secondary" href="/">Dashboard</a>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      <section className="card">
        <h2>Firmă</h2>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {orgs.map((org) => (
            <button
              key={org.id}
              className={org.id === activeOrg ? "btn" : "btn secondary"}
              onClick={() => setActiveOrg(org.id)}
            >
              {org.name}
            </button>
          ))}
        </div>
      </section>

      {workspace && (
        <>
          <section className="card" style={{ marginTop: 18 }}>
            <div className="header">
              <div>
                <h2>{workspace.organization.name}</h2>
                <p>CUI: {workspace.organization.cui} · v{workspace.app.version} · {workspace.app.environment}</p>
              </div>
              <a className="btn" href="/onboarding">Onboarding {workspace.summary.onboarding_percent}%</a>
            </div>

            <div className="grid grid-4">
              <div style={cardStyle()}><b style={{ fontSize: 28 }}>{workspace.summary.invoice_count}</b><p>Facturi</p></div>
              <div style={cardStyle()}><b style={{ fontSize: 28 }}>{workspace.summary.document_count}</b><p>Documente</p></div>
              <div style={cardStyle()}><b style={{ fontSize: 28 }}>{workspace.summary.payment_count}</b><p>Plăți</p></div>
              <div style={cardStyle()}><b style={{ fontSize: 28 }}>{workspace.readiness_status}</b><p>Deployment</p></div>
            </div>
          </section>

          <section className="card" style={{ marginTop: 18 }}>
            <h2>Următorii pași</h2>
            <div style={{ display: "grid", gap: 12 }}>
              {workspace.next_actions.map((action: any, index: number) => (
                <div key={`${action.title}-${index}`} style={cardStyle()}>
                  <div className="header">
                    <div>
                      <h3>{action.title}</h3>
                      <p>{action.description}</p>
                    </div>
                    <span style={priorityStyle(action.priority)}>{action.priority}</span>
                  </div>
                  <a className="btn secondary" href={action.href}>Deschide</a>
                </div>
              ))}
            </div>
          </section>

          <section className="card" style={{ marginTop: 18 }}>
            <h2>Integrare și runtime</h2>
            <table className="table">
              <tbody>
                <tr><td><b>ANAF</b></td><td>{workspace.summary.anaf_mode}</td></tr>
                <tr><td><b>NETOPIA</b></td><td>{workspace.summary.netopia_provider}</td></tr>
                <tr><td><b>Deployment readiness</b></td><td>{workspace.readiness_status}</td></tr>
                <tr><td><b>Warnings</b></td><td>{workspace.readiness_summary.warnings}</td></tr>
                <tr><td><b>Failed</b></td><td>{workspace.readiness_summary.failed}</td></tr>
              </tbody>
            </table>
          </section>
        </>
      )}
    </main>
  );
}
