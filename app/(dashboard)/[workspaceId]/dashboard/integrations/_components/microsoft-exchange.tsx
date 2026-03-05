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

interface ExchangeProps {
    integrations: any[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function MicrosoftExchangeIntegration({ integrations, expanded, onToggleExpand }: ExchangeProps) {
    const isExpanded = expanded === 'exchange';
    const isActive = integrations?.some((i: any) => i.provider === 'exchange' && i.is_active) ?? false;

    // State for Exchange credentials
    const [exchangeEmail, setExchangeEmail] = useState("");
    const [exchangeServer, setExchangeServer] = useState("");
    const [exchangePassword, setExchangePassword] = useState("");

    async function handleConnectExchange() {
        console.log("handleConnectExchange called");
        if (!exchangeEmail || !exchangeServer || !exchangePassword) {
            toast.error("Please fill in all Exchange fields");
            return;
        }
        if (!exchangeEmail.includes("@")) {
            toast.error("Please enter a valid email address");
            return;
        }

        try {
            console.log("Sending request to connect Microsoft Exchange");
            const response = await fetch(`/api/agent/integrations/exchange`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: 'exchange',
                    credentials: {
                        email: exchangeEmail,
                        server: exchangeServer,
                        password: exchangePassword
                    },
                    settings: {}
                })
            });
            console.log("Exchange response received:", response.status);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            toast.success("Microsoft Exchange connected successfully");
            mutate("/api/agent/integrations");
            // Clear sensitive fields
            setExchangePassword("");
        } catch (error: any) {
            console.error("Error connecting Microsoft Exchange:", error);
            toast.error(error.message || "Failed to connect Microsoft Exchange");
        }
    }

    const updatePermission = async (permission: string, checked: boolean) => {
        const integration = integrations?.find((i: any) => i.provider === 'exchange');
        const currentSettings = integration?.settings && typeof integration.settings === 'string'
            ? JSON.parse(integration.settings)
            : (integration?.settings || {});

        const credentials = integration?.credentials && typeof integration.credentials === 'string'
            ? JSON.parse(integration.credentials)
            : (integration?.credentials || {});

        const newSettings = { ...currentSettings, [permission]: checked };

        await fetch(`/api/agent/integrations/exchange`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: 'exchange',
                credentials: credentials,
                settings: newSettings
            })
        });
        mutate("/api/agent/integrations");
        toast.success(checked ? "Permission enabled" : "Permission disabled");
    };

    const getPermission = (permission: string) => {
        const integration = integrations?.find((i: any) => i.provider === 'exchange');
        if (!integration?.settings) return false;
        const settings = typeof integration.settings === 'string' ? JSON.parse(integration.settings) : integration.settings;
        return settings[permission] || false;
    };

    return (
        <Card>
            <CardHeader className="cursor-pointer" onClick={() => onToggleExpand('exchange')}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <CardTitle>Microsoft Exchange</CardTitle>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                    <Switch
                        checked={isActive}
                        onCheckedChange={(c) => toggleIntegration('exchange', c)}
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
                <CardDescription>Sync appointments with Microsoft Exchange</CardDescription>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-4">
                    <div className="grid gap-2">
                        <Label htmlFor="exchange-email">Email <span className="text-red-500">*</span></Label>
                        <Input
                            id="exchange-email"
                            type="email"
                            placeholder="user@company.com"
                            value={exchangeEmail}
                            onChange={(e) => setExchangeEmail(e.target.value)}
                            disabled={isActive}
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="exchange-server">Server <span className="text-red-500">*</span></Label>
                        <Input
                            id="exchange-server"
                            type="text"
                            placeholder="outlook.office365.com"
                            value={exchangeServer}
                            onChange={(e) => setExchangeServer(e.target.value)}
                            disabled={isActive}
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="exchange-password">Password <span className="text-red-500">*</span></Label>
                        <Input
                            id="exchange-password"
                            type="password"
                            placeholder="••••••••"
                            value={exchangePassword}
                            onChange={(e) => setExchangePassword(e.target.value)}
                            disabled={isActive}
                        />
                    </div>

                    {isActive && (
                        <div className="space-y-4 p-4 border rounded-lg">
                            <h4 className="font-semibold text-sm">Calendar Permissions</h4>
                            <p className="text-xs text-muted-foreground">Control what the AI agents can do with your calendar events</p>

                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="exchange-can-view">View own events</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to check calendar availability</p>
                                    </div>
                                    <Switch
                                        id="exchange-can-view"
                                        checked={getPermission('can_view_own_events')}
                                        onCheckedChange={(c) => updatePermission('can_view_own_events', c)}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="exchange-can-edit">Edit own events</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to modify existing events</p>
                                    </div>
                                    <Switch
                                        id="exchange-can-edit"
                                        checked={getPermission('can_edit_own_events')}
                                        onCheckedChange={(c) => updatePermission('can_edit_own_events', c)}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="exchange-can-delete">Delete own events</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to cancel appointments</p>
                                    </div>
                                    <Switch
                                        id="exchange-can-delete"
                                        checked={getPermission('can_delete_own_events')}
                                        onCheckedChange={(c) => updatePermission('can_delete_own_events', c)}
                                    />
                                </div>
                            </div>

                            <div className="text-xs text-muted-foreground bg-yellow-50 dark:bg-yellow-950/20 p-2 rounded border border-yellow-200 dark:border-yellow-800">
                                <strong>Note:</strong> Agents can never access other users' events, regardless of these settings.
                            </div>
                        </div>
                    )}

                    <Button
                        variant={isActive ? "destructive" : "outline"}
                        onClick={() => {
                            if (isActive) {
                                toggleIntegration('exchange', false);
                            } else {
                                handleConnectExchange();
                            }
                        }}
                    >
                        {isActive ? "Disconnect Exchange" : "Connect Exchange"}
                    </Button>
                </CardContent>
            )}
        </Card>
    );
}
