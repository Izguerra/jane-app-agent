"use client";

import { useState } from "react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Loader2, CreditCard, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

interface UpgradeModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => Promise<void>;
    planName: string;
    amount: number;
    paymentMethod?: {
        brand: string;
        last4: string;
    };
    breakdown?: Array<{
        description: string;
        amount: number;
        period_start?: number;
        period_end?: number;
    }>;
    isLoading: boolean;
}

export function UpgradeModal({
    isOpen,
    onClose,
    onConfirm,
    planName,
    amount,
    paymentMethod,
    breakdown,
    isLoading
}: UpgradeModalProps) {
    const router = useRouter();
    const [isRedirecting, setIsRedirecting] = useState(false);

    const handleChangePaymentMethod = async () => {
        try {
            setIsRedirecting(true);
            const res = await fetch("/api/billing/portal", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
            });

            if (!res.ok) throw new Error("Failed to create portal session");

            const data = await res.json();
            window.location.href = data.url;
        } catch (error) {
            console.error("Portal error:", error);
            toast.error("Failed to redirect to billing portal");
            setIsRedirecting(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !isLoading && !isRedirecting && onClose()}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Confirm Upgrade to {planName}</DialogTitle>
                    <DialogDescription>
                        Review the immediate charges and confirm your payment method.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-6 py-4">
                    {/* Amount Summary */}
                    <div className="bg-muted/50 p-4 rounded-lg space-y-3">
                        <div className="flex justify-between items-center font-medium">
                            <span>Immediate Payment</span>
                            <span className="text-lg">${amount.toFixed(2)}</span>
                        </div>
                        {breakdown && breakdown.length > 0 && (
                            <div className="text-xs text-muted-foreground space-y-1 border-t pt-2">
                                {breakdown.map((item, i) => (
                                    <div key={i} className="flex justify-between">
                                        <span>{item.description}</span>
                                        <span>${item.amount.toFixed(2)}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                        <p className="text-xs text-muted-foreground mt-2">
                            This amount covers the prorated difference for the remainder of your current billing cycle.
                        </p>
                    </div>

                    {/* Payment Method */}
                    <div className="flex items-center justify-between border rounded-lg p-3">
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center">
                                <CreditCard className="h-5 w-5" />
                            </div>
                            <div>
                                <p className="font-medium text-sm">Payment Method</p>
                                <p className="text-xs text-muted-foreground">
                                    {paymentMethod ? (
                                        <span className="capitalize">{paymentMethod.brand} ending in {paymentMethod.last4}</span>
                                    ) : (
                                        "Default Payment Method"
                                    )}
                                </p>
                            </div>
                        </div>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="text-xs h-8"
                            onClick={handleChangePaymentMethod}
                            disabled={isLoading || isRedirecting}
                        >
                            Change
                        </Button>
                    </div>
                </div>

                <DialogFooter className="gap-2 sm:gap-0">
                    <Button
                        variant="outline"
                        onClick={onClose}
                        disabled={isLoading || isRedirecting}
                    >
                        Cancel
                    </Button>
                    <Button
                        onClick={onConfirm}
                        disabled={isLoading || isRedirecting}
                        className="bg-green-600 hover:bg-green-700"
                    >
                        {isLoading || isRedirecting ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                {isRedirecting ? "Redirecting..." : "Processing..."}
                            </>
                        ) : (
                            <>
                                Confirm & Pay ${amount.toFixed(2)}
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </>
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
