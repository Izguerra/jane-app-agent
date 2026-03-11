'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import useSWR, { mutate } from 'swr';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ArrowLeft, AlertTriangle } from 'lucide-react';
import Link from 'next/link';
import { toast } from 'sonner';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Import Tab Components
import { OverviewTab } from './_components/overview-tab';
import { CustomersTab } from './_components/customers-tab';
import { CommunicationsTab } from './_components/communications-tab';
import { AppointmentsTab } from './_components/appointments-tab';
import { CampaignsTab } from './_components/campaigns-tab';
import { WorkforceTab } from './_components/workforce-tab';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface Agent {
    id: string;
    name: string;
    phone_numbers: Array<{
        number: string;
        provider: string;
        is_active: boolean;
    }>;
}

interface Integration {
    id: string;
    provider: string;
    is_active: boolean;
    created_at: string | null;
}

interface WorkspaceDetails {
    id: string;
    name: string;
    team_id: string;
    owner_email: string;
    owner_name: string;
    owner_first_name: string;
    owner_last_name: string;
    plan: string;
    status: string;
    created_at: string;
    address: string | null;
    phone: string | null;
    email: string | null;
    website: string | null;
    custom_agent_limit: number | null;
    custom_call_limit: number | null;
    custom_chat_limit: number | null;
    stats: {
        total_conversations: number;
        voice_usage_minutes: number;
        lifetime_value: number;
    };
    agents: Agent[];
    integrations: Integration[];
    billing_history: any[];
    limits?: {
        agents: number;
        voice_minutes: number;
        conv_limit: number;
    };
}

