import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, Mail, Settings as SettingsIcon, History } from "lucide-react";

export default function Home() {
  return (
    <div className="space-y-6">
      {/* Header (matches Settings/Example tone) */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Welcome to Newsletter Agent</h1>
        <p className="text-muted-foreground">Configure topics, generate a sample, and schedule delivery.</p>
      </div>

      {/* Get Started Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <SettingsIcon className="h-6 w-6" />
            Get Started
          </CardTitle>
          <CardDescription>Set your preferences and try a sample generation.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col sm:flex-row gap-3">
          <a href="/settings">
            <Button className="w-full sm:w-auto">
              Open Settings <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </a>
          <a href="/examples/newsletter">
            <Button variant="outline" className="w-full sm:w-auto">View Example</Button>
          </a>
          <a href="/history">
            <Button variant="ghost" className="w-full sm:w-auto">View History</Button>
          </a>
        </CardContent>
      </Card>

      {/* How it works */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">How it works</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <SettingsIcon className="h-7 w-7 text-primary" />
              <CardTitle>Configure</CardTitle>
              <CardDescription>Choose topics, tone, and sources</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              Add RSS feeds and select your style. The agent will focus on what matters.
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <Mail className="h-7 w-7 text-primary" />
              <CardTitle>Generate</CardTitle>
              <CardDescription>AI writes concise summaries</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              It summarizes fresh articles and formats an email-friendly newsletter.
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <History className="h-7 w-7 text-primary" />
              <CardTitle>Deliver</CardTitle>
              <CardDescription>Send on your schedule</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              Receive emails daily, weekly, or via a custom schedule.
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Final CTA */}
      <Card>
        <CardContent className="p-6 flex flex-col items-center text-center gap-3">
          <h3 className="text-xl font-semibold">Ready to get started?</h3>
          <p className="text-muted-foreground max-w-xl">Open settings to configure your first newsletter and send a test email.</p>
          <a href="/settings">
            <Button size="lg">Go to Settings</Button>
          </a>
        </CardContent>
      </Card>
    </div>
  );
}
