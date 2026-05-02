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
  const [portfolio, setPortfolio] = useState<any>(null);
  const [portfolioSearch, setPortfolioSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("client_viewer");
  const [invitations, setInvitations] = useState<any[]>([]);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => { setAuthed(Boolean(getToken())); setReady(true); }, []);
  useEffect(() => { if (authed) { loadOrganizations(); loadPortfolio(); } }, [authed]);
  useEffect(() => { if (active) refresh(active); }, [active]);

  async function refresh(id: number) {
    await Promise.all([loadDashboard(id), loadInvoices(id), loadAlerts(id), loadPortfolio(), loadInvitations(id)]);
  }

  async function loadPortfolio() {
    const params = new URLSearchParams();
    if (portfolioSearch) params.set("search", portfolioSearch);
    if (riskFilter) params.set("risk", riskFilter);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    setPortfolio(await apiFetch(`/portfolio${suffix}`));
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

  async function loadInvitations(id: number) {
    try {
      setInvitations(await apiFetch(`/organizations/${id}/invitations`));
    } catch {
      setInvitations([]);
    }
  }

  async function sendInvitation() {
    if (!active || !inviteEmail) return;
    await apiFetch(`/organizations/${active}/invitations`, {
      method: "POST",
      body: JSON.stringify({ email: inviteEmail, role: inviteRole }),
    });
    setMsg(`Invitație trimisă către ${inviteEmail}.`);
    setInviteEmail("");
    await loadInvitations(active);
  }

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

  async function testAnafAndSync() {
    if (!active) return;
    await apiFetch(`/organizations/${active}/integrations/anaf/test`, { method: "POST" });
    const data = await apiFetch(`/organizations/${active}/invoices/sync-statuses`, { method: "POST" });
    setMsg(`Mock ANAF sync: ${data.checked} facturi verificate, ${data.changed} schimbate.`);
    await refresh(active);
  }

  async function downloadExport(path: string, filename: string) {
    const token = getToken();
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
    const response = await fetch(`${base}${path}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      setErr("Exportul nu a putut fi generat.");
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  function logout() { clearToken(); setAuthed(false); setOrgs([]); setInvoices([]); setAlerts([]); setSummary(null); setPortfolio(null); setActive(null); }

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


      <section className="card" style={{ marginBottom: 18 }}>
        <div className="header">
          <div>
            <h2>Portofoliu contabil</h2>
            <p>Vedere multi-firmă cu risc, alerte și status facturi.</p>
          </div>
          <button className="btn secondary" onClick={loadPortfolio}>Aplică filtre</button>
        </div>

        <div className="grid grid-2" style={{ marginBottom: 18 }}>
          <input className="input" placeholder="Caută firmă sau CUI..." value={portfolioSearch} onChange={(e) => setPortfolioSearch(e.target.value)} />
          <select className="input" value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
            <option value="">Toate riscurile</option>
            <option value="high">Risc mare</option>
            <option value="medium">Risc mediu</option>
            <option value="low">Risc mic</option>
          </select>
        </div>

        <section className="grid grid-4">
          <Metric icon={<FileText />} label="Firme" value={portfolio?.total_organizations ?? 0} />
          <Metric icon={<AlertTriangle />} label="Risc mare" value={portfolio?.high_risk ?? 0} />
          <Metric icon={<BellRing />} label="Alerte" value={portfolio?.total_open_alerts ?? 0} />
          <Metric icon={<CheckCircle2 />} label="Risc mic" value={portfolio?.low_risk ?? 0} />
        </section>

        <div style={{ marginTop: 18, overflowX: "auto" }}>
          <table className="table">
            <thead>
              <tr>
                <th>Firmă</th>
                <th>CUI</th>
                <th>Facturi</th>
                <th>Validate</th>
                <th>Probleme</th>
                <th>Alerte</th>
                <th>Risc</th>
              </tr>
            </thead>
            <tbody>
              {(portfolio?.organizations ?? []).map((org: any) => (
                <tr key={org.organization_id} onClick={() => setActive(org.organization_id)} style={{ cursor: "pointer" }}>
                  <td><b>{org.name}</b></td>
                  <td>{org.cui}</td>
                  <td>{org.total_invoices}</td>
                  <td>{org.validated}</td>
                  <td>{org.rejected + org.unsent + org.near_deadline + org.overdue}</td>
                  <td>{org.open_alerts}</td>
                  <td><span className={`badge ${org.risk_label === "high" ? "high" : org.risk_label === "medium" ? "medium" : "validated"}`}>{org.risk_label} · {org.risk_score}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

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

      <section className="card" style={{ marginTop: 18 }}>
        <div className="header">
          <div>
            <h2>Invitații firmă</h2>
            <p>Trimite acces către client sau operator. În MVP, emailul poate fi dry-run în backend.</p>
          </div>
        </div>
        <div className="grid grid-2">
          <input className="input" placeholder="email@firma.ro" value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} />
          <select className="input" value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}>
            <option value="client_viewer">Client viewer</option>
            <option value="client_operator">Client operator</option>
            <option value="accountant_owner">Accountant owner</option>
          </select>
        </div>
        <button className="btn" style={{ marginTop: 12 }} onClick={sendInvitation}>Trimite invitație</button>
        <div style={{ marginTop: 18, overflowX: "auto" }}>
          <table className="table">
            <thead><tr><th>Email</th><th>Rol</th><th>Status</th><th>Expiră</th></tr></thead>
            <tbody>
              {invitations.map((invite) => (
                <tr key={invite.id}>
                  <td>{invite.invited_email}</td>
                  <td>{invite.role}</td>
                  <td><span className={`badge ${invite.status === "accepted" ? "validated" : "medium"}`}>{invite.status}</span></td>
                  <td>{new Date(invite.expires_at).toLocaleDateString()}</td>
                </tr>
              ))}
              {invitations.length === 0 && <tr><td colSpan={4}>Nu există invitații.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid grid-4" style={{ marginTop: 18 }}>
        <Metric icon={<FileText />} label="Total facturi" value={summary?.total_invoices ?? 0} />
        <Metric icon={<CheckCircle2 />} label="Validate" value={summary?.validated ?? 0} />
        <Metric icon={<AlertTriangle />} label="Respinse" value={summary?.rejected ?? 0} />
        <Metric icon={<BellRing />} label="Alerte" value={summary?.open_alerts ?? 0} />
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <div className="header"><h2>Alerte</h2><button className="btn secondary" onClick={runStatusCheck}>Rulează verificarea</button><button className="btn secondary" onClick={testAnafAndSync}>Mock ANAF sync</button><button className="btn secondary" onClick={() => active && downloadExport(`/organizations/${active}/invoices/export.csv`, "facturaguard-invoices.csv")}>Export CSV</button><button className="btn secondary" onClick={() => active && downloadExport(`/organizations/${active}/reports/monthly.pdf?year=2026&month=4`, "facturaguard-report.pdf")}>Raport PDF</button></div>
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