export default function WorkspaceDetailsPage() {
    const params = useParams();
    const router = useRouter();
    const workspaceId = params?.workspaceId as string;

    const { data: workspace, error, isLoading } = useSWR<WorkspaceDetails>(
        workspaceId ? `/api/workspaces/${workspaceId}` : null,
        fetcher
    );

    const [isSuspending, setIsSuspending] = useState(false);
    const [isReactivating, setIsReactivating] = useState(false);
    const [showSuspendConfirm, setShowSuspendConfirm] = useState(false);
    const [showReactivateConfirm, setShowReactivateConfirm] = useState(false);

    const handleSuspendWorkspace = (e?: React.MouseEvent) => {
        e?.preventDefault();
        e?.stopPropagation();

        if (!workspace) return;
        if (isSuspending) return;

        setShowSuspendConfirm(true);
    };

    const confirmSuspend = async () => {
        setShowSuspendConfirm(false);
        setIsSuspending(true);

        try {
            const response = await fetch(`/api/workspaces/${workspace?.id}/status`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'suspended' }),
            });

            if (response.ok) {
                const result = await response.json();
                const actions = result.actions_taken?.join(', ') || 'Workspace suspended';
                toast.success(`Workspace "${workspace?.name}" has been suspended. ${actions}`);
                mutate(`/api/workspaces/${workspaceId}`);
                mutate('/api/workspaces');
            } else {
                const error = await response.json();
                toast.error(error.detail || 'Failed to suspend workspace');
            }
        } catch (error) {
            console.error('Suspend error:', error);
            toast.error('An error occurred while suspending the workspace');
        } finally {
            setIsSuspending(false);
        }
    };

    const handleReactivateWorkspace = (e?: React.MouseEvent) => {
        e?.preventDefault();
        e?.stopPropagation();

        if (!workspace) return;
        if (isReactivating) return;

        setShowReactivateConfirm(true);
    };

    const confirmReactivate = async () => {
        setShowReactivateConfirm(false);
        setIsReactivating(true);

        try {
            const response = await fetch(`/api/workspaces/${workspace?.id}/status`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'active' }),
            });

            if (response.ok) {
                const result = await response.json();
                const actions = result.actions_taken?.join(', ') || 'Workspace reactivated';
                toast.success(`Workspace "${workspace?.name}" has been reactivated. ${actions}`);
                mutate(`/api/workspaces/${workspaceId}`);
                mutate('/api/workspaces');
            } else {
                const error = await response.json();
                toast.error(error.detail || 'Failed to reactivate workspace');
            }
        } catch (error) {
            toast.error('An error occurred');
        } finally {
            setIsReactivating(false);
        }
    };

    const getInitials = (name: string) => {
        if (!name) return '??';
        const parts = name.split(' ');
        if (parts.length >= 2) {
            return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    };

    const getAvatarColor = (name: string) => {
        if (!name) return 'bg-gray-500';
        const colors = [
            'bg-blue-500',
            'bg-purple-500',
            'bg-pink-500',
            'bg-green-500',
            'bg-orange-500',
        ];
        const index = name.charCodeAt(0) % colors.length;
        return colors[index];
    };

    const getPlanBadge = (plan: string, status: string) => {
        if (status === 'suspended') {
            return <Badge variant="destructive">Suspended</Badge>;
        }
        if (status === 'active') {
            return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">Active</Badge>;
        }
        if (status === 'trialing') {
            return <Badge variant="secondary">Trialing</Badge>;
        }
        return <Badge variant="outline">{status}</Badge>;
    };

    const getIntegrationName = (provider: string) => {
        const names: Record<string, string> = {
            'jane_app': 'Jane App',
            'whatsapp': 'WhatsApp (Twilio)',
            'instagram': 'Instagram',
            'facebook': 'Facebook Messenger',
            'google_calendar': 'Google Calendar',
            'stripe': 'Stripe',
            'hubspot': 'HubSpot',
            'slack': 'Slack',
        };
        return names[provider] || provider;
    };

    const getIntegrationCategory = (provider: string) => {
        const categories: Record<string, string> = {
            'jane_app': 'Clinic Management',
            'whatsapp': 'Messaging',
            'instagram': 'Social Media',
            'facebook': 'Social Media',
            'google_calendar': 'Calendar',
            'stripe': 'Payments',
            'hubspot': 'CRM',
            'slack': 'Communication',
        };
        return categories[provider] || 'Integration';
    };

    if (isLoading) {
        return (
            <div className="p-8">
                <div className="text-muted-foreground">Loading...</div>
            </div>
        );
    }

    if (error || !workspace) {
        return (
            <div className="p-8">
                <div className="text-destructive">Failed to load workspace details</div>
            </div>
        );
    }

    return (
        <div className="p-8 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex flex-row items-center gap-2 flex-nowrap">
                    <Button variant="ghost" size="sm" asChild>
                        <Link href="/admin/workspaces" className="flex items-center gap-2">
                            <ArrowLeft className="h-4 w-4" />
                            <span>Workspaces</span>
                        </Link>
                    </Button>
                    <span className="text-muted-foreground">/</span>
                    <span className="font-medium whitespace-nowrap">{workspace.name}</span>
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant="destructive"
                        onClick={(e) => handleSuspendWorkspace(e)}
                        disabled={isSuspending || workspace.status === 'suspended'}
                    >
                        {isSuspending ? 'Suspending...' : workspace.status === 'suspended' ? 'Suspended' : 'Suspend'}
                    </Button>
                </div>
            </div>

            {/* Suspension Warning */}
            {workspace.status === 'suspended' && (
                <Card className="border-orange-200 bg-orange-50">
                    <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                            <AlertTriangle className="h-5 w-5 text-orange-600 flex-shrink-0 mt-0.5" />
                            <div className="flex-1">
                                <h3 className="font-semibold text-orange-900">Workspace Suspended</h3>
                                <p className="text-sm text-orange-800 mt-1">
                                    This workspace has been suspended. Billing is paused, all integrations are disconnected, and all agents are deactivated.
                                </p>
                            </div>
                            <Button
                                onClick={(e) => handleReactivateWorkspace(e)}
                                disabled={isReactivating}
                                className="bg-orange-600 hover:bg-orange-700"
                            >
                                {isReactivating ? 'Reactivating...' : 'Reactivate'}
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Suspend Confirmation Dialog */}
            {showSuspendConfirm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowSuspendConfirm(false)}>
                    <Card className="w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <AlertTriangle className="h-5 w-5 text-orange-600" />
                                Suspend Workspace
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <p>Are you sure you want to suspend <strong>"{workspace?.name}"</strong>?</p>
                            <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 space-y-2">
                                <p className="text-sm font-medium text-orange-900">This will:</p>
                                <ul className="text-sm text-orange-800 space-y-1 ml-4 list-disc">
                                    <li>Pause Stripe billing</li>
                                    <li>Disconnect all integrations</li>
                                    <li>Deactivate all agents</li>
                                </ul>
                            </div>
                            <div className="flex gap-3 justify-end">
                                <Button variant="outline" onClick={() => setShowSuspendConfirm(false)}>
                                    Cancel
                                </Button>
                                <Button variant="destructive" onClick={confirmSuspend}>
                                    Suspend Workspace
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Reactivate Confirmation Dialog */}
            {showReactivateConfirm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowReactivateConfirm(false)}>
                    <Card className="w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <AlertTriangle className="h-5 w-5 text-green-600" />
                                Reactivate Workspace
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <p>Are you sure you want to reactivate <strong>"{workspace?.name}"</strong>?</p>
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 space-y-2">
                                <p className="text-sm font-medium text-blue-900">This will:</p>
                                <ul className="text-sm text-blue-800 space-y-1 ml-4 list-disc">
                                    <li>Resume Stripe billing</li>
                                    <li>Automatically reactivate orchestrator agent</li>
                                    <li>Integrations will remain disconnected (manual reconnection required)</li>
                                    <li>Other agents will remain inactive (manual reactivation required)</li>
                                </ul>
                            </div>
                            <div className="flex gap-3 justify-end">
                                <Button variant="outline" onClick={() => setShowReactivateConfirm(false)}>
                                    Cancel
                                </Button>
                                <Button className="bg-green-600 hover:bg-green-700" onClick={confirmReactivate}>
                                    Reactivate Workspace
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Tabs */}
            <Tabs defaultValue="overview" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="overview">Overview</TabsTrigger>
                    <TabsTrigger value="customers">Customers</TabsTrigger>
                    <TabsTrigger value="communications">Communications</TabsTrigger>
                    <TabsTrigger value="appointments">Appointments</TabsTrigger>
                    <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
                    <TabsTrigger value="workforce">Workforce</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-4">
                    <OverviewTab
                        workspace={workspace}
                        getPlanBadge={getPlanBadge}
                        getIntegrationName={getIntegrationName}
                        getIntegrationCategory={getIntegrationCategory}
                        getAvatarColor={getAvatarColor}
                        getInitials={getInitials}
                    />
                </TabsContent>

                <TabsContent value="customers" className="space-y-4">
                    <CustomersTab workspaceId={workspaceId} />
                </TabsContent>

                <TabsContent value="communications" className="space-y-4">
                    <CommunicationsTab workspaceId={workspaceId} />
                </TabsContent>

                <TabsContent value="appointments" className="space-y-4">
                    <AppointmentsTab workspaceId={workspaceId} />
                </TabsContent>

                <TabsContent value="campaigns" className="space-y-4">
                    <CampaignsTab workspaceId={workspaceId} />
                </TabsContent>

                <TabsContent value="workforce" className="space-y-4">
                    <WorkforceTab workspaceId={workspaceId} />
                </TabsContent>
            </Tabs>
        </div>
    );
}

