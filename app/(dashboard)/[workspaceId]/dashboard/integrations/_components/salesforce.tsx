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

interface SalesforceProps {
    integrations: any[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function SalesforceIntegration({ integrations, expanded, onToggleExpand }: SalesforceProps) {
    const isExpanded = expanded === 'salesforce';
    const isActive = integrations?.some((i: any) => i.provider === 'salesforce' && i.is_active) ?? false;

    // State for Salesforce credentials
    const [salesforceKey, setSalesforceKey] = useState("");
    const [salesforceSecret, setSalesforceSecret] = useState("");

    async function handleConnectSalesforce() {
        if (!salesforceKey || !salesforceSecret) {
            toast.error("Please fill in all Salesforce fields");
            return;
        }

        try {
            const response = await fetch(`/api/agent/integrations/salesforce`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: 'salesforce',
                    credentials: {
                        consumer_key: salesforceKey,
                        consumer_secret: salesforceSecret
                    },
                    settings: {}
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Failed to connect");
            }

            toast.success("Salesforce connected successfully");
            mutate("/api/agent/integrations");
            setSalesforceKey("");
            setSalesforceSecret("");
        } catch (error: any) {
            console.error("Error connecting Salesforce:", error);
            toast.error(error.message || "Failed to connect Salesforce");
        }
    }

    return (
        <Card>
            <CardHeader className="cursor-pointer" onClick={() => onToggleExpand('salesforce')}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <CardTitle>Salesforce</CardTitle>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                    <Switch defaultChecked={false} checked={isActive} onCheckedChange={(c) => toggleIntegration('salesforce', c)} onClick={(e) => e.stopPropagation()} />
                </div>
                <CardDescription>Connect your Salesforce CRM</CardDescription>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-4">
                    <div className="grid gap-2">
                        <Label htmlFor="sf-client-id">Consumer Key <span className="text-red-500">*</span></Label>
                        <Input
                            id="sf-client-id"
                            type="password"
                            placeholder="Consumer Key"
                            value={salesforceKey}
                            onChange={(e) => setSalesforceKey(e.target.value)}
                            disabled={isActive}
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="sf-client-secret">Consumer Secret <span className="text-red-500">*</span></Label>
                        <Input
                            id="sf-client-secret"
                            type="password"
                            placeholder="Consumer Secret"
                            value={salesforceSecret}
                            onChange={(e) => setSalesforceSecret(e.target.value)}
                            disabled={isActive}
                        />
                    </div>
                    <Button
                        variant={isActive ? "destructive" : "outline"}
                        onClick={() => {
                            if (isActive) {
                                toggleIntegration('salesforce', false);
                            } else {
                                handleConnectSalesforce();
                            }
                        }}
                    >
                        {isActive ? "Disconnect Salesforce" : "Connect Salesforce"}
                    </Button>
                </CardContent>
            )}
        </Card>
    );
}
