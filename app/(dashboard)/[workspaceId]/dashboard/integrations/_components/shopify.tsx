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

interface ShopifyProps {
    integrations: any[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function ShopifyIntegration({ integrations, expanded, onToggleExpand }: ShopifyProps) {
    const isExpanded = expanded === 'shopify';
    const isActive = integrations?.some((i: any) => i.provider === 'shopify' && i.is_active) ?? false;

    // State for Shopify credentials
    const [shopifyUrl, setShopifyUrl] = useState("");
    const [shopifyToken, setShopifyToken] = useState("");

    async function handleConnectShopify() {
        if (!shopifyUrl || !shopifyToken) {
            toast.error("Please fill in all Shopify fields");
            return;
        }
        if (!shopifyUrl.includes("myshopify.com")) {
            toast.error("Store URL must be a valid .myshopify.com domain");
            return;
        }
        if (!shopifyToken.startsWith("shpat_")) {
            toast.error("Access Token must start with 'shpat_'");
            return;
        }

        try {
            const response = await fetch(`/api/agent/integrations/shopify`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: 'shopify',
                    credentials: {
                        access_token: shopifyToken
                    },
                    settings: {
                        shop_url: shopifyUrl
                    }
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Failed to connect");
            }

            toast.success("Shopify connected successfully");
            mutate("/api/agent/integrations");
            setShopifyToken("");
        } catch (error: any) {
            console.error("Error connecting Shopify:", error);
            toast.error(error.message || "Failed to connect Shopify");
        }
    }

    return (
        <Card>
            <CardHeader className="cursor-pointer" onClick={() => onToggleExpand('shopify')}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <CardTitle>Shopify</CardTitle>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                    <Switch defaultChecked={false}
                        checked={isActive}
                        onCheckedChange={(c) => toggleIntegration('shopify', c)}
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
                <CardDescription>Connect your Shopify store</CardDescription>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-4">
                    <div className="p-4 bg-muted rounded-lg text-sm space-y-2">
                        <p className="font-semibold">Setup Instructions:</p>
                        <ol className="list-decimal list-inside space-y-1 text-xs">
                            <li>Go to your Shopify Admin → <strong>Settings</strong> → <strong>Apps and sales channels</strong></li>
                            <li>Click <strong>Develop apps</strong> → <strong>Create an app</strong></li>
                            <li>Give it a name (e.g., "SupaAgent") and click <strong>Create app</strong></li>
                            <li>Go to <strong>Configuration</strong> → <strong>Admin API integration</strong></li>
                            <li>Enable: <code>read_products</code>, <code>read_orders</code>, <code>write_orders</code>, <code>read_customers</code></li>
                            <li>Click <strong>Save</strong>, then go to <strong>API credentials</strong></li>
                            <li>Click <strong>Install app</strong> → Copy the <strong>Admin API access token</strong></li>
                            <li>Your <strong>Store URL</strong> is: <code>your-store.myshopify.com</code></li>
                        </ol>
                    </div>

                    {isActive && (
                        <div className="space-y-4 p-4 border rounded-lg">
                            <h4 className="font-semibold text-sm">Order Permissions</h4>
                            <p className="text-xs text-muted-foreground">Control what the AI agents can do with customer orders</p>

                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="shopify-can-cancel">Cancel Orders</Label>
                                        <p className="text-xs text-muted-foreground">Allow agents to cancel orders after identity verification</p>
                                    </div>
                                    <Switch
                                        id="shopify-can-cancel"
                                        checked={(() => {
                                            const integration = integrations?.find((i: any) => i.provider === 'shopify');
                                            if (!integration?.settings) return false;
                                            const settings = typeof integration.settings === 'string' ? JSON.parse(integration.settings) : integration.settings;
                                            return settings.can_cancel_orders || false;
                                        })()}
                                        onCheckedChange={async (checked) => {
                                            const integration = integrations?.find((i: any) => i.provider === 'shopify');
                                            const currentSettings = integration?.settings && typeof integration.settings === 'string'
                                                ? JSON.parse(integration.settings)
                                                : (integration?.settings || {});

                                            const credentials = integration?.credentials && typeof integration.credentials === 'string'
                                                ? JSON.parse(integration.credentials)
                                                : (integration?.credentials || {});

                                            await fetch(`/api/agent/integrations/shopify`, {
                                                method: 'POST',
                                                headers: { 'Content-Type': 'application/json' },
                                                body: JSON.stringify({
                                                    provider: 'shopify',
                                                    credentials: credentials,
                                                    settings: { ...currentSettings, can_cancel_orders: checked }
                                                })
                                            });
                                            mutate("/api/agent/integrations");
                                            toast.success(checked ? "Cancellation enabled" : "Cancellation disabled");
                                        }}
                                    />
                                </div>
                            </div>

                            <div className="text-xs text-muted-foreground bg-yellow-50 dark:bg-yellow-950/20 p-2 rounded border border-yellow-200 dark:border-yellow-800">
                                <strong>Security:</strong> Agents must verify customer identity (Name + Email + Order #) before accessing any order information. Refunds are never allowed.
                            </div>
                        </div>
                    )}

                    <div className="grid gap-2">
                        <Label htmlFor="shopify-store-url">Store URL <span className="text-red-500">*</span></Label>
                        <Input
                            id="shopify-store-url"
                            type="text"
                            placeholder="your-store.myshopify.com"
                            value={shopifyUrl}
                            onChange={(e) => setShopifyUrl(e.target.value)}
                            disabled={isActive}
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="shopify-access-token">Admin API Access Token <span className="text-red-500">*</span></Label>
                        <Input
                            id="shopify-access-token"
                            type="password"
                            placeholder="shpat_..."
                            value={shopifyToken}
                            onChange={(e) => setShopifyToken(e.target.value)}
                            disabled={isActive}
                        />
                    </div>
                    <Button
                        variant={isActive ? "destructive" : "outline"}
                        onClick={() => {
                            if (isActive) {
                                toggleIntegration('shopify', false);
                            } else {
                                handleConnectShopify();
                            }
                        }}
                    >
                        {isActive ? "Disconnect Store" : "Connect Store"}
                    </Button>
                </CardContent>
            )}
        </Card>
    );
}
