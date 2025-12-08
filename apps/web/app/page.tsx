import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, Mail, Settings, History } from "lucide-react";

export default function Home() {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <section className="py-12">
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">
          Your personalized news newsletter
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mb-8">
          Configure topics and sources, choose a frequency, and get an AI-powered email newsletter curated just for you.
        </p>
        <div className="flex flex-col sm:flex-row gap-4">
          <a href="/settings">
            <Button size="lg" className="w-full sm:w-auto">
              Get Started <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </a>
          <a href="/history">
            <Button size="lg" variant="outline" className="w-full sm:w-auto">
              View History
            </Button>
          </a>
        </div>
      </section>

      {/* Features Grid */}
      <section>
        <h2 className="text-2xl font-bold mb-6">How it works</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <Settings className="h-8 w-8 mb-2 text-primary" />
              <CardTitle>Configure</CardTitle>
              <CardDescription>Set up topics, sources, and preferences</CardDescription>
            </CardHeader>
            <CardContent>
              Choose from RSS feeds, NYT, X (Twitter), and more. Filter by topics and set your tone.
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Mail className="h-8 w-8 mb-2 text-primary" />
              <CardTitle>Generate</CardTitle>
              <CardDescription>AI creates your newsletter</CardDescription>
            </CardHeader>
            <CardContent>
              Our agent reads recent articles and writes a personalized summary just for you.
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <History className="h-8 w-8 mb-2 text-primary" />
              <CardTitle>Receive</CardTitle>
              <CardDescription>Get newsletters on schedule</CardDescription>
            </CardHeader>
            <CardContent>
              Emails arrive on your preferred schedule—daily, weekly, or custom cron.
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-muted rounded-lg p-8 text-center">
        <h2 className="text-3xl font-bold mb-4">Ready to get started?</h2>
        <p className="text-muted-foreground mb-6 max-w-xl mx-auto">
          Configure your first newsletter and send a test email to see it in action.
        </p>
        <a href="/settings">
          <Button size="lg">Go to Settings</Button>
        </a>
      </section>
    </div>
  );
}
