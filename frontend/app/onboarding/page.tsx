"use client";

import { useEffect, useState } from "react";
import { apiFetch, getToken } from "../api";
import { CheckCircle2, Building2, UploadCloud, RefreshCw, LayoutDashboard } from "lucide-react";

export default function OnboardingPage() {
  const [status, setStatus] = useState<any>(null);
  const [orgForm, setOrgForm] = useState({ name: "", cui: "", address: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    setError("");
    try {
      const data = await apiFetch("/onboarding/status");
      setStatus(data);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function createOrganization(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");

    try {
      await apiFetch("/organizations", {
        method: "POST",
        body: JSON.stringify(orgForm),
      });
      setOrgForm({ name: "", cui: "", address: "" });
      setMessage("Firma a fost creată.");
      await loadStatus();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function uploadFile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");

    if (!status?.organization_id) {
      setError("Creează firma înainte de upload.");
      return;
    }

    const input = event.currentTarget.elements.namedItem("file") as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) {
      setError("Alege un fișier CSV, XML sau ZIP.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      await apiFetch(`/organizations/${status.organization_id}/invoices/upload`, {
        method: "POST",
        body: formData,
      });
      input.value = "";
      setMessage("Facturile au fost importate.");
      await loadStatus();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function runMockSync() {
    setError("");
    setMessage("");

    if (!status?.organization_id) return;

    try {
      await apiFetch(`/organizations/${status.organization_id}/integrations/anaf/test`, {
        method: "POST",
      });
      const data = await apiFetch(`/organizations/${status.organization_id}/invoices/sync-statuses`, {
        method: "POST",
      });
      setMessage(`Sync rulat: ${data.checked} facturi verificate.`);
      await loadStatus();
    } catch (err: any) {
      setError(err.message);
    }
  }

  const steps = [
    {
      key: "create_organization",
      title: "Creează prima firmă",
      done: status?.has_organization,
      icon: <Building2 />,
    },
    {
      key: "upload_invoices",
      title: "Încarcă primul CSV/XML/ZIP",
      done: status?.has_invoices,
      icon: <UploadCloud />,
    },
    {
      key: "run_sync",
      title: "Rulează primul Mock ANAF sync",
      done: status?.has_run_sync,
      icon: <RefreshCw />,
    },
    {
      key: "review_dashboard",
      title: "Revizuiește dashboard-ul",
      done: status?.completed,
      icon: <LayoutDashboard />,
    },
  ];

  if (!getToken()) {
    return (
      <main className="container">
        <div className="card">
          <h1>Onboarding FacturaGuard</h1>
          <p>Trebuie să fii autentificat pentru onboarding.</p>
          <a className="btn" href="/">Mergi la login</a>
        </div>
      </main>
    );
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>Onboarding FacturaGuard</h1>
          <p>Configurează primul flux în câteva minute.</p>
        </div>
        <a className="btn secondary" href="/">Dashboard</a>
      </div>

      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}

      <section className="grid grid-4">
        {steps.map((step) => (
          <div className="card" key={step.key}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              {step.icon}
              {step.done && <CheckCircle2 />}
            </div>
            <h3>{step.title}</h3>
            <span className={`badge ${step.done ? "validated" : "medium"}`}>
              {step.done ? "complet" : "în așteptare"}
            </span>
          </div>
        ))}
      </section>

      <section className="grid grid-2" style={{ marginTop: 18 }}>
        <div className="card">
          <h2>1. Firmă</h2>
          {status?.has_organization ? (
            <p>Firmă activă: <b>{status.organization_name}</b></p>
          ) : (
            <form className="grid" onSubmit={createOrganization}>
              <input className="input" placeholder="Nume firmă" value={orgForm.name} onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })} />
              <input className="input" placeholder="CUI" value={orgForm.cui} onChange={(e) => setOrgForm({ ...orgForm, cui: e.target.value })} />
              <input className="input" placeholder="Adresă, opțional" value={orgForm.address} onChange={(e) => setOrgForm({ ...orgForm, address: e.target.value })} />
              <button className="btn" type="submit">Creează firmă</button>
            </form>
          )}
        </div>

        <div className="card">
          <h2>2. Upload facturi</h2>
          <p>Facturi importate: <b>{status?.invoice_count ?? 0}</b></p>
          <form className="grid" onSubmit={uploadFile}>
            <input className="input" type="file" name="file" accept=".csv,.xml,.zip" />
            <button className="btn" type="submit">Importă fișier</button>
          </form>
        </div>
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>3. Sync și verificare</h2>
        <p>
          Rulează conectorul Mock ANAF pentru a simula actualizarea statusurilor.
          Alerte deschise: <b>{status?.open_alerts ?? 0}</b>
        </p>
        <button className="btn" onClick={runMockSync}>Rulează Mock ANAF sync</button>
      </section>

      {status?.completed && (
        <section className="card" style={{ marginTop: 18 }}>
          <h2>Setup complet</h2>
          <p>Ai finalizat fluxul de bază. Poți continua în dashboard.</p>
          <a className="btn" href="/">Mergi la dashboard</a>
        </section>
      )}
    </main>
  );
}
