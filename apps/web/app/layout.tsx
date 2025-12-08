export const metadata = {
  title: "Newsletter Agent",
  description: "Build your personalized industry news newsletter",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "ui-sans-serif, system-ui", margin: 0 }}>
        <div style={{ maxWidth: 920, margin: "0 auto", padding: 20 }}>
          <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <a href="/" style={{ textDecoration: "none", color: "inherit" }}><h2>Newsletter Agent</h2></a>
            <nav style={{ display: "flex", gap: 12 }}>
              <a href="/settings">Settings</a>
              <a href="/history">History</a>
            </nav>
          </header>
          <hr />
          {children}
        </div>
      </body>
    </html>
  );
}
