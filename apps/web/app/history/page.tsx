"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function History() {
  const [subscriptionId, setSubscriptionId] = useState("");
  const [runs, setRuns] = useState<any[]>([]);
  const [status, setStatus] = useState("");

  async function load() {
    setStatus("Loading...");
    const data = await fetch(`${API_BASE}/v1/subscriptions/${subscriptionId}/runs`).then(r => r.json());
    setRuns(data);
    setStatus(`Loaded ${data.length} runs`);
  }

  return (
    <main>
      <h3>History</h3>
      <p style={{ opacity: 0.8 }}>Paste a subscription ID to view its send history.</p>

      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <input style={{ flex: 1, padding: 8 }} placeholder="subscription id" value={subscriptionId} onChange={e => setSubscriptionId(e.target.value)} />
        <button onClick={load} style={{ padding: "10px 14px" }}>Load</button>
      </div>
      <div style={{ fontFamily: "ui-monospace", fontSize: 12, marginTop: 8 }}>{status}</div>

      <div style={{ marginTop: 16, display: "grid", gap: 12 }}>
        {runs.map(r => (
          <div key={r.id} style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
            <div><strong>{r.subject || "(no subject)"}</strong></div>
            <div style={{ opacity: 0.8, fontSize: 12 }}>{r.run_at} — {r.status}</div>
            {r.error ? <pre style={{ whiteSpace: "pre-wrap" }}>{r.error}</pre> : null}
            {r.text ? <details><summary>Text</summary><pre style={{ whiteSpace: "pre-wrap" }}>{r.text}</pre></details> : null}
          </div>
        ))}
      </div>
    </main>
  );
}
