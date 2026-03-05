"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Phone } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { mutate } from "swr";

interface PhoneManagementProps {
    phoneNumbers: any[];
}

export function PhoneManagement({ phoneNumbers }: PhoneManagementProps) {
    const [isPurchasingTwilio, setIsPurchasingTwilio] = useState(false);
    const [isPurchasingTelnyx, setIsPurchasingTelnyx] = useState(false);

    async function handlePurchaseNumber(provider: 'twilio' | 'telnyx') {
        if (provider === 'twilio') setIsPurchasingTwilio(true);
        else setIsPurchasingTelnyx(true);

        try {
            const purchaseRes = await fetch("/api/billing/purchase-phone-number", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ provider })
            });

            if (!purchaseRes.ok) {
                const errorData = await purchaseRes.json().catch(() => ({}));
                throw new Error(errorData.detail || `Purchase from ${provider} failed`);
            }

            const result = await purchaseRes.json();
            toast.success(`Successfully purchased ${result.phone_number} via ${provider}`);
            mutate("/api/agent/phone-numbers");

        } catch (e) {
            toast.error(e instanceof Error ? e.message : `Failed to purchase ${provider} number`);
        } finally {
            if (provider === 'twilio') setIsPurchasingTwilio(false);
            else setIsPurchasingTelnyx(false);
        }
    }

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <CardTitle>Phone Management</CardTitle>
                    </div>
                </div>
                <CardDescription>Manage your phone numbers across Twilio and Telnyx.</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {phoneNumbers && phoneNumbers.length > 0 ? (
                        <div className="space-y-3">
                            {phoneNumbers.map((phone: any) => (
                                <div key={phone.id} className="flex items-center justify-between p-4 bg-secondary rounded-lg">
                                    <div className="flex items-center space-x-4">
                                        <div className="p-2 bg-green-100 dark:bg-green-900 rounded-full">
                                            <Phone className="h-5 w-5 text-green-600 dark:text-green-400" />
                                        </div>
                                        <div>
                                            <p className="font-bold">{phone.phone_number}</p>
                                            <div className="flex flex-wrap gap-2 mt-1">
                                                <span className="text-xs text-muted-foreground">{phone.friendly_name}</span>
                                                <span className={`text-xs px-1.5 py-0.5 rounded capitalize ${phone.provider === 'telnyx' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                                                    {phone.provider || 'twilio'}
                                                </span>
                                                {phone.voice_enabled && <span className="text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">Voice</span>}
                                                {phone.sms_enabled && <span className="text-xs bg-green-100 text-green-800 px-1.5 py-0.5 rounded">SMS</span>}
                                                {phone.agent_id ? (
                                                    <span className="text-xs bg-purple-100 text-purple-800 px-1.5 py-0.5 rounded">
                                                        Assigned to {phone.agent_name || "Agent"}
                                                    </span>
                                                ) : (
                                                    <span className="text-xs bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded">Unassigned</span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive" onClick={async () => {
                                        if (confirm("Are you sure? This cannot be undone.")) {
                                            await fetch(`/api/agent/phone-numbers?id=${phone.id}`, { method: 'DELETE' });
                                            mutate("/api/agent/phone-numbers");
                                        }
                                    }}>Release</Button>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-sm text-muted-foreground">You don't have any phone numbers.</p>
                    )}

                    <div className="flex items-center gap-2 pt-2 flex-wrap">
                        <Button onClick={() => handlePurchaseNumber('twilio')} disabled={isPurchasingTwilio || isPurchasingTelnyx} variant="outline">
                            {isPurchasingTwilio ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Phone className="mr-2 h-4 w-4 text-red-500" />}
                            {isPurchasingTwilio ? "Purchasing..." : "Purchase Twilio Number ($9.99/mo)"}
                        </Button>
                        <Button onClick={() => handlePurchaseNumber('telnyx')} disabled={isPurchasingTwilio || isPurchasingTelnyx} className="bg-emerald-600 hover:bg-emerald-700 text-white">
                            {isPurchasingTelnyx ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Phone className="mr-2 h-4 w-4" />}
                            {isPurchasingTelnyx ? "Purchasing..." : "Purchase Telnyx Number ($2.00/mo)"}
                        </Button>
                        <p className="text-xs text-muted-foreground ml-2 w-full mt-2">
                            Telnyx is recommended for better scalability and cheaper rates. Numbers are provisioned instantly.
                        </p>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
