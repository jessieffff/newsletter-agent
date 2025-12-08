import "./globals.css"

export const metadata = {
  title: "Newsletter Agent",
  description: "Build your personalized industry news newsletter",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-background text-foreground antialiased">
        <div className="min-h-screen">
          <header className="border-b border-border sticky top-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
              <div className="flex items-center justify-between">
                <a href="/" className="text-2xl font-bold font-semibold hover:opacity-80 transition-opacity">
                  📧 Newsletter Agent
                </a>
                <nav className="flex items-center gap-6">
                  <a href="/settings" className="text-sm font-medium hover:text-foreground/80 transition-colors">
                    Settings
                  </a>
                  <a href="/history" className="text-sm font-medium hover:text-foreground/80 transition-colors">
                    History
                  </a>
                </nav>
              </div>
            </div>
          </header>
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
