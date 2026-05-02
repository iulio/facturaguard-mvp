"use client";

import { useEffect, useState } from "react";
import { setToken } from "../api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function AcceptInvitePage() {
  const [tokenParam, setTokenParam] = useState("");
  const [invite, setInvite] = useState<any>(null);
  const [form, setForm] = useState({ name: "", password: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token") || "";
    setTokenParam(token);
    if (token) loadInvite(token);
  }, []);

  async function loadInvite(token: string) {
    setError("");
    try {
      const response = await fetch(`${API_BASE}/invitations/public/${token}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Invitația nu poate fi citită.");
      setInvite(data);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function acceptInvite(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${API_BASE}/invitations/accept-with-account`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: tokenParam, name: form.name, password: form.password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Invitația nu a putut fi acceptată.");

      setToken(data.access_token);
      setMessage(`Invitația a fost acceptată. Ai acces la ${data.organization_name}. Redirecționare...`);
      setTimeout(() => {
        window.location.href = "/";
      }, 1200);
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <main className="container">
      <div className="card" style={{ maxWidth: 560, margin: "40px auto" }}>
        <h1>Acceptă invitația FacturaGuard</h1>

        {!tokenParam && <p className="error">Linkul nu conține token de invitație.</p>}
        {error && <p className="error">{error}</p>}
        {message && <p className="success">{message}</p>}

        {invite && (
          <>
            <p>
              Ai fost invitat pentru firma <b>{invite.organization_name}</b>.
            </p>
            <p>
              Email: <b>{invite.invited_email}</b>
              <br />
              Rol: <b>{invite.role}</b>
            </p>

            <form className="grid" onSubmit={acceptInvite}>
              <input
                className="input"
                placeholder="Numele tău"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
              />
              <input
                className="input"
                placeholder="Parolă"
                type="password"
                value={form.password}
                onChange={(event) => setForm({ ...form, password: event.target.value })}
              />
              <button className="btn" type="submit">
                Creează cont și acceptă invitația
              </button>
            </form>
          </>
        )}
      </div>
    </main>
  );
}
