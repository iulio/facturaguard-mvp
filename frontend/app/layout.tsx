import "./styles.css";

export const metadata = {
  title: "FacturaGuard MVP",
  description: "Monitorizare RO e-Factura",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ro">
      <body>{children}</body>
    </html>
  );
}
