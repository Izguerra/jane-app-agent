'use client';

import Link from 'next/link';
import { AlertTriangle, XCircle, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SubscriptionBannerProps {
    status: string;
    workspaceId?: string;
    trialEndDate?: string | null;
    isTrialExpired?: boolean;
    daysUntilTrialEnd?: number | null;
}

export function SubscriptionBanner({
    status,
    workspaceId,
    trialEndDate,
    isTrialExpired,
    daysUntilTrialEnd
}: SubscriptionBannerProps) {
    // No banner needed for active subscriptions
    if (status === 'active') {
        return null;
    }

    // Handle trialing status
    if (status === 'trialing') {
        // Trial expired - show red alert
        if (isTrialExpired) {
            return (
                <div className="w-full px-4 py-3 flex items-center justify-between bg-red-50 border-b border-red-200">
                    <div className="flex items-center gap-3">
                        <XCircle className="h-5 w-5 text-red-500" />
                        <span className="text-sm font-medium text-red-800">
                            Your free trial has ended. Choose a plan to continue using all features.
                        </span>
                    </div>
                    <Link href={workspaceId ? `/${workspaceId}/dashboard/account` : '/dashboard/account'}>
                        <Button
                            size="sm"
                            variant="destructive"
                        >
                            Choose a Plan
                        </Button>
                    </Link>
                </div>
            );
        }

        // Trial ending soon (7 days or less) - show yellow warning
        if (daysUntilTrialEnd !== null && daysUntilTrialEnd !== undefined && daysUntilTrialEnd <= 7) {
            const daysText = daysUntilTrialEnd === 0
                ? 'today'
                : daysUntilTrialEnd === 1
                    ? 'in 1 day'
                    : `in ${daysUntilTrialEnd} days`;

            return (
                <div className="w-full px-4 py-3 flex items-center justify-between bg-yellow-50 border-b border-yellow-200">
                    <div className="flex items-center gap-3">
                        <Clock className="h-5 w-5 text-yellow-600" />
                        <span className="text-sm font-medium text-yellow-800">
                            Your free trial ends {daysText}. Upgrade now to keep all your data and features.
                        </span>
                    </div>
                    <Link href={workspaceId ? `/${workspaceId}/dashboard/account` : '/dashboard/account'}>
                        <Button
                            size="sm"
                            variant="outline"
                            className="border-yellow-600 text-yellow-700 hover:bg-yellow-100"
                        >
                            Upgrade Now
                        </Button>
                    </Link>
                </div>
            );
        }

        // Active trial with more than 7 days - no banner
        return null;
    }

    // Handle suspended, canceled, and past_due statuses
    const isSuspended = status === 'suspended';
    const isCanceled = status === 'canceled' || status === 'past_due';

    if (!isSuspended && !isCanceled) {
        return null;
    }

    return (
        <div className={`w-full px-4 py-3 flex items-center justify-between ${isCanceled
            ? 'bg-red-50 border-b border-red-200'
            : 'bg-yellow-50 border-b border-yellow-200'
            }`}>
            <div className="flex items-center gap-3">
                {isCanceled ? (
                    <XCircle className="h-5 w-5 text-red-500" />
                ) : (
                    <AlertTriangle className="h-5 w-5 text-yellow-600" />
                )}
                <span className={`text-sm font-medium ${isCanceled ? 'text-red-800' : 'text-yellow-800'
                    }`}>
                    {isCanceled
                        ? 'Your subscription has been canceled. Reactivate to regain full access.'
                        : 'Your account is suspended. Some features are disabled.'}
                </span>
            </div>
            <Link href={workspaceId ? `/${workspaceId}/dashboard/account` : '/dashboard/account'}>
                <Button
                    size="sm"
                    variant={isCanceled ? 'destructive' : 'outline'}
                    className={isCanceled ? '' : 'border-yellow-600 text-yellow-700 hover:bg-yellow-100'}
                >
                    Reactivate Your Account
                </Button>
            </Link>
        </div>
    );
}
