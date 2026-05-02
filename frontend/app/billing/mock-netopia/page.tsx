"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
const MOCK_SECRET = "dev-netopia-webhook-secret";

export default function MockNetopiaPage() {
  const [sessionId, setSessionId] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setSessionId(params.get("session_id") || "");
  }, []);

  async function sendWebhook(status: "paid" | "failed" | "cancelled") {
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${API_BASE}/billing/netopia-mock/webhook`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, status, secret: MOCK_SECRET }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Plata mock nu a putut fi procesată.");

      setMessage(`Status plată: ${data.status}. Plan: ${data.plan_code}.`);
      if (status === "paid") {
        setTimeout(() => {
          window.location.href = "/";
        }, 1200);
      }
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <main className="container">
      <div className="card" style={{ maxWidth: 560, margin: "40px auto" }}>
        <h1>NETOPIA Payments - Mock Checkout</h1>
        <p>Aceasta este o pagină simulată pentru development. Nu procesează bani reali.</p>
        <p>
          Session ID:<br />
          <b>{sessionId || "lipsește"}</b>
        </p>

        {error && <p className="error">{error}</p>}
        {message && <p className="success">{message}</p>}

        <div className="grid">
          <button className="btn" onClick={() => sendWebhook("paid")}>Simulează plată reușită</button>
          <button className="btn secondary" onClick={() => sendWebhook("failed")}>Simulează plată eșuată</button>
          <button className="btn secondary" onClick={() => sendWebhook("cancelled")}>Simulează anulare</button>
        </div>
      </div>
    </main>
  );
}
