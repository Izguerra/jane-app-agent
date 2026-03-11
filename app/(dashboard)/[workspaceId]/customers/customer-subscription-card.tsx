'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { CreditCard, TrendingUp } from 'lucide-react';
import { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

const PLAN_DETAILS = {
    Starter: { price: '$29/mo', limit: 1000 },
    Professional: { price: '$99/mo', limit: 5000 },
    Enterprise: { price: '$299/mo', limit: 999999 },
};

function PaymentMethodForm({ customer, onSuccess, onCancel }: any) {
    const stripe = useStripe();
    const elements = useElements();
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!stripe || !elements) return;

        setLoading(true);
        try {
            // Create setup intent
            const setupResponse = await fetch(`/api/customers/${customer.id}/setup-intent`, {
                method: 'POST',
                credentials: 'include',
            });
            const { client_secret } = await setupResponse.json();

            // Confirm card setup
            const { error, setupIntent } = await stripe.confirmCardSetup(client_secret, {
                payment_method: {
                    card: elements.getElement(CardElement)!,
                },
            });

            if (error) {
                toast.error(error.message);
            } else {
                // Attach payment method to customer
                await fetch(`/api/customers/${customer.id}/payment-method`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ payment_method_id: setupIntent.payment_method }),
                });

                toast.success('Payment method added successfully');
                onSuccess();
            }
        } catch (error: any) {
            toast.error(error.message || 'Failed to add payment method');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <Label>Card Details</Label>
                <div className="mt-2 p-3 border rounded-md">
                    <CardElement options={{
                        hidePostalCode: false,
                        style: {
                            base: {
                                fontSize: '16px',
                                color: '#424770',
                                '::placeholder': { color: '#aab7c4' },
                            },
                        },
                    }} />
                </div>
            </div>
            <div className="flex gap-2">
                <Button type="button" variant="outline" onClick={onCancel} className="flex-1">
                    Cancel
                </Button>
                <Button type="submit" disabled={!stripe || loading} className="flex-1">
                    {loading ? 'Processing...' : 'Add Payment Method'}
                </Button>
            </div>
        </form>
    );
}

