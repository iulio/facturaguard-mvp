import Link from "next/link";
import { AlertTriangle, BarChart3, FileCheck2, FileText, ShieldCheck, Users } from "lucide-react";

const features = [
  {
    icon: <FileCheck2 size={28} />,
    title: "Monitorizare e-Factura",
    description: "Centralizează facturile, statusurile și alertele într-un dashboard clar pentru firme și contabili.",
  },
  {
    icon: <AlertTriangle size={28} />,
    title: "Alerte de risc",
    description: "Identifică facturi respinse, netrimise, aproape de termen sau depășite.",
  },
  {
    icon: <BarChart3 size={28} />,
    title: "Portofoliu contabil",
    description: "Vezi toate firmele administrate, scorul de risc și alertele deschise.",
  },
  {
    icon: <FileText size={28} />,
    title: "Rapoarte PDF și CSV",
    description: "Generează rapoarte lunare și exporturi utile pentru client sau audit.",
  },
  {
    icon: <ShieldCheck size={28} />,
    title: "Audit și documente",
    description: "Păstrează fișierele originale CSV/XML/ZIP și istoricul acțiunilor.",
  },
  {
    icon: <Users size={28} />,
    title: "Invitații client",
    description: "Invită clienți sau operatori direct în organizație, cu roluri și acces controlat.",
  },
];

export default function LandingPage() {
  return (
    <main>
      <section className="marketing-hero">
        <nav className="marketing-nav">
          <div className="brand">FacturaGuard</div>
          <div className="marketing-links">
            <Link href="/pricing">Prețuri</Link>
            <Link href="/roi">ROI</Link>
            <Link href="/help">Help</Link>
            <Link href="/templates">Templates</Link>
            <Link href="/status">Status</Link>
            <Link href="/">Login</Link>
          </div>
        </nav>

        <div className="hero-grid">
          <div>
            <span className="eyebrow">SaaS B2B pentru firme și cabinete contabile</span>
            <h1>Monitorizare RO e-Factura fără haos în emailuri, XML-uri și deadline-uri.</h1>
            <p>
              FacturaGuard ajută contabilii și firmele din România să urmărească statusuri,
              alerte, documente și rapoarte pentru fluxul e-Factura.
            </p>
            <div className="hero-actions">
              <Link href="/" className="btn">Începe demo</Link>
              <Link href="/pricing" className="btn secondary">Vezi prețuri</Link>
              <Link href="/roi" className="btn secondary">Calculează ROI</Link>
            </div>
          </div>

          <div className="hero-card">
            <h2>Dashboard risc</h2>
            <div className="risk-row"><span>Firme monitorizate</span><b>25</b></div>
            <div className="risk-row"><span>Alerte deschise</span><b>14</b></div>
            <div className="risk-row"><span>Facturi respinse</span><b>6</b></div>
            <div className="risk-row"><span>Raport lunar</span><b>PDF</b></div>
            <div className="hero-status">Mock ANAF sync activ · Audit log complet</div>
          </div>
        </div>
      </section>

      <section className="marketing-section">
        <h2>Ce rezolvă</h2>
        <p className="section-subtitle">
          Pentru firmele care nu vor să descopere prea târziu că o factură a fost respinsă,
          netrimisă sau blocată într-un flux manual.
        </p>
        <div className="feature-grid">
          {features.map((feature) => (
            <div className="feature-card" key={feature.title}>
              {feature.icon}
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="marketing-section split-section">
        <div>
          <h2>Pentru cabinete contabile</h2>
          <p>
            Ai o vedere multi-firmă, scor de risc, alerte pe fiecare client, invitații și exporturi.
            În loc să cauți statusuri manual, vezi rapid unde trebuie intervenit.
          </p>
        </div>
        <div>
          <h2>Pentru firme</h2>
          <p>
            Ai transparență asupra facturilor, documentelor încărcate, erorilor și rapoartelor lunare
            pe care le poți trimite intern sau către contabil.
          </p>
        </div>
      </section>
    </main>
  );
}
