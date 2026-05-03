"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function PricingPage() {
  const [plans, setPlans] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/billing/plans`)
      .then((response) => response.json())
      .then(setPlans)
      .catch(() => setError("Nu am putut încărca planurile."));
  }, []);

  return (
    <main>
      <section className="marketing-hero compact">
        <nav className="marketing-nav">
          <Link href="/landing" className="brand">FacturaGuard</Link>
          <div className="marketing-links">
            <Link href="/landing">Acasă</Link>
            <Link href="/roi">ROI</Link>
            <Link href="/">Login</Link>
          </div>
        </nav>

        <div className="pricing-header">
          <span className="eyebrow">Prețuri MVP</span>
          <h1>Planuri simple pentru firme și contabili.</h1>
          <p>
            Planurile sunt pregătite pentru monetizare SaaS. În v1.7 plata este simulată prin NETOPIA mock.
          </p>
        </div>
      </section>

      <section className="marketing-section">
        {error && <p className="error">{error}</p>}

        <div className="pricing-grid">
          {plans.map((plan) => (
            <div className="pricing-card" key={plan.code}>
              <h2>{plan.name}</h2>
              <p className="price">{plan.monthly_price_eur} EUR<span>/lună</span></p>
              <p>{plan.max_organizations} firme</p>
              <p>{plan.max_invoices_per_month} facturi/lună</p>
              <p>{plan.max_documents} documente</p>
              <ul>
                {plan.features.map((feature: string) => (
                  <li key={feature}>{feature}</li>
                ))}
              </ul>
              <Link href="/" className="btn">Alege planul</Link>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
