"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { mutate } from "swr";
import { toggleIntegration } from "./utils";

interface WhatsAppMetaProps {
    integrations: any[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function WhatsAppMeta({ integrations, expanded, onToggleExpand }: WhatsAppMetaProps) {
    const isExpanded = expanded === 'meta_whatsapp';
    const isActive = integrations?.some((i: any) => i.provider === 'meta_whatsapp' && i.is_active) ?? false;

    // State for Meta WhatsApp credentials
    const [metaWhatsappPhoneId, setMetaWhatsappPhoneId] = useState("");
    const [metaWhatsappToken, setMetaWhatsappToken] = useState("");

    // Facebook SDK
    useEffect(() => {
        // Load Facebook SDK
        (window as any).fbAsyncInit = function () {
            (window as any).FB.init({
                appId: process.env.NEXT_PUBLIC_META_APP_ID || '3937037266586396',
                cookie: true,
                xfbml: true,
                version: 'v24.0'
            });
        };

        (function (d, s, id) {
            var js, fjs = d.getElementsByTagName(s)[0] as HTMLScriptElement;
            if (d.getElementById(id)) { return; }
            js = d.createElement(s) as HTMLScriptElement; js.id = id;
            js.src = "https://connect.facebook.net/en_US/sdk.js";
            fjs.parentNode?.insertBefore(js, fjs);
        }(document, 'script', 'facebook-jssdk'));
    }, []);

    const handleFacebookLogin = () => {
        if (!(window as any).FB) {
            toast.error("Facebook SDK validation failed. Please disable ad-blockers.");
            return;
        }

        (window as any).FB.login(async function (response: any) {
            if (response.authResponse) {
                const accessToken = response.authResponse.accessToken;
                toast.loading("Verifying with Meta...");

                try {
                    // Exchange token
                    const res = await fetch('/api/auth/meta/exchange', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ access_token: accessToken })
                    });

                    if (!res.ok) throw new Error("Token exchange failed");

                    const data = await res.json();

                    setMetaWhatsappToken(data.access_token);
                    toast.dismiss();
                    toast.success("Logged in! Please select your WhatsApp account.");

                } catch (e) {
                    toast.dismiss();
                    toast.error("Login failed");
                }
            } else {
                toast.error("User cancelled login");
            }
        }, {
            scope: 'whatsapp_business_management,whatsapp_business_messaging,instagram_basic,instagram_manage_messages,pages_show_list,pages_messaging'
        });
    }


    async function handleConnectMetaWhatsApp() {
        if (!metaWhatsappPhoneId) {
            toast.error("Please enter your Phone Number ID");
            return;
        }
        if (!metaWhatsappToken) {
            toast.error("Please enter your System User Access Token");
            return;
        }

        try {
            const response = await fetch(`/api/agent/integrations/meta_whatsapp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: 'meta_whatsapp',
                    credentials: {},
                    settings: {
                        phone_number_id: metaWhatsappPhoneId,
                        access_token: metaWhatsappToken
                    }
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Failed to connect");
            }

            toast.success("Meta WhatsApp connected successfully");
            mutate("/api/agent/integrations");
            setMetaWhatsappToken("");
        } catch (error: any) {
            console.error("Error connecting Meta WhatsApp:", error);
            toast.error(error.message || "Failed to connect Meta WhatsApp");
        }
    }

    return (
        <Card>
            <CardHeader className="cursor-pointer" onClick={() => onToggleExpand('meta_whatsapp')}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <CardTitle>WhatsApp (Meta)</CardTitle>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                    <Switch
                        checked={isActive}
                        onCheckedChange={(c) => toggleIntegration('meta_whatsapp', c)}
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
                <CardDescription>Official WhatsApp Business API (Lower cost, more features)</CardDescription>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-4">
                    <div className="flex flex-col space-y-4 p-4 border rounded-lg bg-blue-50 dark:bg-blue-950/20 border-blue-100 dark:border-blue-900">
                        <h4 className="font-semibold text-blue-900 dark:text-blue-100">Recommended Connection</h4>
                        <p className="text-xs text-blue-700 dark:text-blue-300">Connect your WhatsApp Business account securely with one click.</p>
                        <Button
                            onClick={handleFacebookLogin}
                            className="bg-[#1877F2] hover:bg-[#166fe5] text-white w-full sm:w-auto"
                            disabled={isActive}
                        >
                            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.791-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" /></svg>
                            Connect with Facebook
                        </Button>
                    </div>

                    <div className="relative py-2">
                        <div className="absolute inset-0 flex items-center">
                            <span className="w-full border-t" />
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-background px-2 text-muted-foreground">Or connect manually (Developer Mode)</span>
                        </div>
                    </div>

                    <div className="p-4 bg-muted rounded-lg text-sm space-y-2">
                        <p className="font-semibold">Setup Instructions:</p>
                        <ol className="list-decimal list-inside space-y-1 text-xs">
                            <li>Go to <a href="https://developers.facebook.com" target="_blank" className="text-blue-600 underline">Meta for Developers</a></li>
                            <li>Create a Business App and add <strong>WhatsApp</strong> product</li>
                            <li>Go to <strong>API Setup</strong> to get your <strong>Phone Number ID</strong></li>
                            <li>Generate a <strong>System User Access Token</strong> (Permanent) in Business Settings</li>
                            <li>Set Webhook URL to: <code>{typeof window !== 'undefined' ? `${window.location.origin}/api/webhooks/meta-whatsapp` : ''}</code></li>
                            <li>Verify Token: <code>{process.env.NEXT_PUBLIC_META_VERIFY_TOKEN || 'See .env file'}</code></li>
                        </ol>
                    </div>

                    <div className="grid gap-2">
                        <Label htmlFor="meta-phone-id">Phone Number ID <span className="text-red-500">*</span></Label>
                        <Input
                            id="meta-phone-id"
                            type="text"
                            placeholder="e.g. 3937037266586396"
                            value={metaWhatsappPhoneId}
                            onChange={(e) => setMetaWhatsappPhoneId(e.target.value)}
                            disabled={isActive}
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="meta-token">System User Access Token <span className="text-red-500">*</span></Label>
                        <Input
                            id="meta-token"
                            type="password"
                            placeholder="EAA..."
                            value={metaWhatsappToken}
                            onChange={(e) => setMetaWhatsappToken(e.target.value)}
                            disabled={isActive}
                        />
                    </div>

                    <Button
                        variant={isActive ? "destructive" : "outline"}
                        onClick={() => {
                            if (isActive) {
                                toggleIntegration('meta_whatsapp', false);
                            } else {
                                handleConnectMetaWhatsApp();
                            }
                        }}
                    >
                        {isActive ? "Disconnect WhatsApp (Meta)" : "Connect WhatsApp (Meta)"}
                    </Button>
                </CardContent>
            )}
        </Card>
    );
}
