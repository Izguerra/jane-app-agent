"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ChevronDown, ChevronUp } from "lucide-react";
import { toast } from "sonner";
import { mutate } from "swr";
import { toggleIntegration } from "./utils";

interface GoogleCalendarProps {
    integrations: any[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function GoogleCalendarIntegration({ integrations, expanded, onToggleExpand }: GoogleCalendarProps) {
    const isExpanded = expanded === 'google_calendar';
    const isActive = integrations?.some((i: any) => i.provider === 'google_calendar' && i.is_active) ?? false;

    async function handleConnectGoogle() {
        console.log("handleConnectGoogle called");
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
        console.log("Redirecting to:", `${backendUrl}/api/auth/google/login`);
        window.location.assign(`${backendUrl}/api/auth/google/login`);
    }

    const updatePermission = async (permission: string, checked: boolean) => {
        const integration = integrations?.find((i: any) => i.provider === 'google_calendar');
        const currentSettings = integration?.settings && typeof integration.settings === 'string'
            ? JSON.parse(integration.settings)
            : (integration?.settings || {});

        const credentials = integration?.credentials && typeof integration.credentials === 'string'
            ? JSON.parse(integration.credentials)
            : (integration?.credentials || {});

        const newSettings = { ...currentSettings, [permission]: checked };

        await fetch(`/api/agent/integrations/google_calendar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: 'google_calendar',
                credentials: credentials,
                settings: newSettings
            })
        });
        mutate("/api/agent/integrations");
        toast.success(checked ? "Permission enabled" : "Permission disabled");
    };

    const getPermission = (permission: string) => {
        const integration = integrations?.find((i: any) => i.provider === 'google_calendar');
        if (!integration?.settings) return false;
        const settings = typeof integration.settings === 'string' ? JSON.parse(integration.settings) : integration.settings;
        return settings[permission] || false;
    };

    return (
        <Card>
            <CardHeader className="cursor-pointer" onClick={() => onToggleExpand('google_calendar')}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <CardTitle>Google Calendar</CardTitle>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                    <Switch
                        checked={isActive}
                        onCheckedChange={(c) => toggleIntegration('google_calendar', c)}
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
                <CardDescription>Sync appointments with Google Calendar</CardDescription>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-4">
                    <div className="p-4 bg-muted rounded-lg text-sm">
                        <p>To connect Google Calendar, you'll need to set up OAuth credentials in the Google Cloud Console.</p>
                    </div>

                    {isActive && (
                        <div className="space-y-4 p-4 border rounded-lg">
                            <h4 className="font-semibold text-sm">Calendar Permissions</h4>
                            <p className="text-xs text-muted-foreground">Control what the AI agents can do with your calendar events</p>

                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="can-view">View own events</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to check calendar availability</p>
                                    </div>
                                    <Switch
                                        id="can-view"
                                        checked={getPermission('can_view_own_events')}
                                        onCheckedChange={(c) => updatePermission('can_view_own_events', c)}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="can-edit">Edit own events</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to modify existing events</p>
                                    </div>
                                    <Switch
                                        id="can-edit"
                                        checked={getPermission('can_edit_own_events')}
                                        onCheckedChange={(c) => updatePermission('can_edit_own_events', c)}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="can-delete">Delete own events</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to cancel appointments</p>
                                    </div>
                                    <Switch
                                        id="can-delete"
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
                        type="button"
                        variant={isActive ? "destructive" : "outline"}
                        onClick={() => {
                            if (isActive) {
                                toggleIntegration('google_calendar', false);
                            } else {
                                handleConnectGoogle();
                            }
                        }}
                    >
                        {isActive ? "Disconnect Google Account" : "Connect Google Account"}
                    </Button>
                </CardContent>
            )}
        </Card>
    );
}
