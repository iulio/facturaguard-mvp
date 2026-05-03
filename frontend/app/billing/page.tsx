"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../api";

export default function BillingPage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [activeOrg, setActiveOrg] = useState<number | null>(null);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [config, setConfig] = useState<any>(null);
  const [statusResult, setStatusResult] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    loadOrganizations();
    loadConfig();
  }, []);

  useEffect(() => {
    if (activeOrg) loadTransactions(activeOrg);
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

  async function loadConfig() {
    try {
      setConfig(await apiFetch("/billing/netopia/config-check"));
    } catch {
      setConfig(null);
    }
  }

  async function loadTransactions(orgId = activeOrg) {
    if (!orgId) return;
    setTransactions(await apiFetch(`/organizations/${orgId}/billing/transactions`));
  }

  async function checkStatus(transactionId: number) {
    if (!activeOrg) return;
    setError("");
    setStatusResult(null);

    try {
      const result = await apiFetch(`/organizations/${activeOrg}/billing/transactions/${transactionId}/status-check`, {
        method: "POST",
      });
      setStatusResult(result);
      await loadTransactions(activeOrg);
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>Billing</h1>
          <p>Tranzacții NETOPIA, statusuri și reconciliere manuală.</p>
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

      {config && (
        <section className="card" style={{ marginTop: 18 }}>
          <h2>NETOPIA config</h2>
          <table className="table">
            <tbody>
              <tr><td><b>Provider</b></td><td>{config.provider}</td></tr>
              <tr><td><b>Mode</b></td><td>{config.mode}</td></tr>
              <tr><td><b>Configured</b></td><td>{String(config.configured)}</td></tr>
              <tr><td><b>Base URL</b></td><td>{config.base_url}</td></tr>
              <tr><td><b>Missing</b></td><td>{config.missing_variables?.join(", ") || "-"}</td></tr>
            </tbody>
          </table>
        </section>
      )}

      {statusResult && (
        <section className="card" style={{ marginTop: 18 }}>
          <h2>Rezultat status check</h2>
          <p><b>Previous:</b> {statusResult.previous_status}</p>
          <p><b>Current:</b> {statusResult.current_status}</p>
          <p><b>Provider status:</b> {statusResult.provider_status || "-"}</p>
          <p><b>Changed:</b> {String(statusResult.changed)}</p>
          <p>{statusResult.message}</p>
        </section>
      )}

      <section className="card" style={{ marginTop: 18 }}>
        <div className="header">
          <h2>Tranzacții</h2>
          <button className="btn secondary" onClick={() => loadTransactions()}>Refresh</button>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Provider</th>
                <th>Plan</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Order ID</th>
                <th>Payment ID</th>
                <th>Creată</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <tr key={tx.id}>
                  <td>{tx.id}</td>
                  <td>{tx.provider}</td>
                  <td>{tx.plan_code}</td>
                  <td>{tx.amount_eur} {tx.currency}</td>
                  <td>{tx.status}</td>
                  <td>{tx.provider_order_id || tx.provider_session_id}</td>
                  <td>{tx.provider_payment_id || "-"}</td>
                  <td>{new Date(tx.created_at).toLocaleString()}</td>
                  <td><button className="btn secondary" onClick={() => checkStatus(tx.id)}>Status check</button></td>
                </tr>
              ))}
              {transactions.length === 0 && <tr><td colSpan={9}>Nu există tranzacții.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
