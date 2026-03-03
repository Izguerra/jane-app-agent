'use client';

import { useParams, useRouter } from 'next/navigation';
import useSWR from 'swr';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { StepBuilder } from '@/components/campaigns/step-builder';
import { CampaignAudience } from '@/components/campaigns/campaign-audience';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function CampaignDetailPage() {
    const params = useParams();
    const router = useRouter();
    const campaignId = params.campaignId as string;

    const { data: campaign, isLoading } = useSWR(campaignId ? `/api/campaigns/${campaignId}` : null, fetcher);
    const { data: steps, isLoading: isLoadingSteps, mutate: mutateSteps } = useSWR(campaignId ? `/api/campaigns/${campaignId}/steps` : null, fetcher);

    if (isLoading || isLoadingSteps) {
        return <div className="flex h-screen items-center justify-center"><Loader2 className="h-8 w-8 animate-spin" /></div>;
    }

    if (!campaign) {
        return <div className="p-8">Campaign not found</div>;
    }

    return (
        <div className="space-y-6 p-8 pt-6">
            <div className="flex items-center gap-4">
                <Button variant="ghost" size="icon" onClick={() => router.back()}>
                    <ArrowLeft className="h-4 w-4" />
                </Button>
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">{campaign.name}</h2>
                    <p className="text-muted-foreground">{campaign.description || "Manage campaign steps and configuration."}</p>
                </div>
                <div className="ml-auto flex items-center gap-2">
                    <Badge variant={campaign.is_active ? "default" : "secondary"}>
                        {campaign.status || (campaign.is_active ? "Active" : "Paused")}
                    </Badge>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
                <div className="md:col-span-2 space-y-6">
                    {/* Step Builder */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Campaign Steps</CardTitle>
                            <CardDescription>Define the sequence of actions for this campaign.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <StepBuilder
                                campaignId={campaignId}
                                steps={steps || []}
                                onUpdate={() => mutateSteps()}
                            />
                        </CardContent>
                    </Card>

                    {/* Audience & Enrollments */}
                    <CampaignAudience campaignId={campaignId} />
                </div>

                <div className="space-y-6">
                    {/* Sidebar Configuration (Configuration, Audience Stats, etc.) */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Configuration</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3 text-sm">
                            <div className="flex justify-between gap-2">
                                <span className="text-muted-foreground shrink-0">Trigger:</span>
                                <span className="font-medium capitalize text-right">{campaign.trigger_type}</span>
                            </div>
                            {campaign.trigger_event && (
                                <div className="flex justify-between gap-2">
                                    <span className="text-muted-foreground shrink-0">Event:</span>
                                    <span className="font-medium text-right">
                                        {(() => {
                                            const eventNames: Record<string, string> = {
                                                'appointment_booked': 'Appointment Booked',
                                                'appointment_cancelled': 'Appointment Cancelled',
                                                'appointment_completed': 'Appointment Completed',
                                                'customer_created': 'Customer Created',
                                                'deal_won': 'Deal Won',
                                                'deal_lost': 'Deal Lost',
                                            };
                                            return eventNames[campaign.trigger_event] || campaign.trigger_event.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase());
                                        })()}
                                    </span>
                                </div>
                            )}
                            <div className="flex justify-between gap-2">
                                <span className="text-muted-foreground shrink-0">Stop on Reply:</span>
                                <span className="font-medium text-right">{campaign.stop_on_response ? "Yes" : "No"}</span>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
