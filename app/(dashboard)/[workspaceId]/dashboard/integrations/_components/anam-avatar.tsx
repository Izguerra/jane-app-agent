"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronDown, ChevronUp, Sparkles, Info, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { mutate } from "swr";

interface Integration {
    id: number;
    workspace_id: number;
    provider: string;
    is_active: boolean;
    settings?: any;
}

interface AnamIntegrationProps {
    integrations: Integration[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function AnamIntegration({ integrations, expanded, onToggleExpand }: AnamIntegrationProps) {
    const providerName = 'anam';
    const integration = integrations.find(i => i.provider === providerName);
    const isExpanded = expanded === providerName;

    const [isConnected, setIsConnected] = useState(false);
    const [isEnabled, setIsEnabled] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (integration) {
            setIsConnected(integration.is_active);
            setIsEnabled(integration.is_active);
        } else {
            setIsConnected(false);
            setIsEnabled(false);
        }
    }, [integration]);

    const handleConnect = async () => {
        setLoading(true);
        try {
            const formData = {
                provider: "anam",
                credentials: {},
                settings: {}
            };

            const response = await fetch("/api/agent/integrations/anam", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to enable Anam integration: ${response.status} ${errorText}`);
            }

            toast.success("Anam.ai Avatar integration enabled. Tavus has been deactivated.");
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

    const handleDisconnect = async () => {
        setLoading(true);
        try {
            const response = await fetch("/api/agent/integrations/anam", { method: "DELETE" });
            if (!response.ok) throw new Error("Failed to disable integration");

            toast.success("Anam.ai integration disabled");
            setIsConnected(false);
            setIsEnabled(false);
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
                    <div className="h-10 w-10 relative rounded-full overflow-hidden border bg-gradient-to-br from-cyan-100 to-blue-100 flex items-center justify-center">
                        <Sparkles className="h-6 w-6 text-cyan-600" />
                    </div>
                    <div>
                        <CardTitle className="text-base font-medium">Anam.ai Avatar</CardTitle>
                        <CardDescription>Next-gen real-time AI avatars with lip-sync &amp; expressions.</CardDescription>
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
                        <Label htmlFor="anam-enable" className="flex flex-col space-y-1">
                            <span className="font-medium">Enable Integration</span>
                            <span className="font-normal text-xs text-muted-foreground">
                                Activate Anam.ai Avatars for this workspace. This will deactivate Tavus if active.
                            </span>
                        </Label>
                        <Switch
                            id="anam-enable"
                            checked={isEnabled}
                            onCheckedChange={(checked) => {
                                if (checked) handleConnect();
                                else handleDisconnect();
                            }}
                            disabled={loading}
                        />
                    </div>

                    {!isConnected && (
                        <div className="rounded-md bg-muted p-3 text-xs text-muted-foreground flex items-center gap-2">
                            <Info className="h-4 w-4" />
                            This integration uses the platform&apos;s managed API key. No configuration required.
                        </div>
                    )}

                    {isConnected && (
                        <div className="rounded-md bg-cyan-50 border border-cyan-200 p-3 text-xs text-cyan-700 flex items-center gap-2">
                            <Sparkles className="h-4 w-4" />
                            Anam.ai is your active avatar provider. Go to Agent Setup → Visual Presence to select an avatar.
                        </div>
                    )}
                </CardContent>
            )}
        </Card>
    );
}
