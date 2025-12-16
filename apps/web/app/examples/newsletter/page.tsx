"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export const dynamic = "force-static";

const WIDTH_PRESETS = [
  { key: "mobile", label: "Mobile", width: 375 },
  { key: "email", label: "Email", width: 640 },
  { key: "desktop", label: "Desktop", width: 960 },
];

export default function NewsletterExamplePage() {
  const [frameWidth, setFrameWidth] = useState<number>(640);

  return (
    <main className="mx-auto max-w-7xl p-6 space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-border bg-gradient-to-b from-background to-muted/40 p-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <a href="/">
              <Button variant="outline" size="sm">
                <ArrowLeft className="mr-2 h-4 w-4" /> Home
              </Button>
            </a>
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">Newsletter Example</h1>
              <p className="text-sm text-muted-foreground">Rendered from a generated HTML sample for quick preview.</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {WIDTH_PRESETS.map((p) => (
              <Button
                key={p.key}
                size="sm"
                variant={frameWidth === p.width ? "default" : "outline"}
                onClick={() => setFrameWidth(p.width)}
              >
                {p.label}
              </Button>
            ))}
            <a
              href="/examples/newsletter.html"
              target="_blank"
              rel="noreferrer"
              className="text-sm underline underline-offset-4 text-primary ml-2"
            >
              Open raw HTML ↗
            </a>
          </div>
        </div>
      </div>

      {/* Preview surface */}
      <div className="rounded-xl border border-border bg-background p-4 md:p-6">
        <div className="mx-auto overflow-hidden rounded-lg border shadow-sm bg-white" style={{ width: frameWidth }}>
          <div className="flex items-center justify-between px-3 py-2 border-b bg-muted/30">
            <div className="flex items-center gap-1">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-400" />
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-yellow-400" />
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-green-400" />
            </div>
            <span className="text-xs text-muted-foreground">Preview • {frameWidth}px</span>
          </div>
          <iframe
            src="/examples/newsletter.html"
            title="Newsletter Preview"
            className="block w-full"
            style={{ height: 900, border: 0 }}
          />
        </div>
        <p className="mt-4 text-xs text-muted-foreground">
          Tip: Use the presets above to check readability across common widths.
        </p>
      </div>
    </main>
  );
}
