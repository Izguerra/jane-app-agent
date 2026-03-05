"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ChevronDown, ChevronUp, Mail } from "lucide-react";
import { toast } from "sonner";
import { mutate } from "swr";
import { toggleIntegration } from "./utils";

interface GmailMailboxProps {
    integrations: any[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function GmailMailboxIntegration({ integrations, expanded, onToggleExpand }: GmailMailboxProps) {
    const isExpanded = expanded === 'gmail_mailbox';
    const isActive = integrations?.some((i: any) => i.provider === 'gmail_mailbox' && i.is_active) ?? false;

    async function handleConnectGmail() {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
        window.location.assign(`${backendUrl}/api/auth/gmail/login`);
    }

    const updatePermission = async (permission: string, checked: boolean) => {
        const integration = integrations?.find((i: any) => i.provider === 'gmail_mailbox');
        const currentSettings = integration?.settings && typeof integration.settings === 'string'
            ? JSON.parse(integration.settings)
            : (integration?.settings || {});

        const credentials = integration?.credentials && typeof integration.credentials === 'string'
            ? JSON.parse(integration.credentials)
            : (integration?.credentials || {});

        const newSettings = { ...currentSettings, [permission]: checked };

        await fetch(`/api/agent/integrations/gmail_mailbox`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: 'gmail_mailbox',
                credentials: credentials,
                settings: newSettings
            })
        });
        mutate("/api/agent/integrations");
        toast.success(checked ? "Permission enabled" : "Permission disabled");
    };

    const getPermission = (permission: string) => {
        const integration = integrations?.find((i: any) => i.provider === 'gmail_mailbox');
        if (!integration?.settings) return false;
        const settings = typeof integration.settings === 'string' ? JSON.parse(integration.settings) : integration.settings;
        return settings[permission] || false;
    };

    return (
        <Card>
            <CardHeader className="cursor-pointer" onClick={() => onToggleExpand('gmail_mailbox')}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <Mail className="h-5 w-5 text-red-500" />
                        <CardTitle>Gmail</CardTitle>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                    <Switch
                        checked={isActive}
                        onCheckedChange={(c) => toggleIntegration('gmail_mailbox', c)}
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
                <CardDescription>Read and send emails via Gmail</CardDescription>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-4">
                    <div className="p-4 bg-muted rounded-lg text-sm">
                        <p>Connect your Gmail account to allow agents to read and send emails on your behalf.</p>
                    </div>

                    {isActive && (
                        <div className="space-y-4 p-4 border rounded-lg">
                            <h4 className="font-semibold text-sm">Email Permissions</h4>
                            <p className="text-xs text-muted-foreground">Control what agents can do with your emails</p>

                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="can-read">Read emails</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to view your inbox</p>
                                    </div>
                                    <Switch
                                        id="can-read"
                                        checked={getPermission('can_read_emails')}
                                        onCheckedChange={(c) => updatePermission('can_read_emails', c)}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="can-send">Send emails</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to send emails from your account</p>
                                    </div>
                                    <Switch
                                        id="can-send"
                                        checked={getPermission('can_send_emails')}
                                        onCheckedChange={(c) => updatePermission('can_send_emails', c)}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="can-search">Search emails</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to search your inbox</p>
                                    </div>
                                    <Switch
                                        id="can-search"
                                        checked={getPermission('can_search_emails')}
                                        onCheckedChange={(c) => updatePermission('can_search_emails', c)}
                                    />
                                </div>
                            </div>
                        </div>
                    )}

                    <Button
                        type="button"
                        variant={isActive ? "destructive" : "outline"}
                        onClick={() => {
                            if (isActive) {
                                toggleIntegration('gmail_mailbox', false);
                            } else {
                                handleConnectGmail();
                            }
                        }}
                    >
                        {isActive ? "Disconnect Gmail" : "Connect Gmail Account"}
                    </Button>
                </CardContent>
            )}
        </Card>
    );
}
