"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../api";

function statusStyle(done: boolean): React.CSSProperties {
  return {
    display: "inline-flex",
    borderRadius: 999,
    padding: "4px 10px",
    fontSize: 12,
    fontWeight: 700,
    background: done ? "#dcfce7" : "#fef3c7",
    color: done ? "#166534" : "#92400e",
  };
}

export default function OnboardingPage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [activeOrg, setActiveOrg] = useState<number | null>(null);
  const [checklist, setChecklist] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    if (activeOrg) loadChecklist(activeOrg);
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

  async function loadChecklist(orgId = activeOrg) {
    if (!orgId) return;
    setError("");
    try {
      setChecklist(await apiFetch(`/organizations/${orgId}/onboarding`));
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>Onboarding checklist</h1>
          <p>Pașii minimi pentru a duce FacturaGuard de la demo la pilot funcțional.</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn secondary" onClick={() => loadChecklist()}>Refresh</button>
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

      {checklist && (
        <>
          <section className="card" style={{ marginTop: 18 }}>
            <div className="header">
              <div>
                <h2>{checklist.organization_name}</h2>
                <p>{checklist.progress.done} din {checklist.progress.total} pași completați</p>
              </div>
              <div style={{ fontSize: 36, fontWeight: 800 }}>
                {checklist.progress.percent}%
              </div>
            </div>
            <div style={{ height: 12, borderRadius: 999, background: "#e5e7eb", overflow: "hidden" }}>
              <div
                style={{
                  width: `${checklist.progress.percent}%`,
                  height: "100%",
                  background: "#111827",
                }}
              />
            </div>
            {checklist.next_step && (
              <p style={{ marginTop: 16 }}>
                Următorul pas: <a href={checklist.next_step.href}><b>{checklist.next_step.title}</b></a>
              </p>
            )}
          </section>

          <section className="card" style={{ marginTop: 18 }}>
            <h2>Pași</h2>
            <div style={{ overflowX: "auto" }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Pas</th>
                    <th>Categorie</th>
                    <th>Descriere</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {checklist.steps.map((step: any) => (
                    <tr key={step.key}>
                      <td><span style={statusStyle(step.done)}>{step.done ? "done" : "todo"}</span></td>
                      <td><b>{step.title}</b></td>
                      <td>{step.category}</td>
                      <td>{step.description}</td>
                      <td><a className="btn secondary" href={step.href}>Deschide</a></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="card" style={{ marginTop: 18 }}>
            <h2>Context</h2>
            <pre style={{ whiteSpace: "pre-wrap", overflowX: "auto" }}>{JSON.stringify(checklist.context, null, 2)}</pre>
          </section>
        </>
      )}
    </main>
  );
}
