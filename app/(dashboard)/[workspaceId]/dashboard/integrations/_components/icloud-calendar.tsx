"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ChevronDown, ChevronUp, Calendar, Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import { mutate } from "swr";
import { toggleIntegration } from "./utils";

interface ICloudCalendarProps {
    integrations: any[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function ICloudCalendarIntegration({ integrations, expanded, onToggleExpand }: ICloudCalendarProps) {
    const isExpanded = expanded === 'icloud_calendar';
    const isActive = integrations?.some((i: any) => i.provider === 'icloud_calendar' && i.is_active) ?? false;

    const [email, setEmail] = useState("");
    const [appPassword, setAppPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);

    async function handleConnect() {
        if (!email || !appPassword) {
            toast.error("Please enter your iCloud email and app-specific password");
            return;
        }

        setIsConnecting(true);
        try {
            const response = await fetch(`/api/agent/integrations/icloud_calendar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: 'icloud_calendar',
                    credentials: { email, app_password: appPassword },
                    settings: { can_view_events: true, can_create_events: true, can_edit_events: true }
                })
            });

            if (response.ok) {
                toast.success("iCloud Calendar connected successfully");
                mutate("/api/agent/integrations");
                setEmail("");
                setAppPassword("");
            } else {
                toast.error("Failed to connect iCloud Calendar");
            }
        } catch (error) {
            toast.error("Error connecting iCloud Calendar");
        } finally {
            setIsConnecting(false);
        }
    }

    const updatePermission = async (permission: string, checked: boolean) => {
        const integration = integrations?.find((i: any) => i.provider === 'icloud_calendar');
        const currentSettings = integration?.settings && typeof integration.settings === 'string'
            ? JSON.parse(integration.settings)
            : (integration?.settings || {});

        const credentials = integration?.credentials && typeof integration.credentials === 'string'
            ? JSON.parse(integration.credentials)
            : (integration?.credentials || {});

        const newSettings = { ...currentSettings, [permission]: checked };

        await fetch(`/api/agent/integrations/icloud_calendar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: 'icloud_calendar',
                credentials: credentials,
                settings: newSettings
            })
        });
        mutate("/api/agent/integrations");
        toast.success(checked ? "Permission enabled" : "Permission disabled");
    };

    const getPermission = (permission: string) => {
        const integration = integrations?.find((i: any) => i.provider === 'icloud_calendar');
        if (!integration?.settings) return false;
        const settings = typeof integration.settings === 'string' ? JSON.parse(integration.settings) : integration.settings;
        return settings[permission] || false;
    };

    return (
        <Card>
            <CardHeader className="cursor-pointer" onClick={() => onToggleExpand('icloud_calendar')}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <Calendar className="h-5 w-5 text-gray-500" />
                        <CardTitle>iCloud Calendar</CardTitle>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                    <Switch
                        checked={isActive}
                        onCheckedChange={(c) => toggleIntegration('icloud_calendar', c)}
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
                <CardDescription>Sync appointments with Apple iCloud Calendar</CardDescription>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-4">
                    <div className="p-4 bg-muted rounded-lg text-sm space-y-2">
                        <p>iCloud Calendar uses CalDAV and requires an <strong>app-specific password</strong>.</p>
                        <p className="text-xs text-muted-foreground">
                            Generate one at <a href="https://appleid.apple.com/account/manage" target="_blank" rel="noopener noreferrer" className="text-blue-500 underline">appleid.apple.com</a>
                        </p>
                    </div>

                    {!isActive ? (
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="icloud-email">iCloud Email</Label>
                                <Input
                                    id="icloud-email"
                                    type="email"
                                    placeholder="you@icloud.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="app-password">App-Specific Password</Label>
                                <div className="relative">
                                    <Input
                                        id="app-password"
                                        type={showPassword ? "text" : "password"}
                                        placeholder="xxxx-xxxx-xxxx-xxxx"
                                        value={appPassword}
                                        onChange={(e) => setAppPassword(e.target.value)}
                                    />
                                    <button
                                        type="button"
                                        className="absolute right-3 top-1/2 -translate-y-1/2"
                                        onClick={() => setShowPassword(!showPassword)}
                                    >
                                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                    </button>
                                </div>
                            </div>
                            <Button onClick={handleConnect} disabled={isConnecting}>
                                {isConnecting ? "Connecting..." : "Connect iCloud Calendar"}
                            </Button>
                        </div>
                    ) : (
                        <>
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
                                </div>
                            </div>
                            <Button variant="destructive" onClick={() => toggleIntegration('icloud_calendar', false)}>
                                Disconnect iCloud Calendar
                            </Button>
                        </>
                    )}
                </CardContent>
            )}
        </Card>
    );
}
