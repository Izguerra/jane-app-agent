"use client";

import { useState } from "react";

import { PricingTable, PRICING_PLANS } from "@/components/pricing-table";
import { useRouter, useParams } from "next/navigation";
import { toast } from "sonner";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

import { useUpgradeFees } from "@/hooks/use-upgrade-fees";
import { UpgradeModal } from "./upgrade-modal";

import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function PlansPage() {
    const router = useRouter();
    const params = useParams();
    const workspaceId = params.workspaceId as string;

    const { data: subscription } = useSWR('/api/billing/subscription', fetcher);

    // Use shared hook for fees
    const { data: upgrades = {}, isLoading: isLoadingFees } = useUpgradeFees();

    const [selectedUpgrade, setSelectedUpgrade] = useState<{
        priceId: string;
        planName: string;
        amount: number;
        paymentMethod?: any;
        breakdown?: any;
    } | null>(null);

    const [isProcessingUpgrade, setIsProcessingUpgrade] = useState(false);

    const handleSelectPlan = async (priceId: string) => {
        try {
            const upgradeParams = upgrades[priceId];

            // If canUpgrade is true, we open the confirmation modal
            if (upgradeParams?.canUpgrade) {
                const plan = PRICING_PLANS.find(p => p.priceId === priceId);
                setSelectedUpgrade({
                    priceId,
                    planName: plan?.name || "New Plan",
                    amount: upgradeParams.amount,
                    paymentMethod: upgradeParams.payment_method,
                    breakdown: upgradeParams.breakdown
                });
                return;
            }

            // Checkout Flow (Fallback or New Subscription)
            const res = await fetch('/api/billing/create-checkout-session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ price_id: priceId, mode: 'subscription' })
            });

            if (!res.ok) {
                const error = await res.json();
                toast.error(error.detail || "Failed to start checkout");
                return;
            }

            const data = await res.json();
            if (data && data.url) {
                window.location.href = data.url;
            } else {
                console.error("Invalid checkout response:", data);
                toast.error("Invalid checkout session URL");
            }
        } catch (error) {
            console.error("Plan selection error:", error);
            toast.error("An error occurred. Please try again.");
        }
    };

    const confirmUpgrade = async () => {
        if (!selectedUpgrade) return;

        setIsProcessingUpgrade(true);
        try {
            const res = await fetch('/api/billing/update-subscription', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ price_id: selectedUpgrade.priceId })
            });

            if (res.ok) {
                toast.success("Plan updated successfully!");
                router.push(`/${workspaceId}/dashboard/account`);
                setSelectedUpgrade(null); // Close modal
            } else {
                const err = await res.json();
                toast.error(err.detail || "Failed to update plan");
            }
        } catch (error) {
            console.error("Upgrade error:", error);
            toast.error("Failed to process upgrade");
        } finally {
            setIsProcessingUpgrade(false);
        }
    };

    // Getting the current plan name from subscription data
    const currentPlanName = subscription?.plan || "Free";

    return (
        <div className="space-y-8">
            <div className="flex items-center gap-4">
                <Link href={`/${workspaceId}/dashboard/account`}>
                    <Button variant="ghost" size="icon">
                        <ArrowLeft className="h-4 w-4" />
                    </Button>
                </Link>
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Available Plans</h1>
                    <p className="text-muted-foreground">
                        Upgrade or downgrade your subscription plan
                    </p>
                </div>
            </div>

            <PricingTable
                mode="internal"
                onSelectPlan={handleSelectPlan}
                upgradeInfo={upgrades}
                currentPlanName={currentPlanName}
                isLoading={isLoadingFees}
            />

            {selectedUpgrade && (
                <UpgradeModal
                    isOpen={!!selectedUpgrade}
                    onClose={() => setSelectedUpgrade(null)}
                    onConfirm={confirmUpgrade}
                    planName={selectedUpgrade.planName}
                    amount={selectedUpgrade.amount}
                    paymentMethod={selectedUpgrade.paymentMethod}
                    breakdown={selectedUpgrade.breakdown}
                    isLoading={isProcessingUpgrade}
                />
            )}
        </div>
    );
}
