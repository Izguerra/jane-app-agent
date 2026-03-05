"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { mutate } from "swr";
import { toggleIntegration } from "./utils";

interface TelnyxProps {
    integrations: any[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function TelnyxIntegration({ integrations, expanded, onToggleExpand }: TelnyxProps) {
    const isExpanded = expanded === 'telnyx';
    const isActive = integrations?.some((i: any) => i.provider === 'telnyx' && i.is_active) ?? false;
    const integration = integrations?.find((i: any) => i.provider === 'telnyx');

    // State for Telnyx credentials
    const [apiKey, setApiKey] = useState("");
    const [publicKey, setPublicKey] = useState("");

    async function handleConnectTelnyx() {
        if (!apiKey) {
            toast.error("Please enter your Telnyx API Key");
            return;
        }

        try {
            console.log("Sending request to connect Telnyx");
            const response = await fetch(`/api/agent/integrations/telnyx`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: 'telnyx',
                    credentials: {
                        api_key: apiKey,
                    },
                    settings: {
                        public_key: publicKey
                    }
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            toast.success("Telnyx connected successfully");
            mutate("/api/agent/integrations");
            // Clear sensitive fields
            setApiKey("");
        } catch (error: any) {
            console.error("Error connecting Telnyx:", error);
            toast.error(error.message || "Failed to connect Telnyx");
        }
    }

    const sipUri = typeof window !== 'undefined' ? `sip:workspace@${window.location.hostname}` : 'sip:workspace@yourdomain.com';
    const webhookUrl = typeof window !== 'undefined' ? `${window.location.origin}/api/telnyx/texml/inbound` : '';

    return (
        <Card>
            <CardHeader className="cursor-pointer" onClick={() => onToggleExpand('telnyx')}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <CardTitle>Telnyx</CardTitle>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                    <Switch
                        checked={isActive}
                        onCheckedChange={(c) => toggleIntegration('telnyx', c)}
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
                <CardDescription>Connect Telnyx for SMS and Voice (Cost-effective Twilio Alternative)</CardDescription>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-4">
                    <div className="p-4 bg-muted rounded-lg text-sm space-y-2">
                        <p className="font-semibold">Setup Instructions:</p>
                        <ol className="list-decimal list-inside space-y-1 text-xs">
                            <li>Sign up for a <strong>Telnyx account</strong> at <a href="https://telnyx.com/" target="_blank" className="text-blue-600 underline">telnyx.com</a></li>
                            <li>Go to <strong>Keys & Credentials</strong> → <strong>API Keys</strong> to generate an API Key.</li>
                            <li>Enter your API Key below to connect your account.</li>
                            <li><strong>To connect your existing PBX or phone numbers:</strong> Create a <strong>TeXML Application</strong> in Telnyx.</li>
                            <li>Set the TeXML Application's <strong>Webhook URL</strong> to: <code>{webhookUrl}</code></li>
                        </ol>
                    </div>

                    {isActive && (
                        <div className="p-4 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800 rounded-lg text-sm space-y-2">
                            <p className="font-semibold text-emerald-800 dark:text-emerald-300">PBX / SIP Integration Guidance</p>
                            <p className="text-xs text-muted-foreground">To route calls from your existing PBX to our AI agents, configure your Telnyx SIP Connection or TeXML Application with the following details:</p>
                            <div className="mt-2 space-y-2">
                                <div>
                                    <Label className="text-xs font-semibold">Inbound Webhook URL (TeXML):</Label>
                                    <code className="block mt-1 p-2 bg-background border rounded text-xs break-all">{webhookUrl}</code>
                                </div>
                                <div>
                                    <Label className="text-xs font-semibold">SIP URI (Direct SIP Routing):</Label>
                                    <code className="block mt-1 p-2 bg-background border rounded text-xs">{sipUri}</code>
                                </div>
                            </div>
                        </div>
                    )}

                    {!isActive && (
                        <>
                            <div className="grid gap-2">
                                <Label htmlFor="telnyx-api-key">API Key (V2) <span className="text-red-500">*</span></Label>
                                <Input
                                    id="telnyx-api-key"
                                    type="password"
                                    placeholder="KEYxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                                    value={apiKey}
                                    onChange={(e) => setApiKey(e.target.value)}
                                />
                                <p className="text-xs text-muted-foreground">Used for provisioning and sending SMS.</p>
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="telnyx-public-key">Public Key (Optional)</Label>
                                <Input
                                    id="telnyx-public-key"
                                    type="text"
                                    placeholder="Enter your Telnyx Public Key for webhook validation"
                                    value={publicKey}
                                    onChange={(e) => setPublicKey(e.target.value)}
                                />
                            </div>
                        </>
                    )}

                    <Button
                        variant={isActive ? "destructive" : "outline"}
                        onClick={() => {
                            if (isActive) {
                                toggleIntegration('telnyx', false);
                            } else {
                                handleConnectTelnyx();
                            }
                        }}
                    >
                        {isActive ? "Disconnect Telnyx" : "Connect Telnyx"}
                    </Button>
                </CardContent>
            )}
        </Card>
    );
}
