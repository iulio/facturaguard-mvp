"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../api";

export default function IntegrationsPage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [activeOrg, setActiveOrg] = useState<number | null>(null);
  const [config, setConfig] = useState<any>(null);
  const [authorizations, setAuthorizations] = useState<any[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    if (activeOrg) {
      loadConfig(activeOrg);
      loadAuthorizations(activeOrg);
    }
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

  async function loadConfig(orgId: number) {
    try {
      setConfig(await apiFetch(`/organizations/${orgId}/integrations/anaf/config-check`));
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function loadAuthorizations(orgId: number) {
    try {
      setAuthorizations(await apiFetch(`/organizations/${orgId}/integrations/anaf/authorizations`));
    } catch {
      setAuthorizations([]);
    }
  }

  async function connectAnaf() {
    if (!activeOrg) return;
    setError("");
    setMessage("");

    try {
      const payload = await apiFetch(`/organizations/${activeOrg}/integrations/anaf/connect`);
      window.location.href = payload.authorization_url;
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function disconnectAnaf() {
    if (!activeOrg) return;
    await apiFetch(`/organizations/${activeOrg}/integrations/anaf/disconnect`, { method: "POST" });
    setMessage("Conectarea ANAF a fost dezactivată în FacturaGuard.");
    await loadAuthorizations(activeOrg);
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>Integrări</h1>
          <p>Conectare reală ANAF/SPV prin OAuth. Folosește întâi ANAF_ENV=test.</p>
        </div>
        <a className="btn secondary" href="/">Dashboard</a>
      </div>

      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}

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

      <section className="card" style={{ marginTop: 18 }}>
        <div className="header">
          <div>
            <h2>ANAF/SPV OAuth</h2>
            <p>Callback URL trebuie să fie identic cu cel configurat în portalul ANAF.</p>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn" onClick={connectAnaf}>Conectează ANAF</button>
            <button className="btn secondary" onClick={disconnectAnaf}>Deconectează</button>
          </div>
        </div>

        {config && (
          <table className="table">
            <tbody>
              <tr><td><b>Mode</b></td><td>{config.mode}</td></tr>
              <tr><td><b>Environment</b></td><td>{config.environment}</td></tr>
              <tr><td><b>Configured</b></td><td>{String(config.configured)}</td></tr>
              <tr><td><b>Auth base</b></td><td>{config.auth_base}</td></tr>
              <tr><td><b>API base</b></td><td>{config.api_base}</td></tr>
              <tr><td><b>Redirect URI</b></td><td>{config.redirect_uri || "-"}</td></tr>
              <tr><td><b>Missing variables</b></td><td>{config.missing_variables.join(", ") || "-"}</td></tr>
            </tbody>
          </table>
        )}
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>Autorizări ANAF</h2>
        <table className="table">
          <thead>
            <tr><th>CIF</th><th>Status</th><th>Token type</th><th>Expiră</th><th>Ultimul refresh</th></tr>
          </thead>
          <tbody>
            {authorizations.map((auth) => (
              <tr key={auth.id}>
                <td>{auth.authorized_cif}</td>
                <td>{auth.status}</td>
                <td>{auth.token_type}</td>
                <td>{auth.expires_at ? new Date(auth.expires_at).toLocaleString() : "-"}</td>
                <td>{auth.last_refresh_at ? new Date(auth.last_refresh_at).toLocaleString() : "-"}</td>
              </tr>
            ))}
            {authorizations.length === 0 && <tr><td colSpan={5}>Nu există autorizări ANAF încă.</td></tr>}
          </tbody>
        </table>
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>Înainte de deploy pe Railway</h2>
        <pre style={{ whiteSpace: "pre-wrap" }}>
{`ANAF_CONNECTOR_MODE=real
ANAF_ENV=test
ANAF_CLIENT_ID=...
ANAF_CLIENT_SECRET=...
ANAF_REDIRECT_URI=https://api.facturaguard.ro/integrations/anaf/oauth/callback
FRONTEND_BASE_URL=https://app.facturaguard.ro
TOKEN_ENCRYPTION_KEY=<fernet-key>`}
        </pre>
      </section>
    </main>
  );
}
