"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, FileText, LogOut, UploadCloud, BellRing } from "lucide-react";
import { apiFetch, clearToken, getToken, setToken } from "./api";

export default function Home() {
  const [ready, setReady] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("register");
  const [auth, setAuth] = useState({ name: "", email: "", password: "" });
  const [orgForm, setOrgForm] = useState({ name: "", cui: "", address: "" });
  const [orgs, setOrgs] = useState<any[]>([]);
  const [active, setActive] = useState<number | null>(null);
  const [summary, setSummary] = useState<any>(null);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => { setAuthed(Boolean(getToken())); setReady(true); }, []);
  useEffect(() => { if (authed) loadOrganizations(); }, [authed]);
  useEffect(() => { if (active) refresh(active); }, [active]);

  async function refresh(id: number) {
    await Promise.all([loadDashboard(id), loadInvoices(id), loadAlerts(id)]);
  }

  async function submitAuth(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setMsg("");
    try {
      const path = mode === "register" ? "/auth/register" : "/auth/login";
      const body = mode === "register" ? auth : { email: auth.email, password: auth.password };
      const data = await apiFetch(path, { method: "POST", body: JSON.stringify(body) });
      setToken(data.access_token); setAuthed(true); setMsg("Autentificare reușită.");
    } catch (x: any) { setErr(x.message); }
  }

  async function loadOrganizations() {
    const data = await apiFetch("/organizations");
    setOrgs(data);
    if (data.length && !active) setActive(data[0].id);
  }

  async function createOrg(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setMsg("");
    try {
      const org = await apiFetch("/organizations", { method: "POST", body: JSON.stringify(orgForm) });
      setOrgs([...orgs, org]); setActive(org.id); setOrgForm({ name: "", cui: "", address: "" });
    } catch (x: any) { setErr(x.message); }
  }

  async function loadDashboard(id: number) { setSummary(await apiFetch(`/organizations/${id}/dashboard`)); }
  async function loadInvoices(id: number) { setInvoices(await apiFetch(`/organizations/${id}/invoices`)); }
  async function loadAlerts(id: number) { setAlerts(await apiFetch(`/organizations/${id}/alerts`)); }

  async function uploadFile(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault(); setErr(""); setMsg("");
    if (!active) { setErr("Creează sau selectează o firmă înainte de upload."); return; }
    const input = e.currentTarget.elements.namedItem("file") as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) { setErr("Alege un fișier CSV, XML sau ZIP."); return; }
    try {
      const fd = new FormData(); fd.append("file", file);
      await apiFetch(`/organizations/${active}/invoices/upload`, { method: "POST", body: fd });
      input.value = ""; setMsg("Facturile au fost importate."); await refresh(active);
    } catch (x: any) { setErr(x.message); }
  }

  async function runStatusCheck() {
    if (!active) return;
    const data = await apiFetch("/jobs/run-status-check", { method: "POST" });
    setMsg(`Verificare rulată: ${data.checked} facturi, ${data.changed} statusuri schimbate.`);
    await refresh(active);
  }

  function logout() { clearToken(); setAuthed(false); setOrgs([]); setInvoices([]); setAlerts([]); setSummary(null); setActive(null); }

  if (!ready) return null;

  if (!authed) {
    return (
      <main className="container">
        <h1>FacturaGuard MVP</h1>
        <div className="card" style={{ maxWidth: 520 }}>
          <h2>{mode === "register" ? "Creează cont" : "Login"}</h2>
          <form onSubmit={submitAuth} className="grid">
            {mode === "register" && <input className="input" placeholder="Nume" value={auth.name} onChange={(e) => setAuth({ ...auth, name: e.target.value })} />}
            <input className="input" placeholder="Email" type="email" value={auth.email} onChange={(e) => setAuth({ ...auth, email: e.target.value })} />
            <input className="input" placeholder="Parolă" type="password" value={auth.password} onChange={(e) => setAuth({ ...auth, password: e.target.value })} />
            <button className="btn" type="submit">{mode === "register" ? "Creează cont" : "Intră în cont"}</button>
          </form>
          <button className="btn secondary" style={{ marginTop: 12 }} onClick={() => setMode(mode === "register" ? "login" : "register")}>
            {mode === "register" ? "Am deja cont" : "Creează cont nou"}
          </button>
          {err && <p className="error">{err}</p>}
          {msg && <p className="success">{msg}</p>}
        </div>
      </main>
    );
  }

  return (
    <main className="container">
      <div className="header">
        <div><h1>FacturaGuard Dashboard</h1><p>MVP e-Factura monitorizare.</p></div>
        <button className="btn secondary" onClick={logout}><LogOut size={16} /> Logout</button>
      </div>

      {err && <p className="error">{err}</p>}
      {msg && <p className="success">{msg}</p>}

      <section className="grid grid-2">
        <div className="card">
          <h2>Firme</h2>
          <form onSubmit={createOrg} className="grid">
            <input className="input" placeholder="Nume firmă" value={orgForm.name} onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })} />
            <input className="input" placeholder="CUI" value={orgForm.cui} onChange={(e) => setOrgForm({ ...orgForm, cui: e.target.value })} />
            <button className="btn" type="submit">Adaugă firmă</button>
          </form>
          <div style={{ marginTop: 18 }}>{orgs.map((o) => <button key={o.id} className={o.id === active ? "btn" : "btn secondary"} style={{ marginRight: 8, marginBottom: 8 }} onClick={() => setActive(o.id)}>{o.name}</button>)}</div>
        </div>

        <div className="card">
          <h2>Upload facturi</h2>
          <form onSubmit={uploadFile} className="grid">
            <input className="input" type="file" name="file" accept=".csv,.xml,.zip" />
            <button className="btn" type="submit"><UploadCloud size={16} /> Importă</button>
          </form>
        </div>
      </section>

      <section className="grid grid-4" style={{ marginTop: 18 }}>
        <Metric icon={<FileText />} label="Total facturi" value={summary?.total_invoices ?? 0} />
        <Metric icon={<CheckCircle2 />} label="Validate" value={summary?.validated ?? 0} />
        <Metric icon={<AlertTriangle />} label="Respinse" value={summary?.rejected ?? 0} />
        <Metric icon={<BellRing />} label="Alerte" value={summary?.open_alerts ?? 0} />
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <div className="header"><h2>Alerte</h2><button className="btn secondary" onClick={runStatusCheck}>Rulează verificarea</button></div>
        {alerts.map((a) => <div key={a.id} className="card" style={{ boxShadow: "none", marginBottom: 12 }}><span className={`badge ${a.severity}`}>{a.severity}</span><h3>{a.title}</h3><p>{a.message}</p></div>)}
        {alerts.length === 0 && <p>Nu există alerte.</p>}
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>Facturi</h2>
        <table className="table"><thead><tr><th>Număr</th><th>Data</th><th>Deadline</th><th>Client</th><th>Total</th><th>Status</th></tr></thead>
          <tbody>{invoices.map((i) => <tr key={i.id}><td>{i.invoice_number}</td><td>{i.issue_date}</td><td>{i.due_submission_date}</td><td>{i.customer_name}</td><td>{i.total_amount} {i.currency}</td><td><span className={`badge ${i.internal_status}`}>{i.internal_status}</span></td></tr>)}</tbody>
        </table>
      </section>
    </main>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return <div className="card"><div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}><p>{label}</p>{icon}</div><h2>{value}</h2></div>;
}
