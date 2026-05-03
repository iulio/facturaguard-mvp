"use client";

import { useEffect, useState } from "react";
import { apiFetch, getToken } from "../api";

export default function SystemStatusPage() {
  const [status, setStatus] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    setError("");
    try {
      setStatus(await apiFetch("/system/status"));
    } catch (err: any) {
      setError(err.message);
    }
  }

  if (!getToken()) {
    return (
      <main className="container">
        <div className="card">
          <h1>System status</h1>
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
          <h1>System status</h1>
          <p>Diagnostic rapid pentru API, DB și configurare.</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn secondary" onClick={loadStatus}>Refresh</button>
          <a className="btn secondary" href="/">Dashboard</a>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {status && (
        <>
          <section className="grid grid-4">
            <Metric label="DB" value={status.database} />
            <Metric label="Versiune" value={status.app_version} />
            <Metric label="Environment" value={status.environment} />
            <Metric label="Storage" value={status.storage_backend} />
          </section>

          <section className="grid grid-4" style={{ marginTop: 18 }}>
            <Metric label="Firme" value={status.total_organizations} />
            <Metric label="Facturi" value={status.total_invoices} />
            <Metric label="Documente" value={status.total_documents} />
            <Metric label="Alerte deschise" value={status.total_open_alerts} />
          </section>

          <section className="card" style={{ marginTop: 18 }}>
            <h2>Config</h2>
            <table className="table">
              <tbody>
                <Row label="App" value={status.app_name} />
                <Row label="Scheduler" value={String(status.scheduler_enabled)} />
                <Row label="Email dry-run" value={String(status.email_dry_run)} />
                <Row label="ANAF connector" value={status.anaf_connector_mode} />
                <Row label="NETOPIA mock" value={String(status.netopia_mock_enabled)} />
                <Row label="Rate limit" value={String(status.rate_limit_enabled)} />
              </tbody>
            </table>
          </section>
        </>
      )}
    </main>
  );
}

function Metric({ label, value }: { label: string; value: any }) {
  return (
    <div className="card">
      <p>{label}</p>
      <h2>{value}</h2>
    </div>
  );
}

function Row({ label, value }: { label: string; value: any }) {
  return (
    <tr>
      <td><b>{label}</b></td>
      <td>{value}</td>
    </tr>
  );
}
