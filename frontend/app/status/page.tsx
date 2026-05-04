const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function getStatus() {
  try {
    const response = await fetch(`${API_BASE}/public/status`, { cache: "no-store" });
    if (!response.ok) {
      return { status: "degraded", error: `HTTP ${response.status}` };
    }
    return response.json();
  } catch (error: any) {
    return { status: "degraded", error: error.message };
  }
}

function statusColor(status: string) {
  if (status === "operational" || status === "ok" || status === "configured") return "#166534";
  if (status === "mock" || status === "dry_run") return "#92400e";
  return "#991b1b";
}

export default async function StatusPage() {
  const status = await getStatus();

  return (
    <main style={{ maxWidth: 860, margin: "40px auto", padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <section style={{ border: "1px solid #e5e7eb", borderRadius: 24, padding: 28, background: "white" }}>
        <p style={{ margin: 0, color: "#64748b", fontWeight: 700, textTransform: "uppercase", letterSpacing: 1 }}>
          Public status
        </p>
        <h1 style={{ fontSize: 42, margin: "12px 0" }}>FacturaGuard</h1>
        <p style={{ color: "#475569", fontSize: 18 }}>
          Status public pentru deployment, disponibilitate API și moduri de integrare.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginTop: 24 }}>
          <Card label="Status" value={status.status || "unknown"} />
          <Card label="Database" value={status.database || "unknown"} />
          <Card label="Environment" value={status.environment || "-"} />
          <Card label="Version" value={status.version || "-"} />
        </div>

        {status.providers && (
          <div style={{ marginTop: 28 }}>
            <h2>Providers</h2>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <tbody>
                {Object.entries(status.providers).map(([key, value]) => (
                  <tr key={key}>
                    <td style={{ padding: "12px 0", borderBottom: "1px solid #e5e7eb", color: "#475569" }}>{key}</td>
                    <td style={{ padding: "12px 0", borderBottom: "1px solid #e5e7eb", textAlign: "right", fontWeight: 700, color: statusColor(String(value)) }}>
                      {String(value)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {status.error && (
          <p style={{ color: "#991b1b", marginTop: 24 }}>
            {status.error}
          </p>
        )}

        <p style={{ color: "#64748b", marginTop: 28 }}>
          Last updated: {status.timestamp_utc || "unknown"}
        </p>

        <div style={{ display: "flex", gap: 12, marginTop: 24, flexWrap: "wrap" }}>
          <a href="/landing" style={buttonStyle}>Landing</a>
          <a href="/" style={secondaryButtonStyle}>App login</a>
        </div>
      </section>
    </main>
  );
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ border: "1px solid #e5e7eb", borderRadius: 18, padding: 16 }}>
      <p style={{ margin: 0, color: "#64748b", fontSize: 13 }}>{label}</p>
      <p style={{ margin: "8px 0 0", fontSize: 22, fontWeight: 800, color: statusColor(value) }}>{value}</p>
    </div>
  );
}

const buttonStyle = {
  display: "inline-flex",
  background: "#111827",
  color: "white",
  padding: "10px 16px",
  borderRadius: 12,
  textDecoration: "none",
  fontWeight: 700,
};

const secondaryButtonStyle = {
  ...buttonStyle,
  background: "#f1f5f9",
  color: "#111827",
};
