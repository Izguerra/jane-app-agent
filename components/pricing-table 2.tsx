"use client";

import { Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

// Updated Pricing Data matching .env
export const PRICING_PLANS = [
    {
        name: 'Starter',
        price: 2900,
        interval: 'month',
        trialDays: 14,
        features: [
            '1,000 conversations/month',
            '100 voice minutes/month',
            '1 Phone Number',
            'Basic Support',
        ],
        priceId: 'price_1SffxH6Rc2ce57mvgxJPdVEx',
        popular: false,
    },
    {
        name: 'Pro',
        price: 12900,
        interval: 'month',
        trialDays: 14,
        features: [
            '2 AI Personalities',
            '1 Local Phone Number',
            'Voice: $0.22 / min',
            'Chat: $0.06 / msg',
            'Basic Integrations (Cal, CRM)',
            'Standard HD Voice',
        ],
        priceId: 'price_1SpuwS6Rc2ce57mvuoenTeSt',
        popular: false,
    },
    {
        name: 'Pro+',
        price: 34900,
        interval: 'month',
        trialDays: 14,
        features: [
            '8 AI Personalities',
            '3 Local Phone Numbers',
            'Voice: $0.15 / min',
            'Chat: $0.04 / msg',
            'Advanced Integrations',
            'Premium Emotional Voice',
            'Outcome Fee: $2.50 / booking',
        ],
        priceId: 'price_1Spv0g6Rc2ce57mvskyImgME',
        popular: true,
    },
    {
        name: 'ProMax',
        price: 89900,
        interval: 'month',
        trialDays: 14,
        features: [
            '25 AI Personalities',
            '10 Local Phone Numbers',
            'Voice: $0.09 / min',
            'Chat: $0.02 / msg',
            'Premium Support',
            'Outcome Fee: $1.50 / booking',
        ],
        priceId: 'price_1Spv0j6Rc2ce57mv14JuYQcR',
        popular: false,
    },
    {
        name: 'Enterprise',
        price: null,
        interval: 'month',
        trialDays: 0,
        features: [
            'Unlimited AI Agents',
            'Volume Discounts',
            'Dedicated Engineering Support',
            'Low-Latency Edge Routing',
            'HIPAA + BAA Signed',
        ],
        popular: false,
        isEnterprise: true,
    },
];

interface UpgradeInfo {
    amount: number;
    canUpgrade: boolean;
    breakdown?: {
        description: string;
        amount: number;
    }[];
}

interface PricingTableProps {
    mode?: 'public' | 'internal';
    currentPlanId?: string;
    currentPlanName?: string;
    onSelectPlan?: (priceId: string) => void;
    upgradeInfo?: Record<string, UpgradeInfo>;
    isLoading?: boolean;
}

export function PricingTable({ mode = 'public', currentPlanId, currentPlanName, onSelectPlan, upgradeInfo, isLoading }: PricingTableProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-[1600px] mx-auto">
            {PRICING_PLANS.map((plan) => {
                const info = upgradeInfo?.[plan.priceId || ''];
                const upgradeFee = info?.amount;
                const canUpgrade = info?.canUpgrade;

                // Match by ID or Name (fuzzy match due to "Start Plan" vs "Starter" variants possible)
                // Assuming plan.name is "Starter", "Pro", etc.
                const isCurrent = !!((currentPlanId && currentPlanId === plan.priceId) ||
                    (currentPlanName && (
                        currentPlanName.toLowerCase() === plan.name.toLowerCase() ||
                        (currentPlanName.toLowerCase().includes(plan.name.toLowerCase()) && plan.name !== "Pro")
                    )));

                let buttonText = mode === 'internal' ? "Switch Plan" : "Get Started";
                if (isLoading) {
                    buttonText = "Calculating...";
                } else if (isCurrent) {
                    buttonText = "Current Plan";
                } else if (canUpgrade && upgradeFee !== undefined) {
                    if (upgradeFee > 0) buttonText = `Pay $${upgradeFee.toFixed(2)} to Switch`;
                    else if (upgradeFee < 0) buttonText = `Switch (Credit $${Math.abs(upgradeFee).toFixed(2)})`;
                    else buttonText = "Switch Plan (No Charge)";
                }

                return (
                    <PricingCard
                        key={plan.name}
                        {...plan}
                        mode={mode}
                        isCurrent={isCurrent}
                        priceOverride={(!isCurrent && canUpgrade && !isLoading) ? upgradeFee : null}
                        customButtonText={buttonText}
                        isDisabled={isLoading}
                        onSelect={() => onSelectPlan && plan.priceId && onSelectPlan(plan.priceId)}
                    />
                )
            })}
        </div>
    );
}