function SubscriptionUpgradeDialog({ customer, open, onOpenChange, onSuccess }: any) {
    const [selectedPlan, setSelectedPlan] = useState(customer.plan);
    const [proration, setProration] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (selectedPlan && selectedPlan !== customer.plan) {
            fetch(`/api/customers/${customer.id}/proration?new_plan=${selectedPlan}`, {
                credentials: 'include',
            })
                .then(res => res.json())
                .then(setProration)
                .catch(() => setProration(null));
        } else {
            setProration(null);
        }
    }, [selectedPlan, customer]);

    const handleUpgrade = async () => {
        setLoading(true);
        try {
            // All customers must have existing subscriptions
            if (!customer.stripe_subscription_id) {
                toast.error('Customer does not have an active subscription');
                return;
            }

            const res = await fetch(`/api/customers/${customer.id}/subscription`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ plan: selectedPlan }),
            });

            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail || 'Failed to update subscription');
            }

            toast.success(`Subscription updated to ${selectedPlan}`);
            onSuccess();
            onOpenChange(false);
        } catch (error: any) {
            toast.error(error.message || 'Failed to update subscription');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Change Subscription Plan</DialogTitle>
                    <DialogDescription>
                        Select a new plan for this customer. Proration will be calculated automatically.
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                    <div>
                        <Label>Select Plan</Label>
                        <Select value={selectedPlan} onValueChange={setSelectedPlan}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                {Object.entries(PLAN_DETAILS).map(([plan, details]) => (
                                    <SelectItem key={plan} value={plan}>
                                        {plan} - {details.price} ({details.limit.toLocaleString()} min/mo)
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {proration && (
                        <div className="p-4 bg-muted rounded-lg space-y-2">
                            <div className="flex justify-between text-sm">
                                <span>Current Plan:</span>
                                <span className="font-medium">{proration.old_plan}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span>New Plan:</span>
                                <span className="font-medium">{proration.new_plan}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span>Days Remaining:</span>
                                <span className="font-medium">{proration.days_remaining}</span>
                            </div>
                            <div className="border-t pt-2 mt-2 flex justify-between font-semibold">
                                <span>{proration.amount >= 0 ? 'Amount Due Today:' : 'Credit Applied:'}</span>
                                <span className={proration.amount >= 0 ? 'text-blue-600' : 'text-green-600'}>
                                    {proration.amount_formatted}
                                </span>
                            </div>
                            {proration.amount >= 0 && (
                                <p className="text-xs text-muted-foreground mt-2">
                                    This amount will be charged immediately for the plan upgrade.
                                </p>
                            )}
                        </div>
                    )}

                    <div className="flex gap-2">
                        <Button variant="outline" onClick={() => onOpenChange(false)} className="flex-1">
                            Cancel
                        </Button>
                        <Button
                            onClick={handleUpgrade}
                            disabled={loading || selectedPlan === customer.plan}
                            className="flex-1"
                        >
                            {loading ? 'Updating...' : 'Update Plan'}
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}

export function CustomerSubscriptionCard({ customer }: { customer: any }) {
    const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
    const [upgradeDialogOpen, setUpgradeDialogOpen] = useState(false);
    const [paymentMethods, setPaymentMethods] = useState<any[]>([]);

    const usagePercent = (customer.usage_used / customer.usage_limit) * 100;
    const planDetails = PLAN_DETAILS[customer.plan as keyof typeof PLAN_DETAILS] || PLAN_DETAILS.Starter;

    useEffect(() => {
        fetch(`/api/customers/${customer.id}/payment-methods`, { credentials: 'include' })
            .then(res => res.json())
            .then(data => setPaymentMethods(data.payment_methods || []))
            .catch(() => setPaymentMethods([]));
    }, [customer.id]);

    const defaultPaymentMethod = paymentMethods.find(pm => pm.id === customer.stripe_payment_method_id);

    return (
        <Card>
            <CardHeader>
                <CardTitle>Subscription & Usage</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Current Plan</span>
                    <span className="font-medium">{customer.plan}</span>
                </div>

                <Button variant="outline" className="w-full" onClick={() => setUpgradeDialogOpen(true)}>
                    <TrendingUp className="mr-2 h-4 w-4" />
                    Change Plan
                </Button>

                <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Usage</span>
                        <span className="text-green-600 font-medium">
                            {customer.usage_used || 0} / {(customer.usage_limit || 0).toLocaleString()} minutes
                        </span>
                    </div>
                    <Progress value={usagePercent} className="h-2" />
                    <p className="text-xs text-muted-foreground">
                        {usagePercent.toFixed(1)}% of monthly limit used
                    </p>
                </div>

                <div className="pt-4 border-t space-y-2">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <CreditCard className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground">Payment Method</span>
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => setPaymentDialogOpen(true)}>
                            Update
                        </Button>
                    </div>
                    {defaultPaymentMethod ? (
                        <p className="text-sm">
                            {defaultPaymentMethod.card.brand.toUpperCase()} •••• {defaultPaymentMethod.card.last4}
                        </p>
                    ) : (
                        <p className="text-sm text-muted-foreground">No payment method on file</p>
                    )}
                </div>
            </CardContent>

            <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Update Payment Method</DialogTitle>
                        <DialogDescription>
                            Add a new payment method for this customer. Card details are securely processed by Stripe.
                        </DialogDescription>
                    </DialogHeader>
                    <Elements stripe={stripePromise}>
                        <PaymentMethodForm
                            customer={customer}
                            onSuccess={() => {
                                setPaymentDialogOpen(false);
                                window.location.reload();
                            }}
                            onCancel={() => setPaymentDialogOpen(false)}
                        />
                    </Elements>
                </DialogContent>
            </Dialog>

            <SubscriptionUpgradeDialog
                customer={customer}
                open={upgradeDialogOpen}
                onOpenChange={setUpgradeDialogOpen}
                onSuccess={() => window.location.reload()}
            />
        </Card>
    );
}
