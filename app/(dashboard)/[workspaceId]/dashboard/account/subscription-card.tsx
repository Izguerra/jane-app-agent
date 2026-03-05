'use client';

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, CreditCard, CheckCircle } from "lucide-react";
import useSWR from 'swr';
import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { preloadUpgradeFees } from "@/hooks/use-upgrade-fees";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export function SubscriptionCard() {
    const { data: subscription, isLoading } = useSWR('/api/billing/subscription', fetcher);

    useEffect(() => {
        preloadUpgradeFees();
    }, []);

    const [isManaging, setIsManaging] = useState(false);
    const [isPurchasing, setIsPurchasing] = useState(false);
    const [areaCode, setAreaCode] = useState('');

    const handlePurchaseNumber = async () => {
        setIsPurchasing(true);
        try {
            const res = await fetch('/api/billing/purchase-phone-number', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ area_code: areaCode || undefined })
            });

            if (!res.ok) {
                const error = await res.json();
                toast.error(error.detail || "Failed to purchase number");
                setIsPurchasing(false);
                return;
            }

            const data = await res.json();
            toast.success(`Successfully purchased ${data.phone_number}!`);
            setAreaCode('');
        } catch (error) {
            console.error('Purchase error:', error);
            toast.error("An error occurred while purchasing number");
        } finally {
            setIsPurchasing(false);
        }
    };

    const handleManageSubscription = async () => {
        setIsManaging(true);
        try {
            const res = await fetch('/api/billing/portal', {
                method: 'POST'
            });

            if (!res.ok) {
                const error = await res.json();
                toast.error(error.detail || "Failed to access billing portal");
                setIsManaging(false);
                return;
            }

            const data = await res.json();
            if (data.url) {
                window.location.href = data.url;
            } else {
                toast.error("Failed to redirect to billing portal");
                setIsManaging(false);
            }
        } catch (error) {
            console.error('Billing portal error:', error);
            toast.error("An error occurred while accessing the billing portal");
            setIsManaging(false);
        }
    };

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Subscription</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center space-x-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span>Loading subscription details...</span>
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Default or Fallback
    const planName = subscription?.plan || "Free";
    const status = subscription?.status || "active";
    const isStripe = subscription?.is_stripe !== false;

    return (
        <Card>
            <CardHeader>
                <CardTitle>Subscription Plan</CardTitle>
                <CardDescription>Manage your billing and subscription preferences</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg bg-gray-50/50">
                    <div className="flex items-center space-x-4">
                        <div className="p-2 bg-orange-100 rounded-full">
                            <CreditCard className="h-6 w-6 text-orange-600" />
                        </div>
                        <div>
                            <p className="font-medium text-lg">{planName} Plan</p>
                            <div className="flex items-center text-sm text-muted-foreground capitalize">
                                <CheckCircle className="h-3 w-3 mr-1 text-green-500" />
                                {status.replace('_', ' ')}
                            </div>
                        </div>
                    </div>
                    {subscription?.amount && (
                        <div className="text-right">
                            <p className="font-bold text-lg">
                                {new Intl.NumberFormat('en-US', { style: 'currency', currency: subscription.currency || 'USD' }).format(subscription.amount)}
                                <span className="text-sm font-normal text-muted-foreground">/mo</span>
                            </p>
                            {subscription.current_period_end && (
                                <p className="text-xs text-muted-foreground">
                                    Renews {new Date(subscription.current_period_end * 1000).toLocaleDateString()}
                                </p>
                            )}
                        </div>
                    )}
                </div>

                {!isStripe && (
                    <div className="text-sm text-yellow-600 bg-yellow-50 p-2 rounded">
                        This workspace is not linked to a billing account yet.
                    </div>
                )}

                {isStripe && (
                    <div className="mt-6 pt-6 border-t">
                        <h4 className="font-medium text-sm mb-4">Additional Services</h4>
                        <div className="flex items-end gap-3 p-4 border rounded-lg bg-gray-50/50">
                            <div className="flex-1">
                                <label className="text-sm font-medium mb-1 block">Purchase Additional Number</label>
                                <p className="text-sm text-muted-foreground mb-3">
                                    Add a dedicated phone number for $9.99/mo.
                                </p>
                                <div className="max-w-[150px]">
                                    <input
                                        type="text"
                                        placeholder="Area Code (e.g. 415)"
                                        className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                                        value={areaCode}
                                        onChange={(e) => setAreaCode(e.target.value)}
                                        maxLength={3}
                                    />
                                </div>
                            </div>
                            <Button
                                onClick={handlePurchaseNumber}
                                disabled={isPurchasing}
                                variant="secondary"
                                className="shrink-0"
                            >
                                {isPurchasing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                Purchase Number
                            </Button>
                        </div>
                    </div>
                )}
            </CardContent>


            <CardFooter className="flex justify-end gap-3 border-t pt-4">
                <Button
                    variant="default"
                    asChild
                >
                    <a href="account/plans">Upgrade Plan</a>
                </Button>
                <Button
                    onClick={handleManageSubscription}
                    disabled={isManaging || !isStripe}
                    variant="outline"
                >
                    {isManaging ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                    Manage Subscription & Billing
                </Button>
            </CardFooter>
        </Card>
    );
}
