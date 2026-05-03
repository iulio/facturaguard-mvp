"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../api";

function badgeStyle(status: string): React.CSSProperties {
  const base: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    borderRadius: 999,
    padding: "4px 10px",
    fontSize: 12,
    fontWeight: 700,
  };

  if (status === "pass") return { ...base, background: "#dcfce7", color: "#166534" };
  if (status === "fail") return { ...base, background: "#fee2e2", color: "#991b1b" };
  return { ...base, background: "#fef3c7", color: "#92400e" };
}

const metricStyle: React.CSSProperties = {
  border: "1px solid #e5e7eb",
  borderRadius: 16,
  padding: 16,
  background: "#fff",
};

export default function DeploymentPage() {
  const [readiness, setReadiness] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    loadReadiness();
  }, []);

  async function loadReadiness() {
    setError("");
    try {
      setReadiness(await apiFetch("/deployment/readiness"));
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>Deployment readiness</h1>
          <p>Checklist runtime pentru Railway/producție: DB, storage, CORS, ANAF, NETOPIA și security.</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn secondary" onClick={loadReadiness}>Refresh</button>
          <a className="btn secondary" href="/">Dashboard</a>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {readiness && (
        <>
          <section className="card">
            <div className="header">
              <div>
                <h2>{readiness.app}</h2>
                <p>Version {readiness.version} · Environment {readiness.environment}</p>
              </div>
              <span style={badgeStyle(readiness.overall_status)}>
                {readiness.overall_status}
              </span>
            </div>

            <div className="grid grid-4">
              <div style={metricStyle}><b style={{ display: "block", fontSize: 28 }}>{readiness.summary.total}</b><span>Total</span></div>
              <div style={metricStyle}><b style={{ display: "block", fontSize: 28 }}>{readiness.summary.passed}</b><span>Passed</span></div>
              <div style={metricStyle}><b style={{ display: "block", fontSize: 28 }}>{readiness.summary.warnings}</b><span>Warnings</span></div>
              <div style={metricStyle}><b style={{ display: "block", fontSize: 28 }}>{readiness.summary.failed}</b><span>Failed</span></div>
            </div>
          </section>

          <section className="card" style={{ marginTop: 18 }}>
            <h2>Checks</h2>
            <div style={{ overflowX: "auto" }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Check</th>
                    <th>Severity</th>
                    <th>Message</th>
                  </tr>
                </thead>
                <tbody>
                  {readiness.checks.map((check: any) => (
                    <tr key={check.key}>
                      <td><span style={badgeStyle(check.status)}>{check.status}</span></td>
                      <td>{check.label}</td>
                      <td>{check.severity}</td>
                      <td>{check.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </main>
  );
}
