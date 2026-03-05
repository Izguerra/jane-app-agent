"use client";

import { useState, useEffect } from "react";
import useSWR, { mutate } from "swr";
import { useSearchParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { PhoneManagement } from "./_components/phone-management";
import { JaneAppIntegration } from "./_components/jane-app";
import { WhatsAppTwilio } from "./_components/whatsapp-twilio";
import { WhatsAppMeta } from "./_components/whatsapp-meta";
import { InstagramIntegration } from "./_components/instagram";
import { ShopifyIntegration } from "./_components/shopify";
import { SalesforceIntegration } from "./_components/salesforce";
import { GoogleCalendarIntegration } from "./_components/google-calendar";
import { MicrosoftExchangeIntegration } from "./_components/microsoft-exchange";
import { WebsiteWidget } from "./_components/website-widget";
// New Integrations
import { GmailMailboxIntegration } from "./_components/gmail-mailbox";
import { OutlookMailboxIntegration } from "./_components/outlook-mailbox";
import { ICloudMailboxIntegration } from "./_components/icloud-mailbox";
import { OutlookCalendarIntegration } from "./_components/outlook-calendar";
import { ICloudCalendarIntegration } from "./_components/icloud-calendar";
import { GoogleDriveIntegration } from "./_components/google-drive";
import { TavusIntegration } from "./_components/tavus-avatar";
import { OpenClawIntegration } from "./_components/openclaw";
import { MCPServersSection } from "./_components/mcp-servers";

const fetcher = (url: string) =>
    fetch(url, { credentials: 'include' }).then(async (res) => {
        if (!res.ok) {
            const text = await res.text();
            throw new Error(text || 'API Error');
        }
        return res.json();
    });

export default function IntegrationsPage() {
    const { data: rawIntegrations, error } = useSWR("/api/agent/integrations", fetcher);
    // Ensure integrations is always an array
    const integrations = Array.isArray(rawIntegrations) ? rawIntegrations : [];

    const { data: settings } = useSWR("/api/agent/settings", fetcher);
    const { data: phoneNumbers } = useSWR("/api/agent/phone-numbers", fetcher);
    const workspaceId = settings?.workspace_id;

    const [expanded, setExpanded] = useState<string | null>(null);
    const searchParams = useSearchParams();
    const router = useRouter();

    useEffect(() => {
        if (searchParams?.get("success")) {
            mutate("/api/agent/integrations");
            toast.success("Integration connected successfully");
            // Clean up URL
            const newUrl = window.location.pathname;
            window.history.replaceState({}, '', newUrl);
        }
    }, [searchParams]);

    useEffect(() => {
        if (searchParams?.get("success")) {
            mutate("/api/agent/integrations");
            toast.success("Integration connected successfully");
            // Clean up URL
            const newUrl = window.location.pathname;
            window.history.replaceState({}, '', newUrl);
        }
    }, [searchParams]);

    const toggleExpand = (provider: string) => {
        setExpanded(expanded === provider ? null : provider);
    };

    return (
        <div className="max-w-4xl mx-auto py-8 space-y-8">
            {/* Communication Channels */}
            <section>
                <h2 className="text-lg font-semibold mb-4 text-muted-foreground">📱 Communication</h2>
                <div className="grid gap-4">
                    <PhoneManagement phoneNumbers={phoneNumbers} />
                    <WhatsAppTwilio integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                    <WhatsAppMeta integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                    <InstagramIntegration integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                    <WebsiteWidget workspaceId={workspaceId} expanded={expanded} onToggleExpand={toggleExpand} />
                </div>
            </section>

            {/* Mailbox Integrations */}
            <section>
                <h2 className="text-lg font-semibold mb-4 text-muted-foreground">📧 Mailboxes</h2>
                <div className="grid gap-4">
                    <GmailMailboxIntegration integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                    <OutlookMailboxIntegration integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                    <ICloudMailboxIntegration integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                </div>
            </section>

            {/* Calendar Integrations */}
            <section>
                <h2 className="text-lg font-semibold mb-4 text-muted-foreground">📅 Calendars</h2>
                <div className="grid gap-4">
                    <GoogleCalendarIntegration integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                    <OutlookCalendarIntegration integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                    <ICloudCalendarIntegration integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                </div>
            </section>

            {/* Cloud Storage */}
            <section>
                <h2 className="text-lg font-semibold mb-4 text-muted-foreground">📁 Cloud Storage</h2>
                <div className="grid gap-4">
                    <GoogleDriveIntegration integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                </div>
            </section>

            {/* AI & Avatars */}
            <section>
                <h2 className="text-lg font-semibold mb-4 text-muted-foreground">🤖 AI & Avatars</h2>
                <div className="grid gap-4">
                    <TavusIntegration integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                </div>
            </section>

            {/* MCP Servers */}
            <MCPServersSection />

            {/* Business Tools */}
            <section>
                <h2 className="text-lg font-semibold mb-4 text-muted-foreground">🏢 Business Tools</h2>
                <div className="grid gap-4">
                    <OpenClawIntegration integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                    <JaneAppIntegration integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                    <ShopifyIntegration integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                    <SalesforceIntegration integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                    <MicrosoftExchangeIntegration integrations={integrations} expanded={expanded} onToggleExpand={toggleExpand} />
                </div>
            </section>
        </div>
    );
}

