import Link from "next/link";

const faqs = [
  {
    question: "Ce este FacturaGuard?",
    answer: "FacturaGuard este un MVP SaaS B2B pentru monitorizarea operațională a fluxurilor RO e-Factura: importuri, statusuri, alerte, documente, rapoarte și audit log.",
  },
  {
    question: "Este conectat real la ANAF?",
    answer: "În acest MVP, conectorul ANAF este mock. Arhitectura este pregătită pentru integrare reală, dar procesarea reală ANAF/SPV trebuie implementată separat și validată legal/contabil.",
  },
  {
    question: "Plățile NETOPIA sunt reale?",
    answer: "Nu. Integrarea actuală este un provider mock pentru demo: checkout, webhook și activare plan simulată.",
  },
  {
    question: "Ce pot face contabilii?",
    answer: "Pot administra mai multe firme, vedea scoruri de risc, work queue, alerte, audit log, rapoarte PDF/CSV, invitații clienți și documente originale.",
  },
  {
    question: "Ce pot vedea clienții?",
    answer: "Clienții invitați pot folosi portalul client read-only pentru facturi, alerte și documente ale firmei la care au acces.",
  },
  {
    question: "Cum se integrează un ERP?",
    answer: "Se creează un API key din pagina /api-keys și se folosește Public API: POST /public-api/v1/invoices cu headerul X-API-Key.",
  },
  {
    question: "Este pregătit pentru producție?",
    answer: "Este pregătit pentru demo, validare de piață și discuții cu utilizatori. Pentru producție reală mai sunt necesare integrare ANAF reală, NETOPIA reală, securizare, backup, observability și validare legală.",
  },
];

const demoSteps = [
  "Deschide landing page și explică problema: firmele descoperă prea târziu facturi respinse, netrimise sau blocate.",
  "Arată pricing și ROI calculator pentru a ancora valoarea economică.",
  "Loghează-te și prezintă portfolio dashboard: firme, risc, alerte, saved views.",
  "Intră în work queue și filtrează după urgent/high/rejected.",
  "Deschide o factură și arată tags, prioritate și note de colaborare.",
  "Arată document storage și audit log pentru trasabilitate.",
  "Deschide portalul client pentru perspectiva read-only.",
  "Arată API keys și developer portal pentru integrare ERP.",
  "Închide cu system status și QA checklist pentru credibilitate tehnică.",
];

export default function HelpPage() {
  return (
    <main>
      <section className="marketing-hero compact">
        <nav className="marketing-nav">
          <Link href="/landing" className="brand">FacturaGuard</Link>
          <div className="marketing-links">
            <Link href="/pricing">Prețuri</Link>
            <Link href="/roi">ROI</Link>
            <Link href="/">Login</Link>
          </div>
        </nav>

        <div className="pricing-header">
          <span className="eyebrow">Help Center</span>
          <h1>Ghid rapid pentru demo, întrebări frecvente și poziționare.</h1>
          <p>
            O pagină publică pentru a explica produsul rapid unui contabil, unei firme sau unui potențial partener ERP.
          </p>
        </div>
      </section>

      <section className="marketing-section">
        <h2>Întrebări frecvente</h2>
        <div className="feature-grid">
          {faqs.map((faq) => (
            <div className="feature-card" key={faq.question}>
              <h3>{faq.question}</h3>
              <p>{faq.answer}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="marketing-section">
        <h2>Demo sales script</h2>
        <p className="section-subtitle">
          Folosește această ordine pentru un demo de 10-15 minute.
        </p>
        <div className="card">
          <ol>
            {demoSteps.map((step) => (
              <li key={step} style={{ marginBottom: 12, lineHeight: 1.6 }}>{step}</li>
            ))}
          </ol>
        </div>
      </section>

      <section className="marketing-section split-section">
        <div>
          <h2>Mesaj pentru contabili</h2>
          <p>
            FacturaGuard reduce timpul pierdut cu verificări manuale și ajută la prioritizarea firmelor unde există risc operațional.
          </p>
        </div>
        <div>
          <h2>Mesaj pentru firme</h2>
          <p>
            FacturaGuard oferă vizibilitate, documente, rapoarte și audit trail pentru facturile care pot genera probleme.
          </p>
        </div>
      </section>
    </main>
  );
}
