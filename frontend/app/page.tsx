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
  const [selectedInvoiceIds, setSelectedInvoiceIds] = useState<number[]>([]);
  const [bulkAction, setBulkAction] = useState("sync_status");
  const [alerts, setAlerts] = useState<any[]>([]);
  const [portfolio, setPortfolio] = useState<any>(null);
  const [portfolioSearch, setPortfolioSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [savedViews, setSavedViews] = useState<any[]>([]);
  const [savedViewName, setSavedViewName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("client_viewer");
  const [invitations, setInvitations] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [plans, setPlans] = useState<any[]>([]);
  const [usage, setUsage] = useState<any>(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [resetEmail, setResetEmail] = useState("");

  useEffect(() => { setAuthed(Boolean(getToken())); setReady(true); }, []);
  useEffect(() => { if (authed) { loadOrganizations(); loadPortfolio(); loadPlans(); loadSavedViews(); } }, [authed]);
  useEffect(() => { if (active) refresh(active); }, [active]);

  async function refresh(id: number) {
    await Promise.all([loadDashboard(id), loadInvoices(id), loadAlerts(id), loadPortfolio(), loadInvitations(id), loadDocuments(id), loadUsage(id)]);
  }

  async function loadPortfolio() {
    const params = new URLSearchParams();
    if (portfolioSearch) params.set("search", portfolioSearch);
    if (riskFilter) params.set("risk", riskFilter);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    setPortfolio(await apiFetch(`/portfolio${suffix}`));
  }

  async function loadSavedViews() {
    try {
      setSavedViews(await apiFetch(`/saved-views?view_type=portfolio`));
    } catch {
      setSavedViews([]);
    }
  }

  async function saveCurrentView() {
    if (!savedViewName) return;
    await apiFetch(`/saved-views`, {
      method: "POST",
      body: JSON.stringify({
        name: savedViewName,
        view_type: "portfolio",
        filters: { search: portfolioSearch, risk: riskFilter },
        is_default: false,
      }),
    });
    setSavedViewName("");
    await loadSavedViews();
  }

  async function applySavedView(view: any) {
    try {
      const filters = JSON.parse(view.filters_json || "{}");
      setPortfolioSearch(filters.search || "");
      setRiskFilter(filters.risk || "");
      const params = new URLSearchParams();
      if (filters.search) params.set("search", filters.search);
      if (filters.risk) params.set("risk", filters.risk);
      const suffix = params.toString() ? `?${params.toString()}` : "";
      setPortfolio(await apiFetch(`/portfolio${suffix}`));
    } catch {
      setErr("Nu am putut aplica vederea salvată.");
    }
  }

  async function deleteSavedView(id: number) {
    await apiFetch(`/saved-views/${id}`, { method: "DELETE" });
    await loadSavedViews();
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

  async function requestPasswordReset() {
    setErr("");
    setMsg("");
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"}/auth/password-reset/request`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: resetEmail }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Nu am putut cere resetarea.");
      setMsg(data.message);
    } catch (x: any) {
      setErr(x.message);
    }
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

  async function loadDocuments(id: number) {
    try {
      setDocuments(await apiFetch(`/organizations/${id}/documents`));
    } catch {
      setDocuments([]);
    }
  }

  async function loadPlans() {
    try {
      setPlans(await apiFetch(`/billing/plans`));
    } catch {
      setPlans([]);
    }
  }

  async function loadUsage(id: number) {
    try {
      setUsage(await apiFetch(`/organizations/${id}/usage`));
    } catch {
      setUsage(null);
    }
  }

  async function changePlan(planCode: string) {
    if (!active) return;
    const checkout = await apiFetch(`/organizations/${active}/billing/netopia/checkout`, {
      method: "POST",
      body: JSON.stringify({ plan_code: planCode }),
    });
    setMsg(`Checkout creat pentru ${planCode}. Redirecționare către NETOPIA...`);
    if (checkout.checkout_url) {
      window.location.href = checkout.checkout_url;
    }
  }

  async function downloadDocument(documentId: number, filename: string) {
    if (!active) return;
    const token = getToken();
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
    const response = await fetch(`${base}/organizations/${active}/documents/${documentId}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      setErr("Documentul nu a putut fi descărcat.");
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

  function toggleInvoiceSelection(id: number) {
    setSelectedInvoiceIds((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    );
  }

  async function runBulkAction() {
    if (!active || selectedInvoiceIds.length === 0) return;
    const result = await apiFetch(`/organizations/${active}/invoices/bulk-action`, {
      method: "POST",
      body: JSON.stringify({ invoice_ids: selectedInvoiceIds, action: bulkAction }),
    });
    setMsg(result.message);
    setSelectedInvoiceIds([]);
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
        <h1>FacturaGuard MVP</h1><p><a href="/landing">Landing</a> · <a href="/pricing">Prețuri</a> · <a href="/roi">ROI</a> · <a href="/help">Help</a> · <a href="/templates">Templates</a> · <a href="/onboarding">Onboarding</a></p>
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

          <div style={{ marginTop: 18 }}>
            <p style={{ color: "#64748b", fontSize: 14 }}>Ai uitat parola?</p>
            <div className="grid">
              <input className="input" placeholder="Email pentru resetare" value={resetEmail} onChange={(e) => setResetEmail(e.target.value)} />
              <button className="btn secondary" type="button" onClick={requestPasswordReset}>Trimite link resetare</button>
            </div>
          </div>

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
        <div style={{ display: "flex", gap: 8 }}><a className="btn secondary" href="/developer">Developer</a><a className="btn secondary" href="/ubl">UBL XML</a><a className="btn secondary" href="/integrations">Integrări</a><a className="btn secondary" href="/deployment">Deployment</a><a className="btn secondary" href="/billing">Billing</a><a className="btn secondary" href="/api-keys">API keys</a><a className="btn secondary" href="/system-status">Status</a><a className="btn secondary" href="/work-queue">Work queue</a><a className="btn secondary" href="/invoice-metadata">Tags/Prioritate</a><a className="btn secondary" href="/invoice-notes">Note facturi</a><a className="btn secondary" href="/client-portal">Portal client</a><a className="btn secondary" href="/settings">Setări</a><a className="btn secondary" href="/audit">Audit</a><a className="btn secondary" href="/onboarding">Onboarding</a><button className="btn secondary" onClick={logout}><LogOut size={16} /> Logout</button></div>
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

        <div className="card" style={{ boxShadow: "none", marginBottom: 18 }}>
          <h3>Saved views</h3>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
            {savedViews.map((view) => (
              <span key={view.id} style={{ display: "inline-flex", gap: 6 }}>
                <button className="btn secondary" onClick={() => applySavedView(view)}>{view.name}</button>
                <button className="btn secondary" onClick={() => deleteSavedView(view.id)}>×</button>
              </span>
            ))}
          </div>
          <div className="grid grid-2">
            <input className="input" placeholder="Nume vedere, ex: Risc mare" value={savedViewName} onChange={(e) => setSavedViewName(e.target.value)} />
            <button className="btn secondary" onClick={saveCurrentView}>Salvează vederea curentă</button>
          </div>
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

      <section className="card" style={{ marginTop: 18 }}>
        <div className="header">
          <div>
            <h2>Billing & usage</h2>
            <p>Plan curent: <b>{usage?.plan_code ?? "one"}</b>. Facturi luna curentă: {usage?.invoices_this_month ?? 0}/{usage?.max_invoices_per_month ?? "-"} · Documente: {usage?.documents_total ?? 0}/{usage?.max_documents ?? "-"}</p>
          </div>
        </div>
        <div className="grid grid-4">
          {plans.map((plan) => (
            <div className="card" key={plan.code} style={{ boxShadow: "none" }}>
              <h3>{plan.name}</h3>
              <p><b>{plan.monthly_price_eur} EUR/lună</b></p>
              <p>{plan.max_organizations} firme</p>
              <p>{plan.max_invoices_per_month} facturi/lună</p>
              <button className="btn secondary" onClick={() => changePlan(plan.code)}>Cumpără {plan.name}</button>
            </div>
          ))}
        </div>
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <div className="header">
          <div>
            <h2>Documente stocate</h2>
            <p>Fișiere originale păstrate pentru audit: CSV, XML sau ZIP.</p>
          </div>
          <button className="btn secondary" onClick={() => active && loadDocuments(active)}>Reîncarcă</button>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table className="table">
            <thead><tr><th>Fișier</th><th>Tip</th><th>Mărime</th><th>Data</th><th>Acțiune</th></tr></thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td>{doc.original_filename}</td>
                  <td>{doc.document_type}</td>
                  <td>{doc.file_size} bytes</td>
                  <td>{new Date(doc.created_at).toLocaleString()}</td>
                  <td><button className="btn secondary" onClick={() => downloadDocument(doc.id, doc.original_filename)}>Download</button></td>
                </tr>
              ))}
              {documents.length === 0 && <tr><td colSpan={5}>Nu există documente stocate.</td></tr>}
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
