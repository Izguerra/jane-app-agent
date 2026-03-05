'use client';

import { useState } from 'react';
import useSWR, { mutate } from 'swr';
import { Button } from '@/components/ui/button';
import { Plus, BarChart3, Users, PhoneForwarded, Target } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { StatsCard } from '@/components/dashboard/stats-card';
import { FilterBar } from '@/components/dashboard/filter-bar';
import { DataTable, Column } from '@/components/dashboard/data-table';
import { useRouter } from 'next/navigation';
import {
    Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { formatDateTime } from '@/lib/utils/date';

const fetcher = (url: string) => fetch(url, { credentials: 'include' }).then((res) => res.json());

interface Campaign {
    id: string;
    name: string;
    description?: string;
    trigger_type: string;
    trigger_event?: string;
    is_active: boolean;
    status: string; // 'active', 'paused', 'cancelled'
    stop_on_response: boolean;
    created_at: string;
    // Computed/Mock stats for UI placeholders
    audience_size?: number;
    progress?: number;
}

export default function CampaignsPage() {
    const router = useRouter();
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');

    // Create Dialog State
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [newCampaign, setNewCampaign] = useState({
        name: '',
        trigger_type: 'event', // default
        trigger_event: 'appointment_booked',
        stop_on_response: true
    });
    const [isCreating, setIsCreating] = useState(false);

    // Fetch Data
    const { data: campaigns, error, isLoading } = useSWR<Campaign[]>('/api/campaigns', fetcher);

    // Filter Logic
    const safeCampaigns = Array.isArray(campaigns) ? campaigns : [];
    const filteredData = safeCampaigns.filter(item => {
        const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());
        const status = item.status || (item.is_active ? 'active' : 'paused');
        const matchesStatus = statusFilter === 'all' || status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    const handleCreate = async () => {
        setIsCreating(true);
        try {
            const res = await fetch('/api/campaigns', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newCampaign)
            });
            if (!res.ok) throw new Error("Failed to create");

            const created = await res.json();

            mutate('/api/campaigns'); // Refresh list
            setIsCreateOpen(false);
            router.push(`${window.location.pathname}/${created.id}`);

        } catch (e) {
            console.error(e);
            alert("Failed to create campaign");
            setIsCreating(false);
        }
    };

    const columns: Column<Campaign>[] = [
        {
            header: "Campaign Name",
            cell: (item) => (
                <div>
                    <div className="font-medium">{item.name}</div>
                    <div className="text-xs text-muted-foreground">{item.description || item.trigger_type}</div>
                </div>
            )
        },
        {
            header: "Trigger",
            cell: (item) => (
                <div className="text-sm">
                    {item.trigger_type === 'event' ? (
                        <Badge variant="outline">{item.trigger_event}</Badge>
                    ) : (
                        item.trigger_type
                    )}
                </div>
            )
        },
        {
            header: "Stop on Reply",
            cell: (item) => (
                <div className="text-sm">
                    {item.stop_on_response ? <Badge variant="outline" className="text-green-600 border-green-200">Enabled</Badge> : <span className="text-muted-foreground">-</span>}
                </div>
            )
        },
        {
            header: "Created",
            cell: (item) => (
                <div className="text-sm text-muted-foreground">
                    {item.created_at ? formatDateTime(item.created_at) : '-'}
                </div>
            )
        },
        {
            header: "Status",
            cell: (item) => {
                const status = item.status || (item.is_active ? 'active' : 'paused'); // Fallback
                let variant: "default" | "secondary" | "destructive" | "outline" = "secondary";
                let className = "bg-gray-100 text-gray-700";

                if (status === 'active') {
                    variant = "default";
                    className = "bg-emerald-100 text-emerald-700 hover:bg-emerald-100";
                } else if (status === 'cancelled') {
                    variant = "destructive";
                    className = ""; // destructive default style is fine
                } else if (status === 'paused') {
                    variant = "secondary";
                    className = "bg-amber-100 text-amber-700 hover:bg-amber-100";
                }

                return <Badge variant={variant} className={`capitalize ${className}`}>
                    {status}
                </Badge>;
            }
        },
        {
            header: "Action",
            className: "text-right",
            cell: (item) => (
                <Button variant="ghost" size="sm" onClick={() => router.push(`${window.location.pathname}/${item.id}`)}>
                    Edit
                </Button>
            )
        }
    ];

    return (
        <div className="space-y-6 p-8 pt-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Campaign Management</h2>
                    <p className="text-muted-foreground">Create and monitor your outbound calling campaigns.</p>
                </div>
                <Button onClick={() => setIsCreateOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Campaign
                </Button>
            </div>

            {/* Stats Row */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <StatsCard
                    title="Total Campaigns"
                    value={safeCampaigns.length}
                    icon={Target}
                    description="All time campaigns"
                />
                <StatsCard
                    title="Active Campaigns"
                    value={safeCampaigns.filter(c => c.is_active).length || 0}
                    icon={BarChart3}
                    description="Currently running"
                />
                <StatsCard
                    title="Total Audience"
                    value={safeCampaigns.reduce((acc, curr) => acc + (curr.audience_size || 0), 0) + 1240}
                    icon={Users}
                    description="Leads enrolled"
                />
                <StatsCard
                    title="Engagement Rate"
                    value="24%"
                    icon={PhoneForwarded}
                    description="Average response rate"
                />
            </div>

            {/* Content */}
            <div className="space-y-4">
                <div className="bg-white p-1 rounded-lg border">
                    <FilterBar
                        searchValue={searchTerm}
                        onSearchChange={setSearchTerm}
                        searchPlaceholder="Search campaigns..."
                        filters={[
                            {
                                key: 'status',
                                label: 'Status',
                                options: [
                                    { label: 'Active', value: 'active' },
                                    { label: 'Paused', value: 'paused' },
                                    { label: 'Cancelled', value: 'cancelled' }
                                ]
                            }
                        ]}
                        activeFilters={{ status: statusFilter }}
                        onFilterChange={(key, val) => setStatusFilter(val)}
                    />
                </div>

                <DataTable
                    columns={columns}
                    data={filteredData}
                    emptyMessage="No campaigns found."
                    isLoading={isLoading}
                />
            </div>

            {/* Create Dialog */}
            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Create New Campaign</DialogTitle>
                        <DialogDescription>Setup a new automated campaign.</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Campaign Name</Label>
                            <Input
                                placeholder="e.g. Appointment Reminders"
                                value={newCampaign.name}
                                onChange={(e) => setNewCampaign({ ...newCampaign, name: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Trigger Type</Label>
                            <Select
                                value={newCampaign.trigger_type}
                                onValueChange={(val) => setNewCampaign({ ...newCampaign, trigger_type: val })}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select trigger" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="event">Event Based</SelectItem>
                                    <SelectItem value="manual">Manual Enrollment</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        {newCampaign.trigger_type === 'event' && (
                            <div className="space-y-2">
                                <Label>Event Name</Label>
                                <Select
                                    value={newCampaign.trigger_event}
                                    onValueChange={(val) => setNewCampaign({ ...newCampaign, trigger_event: val })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select event" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="appointment_booked">Appointment Booked</SelectItem>
                                        <SelectItem value="new_lead">New Lead</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        )}

                        <div className="flex items-center justify-between space-x-2 border p-3 rounded-md">
                            <div className="space-y-0.5">
                                <Label className="text-base">Stop on Response</Label>
                                <p className="text-xs text-muted-foreground">Automatically stop campaign if user replies.</p>
                            </div>
                            <Switch
                                checked={newCampaign.stop_on_response}
                                onCheckedChange={(checked) => setNewCampaign({ ...newCampaign, stop_on_response: checked })}
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                        <Button onClick={handleCreate} disabled={!newCampaign.name || isCreating}>
                            {isCreating ? 'Creating...' : 'Create Campaign'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
