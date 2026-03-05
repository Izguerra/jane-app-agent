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

interface InstagramProps {
    integrations: any[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function InstagramIntegration({ integrations, expanded, onToggleExpand }: InstagramProps) {
    const isExpanded = expanded === 'instagram';
    const isActive = integrations?.some((i: any) => i.provider === 'instagram' && i.is_active) ?? false;

    // State for Instagram credentials
    const [instagramAccessToken, setInstagramAccessToken] = useState("");
    const [instagramAccountId, setInstagramAccountId] = useState("");

    async function handleConnectInstagram() {
        if (!instagramAccessToken || !instagramAccountId) {
            toast.error("Please fill in all Instagram fields");
            return;
        }

        // Instagram Account ID should be numeric
        if (!/^\d+$/.test(instagramAccountId)) {
            toast.error("Instagram Account ID must be numeric");
            return;
        }

        try {
            const response = await fetch(`/api/agent/integrations/instagram`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: 'instagram',
                    credentials: {
                        access_token: instagramAccessToken,
                        instagram_account_id: instagramAccountId
                    },
                    settings: {}
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Failed to connect");
            }

            toast.success("Instagram connected successfully");
            mutate("/api/agent/integrations");
            setInstagramAccessToken("");
        } catch (error: any) {
            console.error("Error connecting Instagram:", error);
            toast.error(error.message || "Failed to connect Instagram");
        }
    }

    return (
        <Card>
            <CardHeader className="cursor-pointer" onClick={() => onToggleExpand('instagram')}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <CardTitle>Instagram Messaging</CardTitle>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                    <Switch
                        checked={isActive}
                        onCheckedChange={(c) => toggleIntegration('instagram', c)}
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
                <CardDescription>Reply to Instagram DMs automatically</CardDescription>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-4">
                    <div className="p-4 bg-muted rounded-lg text-sm space-y-2">
                        <p className="font-semibold">Setup Instructions:</p>
                        <ol className="list-decimal list-inside space-y-1 text-xs">
                            <li>Go to <a href="https://developers.facebook.com" target="_blank" className="text-blue-600 underline">Meta for Developers</a> and log in</li>
                            <li>Click <strong>My Apps</strong> → <strong>Create App</strong></li>
                            <li>Select <strong>Business</strong> as the app type</li>
                            <li>On "Add use cases", select <strong>Instagram Graph API</strong></li>
                            <li>Go to <strong>Tools</strong> → <strong>Graph API Explorer</strong></li>
                            <li>Select your app, then select your <strong>Instagram Business Account</strong></li>
                            <li>Under Permissions, add: <code>instagram_basic</code>, <code>instagram_manage_messages</code>, <code>pages_show_list</code></li>
                            <li>Click <strong>Generate Access Token</strong> and copy it</li>
                            <li>To get your <strong>Instagram Account ID</strong>, make a GET request to: <code>me/accounts</code> in the Graph API Explorer</li>
                            <li>Set your <strong>Webhook URL</strong> in Meta App settings to: <code>{typeof window !== 'undefined' ? `${window.location.origin}/api/webhooks/instagram` : ''}</code></li>
                        </ol>
                        <p className="text-xs text-yellow-600 dark:text-yellow-500 mt-2">⚠️ <strong>Note:</strong> Your Instagram account must be a Business or Creator account linked to a Facebook Page.</p>
                    </div>

                    <div className="grid gap-2">
                        <Label htmlFor="ig-account-id">Instagram Account ID <span className="text-red-500">*</span></Label>
                        <Input
                            id="ig-account-id"
                            type="text"
                            placeholder="17841..."
                            value={instagramAccountId}
                            onChange={(e) => setInstagramAccountId(e.target.value)}
                            disabled={isActive}
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="ig-access-token">Page Access Token <span className="text-red-500">*</span></Label>
                        <Input
                            id="ig-access-token"
                            type="password"
                            placeholder="EAA..."
                            value={instagramAccessToken}
                            onChange={(e) => setInstagramAccessToken(e.target.value)}
                            disabled={isActive}
                        />
                    </div>

                    <Button
                        variant={isActive ? "destructive" : "outline"}
                        onClick={() => {
                            if (isActive) {
                                toggleIntegration('instagram', false);
                            } else {
                                handleConnectInstagram();
                            }
                        }}
                    >
                        {isActive ? "Disconnect Instagram" : "Connect Instagram"}
                    </Button>
                </CardContent>
            )}
        </Card>
    );
}
