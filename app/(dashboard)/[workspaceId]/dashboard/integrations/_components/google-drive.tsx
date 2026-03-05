"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ChevronDown, ChevronUp, HardDrive } from "lucide-react";
import { toast } from "sonner";
import { mutate } from "swr";
import { toggleIntegration } from "./utils";

interface GoogleDriveProps {
    integrations: any[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function GoogleDriveIntegration({ integrations, expanded, onToggleExpand }: GoogleDriveProps) {
    const isExpanded = expanded === 'google_drive';
    const isActive = integrations?.some((i: any) => i.provider === 'google_drive' && i.is_active) ?? false;

    async function handleConnectDrive() {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
        window.location.assign(`${backendUrl}/api/auth/google/login?scope=drive`);
    }

    const updatePermission = async (permission: string, checked: boolean) => {
        const integration = integrations?.find((i: any) => i.provider === 'google_drive');
        const currentSettings = integration?.settings && typeof integration.settings === 'string'
            ? JSON.parse(integration.settings)
            : (integration?.settings || {});

        const credentials = integration?.credentials && typeof integration.credentials === 'string'
            ? JSON.parse(integration.credentials)
            : (integration?.credentials || {});

        const newSettings = { ...currentSettings, [permission]: checked };

        await fetch(`/api/agent/integrations/google_drive`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: 'google_drive',
                credentials: credentials,
                settings: newSettings
            })
        });
        mutate("/api/agent/integrations");
        toast.success(checked ? "Permission enabled" : "Permission disabled");
    };

    const getPermission = (permission: string) => {
        const integration = integrations?.find((i: any) => i.provider === 'google_drive');
        if (!integration?.settings) return false;
        const settings = typeof integration.settings === 'string' ? JSON.parse(integration.settings) : integration.settings;
        return settings[permission] || false;
    };

    return (
        <Card>
            <CardHeader className="cursor-pointer" onClick={() => onToggleExpand('google_drive')}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <HardDrive className="h-5 w-5 text-green-500" />
                        <CardTitle>Google Drive</CardTitle>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                    <Switch
                        checked={isActive}
                        onCheckedChange={(c) => toggleIntegration('google_drive', c)}
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
                <CardDescription>Access and manage files in Google Drive</CardDescription>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-4">
                    <div className="p-4 bg-muted rounded-lg text-sm">
                        <p>Connect your Google Drive to allow agents to read, search, and manage files.</p>
                    </div>

                    {isActive && (
                        <div className="space-y-4 p-4 border rounded-lg">
                            <h4 className="font-semibold text-sm">Drive Permissions</h4>
                            <p className="text-xs text-muted-foreground">Control what agents can do with your files</p>

                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label>List files</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to browse your Drive</p>
                                    </div>
                                    <Switch
                                        checked={getPermission('can_list_files')}
                                        onCheckedChange={(c) => updatePermission('can_list_files', c)}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label>Read files</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to read file contents</p>
                                    </div>
                                    <Switch
                                        checked={getPermission('can_read_files')}
                                        onCheckedChange={(c) => updatePermission('can_read_files', c)}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label>Search files</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to search your Drive</p>
                                    </div>
                                    <Switch
                                        checked={getPermission('can_search_files')}
                                        onCheckedChange={(c) => updatePermission('can_search_files', c)}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label>Upload files</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to upload new files</p>
                                    </div>
                                    <Switch
                                        checked={getPermission('can_upload_files')}
                                        onCheckedChange={(c) => updatePermission('can_upload_files', c)}
                                    />
                                </div>
                            </div>

                            <div className="text-xs text-muted-foreground bg-yellow-50 dark:bg-yellow-950/20 p-2 rounded border border-yellow-200 dark:border-yellow-800">
                                <strong>Note:</strong> Agents can only access files you own or have been shared with you.
                            </div>
                        </div>
                    )}

                    <Button
                        type="button"
                        variant={isActive ? "destructive" : "outline"}
                        onClick={() => {
                            if (isActive) {
                                toggleIntegration('google_drive', false);
                            } else {
                                handleConnectDrive();
                            }
                        }}
                    >
                        {isActive ? "Disconnect Google Drive" : "Connect Google Drive"}
                    </Button>
                </CardContent>
            )}
        </Card>
    );
}
