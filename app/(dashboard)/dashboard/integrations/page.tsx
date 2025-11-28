"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useState, useEffect } from "react";
import { CheckCircle2, AlertCircle, Phone, Search, Loader2, ShoppingBag, Database, Plus } from "lucide-react";
import { toast } from "sonner";

interface PhoneNumber {
    friendly_name: string;
    phone_number: string;
    iso_country: string;
}

interface Integration {
    id: number;
    provider: string;
    is_active: boolean;
    settings: any;
}

const AVAILABLE_INTEGRATIONS = [
    {
        id: "jane",
        name: "Jane App",
        description: "Sync appointments and patient data.",
        icon: CheckCircle2,
        color: "text-green-600",
        bgColor: "bg-green-500/20",
    },
    {
        id: "shopify",
        name: "Shopify",
        description: "Connect your store for product recommendations.",
        icon: ShoppingBag,
        color: "text-purple-600",
        bgColor: "bg-purple-500/20",
    },
    {
        id: "salesforce",
        name: "Salesforce",
        description: "Sync leads and customer interactions.",
        icon: Database,
        color: "text-blue-600",
        bgColor: "bg-blue-500/20",
    },
];

export default function IntegrationsPage() {
    const [activeIntegrations, setActiveIntegrations] = useState<Integration[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    // Phone state
    const [isSearching, setIsSearching] = useState(false);
    const [areaCode, setAreaCode] = useState("");
    const [availableNumbers, setAvailableNumbers] = useState<PhoneNumber[]>([]);
    const [purchasedNumber, setPurchasedNumber] = useState<string | null>(null);

    // Dialog state
    const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
    const [credentials, setCredentials] = useState<any>({});

    useEffect(() => {
        fetchIntegrations();
    }, []);

    async function fetchIntegrations() {
        try {
            const res = await fetch("/api/agent/integrations");
            const data = await res.json();
            setActiveIntegrations(data);
        } catch (error) {
            console.error("Failed to fetch integrations", error);
        }
    }

    async function handleConnect(provider: string) {
        setIsLoading(true);
        try {
            const res = await fetch(`/api/agent/integrations/${provider}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    provider,
                    credentials,
                    settings: {}
                }),
            });
            const data = await res.json();
            if (data.status === "success") {
                toast.success(`Connected to ${provider}`);
                fetchIntegrations();
                setSelectedProvider(null);
                setCredentials({});
            }
        } catch (error) {
            console.error("Failed to connect", error);
            toast.error("Failed to connect");
        } finally {
            setIsLoading(false);
        }
    }

    async function handleDisconnect(provider: string) {
        if (!confirm("Are you sure you want to disconnect?")) return;
        try {
            await fetch(`/api/agent/integrations/${provider}`, { method: "DELETE" });
            toast.success(`Disconnected ${provider}`);
            fetchIntegrations();
        } catch (error) {
            console.error("Failed to disconnect", error);
        }
    }

    // Phone functions (kept from previous version)
    async function searchNumbers() {
        if (!areaCode) return;
        setIsSearching(true);
        try {
            const res = await fetch(`/api/agent/phone/search?area_code=${areaCode}`);
            const data = await res.json();
            setAvailableNumbers(data);
        } catch (error) {
            console.error("Failed to search numbers", error);
        } finally {
            setIsSearching(false);
        }
    }

    async function buyNumber(phoneNumber: string) {
        setIsLoading(true);
        try {
            const res = await fetch("/api/agent/phone/buy", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ phone_number: phoneNumber, area_code: areaCode }),
            });
            const data = await res.json();
            if (data.status === "success") {
                setPurchasedNumber(phoneNumber);
                setAvailableNumbers([]);
            }
        } catch (error) {
            console.error("Failed to buy number", error);
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div className="max-w-4xl mx-auto py-8">
            <h1 className="text-2xl font-bold mb-6">Integrations</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
                {AVAILABLE_INTEGRATIONS.map((integration) => {
                    const isActive = activeIntegrations.some(i => i.provider === integration.id);
                    const Icon = integration.icon;

                    return (
                        <Card key={integration.id} className="card-modern">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className={`h-12 w-12 rounded-xl ${integration.bgColor} flex items-center justify-center ${integration.color}`}>
                                            <Icon className="h-6 w-6" />
                                        </div>
                                        <div>
                                            <CardTitle>{integration.name}</CardTitle>
                                            <CardDescription className="line-clamp-1">{integration.description}</CardDescription>
                                        </div>
                                    </div>
                                    {isActive && <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse" />}
                                </div>
                            </CardHeader>
                            <CardContent>
                                {isActive ? (
                                    <Button
                                        variant="destructive"
                                        className="w-full"
                                        onClick={() => handleDisconnect(integration.id)}
                                    >
                                        Disconnect
                                    </Button>
                                ) : (
                                    <Dialog open={selectedProvider === integration.id} onOpenChange={(open) => !open && setSelectedProvider(null)}>
                                        <DialogTrigger asChild>
                                            <Button
                                                className="w-full "
                                                onClick={() => setSelectedProvider(integration.id)}
                                            >
                                                Connect
                                            </Button>
                                        </DialogTrigger>
                                        <DialogContent>
                                            <DialogHeader>
                                                <DialogTitle>Connect {integration.name}</DialogTitle>
                                                <DialogDescription>
                                                    Enter your credentials to enable this integration.
                                                </DialogDescription>
                                            </DialogHeader>
                                            <div className="space-y-4 py-4">
                                                {integration.id === 'jane' && (
                                                    <>
                                                        <div className="space-y-2">
                                                            <Label>Jane App URL</Label>
                                                            <Input
                                                                placeholder="https://clinic.janeapp.com"
                                                                onChange={(e) => setCredentials({ ...credentials, url: e.target.value })}
                                                            />
                                                        </div>
                                                        <div className="space-y-2">
                                                            <Label>Client ID</Label>
                                                            <Input
                                                                type="password"
                                                                onChange={(e) => setCredentials({ ...credentials, clientId: e.target.value })}
                                                            />
                                                        </div>
                                                    </>
                                                )}
                                                {integration.id === 'shopify' && (
                                                    <div className="space-y-2">
                                                        <Label>Shop Domain</Label>
                                                        <Input
                                                            placeholder="your-store.myshopify.com"
                                                            onChange={(e) => setCredentials({ ...credentials, shopDomain: e.target.value })}
                                                        />
                                                    </div>
                                                )}
                                                <div className="space-y-2">
                                                    <Label>API Key / Token</Label>
                                                    <Input
                                                        type="password"
                                                        onChange={(e) => setCredentials({ ...credentials, apiKey: e.target.value })}
                                                    />
                                                </div>
                                            </div>
                                            <DialogFooter>
                                                <Button onClick={() => handleConnect(integration.id)} disabled={isLoading}>
                                                    {isLoading ? "Connecting..." : "Connect Integration"}
                                                </Button>
                                            </DialogFooter>
                                        </DialogContent>
                                    </Dialog>
                                )}
                            </CardContent>
                        </Card>
                    );
                })}
            </div>

            {/* Phone Number Management (Existing) */}
            <h2 className="text-xl font-bold mb-4">Voice & Phone</h2>
            <Card className="card-modern mb-8">
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <CardTitle>Phone Number</CardTitle>
                            <CardDescription>Manage your dedicated AI Agent phone line.</CardDescription>
                        </div>
                        <div className="h-8 w-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-600">
                            <Phone className="h-5 w-5" />
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    {purchasedNumber ? (
                        <div className="flex items-center justify-between p-4 rounded-lg glass bg-green-500/10">
                            <div>
                                <p className="text-sm font-medium text-muted-foreground">Active Number</p>
                                <p className="text-xl font-bold text-green-700">{purchasedNumber}</p>
                            </div>
                            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                        </div>
                    ) : (
                        <div className="space-y-6">
                            <div className="flex gap-4">
                                <div className="flex-1 space-y-2">
                                    <Label htmlFor="areaCode">Search Area Code</Label>
                                    <Input
                                        id="areaCode"
                                        placeholder="e.g. 415"
                                        value={areaCode}
                                        onChange={(e) => setAreaCode(e.target.value)}
                                        className=""
                                    />
                                </div>
                                <div className="pt-8">
                                    <Button
                                        onClick={searchNumbers}
                                        disabled={isSearching || !areaCode}
                                        className=""
                                    >
                                        {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                                    </Button>
                                </div>
                            </div>

                            {availableNumbers.length > 0 && (
                                <div className="space-y-4">
                                    <Label>Available Numbers</Label>
                                    <div className="grid gap-4">
                                        {availableNumbers.map((num) => (
                                            <div key={num.phone_number} className="flex items-center justify-between p-3 rounded-lg glass bg-white/50 dark:bg-black/20">
                                                <span className="font-mono text-lg">{num.friendly_name}</span>
                                                <Button
                                                    size="sm"
                                                    onClick={() => buyNumber(num.phone_number)}
                                                    disabled={isLoading}
                                                    className=""
                                                >
                                                    {isLoading ? "Buying..." : "Buy"}
                                                </Button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
