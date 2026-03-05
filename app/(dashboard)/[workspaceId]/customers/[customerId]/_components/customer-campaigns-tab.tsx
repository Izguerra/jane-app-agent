import { useState } from 'react';
import useSWR, { mutate } from 'swr';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Target, TrendingUp, CheckCircle2, XCircle, Clock, Plus } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { toast } from 'sonner';

const fetcher = (url: string) => fetch(url, { credentials: 'include' }).then((res) => res.json());

interface CustomerCampaignsTabProps {
    customerId: string;
}

export function CustomerCampaignsTab({ customerId }: CustomerCampaignsTabProps) {
    const [isEnrollOpen, setIsEnrollOpen] = useState(false);
    const [selectedCampaignId, setSelectedCampaignId] = useState<string>('');
    const [isEnrolling, setIsEnrolling] = useState(false);

    const { data, isLoading } = useSWR(
        `/api/customers/${customerId}/campaigns`,
        fetcher
    );

    const { data: allCampaigns } = useSWR(
        isEnrollOpen ? '/api/campaigns' : null,
        fetcher
    );

    const handleEnroll = async () => {
        if (!selectedCampaignId) return;
        setIsEnrolling(true);

        try {
            const res = await fetch(`/api/campaigns/${selectedCampaignId}/enroll`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ customer_id: customerId }),
            });

            if (!res.ok) throw new Error("Failed to enroll");

            toast.success("Customer enrolled in campaign");
            setIsEnrollOpen(false);
            setSelectedCampaignId('');
            mutate(`/api/customers/${customerId}/campaigns`); // Refresh list
        } catch (e) {
            console.error(e);
            toast.error("Failed to enroll customer");
        } finally {
            setIsEnrolling(false);
        }
    };

    if (isLoading) {
        return (
            <div className="space-y-4">
                {[1, 2].map((i) => (
                    <Card key={i}>
                        <CardHeader>
                            <Skeleton className="h-6 w-48" />
                            <Skeleton className="h-4 w-32 mt-2" />
                        </CardHeader>
                        <CardContent>
                            <Skeleton className="h-20 w-full" />
                        </CardContent>
                    </Card>
                ))}
            </div>
        );
    }

    const campaigns = data?.items || [];

    const getStatusConfig = (status: string) => {
        const configs: Record<string, { variant: any; icon: any; label: string }> = {
            active: { variant: 'default', icon: Clock, label: 'Active' },
            pending: { variant: 'secondary', icon: Clock, label: 'Pending' },
            responded: { variant: 'default', icon: CheckCircle2, label: 'Responded' },
            contacted: { variant: 'secondary', icon: Clock, label: 'Contacted' },
            converted: { variant: 'default', icon: TrendingUp, label: 'Converted' },
            bounced: { variant: 'destructive', icon: XCircle, label: 'Bounced' },
            completed: { variant: 'secondary', icon: CheckCircle2, label: 'Completed' },
            cancelled: { variant: 'destructive', icon: XCircle, label: 'Cancelled' },
        };

        return configs[status] || configs.contacted;
    };

    return (
        <div className="space-y-4">
            <div className="flex justify-end">
                <Button size="sm" onClick={() => setIsEnrollOpen(true)}>
                    <Plus className="mr-2 h-4 w-4" />
                    Manually Enroll
                </Button>
            </div>

            {campaigns.length === 0 ? (
                <Card>
                    <CardContent className="flex flex-col items-center justify-center py-12">
                        <Target className="h-12 w-12 text-muted-foreground mb-4" />
                        <p className="text-lg font-medium">No campaign interactions</p>
                        <p className="text-sm text-muted-foreground">This customer hasn't been part of any campaigns yet.</p>
                    </CardContent>
                </Card>
            ) : (
                campaigns.map((campaign: any) => {
                    const statusConfig = getStatusConfig(campaign.status);
                    const StatusIcon = statusConfig.icon;

                    return (
                        <Card key={campaign.campaign_id}>
                            <CardHeader>
                                <div className="flex items-start justify-between">
                                    <div className="space-y-1">
                                        <CardTitle className="text-lg flex items-center gap-2">
                                            <Target className="h-5 w-5 text-muted-foreground" />
                                            {campaign.campaign_name}
                                        </CardTitle>
                                        <CardDescription>
                                            Enrolled on {new Date(campaign.enrolled_at || campaign.contacted_at).toLocaleDateString('en-US', {
                                                month: 'long',
                                                day: 'numeric',
                                                year: 'numeric',
                                            })}
                                        </CardDescription>
                                    </div>
                                    <div className="flex gap-2">
                                        <Badge variant={campaign.campaign_status === 'active' ? 'default' : 'outline'} className={campaign.campaign_status === 'active' ? "bg-emerald-600" : "text-muted-foreground"}>
                                            {campaign.campaign_status === 'active' ? 'Campaign Active' : 'Campaign Paused'}
                                        </Badge>
                                        <Badge variant={statusConfig.variant} className="gap-1">
                                            <StatusIcon className="h-3 w-3" />
                                            {statusConfig.label}
                                        </Badge>
                                    </div>
                                </div>
                            </CardHeader>
                            {campaign.current_step && (
                                <CardContent>
                                    <div className="flex items-center gap-2 text-sm">
                                        <span className="font-medium">Current Step:</span>
                                        <span className="text-muted-foreground">Step {campaign.current_step}</span>
                                    </div>
                                    {campaign.next_run_at && (
                                        <div className="flex items-center gap-2 text-sm mt-1">
                                            <span className="font-medium">Next Run:</span>
                                            <span className="text-muted-foreground">{new Date(campaign.next_run_at).toLocaleString()}</span>
                                        </div>
                                    )}
                                </CardContent>
                            )}
                        </Card>
                    );
                })
            )}

            <Dialog open={isEnrollOpen} onOpenChange={setIsEnrollOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Enroll Customer in Campaign</DialogTitle>
                        <DialogDescription>
                            Select an active campaign to start immediately for this customer.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="py-4">
                        <Select value={selectedCampaignId} onValueChange={setSelectedCampaignId}>
                            <SelectTrigger>
                                <SelectValue placeholder="Select campaign..." />
                            </SelectTrigger>
                            <SelectContent>
                                {allCampaigns?.filter((c: any) => c.is_active).map((c: any) => (
                                    <SelectItem key={c.id} value={c.id}>
                                        {c.name}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsEnrollOpen(false)}>Cancel</Button>
                        <Button onClick={handleEnroll} disabled={!selectedCampaignId || isEnrolling}>
                            {isEnrolling ? "Enrolling..." : "Enroll"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