function PricingCard({
    name,
    price,
    interval,
    trialDays,
    features,
    priceId,
    popular = false,
    isEnterprise = false,
    mode,
    isCurrent,
    priceOverride,
    customButtonText,
    isDisabled,
    onSelect
}: {
    name: string;
    price: number | null;
    interval: string;
    trialDays: number;
    features: string[];
    priceId?: string;
    popular?: boolean;
    isEnterprise?: boolean;
    mode: 'public' | 'internal';
    isCurrent: boolean;
    priceOverride?: number | null;
    customButtonText?: string;
    isDisabled?: boolean;
    onSelect: () => void;
}) {
    return (
        <div
            className={`flex flex-col relative pt-6 pb-8 px-6 rounded-2xl ${popular
                ? 'bg-gradient-to-b from-orange-50 to-white border-2 border-orange-500 shadow-xl'
                : 'bg-white border border-gray-200 shadow-sm'
                }`}
        >
            {popular && (
                <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                    <span className="bg-orange-500 text-white px-4 py-1 rounded-full text-sm font-medium whitespace-nowrap shadow-sm">
                        Most Popular
                    </span>
                </div>
            )}

            <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900 mb-2">{name}</h2>
                {!isEnterprise && trialDays > 0 && (
                    <p className="text-xs text-gray-600">
                        {trialDays} day free trial
                    </p>
                )}
            </div>

            <div className="mb-6">
                {priceOverride !== undefined && priceOverride !== null ? (
                    <>
                        <p className="text-4xl font-bold text-gray-900">${priceOverride}</p>
                        <p className="text-gray-600 mt-1 text-sm">pay today</p>
                    </>
                ) : price !== null ? (
                    <>
                        <p className="text-4xl font-bold text-gray-900">${price / 100}</p>
                        <p className="text-gray-600 mt-1 text-sm">per {interval}</p>
                    </>
                ) : (
                    <>
                        <p className="text-4xl font-bold text-gray-900">Custom</p>
                        <p className="text-gray-600 mt-1 text-sm">Contact sales</p>
                    </>
                )}
            </div>

            <ul className="space-y-3 mb-8 flex-grow">
                {features.map((feature, index) => (
                    <li key={index} className="flex items-start text-sm">
                        <Check
                            className={`h-4 w-4 ${popular ? 'text-orange-600' : 'text-orange-500'
                                } mr-2.5 mt-0.5 flex-shrink-0`}
                        />
                        <span className="text-gray-700">{feature}</span>
                    </li>
                ))}
            </ul>

            <div className="mt-auto">
                {isEnterprise ? (
                    <a
                        href="mailto:sales@supaagent.com"
                        className={`block w-full text-center py-2.5 px-4 rounded-full font-medium transition-colors text-sm ${popular
                            ? 'bg-orange-600 text-white hover:bg-orange-700'
                            : 'bg-gray-900 text-white hover:bg-gray-800'
                            }`}
                    >
                        Contact Sales
                    </a>
                ) : (
                    mode === 'public' ? (
                        <Button
                            asChild
                            disabled={isDisabled}
                            className={`w-full py-2.5 px-4 rounded-full font-medium transition-colors text-sm ${popular
                                ? 'bg-orange-600 text-white hover:bg-orange-700'
                                : 'bg-gray-900 text-white hover:bg-gray-800'
                                }`}
                        >
                            <Link href={`/sign-up?redirect=checkout&priceId=${priceId}`}>
                                Get Started
                            </Link>
                        </Button>
                    ) : (
                        <Button
                            onClick={onSelect}
                            disabled={isCurrent || isDisabled}
                            className={`w-full py-2.5 px-4 rounded-full font-medium transition-colors text-sm ${popular
                                ? 'bg-orange-600 text-white hover:bg-orange-700'
                                : 'bg-gray-900 text-white hover:bg-gray-800'
                                }`}
                        >
                            {customButtonText || (isCurrent ? "Current Plan" : "Switch Plan")}
                        </Button>
                    )
                )}
            </div>
        </div>
    );
}
