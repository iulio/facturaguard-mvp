"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function ResetPasswordPage() {
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setToken(params.get("token") || "");
  }, []);

  async function resetPassword(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${API_BASE}/auth/password-reset/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: newPassword }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Parola nu a putut fi resetată.");
      setMessage("Parola a fost resetată. Poți reveni la pagina de login.");
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <main className="container">
      <div className="card" style={{ maxWidth: 520, margin: "40px auto" }}>
        <h1>Resetare parolă</h1>

        {!token && <p className="error">Linkul nu conține token de resetare.</p>}
        {error && <p className="error">{error}</p>}
        {message && <p className="success">{message}</p>}

        <form className="grid" onSubmit={resetPassword}>
          <input
            className="input"
            type="password"
            placeholder="Parolă nouă"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
          />
          <button className="btn" type="submit">
            Resetează parola
          </button>
        </form>
      </div>
    </main>
  );
}
