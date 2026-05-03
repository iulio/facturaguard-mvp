"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../api";

export default function SettingsPage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [active, setActive] = useState<number | null>(null);
  const [settings, setSettings] = useState<any>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    if (active) loadSettings(active);
  }, [active]);

  async function loadOrganizations() {
    try {
      const data = await apiFetch("/organizations");
      setOrgs(data);
      if (data.length > 0) setActive(data[0].id);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function loadSettings(orgId: number) {
    try {
      setSettings(await apiFetch(`/organizations/${orgId}/notification-settings`));
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function saveSettings() {
    if (!active || !settings) return;
    setMessage("");
    setError("");

    try {
      const payload = {
        email_alerts_enabled: settings.email_alerts_enabled,
        alert_email: settings.alert_email || null,
        send_rejected_alerts: settings.send_rejected_alerts,
        send_overdue_alerts: settings.send_overdue_alerts,
        send_near_deadline_alerts: settings.send_near_deadline_alerts,
        near_deadline_days: Number(settings.near_deadline_days || 2),
        daily_digest_enabled: settings.daily_digest_enabled,
      };

      const updated = await apiFetch(`/organizations/${active}/notification-settings`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      setSettings(updated);
      setMessage("Setările au fost salvate.");
    } catch (err: any) {
      setError(err.message);
    }
  }

  function setField(field: string, value: any) {
    setSettings({ ...settings, [field]: value });
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>Setări notificări</h1>
          <p>Controlează emailurile de alertă pentru fiecare firmă.</p>
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
              className={org.id === active ? "btn" : "btn secondary"}
              onClick={() => setActive(org.id)}
            >
              {org.name}
            </button>
          ))}
        </div>
      </section>

      {settings && (
        <section className="card" style={{ marginTop: 18 }}>
          <h2>Email alerts</h2>

          <label className="setting-row">
            <span>Activează email alerts</span>
            <input type="checkbox" checked={settings.email_alerts_enabled} onChange={(e) => setField("email_alerts_enabled", e.target.checked)} />
          </label>

          <label>
            Email alertă
            <input className="input" value={settings.alert_email || ""} onChange={(e) => setField("alert_email", e.target.value)} placeholder="contabil@firma.ro" />
          </label>

          <label className="setting-row">
            <span>Trimite alerte pentru facturi respinse</span>
            <input type="checkbox" checked={settings.send_rejected_alerts} onChange={(e) => setField("send_rejected_alerts", e.target.checked)} />
          </label>

          <label className="setting-row">
            <span>Trimite alerte pentru facturi depășite</span>
            <input type="checkbox" checked={settings.send_overdue_alerts} onChange={(e) => setField("send_overdue_alerts", e.target.checked)} />
          </label>

          <label className="setting-row">
            <span>Trimite alerte pentru facturi aproape de termen</span>
            <input type="checkbox" checked={settings.send_near_deadline_alerts} onChange={(e) => setField("send_near_deadline_alerts", e.target.checked)} />
          </label>

          <label>
            Prag near deadline, zile
            <input className="input" type="number" min={1} max={14} value={settings.near_deadline_days} onChange={(e) => setField("near_deadline_days", e.target.value)} />
          </label>

          <label className="setting-row">
            <span>Digest zilnic, pregătit pentru versiune viitoare</span>
            <input type="checkbox" checked={settings.daily_digest_enabled} onChange={(e) => setField("daily_digest_enabled", e.target.checked)} />
          </label>

          <button className="btn" style={{ marginTop: 18 }} onClick={saveSettings}>Salvează setările</button>
        </section>
      )}
    </main>
  );
}
