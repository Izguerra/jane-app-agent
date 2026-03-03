"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ChevronDown, ChevronUp, Calendar } from "lucide-react";
import { toast } from "sonner";
import { mutate } from "swr";
import { toggleIntegration } from "./utils";

interface OutlookCalendarProps {
    integrations: any[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function OutlookCalendarIntegration({ integrations, expanded, onToggleExpand }: OutlookCalendarProps) {
    const isExpanded = expanded === 'outlook_calendar';
    const isActive = integrations?.some((i: any) => i.provider === 'outlook_calendar' && i.is_active) ?? false;

    async function handleConnectOutlook() {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
        window.location.assign(`${backendUrl}/api/auth/outlook/login?scope=calendar`);
    }

    const updatePermission = async (permission: string, checked: boolean) => {
        const integration = integrations?.find((i: any) => i.provider === 'outlook_calendar');
        const currentSettings = integration?.settings && typeof integration.settings === 'string'
            ? JSON.parse(integration.settings)
            : (integration?.settings || {});

        const credentials = integration?.credentials && typeof integration.credentials === 'string'
            ? JSON.parse(integration.credentials)
            : (integration?.credentials || {});

        const newSettings = { ...currentSettings, [permission]: checked };

        await fetch(`/api/agent/integrations/outlook_calendar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: 'outlook_calendar',
                credentials: credentials,
                settings: newSettings
            })
        });
        mutate("/api/agent/integrations");
        toast.success(checked ? "Permission enabled" : "Permission disabled");
    };

    const getPermission = (permission: string) => {
        const integration = integrations?.find((i: any) => i.provider === 'outlook_calendar');
        if (!integration?.settings) return false;
        const settings = typeof integration.settings === 'string' ? JSON.parse(integration.settings) : integration.settings;
        return settings[permission] || false;
    };

    return (
        <Card>
            <CardHeader className="cursor-pointer" onClick={() => onToggleExpand('outlook_calendar')}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <Calendar className="h-5 w-5 text-blue-500" />
                        <CardTitle>Outlook Calendar</CardTitle>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                    <Switch
                        checked={isActive}
                        onCheckedChange={(c) => toggleIntegration('outlook_calendar', c)}
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
                <CardDescription>Sync appointments with Microsoft Outlook Calendar</CardDescription>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-4">
                    <div className="p-4 bg-muted rounded-lg text-sm">
                        <p>Connect your Microsoft account to sync calendar events.</p>
                    </div>

                    {isActive && (
                        <div className="space-y-4 p-4 border rounded-lg">
                            <h4 className="font-semibold text-sm">Calendar Permissions</h4>
                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label>View events</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to view your calendar</p>
                                    </div>
                                    <Switch
                                        checked={getPermission('can_view_events')}
                                        onCheckedChange={(c) => updatePermission('can_view_events', c)}
                                    />
                                </div>
                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label>Create events</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to create appointments</p>
                                    </div>
                                    <Switch
                                        checked={getPermission('can_create_events')}
                                        onCheckedChange={(c) => updatePermission('can_create_events', c)}
                                    />
                                </div>
                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label>Edit events</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to modify events</p>
                                    </div>
                                    <Switch
                                        checked={getPermission('can_edit_events')}
                                        onCheckedChange={(c) => updatePermission('can_edit_events', c)}
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
                                toggleIntegration('outlook_calendar', false);
                            } else {
                                handleConnectOutlook();
                            }
                        }}
                    >
                        {isActive ? "Disconnect Outlook Calendar" : "Connect Microsoft Account"}
                    </Button>
                </CardContent>
            )}
        </Card>
    );
}
