"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronDown, ChevronUp, Bot, ExternalLink, Loader2, Info } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import useSWR, { mutate } from "swr";

interface Integration {
    id: number;
    workspace_id: number;
    provider: string; // 'tavus'
    is_active: boolean;
    settings?: any;
}

interface TavusIntegrationProps {
    integrations: Integration[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function TavusIntegration({ integrations, expanded, onToggleExpand }: TavusIntegrationProps) {
    const providerName = 'tavus';
    const integration = integrations.find(i => i.provider === providerName);
    const isExpanded = expanded === providerName;

    // Local state for UI
    const [isConnected, setIsConnected] = useState(false);
    const [isEnabled, setIsEnabled] = useState(false);
    const [loading, setLoading] = useState(false);
    const [cameraEnabled, setCameraEnabled] = useState(false);

    useEffect(() => {
        if (integration) {
            setIsConnected(integration.is_active);
            setIsEnabled(integration.is_active);

            // Camera permission is stored in settings
            if (integration.settings?.camera_enabled) {
                setCameraEnabled(true);
            } else {
                setCameraEnabled(false);
            }
        } else {
            setIsConnected(false);
            setIsEnabled(false);
            setCameraEnabled(false);
        }
    }, [integration]);

    const handleConnect = async () => {
        setLoading(true);
        try {
            const formData = {
                provider: "tavus",
                credentials: {}, // No credentials needed for Platform Managed Keys
                settings: {
                    camera_enabled: cameraEnabled
                }
            };

            const response = await fetch("/api/agent/integrations/tavus", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error("Tavus API Error:", response.status, errorText);
                throw new Error(`Failed to enable Tavus integration: ${response.status} ${errorText}`);
            }

            toast.success("Tavus Avatar integration enabled");
            setIsConnected(true);
            setIsEnabled(true);
            mutate("/api/agent/integrations");
        } catch (error: any) {
            toast.error(error.message || "Failed to connect");
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateSettings = async (newCameraState: boolean) => {
        setCameraEnabled(newCameraState);

        if (isConnected) {
            try {
                const formData = {
                    provider: "tavus",
                    credentials: {},
                    settings: {
                        camera_enabled: newCameraState
                    }
                };

                const response = await fetch("/api/agent/integrations/tavus", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(formData),
                });

                if (!response.ok) throw new Error("Failed to update settings");

                toast.success("Settings updated");
                mutate("/api/agent/integrations");
            } catch (e) {
                toast.error("Failed to save setting");
                console.error(e);
                setCameraEnabled(!newCameraState); // Revert
            }
        }
    };

    const handleDisconnect = async () => {
        setLoading(true);
        try {
            const response = await fetch("/api/agent/integrations/tavus", { method: "DELETE" });
            if (!response.ok) throw new Error("Failed to disable integration");

            toast.success("Integration disabled");
            setIsConnected(false);
            setIsEnabled(false);
            setCameraEnabled(false);
            mutate("/api/agent/integrations");
        } catch (error) {
            toast.error("Failed to disconnect");
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="flex items-center gap-2">
                    <div className="h-10 w-10 relative rounded-full overflow-hidden border bg-purple-100 flex items-center justify-center">
                        <Bot className="h-6 w-6 text-purple-600" />
                    </div>
                    <div>
                        <CardTitle className="text-base font-medium">Tavus AI Avatar</CardTitle>
                        <CardDescription>Hyper-realistic video avatars for your agents.</CardDescription>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {isConnected && <Badge variant="default" className="bg-green-600">Active</Badge>}
                    <Button variant="ghost" size="icon" onClick={() => onToggleExpand(providerName)}>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </Button>
                </div>
            </CardHeader>

            {isExpanded && (
                <CardContent className="space-y-6 pt-4 border-t">
                    <div className="flex items-center justify-between space-x-2">
                        <Label htmlFor="tavus-enable" className="flex flex-col space-y-1">
                            <span className="font-medium">Enable Integration</span>
                            <span className="font-normal text-xs text-muted-foreground">
                                Activate AI Avatars for this workspace.
                            </span>
                        </Label>
                        <Switch
                            id="tavus-enable"
                            checked={isEnabled}
                            onCheckedChange={(checked) => {
                                if (checked) handleConnect();
                                else handleDisconnect();
                            }}
                            disabled={loading}
                        />
                    </div>

                    {isEnabled && (
                        <div className="flex items-center justify-between space-x-2 border-t pt-4">
                            <Label htmlFor="tavus-camera" className="flex flex-col space-y-1">
                                <span className="font-medium">Allow Camera Access</span>
                                <span className="font-normal text-xs text-muted-foreground">
                                    Allow the Avatar to see users via their webcam (Vision).
                                </span>
                            </Label>
                            <Switch
                                id="tavus-camera"
                                checked={cameraEnabled}
                                onCheckedChange={handleUpdateSettings}
                                disabled={loading || !isEnabled}
                            />
                        </div>
                    )}

                    {!isConnected && (
                        <div className="rounded-md bg-muted p-3 text-xs text-muted-foreground flex items-center gap-2">
                            <Info className="h-4 w-4" />
                            This integration uses the platform's managed API key. No configuration required.
                        </div>
                    )}
                </CardContent>
            )}
        </Card>
    );
}
