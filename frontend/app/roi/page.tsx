"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

export default function RoiPage() {
  const [companies, setCompanies] = useState(10);
  const [invoicesPerCompany, setInvoicesPerCompany] = useState(80);
  const [minutesPerInvoice, setMinutesPerInvoice] = useState(3);
  const [hourlyCost, setHourlyCost] = useState(15);
  const [monthlyPrice, setMonthlyPrice] = useState(49);

  const result = useMemo(() => {
    const monthlyInvoices = companies * invoicesPerCompany;
    const manualHours = (monthlyInvoices * minutesPerInvoice) / 60;
    const manualCost = manualHours * hourlyCost;
    const estimatedSavedHours = manualHours * 0.55;
    const estimatedSavedCost = estimatedSavedHours * hourlyCost;
    const netMonthlyValue = estimatedSavedCost - monthlyPrice;
    const annualValue = netMonthlyValue * 12;
    const roi = monthlyPrice > 0 ? (netMonthlyValue / monthlyPrice) * 100 : 0;

    return {
      monthlyInvoices,
      manualHours,
      manualCost,
      estimatedSavedHours,
      estimatedSavedCost,
      netMonthlyValue,
      annualValue,
      roi,
    };
  }, [companies, invoicesPerCompany, minutesPerInvoice, hourlyCost, monthlyPrice]);

  return (
    <main>
      <section className="marketing-hero compact">
        <nav className="marketing-nav">
          <Link href="/landing" className="brand">FacturaGuard</Link>
          <div className="marketing-links">
            <Link href="/pricing">Prețuri</Link>
            <Link href="/">Login</Link>
          </div>
        </nav>

        <div className="pricing-header">
          <span className="eyebrow">Calculator comercial</span>
          <h1>Estimează timpul economisit cu FacturaGuard.</h1>
          <p>
            Calculează rapid valoarea potențială pentru un cabinet contabil sau o firmă care urmărește manual e-Factura.
          </p>
        </div>
      </section>

      <section className="marketing-section">
        <div className="grid grid-2">
          <div className="card">
            <h2>Inputuri</h2>
            <NumberField label="Firme monitorizate" value={companies} setValue={setCompanies} />
            <NumberField label="Facturi / firmă / lună" value={invoicesPerCompany} setValue={setInvoicesPerCompany} />
            <NumberField label="Minute manuale / factură" value={minutesPerInvoice} setValue={setMinutesPerInvoice} />
            <NumberField label="Cost orar operator, EUR" value={hourlyCost} setValue={setHourlyCost} />
            <NumberField label="Cost FacturaGuard / lună, EUR" value={monthlyPrice} setValue={setMonthlyPrice} />
          </div>

          <div className="card">
            <h2>Rezultat estimativ</h2>
            <div className="risk-row"><span>Facturi/lună</span><b>{result.monthlyInvoices.toFixed(0)}</b></div>
            <div className="risk-row"><span>Ore manuale/lună</span><b>{result.manualHours.toFixed(1)}</b></div>
            <div className="risk-row"><span>Cost manual/lună</span><b>{result.manualCost.toFixed(0)} EUR</b></div>
            <div className="risk-row"><span>Ore economisite estimativ</span><b>{result.estimatedSavedHours.toFixed(1)}</b></div>
            <div className="risk-row"><span>Valoare economisită/lună</span><b>{result.estimatedSavedCost.toFixed(0)} EUR</b></div>
            <div className="hero-status">Valoare netă lunară: {result.netMonthlyValue.toFixed(0)} EUR</div>
          </div>
        </div>

        <section className="grid grid-3" style={{ marginTop: 18 }}>
          <Metric label="ROI lunar estimativ" value={`${result.roi.toFixed(0)}%`} />
          <Metric label="Valoare anuală netă" value={`${result.annualValue.toFixed(0)} EUR`} />
          <Metric label="Timp salvat anual" value={`${(result.estimatedSavedHours * 12).toFixed(0)} ore`} />
        </section>

        <section className="card" style={{ marginTop: 18 }}>
          <h2>Ipoteză folosită</h2>
          <p>
            Calculatorul presupune că FacturaGuard reduce cu aproximativ 55% timpul de verificare manuală a statusurilor,
            raportării, alertelor și documentelor. Rezultatul este orientativ și trebuie validat în pilot.
          </p>
          <div className="hero-actions">
            <Link href="/pricing" className="btn">Vezi planuri</Link>
            <Link href="/landing" className="btn secondary">Înapoi la landing</Link>
          </div>
        </section>
      </section>
    </main>
  );
}

function NumberField({ label, value, setValue }: { label: string; value: number; setValue: (value: number) => void }) {
  return (
    <label>
      {label}
      <input
        className="input"
        type="number"
        min={0}
        value={value}
        onChange={(event) => setValue(Number(event.target.value))}
      />
    </label>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="card">
      <p>{label}</p>
      <h2>{value}</h2>
    </div>
  );
}
