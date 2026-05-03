"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../api";

export default function ApiKeysPage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [activeOrg, setActiveOrg] = useState<number | null>(null);
  const [keys, setKeys] = useState<any[]>([]);
  const [name, setName] = useState("");
  const [createdKey, setCreatedKey] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { loadOrganizations(); }, []);
  useEffect(() => { if (activeOrg) loadKeys(activeOrg); }, [activeOrg]);

  async function loadOrganizations() {
    try {
      const data = await apiFetch("/organizations");
      setOrgs(data);
      if (data.length > 0) setActiveOrg(data[0].id);
    } catch (err: any) { setError(err.message); }
  }

  async function loadKeys(orgId: number) {
    setKeys(await apiFetch(`/organizations/${orgId}/api-keys`));
  }

  async function createKey() {
    if (!activeOrg) return;
    const data = await apiFetch(`/organizations/${activeOrg}/api-keys`, {
      method: "POST",
      body: JSON.stringify({ name: name || "ERP integration", scopes: "invoices:write" }),
    });
    setCreatedKey(data.raw_key);
    setName("");
    await loadKeys(activeOrg);
  }

  async function revokeKey(id: number) {
    if (!activeOrg) return;
    await apiFetch(`/organizations/${activeOrg}/api-keys/${id}/revoke`, { method: "POST" });
    await loadKeys(activeOrg);
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>API keys</h1>
          <p>Chei pentru integrări ERP sau automatizări externe.</p>
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
        <h2>Creează API key</h2>
        <div className="grid grid-2">
          <input className="input" placeholder="Nume cheie, ex: ERP" value={name} onChange={(e) => setName(e.target.value)} />
          <button className="btn" onClick={createKey}>Creează</button>
        </div>
        {createdKey && (
          <div className="card" style={{ marginTop: 18, boxShadow: "none" }}>
            <h3>Cheia nouă</h3>
            <p>Copieaz-o acum. Nu va mai fi afișată.</p>
            <pre style={{ whiteSpace: "pre-wrap" }}>{createdKey}</pre>
          </div>
        )}
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>Chei existente</h2>
        <table className="table">
          <thead><tr><th>Nume</th><th>Prefix</th><th>Scopes</th><th>Status</th><th>Ultima folosire</th><th></th></tr></thead>
          <tbody>
            {keys.map((key) => (
              <tr key={key.id}>
                <td>{key.name}</td>
                <td>{key.key_prefix}</td>
                <td>{key.scopes}</td>
                <td>{key.status}</td>
                <td>{key.last_used_at ? new Date(key.last_used_at).toLocaleString() : "-"}</td>
                <td><button className="btn secondary" onClick={() => revokeKey(key.id)}>Revocă</button></td>
              </tr>
            ))}
            {keys.length === 0 && <tr><td colSpan={6}>Nu există chei.</td></tr>}
          </tbody>
        </table>
      </section>
    </main>
  );
}
