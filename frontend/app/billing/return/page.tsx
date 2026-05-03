"use client";

import { useEffect, useState } from "react";

export default function BillingReturnPage() {
  const [params, setParams] = useState("");

  useEffect(() => {
    setParams(window.location.search || "");
  }, []);

  return (
    <main className="container">
      <div className="card" style={{ maxWidth: 640, margin: "40px auto" }}>
        <h1>Întoarcere din NETOPIA</h1>
        <p>Am primit întoarcerea din pagina de plată. Statusul final va fi confirmat prin IPN/webhook NETOPIA.</p>
        {params && (
          <>
            <h3>Parametri return</h3>
            <pre style={{ whiteSpace: "pre-wrap" }}>{params}</pre>
          </>
        )}
        <a className="btn" href="/">Înapoi la dashboard</a>
      </div>
    </main>
  );
}
