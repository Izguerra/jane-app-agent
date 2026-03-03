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

interface WhatsAppTwilioProps {
    integrations: any[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function WhatsAppTwilio({ integrations, expanded, onToggleExpand }: WhatsAppTwilioProps) {
    const isExpanded = expanded === 'whatsapp';
    const isActive = integrations?.some((i: any) => i.provider === 'whatsapp' && i.is_active) ?? false;

    // State for WhatsApp credentials
    const [whatsappPhone, setWhatsappPhone] = useState("");
    const [whatsappSid, setWhatsappSid] = useState("");
    const [whatsappToken, setWhatsappToken] = useState("");

    async function handleConnectWhatsApp() {
        if (!whatsappPhone) {
            toast.error("Please enter a WhatsApp phone number");
            return;
        }
        if (!whatsappSid) {
            toast.error("Please enter your Account SID");
            return;
        }
        if (!whatsappSid.startsWith("AC")) {
            toast.error("Account SID must start with 'AC'");
            return;
        }
        if (!whatsappToken) {
            toast.error("Please enter your Auth Token");
            return;
        }

        try {
            console.log("Sending request to connect WhatsApp");
            const response = await fetch(`/api/agent/integrations/whatsapp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: 'whatsapp',
                    credentials: {
                        phone_number: whatsappPhone,
                        account_sid: whatsappSid, // Optional, can use env vars if empty
                        auth_token: whatsappToken // Optional
                    },
                    settings: {}
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            toast.success("WhatsApp connected successfully");
            mutate("/api/agent/integrations");
            // Clear sensitive fields
            setWhatsappSid("");
            setWhatsappToken("");
        } catch (error: any) {
            console.error("Error connecting WhatsApp:", error);
            toast.error(error.message || "Failed to connect WhatsApp");
        }
    }

    return (
        <Card>
            <CardHeader className="cursor-pointer" onClick={() => onToggleExpand('whatsapp')}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <CardTitle>WhatsApp (Twilio)</CardTitle>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                    <Switch
                        checked={isActive}
                        onCheckedChange={(c) => toggleIntegration('whatsapp', c)}
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
                <CardDescription>Connect WhatsApp for messaging (via Twilio)</CardDescription>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-4">
                    <div className="p-4 bg-muted rounded-lg text-sm space-y-2">
                        <p className="font-semibold">Setup Instructions:</p>
                        <ol className="list-decimal list-inside space-y-1 text-xs">
                            <li>Sign up for a <strong>Twilio account</strong> at <a href="https://www.twilio.com/try-twilio" target="_blank" className="text-blue-600 underline">twilio.com</a></li>
                            <li>Go to <strong>Messaging</strong> → <strong>Try it out</strong> → <strong>Send a WhatsApp message</strong></li>
                            <li>Follow the steps to get a <strong>WhatsApp Sandbox number</strong> (e.g., <code>whatsapp:+14155238886</code>)</li>
                            <li>Users must text a code (e.g., "join [code]") to your sandbox number to opt-in</li>
                            <li><strong>Optional:</strong> For production, apply for a <strong>WhatsApp Business Account</strong> (requires approval)</li>
                            <li>Find your <strong>Account SID</strong> and <strong>Auth Token</strong> in the Twilio Console Dashboard</li>
                            <li>Set your <strong>Webhook URL</strong> to: <code>{typeof window !== 'undefined' ? `${window.location.origin}/api/webhooks/whatsapp` : ''}</code></li>
                        </ol>
                    </div>

                    <div className="grid gap-2">
                        <Label htmlFor="whatsapp-phone">WhatsApp Number <span className="text-red-500">*</span></Label>
                        <Input
                            id="whatsapp-phone"
                            type="text"
                            placeholder="whatsapp:+14155238886"
                            value={whatsappPhone}
                            onChange={(e) => setWhatsappPhone(e.target.value)}
                            disabled={isActive}
                        />
                        <p className="text-xs text-muted-foreground">Format: whatsapp:+1[number]</p>
                    </div>

                    {!isActive && (
                        <>
                            <div className="grid gap-2">
                                <Label htmlFor="wa-account-sid">Account SID <span className="text-red-500">*</span></Label>
                                <Input
                                    id="wa-account-sid"
                                    placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                                    value={whatsappSid}
                                    onChange={(e) => setWhatsappSid(e.target.value)}
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="wa-auth-token">Auth Token <span className="text-red-500">*</span></Label>
                                <Input
                                    id="wa-auth-token"
                                    type="password"
                                    placeholder="••••••••••••••••"
                                    value={whatsappToken}
                                    onChange={(e) => setWhatsappToken(e.target.value)}
                                />
                            </div>
                        </>
                    )}

                    <Button
                        variant={isActive ? "destructive" : "outline"}
                        onClick={() => {
                            if (isActive) {
                                toggleIntegration('whatsapp', false);
                            } else {
                                handleConnectWhatsApp();
                            }
                        }}
                    >
                        {isActive ? "Disconnect WhatsApp (Twilio)" : "Connect WhatsApp (Twilio)"}
                    </Button>
                </CardContent>
            )}
        </Card>
    );
}
