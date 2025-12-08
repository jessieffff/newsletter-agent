"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Mail, Settings as SettingsIcon, FileText, X as XIcon } from "lucide-react";

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

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  rss: "📡",
  nyt: "📰",
  x: "𝕏",
  domain: "🌐",
};

export default function Settings() {
  const [email, setEmail] = useState("demo@example.com");
  const [topics, setTopics] = useState("ai agents, cloud, startups");
  const [rss, setRss] = useState("https://www.theverge.com/rss/index.xml");
  const [itemCount, setItemCount] = useState(8);
  const [tone, setTone] = useState("concise, professional");
  const [status, setStatus] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  const topicList = useMemo(
    () => topics.split(",").map(t => t.trim()).filter(Boolean),
    [topics]
  );

  const sourcesList = useMemo(
    () => rss ? [{ kind: "rss" as const, value: rss }] : [],
    [rss]
  );

  const payload: SubscriptionIn = useMemo(() => ({
    topics: topicList,
    sources: sourcesList,
    frequency: "daily",
    cron: null,
    item_count: itemCount,
    tone,
    enabled: true,
  }), [topicList, sourcesList, itemCount, tone]);

  async function save() {
    setIsLoading(true);
    setStatus("Saving...");
    try {
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

      setStatus(`✓ Saved subscription ${sub.id}`);
    } catch (error) {
      setStatus(`✗ Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function runNow() {
    setIsLoading(true);
    setStatus("Running...");
    try {
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

      setStatus(`✓ Run ${run.id}: ${run.status}`);
    } catch (error) {
      setStatus(`✗ Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <SettingsIcon className="h-8 w-8" />
          Newsletter Settings
        </h1>
        <p className="text-muted-foreground">
          Configure your newsletter preferences and test the generation
        </p>
      </div>

      <Tabs defaultValue="content" className="space-y-4">
        <TabsList className="grid w-full max-w-md grid-cols-3">
          <TabsTrigger value="content" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            <span className="hidden sm:inline">Content</span>
          </TabsTrigger>
          <TabsTrigger value="sources" className="flex items-center gap-2">
            <Mail className="h-4 w-4" />
            <span className="hidden sm:inline">Sources</span>
          </TabsTrigger>
          <TabsTrigger value="delivery" className="flex items-center gap-2">
            <SettingsIcon className="h-4 w-4" />
            <span className="hidden sm:inline">Delivery</span>
          </TabsTrigger>
        </TabsList>

        {/* Content Tab */}
        <TabsContent value="content" className="space-y-4">
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Input Panel */}
            <div className="lg:col-span-2 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Email & Content</CardTitle>
                  <CardDescription>
                    Set your email address and newsletter preferences
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Email Address</label>
                    <Input
                      type="email"
                      placeholder="your@email.com"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Topics (comma-separated)</label>
                    <Input
                      placeholder="e.g., ai agents, cloud, startups"
                      value={topics}
                      onChange={e => setTopics(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      These topics help filter content from your sources
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Tone & Style</label>
                    <Input
                      placeholder="e.g., concise, professional, casual"
                      value={tone}
                      onChange={e => setTone(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Describe how you'd like your newsletter written
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Items per newsletter</label>
                    <Input
                      type="number"
                      min={1}
                      max={20}
                      value={itemCount}
                      onChange={e => setItemCount(Number(e.target.value))}
                    />
                    <p className="text-xs text-muted-foreground">
                      How many articles to include (1-20)
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Preview Panel */}
            <div>
              <Card className="sticky top-24">
                <CardHeader>
                  <CardTitle className="text-base">Preview</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-muted-foreground uppercase">Email</p>
                    <p className="text-sm break-all">{email || "not set"}</p>
                  </div>

                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-muted-foreground uppercase">Topics</p>
                    <div className="flex flex-wrap gap-1">
                      {topicList.length > 0 ? (
                        topicList.map(topic => (
                          <Badge key={topic} variant="secondary" className="text-xs">
                            {topic}
                          </Badge>
                        ))
                      ) : (
                        <p className="text-xs text-muted-foreground">No topics set</p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-muted-foreground uppercase">Tone</p>
                    <p className="text-sm">{tone || "not set"}</p>
                  </div>

                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-muted-foreground uppercase">Items</p>
                    <p className="text-sm">{itemCount} per newsletter</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Sources Tab */}
        <TabsContent value="sources" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Content Sources</CardTitle>
              <CardDescription>
                Choose where your newsletter content comes from
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <span>📡 RSS Feed URL</span>
                  <Badge variant="outline" className="text-xs">Primary</Badge>
                </label>
                <Input
                  placeholder="https://example.com/feed.xml"
                  value={rss}
                  onChange={e => setRss(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Add a custom RSS feed for your newsletter content
                </p>
              </div>

              {/* Sources Chips */}
              {sourcesList.length > 0 && (
                <div className="space-y-3">
                  <p className="text-sm font-medium">Active Sources</p>
                  <div className="space-y-2">
                    {sourcesList.map((source, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-secondary rounded-lg">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{SOURCE_ICONS[source.kind] || "📄"}</span>
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-medium capitalize">{source.kind}</p>
                            <p className="text-xs text-muted-foreground truncate">{source.value}</p>
                          </div>
                        </div>
                        <button
                          onClick={() => setRss("")}
                          className="text-muted-foreground hover:text-foreground transition-colors"
                        >
                          <XIcon className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Coming Soon Sources */}
              <div className="space-y-3">
                <p className="text-sm font-medium text-muted-foreground">Coming Soon</p>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { icon: "📰", name: "NYT", disabled: true },
                    { icon: "𝕏", name: "X (Twitter)", disabled: true },
                    { icon: "🌐", name: "Custom Domain", disabled: true },
                  ].map(source => (
                    <button
                      key={source.name}
                      disabled
                      className="p-3 border border-border rounded-lg text-center opacity-50 cursor-not-allowed"
                    >
                      <div className="text-xl mb-1">{source.icon}</div>
                      <p className="text-xs font-medium">{source.name}</p>
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Delivery Tab */}
        <TabsContent value="delivery" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Delivery & Testing</CardTitle>
              <CardDescription>
                Configure when you receive newsletters and test them
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <p className="text-sm font-medium">Frequency</p>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { label: "Daily", value: "daily" },
                    { label: "Weekly", value: "weekly" },
                    { label: "Custom", value: "custom_cron" },
                  ].map(freq => (
                    <button
                      key={freq.value}
                      className="p-3 border border-border rounded-lg text-center hover:bg-accent transition-colors"
                    >
                      <p className="text-sm font-medium">{freq.label}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-2 pt-4 border-t">
                <p className="text-sm font-medium">Test Your Newsletter</p>
                <div className="flex flex-col gap-2">
                  <Button
                    onClick={save}
                    disabled={isLoading}
                    className="w-full"
                  >
                    {isLoading ? "Saving..." : "Save Settings"}
                  </Button>
                  <Button
                    onClick={runNow}
                    disabled={isLoading}
                    variant="outline"
                    className="w-full"
                  >
                    {isLoading ? "Running..." : "Send Test Email"}
                  </Button>
                </div>
              </div>

              {/* Status Message */}
              {status && (
                <div className={`p-3 rounded-lg text-sm font-mono text-xs ${
                  status.startsWith("✓")
                    ? "bg-green-50 text-green-800 border border-green-200 dark:bg-green-900/20 dark:border-green-800 dark:text-green-300"
                    : status.startsWith("✗")
                    ? "bg-red-50 text-red-800 border border-red-200 dark:bg-red-900/20 dark:border-red-800 dark:text-red-300"
                    : "bg-blue-50 text-blue-800 border border-blue-200 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-300"
                }`}>
                  {status}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
