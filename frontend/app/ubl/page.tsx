"use client";

import { useEffect, useState } from "react";
import { apiFetch, getToken } from "../api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function UblPage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [activeOrg, setActiveOrg] = useState<number | null>(null);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [activeInvoice, setActiveInvoice] = useState<number | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [statusCheckResult, setStatusCheckResult] = useState<any>(null);
  const [downloadResponseResult, setDownloadResponseResult] = useState<any>(null);
  const [parseResponseResult, setParseResponseResult] = useState<any>(null);
  const [manualDocumentId, setManualDocumentId] = useState("");
  const [manualMessageId, setManualMessageId] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { loadOrganizations(); }, []);
  useEffect(() => { if (activeOrg) loadInvoices(activeOrg); }, [activeOrg]);
  useEffect(() => { if (activeOrg && activeInvoice) loadPreview(activeOrg, activeInvoice); }, [activeOrg, activeInvoice]);

  async function loadOrganizations() {
    try {
      const data = await apiFetch("/organizations");
      setOrgs(data);
      if (data.length > 0) setActiveOrg(data[0].id);
    } catch (err: any) { setError(err.message); }
  }

  async function loadInvoices(orgId: number) {
    const data = await apiFetch(`/organizations/${orgId}/invoices`);
    setInvoices(data);
    if (data.length > 0) setActiveInvoice(data[0].id);
  }

  async function loadPreview(orgId: number, invoiceId: number) {
    setError("");
    try {
      setPreview(await apiFetch(`/organizations/${orgId}/invoices/${invoiceId}/ubl-preview`));
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function parseAnafResponse() {
    if (!activeOrg || !activeInvoice) return;
    setError("");
    setParseResponseResult(null);

    try {
      const params = new URLSearchParams();
      if (manualDocumentId) params.set("document_id", manualDocumentId);
      params.set("apply_result", "true");
      const result = await apiFetch(`/organizations/${activeOrg}/invoices/${activeInvoice}/anaf-parse-response?${params.toString()}`, {
        method: "POST",
      });
      setParseResponseResult(result);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function downloadAnafResponse() {
    if (!activeOrg || !activeInvoice) return;
    setError("");
    setDownloadResponseResult(null);

    try {
      const suffix = manualMessageId ? `?message_id=${encodeURIComponent(manualMessageId)}` : "";
      const result = await apiFetch(`/organizations/${activeOrg}/invoices/${activeInvoice}/anaf-download-response${suffix}`, {
        method: "POST",
      });
      setDownloadResponseResult(result);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function checkAnafStatus() {
    if (!activeOrg || !activeInvoice) return;
    setError("");
    setStatusCheckResult(null);

    try {
      const result = await apiFetch(`/organizations/${activeOrg}/invoices/${activeInvoice}/anaf-status-check`, {
        method: "POST",
      });
      setStatusCheckResult(result);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function uploadToAnafDraft(dryRun = false) {
    if (!activeOrg || !activeInvoice) return;
    setError("");
    setUploadResult(null);

    try {
      const result = await apiFetch(`/organizations/${activeOrg}/invoices/${activeInvoice}/anaf-upload-draft?dry_run=${dryRun}`, {
        method: "POST",
      });
      setUploadResult(result);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function downloadXml() {
    if (!activeOrg || !activeInvoice) return;
    const token = getToken();
    const response = await fetch(`${API_BASE}/organizations/${activeOrg}/invoices/${activeInvoice}/ubl.xml`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      setError("XML-ul nu a putut fi descărcat.");
      return;
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = preview?.filename || "efactura.xml";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <h1>UBL XML generator</h1>
          <p>Generează XML e-Factura skeleton dintr-o factură existentă.</p>
        </div>
        <a className="btn secondary" href="/">Dashboard</a>
      </div>

      {error && <p className="error">{error}</p>}

      <section className="grid grid-2">
        <div className="card">
          <h2>Firmă</h2>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {orgs.map((org) => (
              <button key={org.id} className={org.id === activeOrg ? "btn" : "btn secondary"} onClick={() => setActiveOrg(org.id)}>
                {org.name}
              </button>
            ))}
          </div>
        </div>

        <div className="card">
          <h2>Factură</h2>
          <select className="input" value={activeInvoice || ""} onChange={(e) => setActiveInvoice(Number(e.target.value))}>
            {invoices.map((invoice) => (
              <option key={invoice.id} value={invoice.id}>
                {invoice.invoice_number} · {invoice.customer_name}
              </option>
            ))}
          </select>
        </div>
      </section>

      {preview && (
        <section className="card" style={{ marginTop: 18 }}>
          <div className="header">
            <div>
              <h2>{preview.filename}</h2>
              <p>{preview.warning}</p>
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button className="btn secondary" onClick={() => uploadToAnafDraft(true)}>Dry-run ANAF</button>
              <button className="btn" onClick={() => uploadToAnafDraft(false)}>Trimite către ANAF test</button>
              <button className="btn secondary" onClick={checkAnafStatus}>Verifică stareMesaj</button>
              <button className="btn secondary" onClick={downloadAnafResponse}>Descarcă răspuns ANAF</button>
              <button className="btn secondary" onClick={parseAnafResponse}>Parsează răspuns</button>
              <button className="btn secondary" onClick={downloadXml}>Descarcă XML</button>
            </div>
          </div>
          {uploadResult && (
            <div className="card" style={{ marginTop: 18, boxShadow: "none" }}>
              <h3>Rezultat upload ANAF</h3>
              <p><b>Mediu:</b> {uploadResult.environment}</p>
              <p><b>Încercat:</b> {String(uploadResult.attempted)}</p>
              <p><b>Uploaded:</b> {String(uploadResult.uploaded)}</p>
              <p><b>id_incarcare:</b> {uploadResult.anaf_upload_id || "-"}</p>
              <p>{uploadResult.message}</p>
              {uploadResult.raw_response && <pre style={{ whiteSpace: "pre-wrap", overflowX: "auto" }}>{uploadResult.raw_response}</pre>}
            </div>
          )}

          <div className="card" style={{ marginTop: 18, boxShadow: "none" }}>
            <h3>Descărcare și parsare răspuns ANAF</h3>
            <p>Lasă gol dacă `stareMesaj` a salvat deja un `anaf_download_id`. Completează manual doar pentru test/debug.</p>
            <input
              className="input"
              placeholder="message_id / id descărcare ANAF opțional"
              value={manualMessageId}
              onChange={(event) => setManualMessageId(event.target.value)}
            />
            <p>Pentru parsare, lasă gol dacă factura are deja document ANAF salvat sau introdu manual document_id.</p>
            <input
              className="input"
              placeholder="document_id opțional pentru parsare"
              value={manualDocumentId}
              onChange={(event) => setManualDocumentId(event.target.value)}
            />
          </div>

          {downloadResponseResult && (
            <div className="card" style={{ marginTop: 18, boxShadow: "none" }}>
              <h3>Rezultat descărcare răspuns</h3>
              <p><b>Mediu:</b> {downloadResponseResult.environment}</p>
              <p><b>Încercat:</b> {String(downloadResponseResult.attempted)}</p>
              <p><b>Downloaded:</b> {String(downloadResponseResult.downloaded)}</p>
              <p><b>id descărcare:</b> {downloadResponseResult.anaf_download_id || "-"}</p>
              <p><b>Document ID:</b> {downloadResponseResult.document_id || "-"}</p>
              <p><b>Fișier:</b> {downloadResponseResult.filename || "-"}</p>
              <p><b>Mărime:</b> {downloadResponseResult.size_bytes || "-"} bytes</p>
              <p>{downloadResponseResult.message}</p>
            </div>
          )}

          {parseResponseResult && (
            <div className="card" style={{ marginTop: 18, boxShadow: "none" }}>
              <h3>Rezultat parsare răspuns ANAF</h3>
              <p><b>Applied:</b> {String(parseResponseResult.applied)}</p>
              <p><b>Document ID:</b> {parseResponseResult.document_id}</p>
              <p><b>Fișiere:</b> {parseResponseResult.file_count}</p>
              <p><b>XML-uri:</b> {parseResponseResult.xml_file_count}</p>
              <p><b>Status extras:</b> {parseResponseResult.summary_status}</p>
              <p>{parseResponseResult.summary_message}</p>
              <pre style={{ whiteSpace: "pre-wrap", overflowX: "auto" }}>{JSON.stringify(parseResponseResult.files, null, 2)}</pre>
            </div>
          )}

          {statusCheckResult && (
            <div className="card" style={{ marginTop: 18, boxShadow: "none" }}>
              <h3>Rezultat stareMesaj</h3>
              <p><b>Mediu:</b> {statusCheckResult.environment}</p>
              <p><b>Încercat:</b> {String(statusCheckResult.attempted)}</p>
              <p><b>Verificat:</b> {String(statusCheckResult.checked)}</p>
              <p><b>id_incarcare:</b> {statusCheckResult.anaf_upload_id || "-"}</p>
              <p><b>ANAF status:</b> {statusCheckResult.anaf_status || "-"}</p>
              <p><b>Internal status:</b> {statusCheckResult.internal_status || "-"}</p>
              <p>{statusCheckResult.message}</p>
              {statusCheckResult.raw_response && <pre style={{ whiteSpace: "pre-wrap", overflowX: "auto" }}>{statusCheckResult.raw_response}</pre>}
            </div>
          )}

          <pre style={{ whiteSpace: "pre-wrap", overflowX: "auto" }}>{preview.xml}</pre>
        </section>
      )}
    </main>
  );
}
