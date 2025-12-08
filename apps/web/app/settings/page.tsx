"use client";

import { useMemo, useState } from "react";

type SourceSpec = { kind: "rss" | "nyt" | "x" | "domain"; value: string };
type SubscriptionIn = {
  topics: string[];
  sources: SourceSpec[];
  frequency: "daily" | "weekly" | "custom_cron";
  cron?: string | null;
  item_count: number;
  tone: string;
  enabled: boolean;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function Settings() {
  const [email, setEmail] = useState("demo@example.com");
  const [topics, setTopics] = useState("ai agents, cloud, startups");
  const [rss, setRss] = useState("https://www.theverge.com/rss/index.xml");
  const [itemCount, setItemCount] = useState(8);
  const [tone, setTone] = useState("concise, professional");
  const [status, setStatus] = useState<string>("");

  const payload: SubscriptionIn = useMemo(() => ({
    topics: topics.split(",").map(t => t.trim()).filter(Boolean),
    sources: rss ? [{ kind: "rss", value: rss }] : [],
    frequency: "daily",
    cron: null,
    item_count: itemCount,
    tone,
    enabled: true,
  }), [topics, rss, itemCount, tone]);

  async function save() {
    setStatus("Saving...");
    const u = await fetch(`${API_BASE}/v1/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    }).then(r => r.json());

    const sub = await fetch(`${API_BASE}/v1/users/${u.id}/subscriptions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(r => r.json());

    setStatus(`Saved subscription ${sub.id}.`);
  }

  async function runNow() {
    setStatus("Running...");
    // naive: create a user + a new sub each time; MVP only
    const u = await fetch(`${API_BASE}/v1/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    }).then(r => r.json());

    const sub = await fetch(`${API_BASE}/v1/users/${u.id}/subscriptions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(r => r.json());

    const run = await fetch(`${API_BASE}/v1/subscriptions/${sub.id}/run?user_email=${encodeURIComponent(email)}`, {
      method: "POST",
    }).then(r => r.json());

    setStatus(`Run ${run.id}: ${run.status}`);
  }

  return (
    <main>
      <h3>Settings</h3>
      <p style={{ opacity: 0.8 }}>MVP UI (no auth). Save your preferences and send a test newsletter.</p>

      <div style={{ display: "grid", gap: 10, maxWidth: 640 }}>
        <label>
          Email
          <input style={{ width: "100%", padding: 8 }} value={email} onChange={e => setEmail(e.target.value)} />
        </label>

        <label>
          Topics (comma-separated)
          <input style={{ width: "100%", padding: 8 }} value={topics} onChange={e => setTopics(e.target.value)} />
        </label>

        <label>
          RSS feed URL (optional)
          <input style={{ width: "100%", padding: 8 }} value={rss} onChange={e => setRss(e.target.value)} />
        </label>

        <label>
          Number of items
          <input type="number" min={1} max={20} style={{ width: "100%", padding: 8 }} value={itemCount} onChange={e => setItemCount(Number(e.target.value))} />
        </label>

        <label>
          Tone
          <input style={{ width: "100%", padding: 8 }} value={tone} onChange={e => setTone(e.target.value)} />
        </label>

        <div style={{ display: "flex", gap: 10 }}>
          <button onClick={save} style={{ padding: "10px 14px" }}>Save</button>
          <button onClick={runNow} style={{ padding: "10px 14px" }}>Send test email</button>
        </div>

        <div style={{ fontFamily: "ui-monospace", fontSize: 12 }}>{status}</div>
      </div>
    </main>
  );
}
