
import useSWR, { mutate } from 'swr';
import { PRICING_PLANS } from '@/components/pricing-table';

export type UpgradeInfo = {
    amount: number;
    canUpgrade: boolean;
    payment_method?: {
        brand: string;
        last4: string;
    };
    breakdown?: {
        description: string;
        amount: number;
        period_start?: number;
        period_end?: number;
    }[];
};

const CACHE_KEY = 'upgrade-fees-all';

const fetcher = async () => {

    const results = await Promise.all(PRICING_PLANS.map(async (plan) => {
        if (!plan.priceId) return null;
        try {
            const res = await fetch('/api/billing/preview-upgrade', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ price_id: plan.priceId })
            });

            if (res.ok) {
                const data = await res.json();
                if (data.can_upgrade) {
                    return {
                        priceId: plan.priceId,
                        info: {
                            amount: data.amount_due,
                            canUpgrade: true,
                            payment_method: data.payment_method,
                            breakdown: data.breakdown
                        } as UpgradeInfo
                    };
                }
            }
        } catch (e) {
            console.error("Fee fetch error", e);
        }
        return null;
    }));

    const newUpgrades: Record<string, UpgradeInfo> = {};
    results.forEach(r => {
        if (r) newUpgrades[r.priceId] = r.info;
    });
    return newUpgrades;
};

export function useUpgradeFees() {
    return useSWR<Record<string, UpgradeInfo>>(CACHE_KEY, fetcher, {
        revalidateOnFocus: false,
        revalidateOnReconnect: false,
        dedupingInterval: 60000 * 5, // Cache for 5 mins
        keepPreviousData: true,
    });
}

export function preloadUpgradeFees() {
    mutate(CACHE_KEY, fetcher(), { populateCache: true, revalidate: false });
}
