'use client';

import { ReactNode } from 'react';
import useSWR from 'swr';
import { useParams, useRouter, usePathname } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Lock, Sparkles, ArrowRight, Clock, AlertTriangle } from 'lucide-react';

const fetcher = async (url: string) => {
    const res = await fetch(url);
    if (!res.ok) return null;
    return res.json();
};

interface FeatureGateProps {
    /** The feature key to check (e.g., 'campaigns', 'appointments', 'analytics') */
    feature: 'campaigns' | 'appointments' | 'deals' | 'analytics' | 'knowledge_base';
    /** Content to render if access is granted */
    children: ReactNode;
    /** Optional custom message for the upgrade prompt */
    upgradeMessage?: string;
    /** Optional: for analytics, check if user needs "advanced" tier */
    requireAdvanced?: boolean;
    /** Show a loading state while checking */
    showLoading?: boolean;
}

/**
 * FeatureGate component - Blocks access to features based on subscription plan
 * 
 * Usage:
 * <FeatureGate feature="campaigns">
 *   <CampaignsPageContent />
 * </FeatureGate>
 */
export function FeatureGate({
    feature,
    children,
    upgradeMessage,
    requireAdvanced = false,
    showLoading = true
}: FeatureGateProps) {
    const params = useParams();
    const router = useRouter();
    const pathname = usePathname();
    const workspaceId = params?.workspaceId as string;

    const { data: features, isLoading } = useSWR(
        workspaceId && workspaceId !== 'undefined'
            ? `/api/workspaces/${workspaceId}/features`
            : null,
        fetcher
    );

    // Show loading state
    if (isLoading && showLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="animate-pulse text-muted-foreground">Loading...</div>
            </div>
        );
    }

    // If we can't fetch features, allow access (fail open for now)
    if (!features) {
        return <>{children}</>;
    }

    // Check if trial is expired - block core features but allow settings access
    const isTrialExpired = features?.is_trial_expired === true;
    const isSettingsPage = pathname?.includes('/account') ||
        pathname?.includes('/team') ||
        pathname?.includes('/security');

    // If trial expired and NOT on a settings page, show trial expired prompt
    if (isTrialExpired && !isSettingsPage) {
        return (
            <div className="flex items-center justify-center min-h-[60vh] p-8">
                <Card className="max-w-lg w-full text-center">
                    <CardHeader className="pb-4">
                        <div className="mx-auto w-16 h-16 bg-gradient-to-br from-red-100 to-orange-100 dark:from-red-900/30 dark:to-orange-900/30 rounded-full flex items-center justify-center mb-4">
                            <Clock className="h-8 w-8 text-red-600 dark:text-red-400" />
                        </div>
                        <CardTitle className="text-2xl">
                            Your Free Trial Has Ended
                        </CardTitle>
                        <CardDescription className="text-base mt-2">
                            Choose a plan to continue using all features. Your data is safe and waiting for you.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex flex-col gap-3">
                            <Button
                                size="lg"
                                onClick={() => router.push(`/${workspaceId}/dashboard/account`)}
                                className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700"
                            >
                                <Sparkles className="mr-2 h-4 w-4" />
                                Choose a Plan
                            </Button>
                            <Button
                                variant="ghost"
                                onClick={() => router.push(`/${workspaceId}/dashboard/account`)}
                            >
                                View Billing Settings
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Check access based on feature type
    let hasAccess = false;
    let featureName = '';
    let defaultMessage = '';

    switch (feature) {
        case 'campaigns':
            hasAccess = features?.features?.campaigns === true;
            featureName = 'Campaigns';
            defaultMessage = 'Automated campaigns are available on Pro and higher plans. Upgrade to create and manage outbound calling campaigns.';
            break;
        case 'appointments':
            hasAccess = features?.features?.appointments === true;
            featureName = 'Appointments';
            defaultMessage = 'To manage appointments, you need to connect a calendar integration first. Go to Integrations to connect Google Calendar or Microsoft Exchange.';
            break;
        case 'analytics':
            if (requireAdvanced) {
                hasAccess = features?.features?.analytics === 'advanced' || features?.features?.analytics === 'custom';
                featureName = 'Advanced Analytics';
                defaultMessage = 'Advanced analytics features are available on Pro and higher plans. Upgrade to access detailed reports and exports.';
            } else {
                hasAccess = true; // Basic analytics is always available
            }
            break;
        case 'knowledge_base':
            // Use the feature flag from backend
            hasAccess = features?.features?.knowledge_base === true;
            featureName = 'Knowledge Base';
            defaultMessage = 'Knowledge Base sources are available on Pro and higher plans. Upgrade to train your AI with custom data.';
            break;
        case 'deals':
            hasAccess = features?.features?.deals !== false;
            featureName = 'Deals';
            defaultMessage = 'Deal tracking is available on Pro and higher plans.';
            break;
        default:
            hasAccess = true;
    }

    // If access granted, render children
    if (hasAccess) {
        return <>{children}</>;
    }

    // Render upgrade prompt
    const isCalendarRequired = feature === 'appointments';

    return (
        <div className="flex items-center justify-center min-h-[60vh] p-8">
            <Card className="max-w-lg w-full text-center">
                <CardHeader className="pb-4">
                    <div className="mx-auto w-16 h-16 bg-gradient-to-br from-violet-100 to-indigo-100 dark:from-violet-900/30 dark:to-indigo-900/30 rounded-full flex items-center justify-center mb-4">
                        {isCalendarRequired ? (
                            <Lock className="h-8 w-8 text-violet-600 dark:text-violet-400" />
                        ) : (
                            <Sparkles className="h-8 w-8 text-violet-600 dark:text-violet-400" />
                        )}
                    </div>
                    <CardTitle className="text-2xl">
                        {isCalendarRequired ? `${featureName} Requires Setup` : `Upgrade to Access ${featureName}`}
                    </CardTitle>
                    <CardDescription className="text-base mt-2">
                        {upgradeMessage || defaultMessage}
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex flex-col gap-3">
                        {isCalendarRequired ? (
                            <Button
                                size="lg"
                                onClick={() => router.push(`/${workspaceId}/dashboard/integrations`)}
                                className="w-full"
                            >
                                Connect Calendar
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        ) : (
                            <Button
                                size="lg"
                                onClick={() => router.push(`/${workspaceId}/dashboard/account`)}
                                className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700"
                            >
                                <Sparkles className="mr-2 h-4 w-4" />
                                Upgrade Plan
                            </Button>
                        )}
                        <Button
                            variant="ghost"
                            onClick={() => router.back()}
                        >
                            Go Back
                        </Button>
                    </div>

                    {!isCalendarRequired && (
                        <div className="pt-4 border-t">
                            <p className="text-sm text-muted-foreground">
                                Current plan: <span className="font-medium capitalize">{features?.tier || 'Starter'}</span>
                            </p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}

/**
 * Hook to check feature access without rendering a gate
 */
export function useFeatureAccess(feature: FeatureGateProps['feature']) {
    const params = useParams();
    const workspaceId = params?.workspaceId as string;

    const { data: features, isLoading } = useSWR(
        workspaceId && workspaceId !== 'undefined'
            ? `/api/workspaces/${workspaceId}/features`
            : null,
        fetcher
    );

    if (isLoading || !features) {
        return { hasAccess: null, isLoading, tier: null, isTrialExpired: false };
    }

    const isTrialExpired = features?.is_trial_expired === true;
    let hasAccess = false;

    switch (feature) {
        case 'campaigns':
            hasAccess = features?.features?.campaigns === true;
            break;
        case 'appointments':
            hasAccess = features?.features?.appointments === true;
            break;
        case 'analytics':
            hasAccess = true; // Basic always available
            break;
        case 'knowledge_base':
            hasAccess = features?.features?.knowledge_base === true;
            break;
        case 'deals':
            hasAccess = features?.features?.deals !== false;
            break;
        default:
            hasAccess = true;
    }

    // If trial expired, no access to features (except settings)
    if (isTrialExpired) {
        hasAccess = false;
    }

    return {
        hasAccess,
        isLoading,
        tier: features?.tier,
        features: features?.features,
        isTrialExpired,
        trialEndDate: features?.trial_end_date,
        daysUntilTrialEnd: features?.days_until_trial_end
    };
}
