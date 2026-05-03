import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

const fields = [
  ["invoice_number", "obligatoriu", "Numărul facturii"],
  ["issue_date", "obligatoriu", "Data emiterii, format YYYY-MM-DD"],
  ["customer_name", "obligatoriu", "Numele clientului"],
  ["customer_cui", "obligatoriu", "CUI client"],
  ["total_amount", "obligatoriu", "Valoarea totală"],
  ["currency", "opțional", "Default: RON"],
  ["anaf_status", "opțional", "pending, validated sau rejected"],
  ["anaf_message", "opțional", "Mesaj ANAF sau explicație eroare"],
];

export default function TemplatesPage() {
  return (
    <main>
      <section className="marketing-hero compact">
        <nav className="marketing-nav">
          <Link href="/landing" className="brand">FacturaGuard</Link>
          <div className="marketing-links">
            <Link href="/help">Help</Link>
            <Link href="/developer">Developer</Link>
            <Link href="/">Login</Link>
          </div>
        </nav>

        <div className="pricing-header">
          <span className="eyebrow">Import templates</span>
          <h1>Șabloane CSV/XML pentru primul import.</h1>
          <p>
            Descarcă fișiere demo compatibile cu uploadul FacturaGuard și folosește-le în onboarding sau testare.
          </p>
        </div>
      </section>

      <section className="marketing-section">
        <div className="grid grid-3">
          <DownloadCard
            title="CSV template"
            description="Recomandat pentru importuri rapide din Excel/ERP."
            href={`${API_BASE}/templates/invoices.csv`}
          />
          <DownloadCard
            title="XML template"
            description="Exemplu XML simplificat pentru testare."
            href={`${API_BASE}/templates/invoices.xml`}
          />
          <DownloadCard
            title="ZIP pack"
            description="Include CSV, XML și README."
            href={`${API_BASE}/templates/facturaguard-import-templates.zip`}
          />
        </div>

        <section className="card" style={{ marginTop: 18 }}>
          <h2>Câmpuri suportate</h2>
          <table className="table">
            <thead>
              <tr><th>Câmp</th><th>Status</th><th>Descriere</th></tr>
            </thead>
            <tbody>
              {fields.map(([field, required, description]) => (
                <tr key={field}>
                  <td><b>{field}</b></td>
                  <td>{required}</td>
                  <td>{description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="card" style={{ marginTop: 18 }}>
          <h2>Cum testezi</h2>
          <ol>
            <li>Descarcă CSV template.</li>
            <li>Autentifică-te în FacturaGuard.</li>
            <li>Intră în onboarding sau dashboard.</li>
            <li>Creează o firmă, dacă nu există.</li>
            <li>Încarcă CSV-ul și verifică facturile importate.</li>
          </ol>
          <div className="hero-actions">
            <Link href="/onboarding" className="btn">Mergi la onboarding</Link>
            <Link href="/help" className="btn secondary">Help center</Link>
          </div>
        </section>
      </section>
    </main>
  );
}

function DownloadCard({ title, description, href }: { title: string; description: string; href: string }) {
  return (
    <div className="card">
      <h2>{title}</h2>
      <p>{description}</p>
      <a className="btn" href={href}>Descarcă</a>
    </div>
  );
}
