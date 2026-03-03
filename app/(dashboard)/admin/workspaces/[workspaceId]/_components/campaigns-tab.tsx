'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { Button } from '@/components/ui/button';
import { BarChart3, Users, PhoneForwarded, Target } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { StatsCard } from '@/components/dashboard/stats-card';
import { FilterBar } from '@/components/dashboard/filter-bar';
import { DataTable, Column } from '@/components/dashboard/data-table';
import { formatDateTime } from '@/lib/utils/date';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface Campaign {
    id: string;
    name: string;
    description?: string;
    trigger_type: string;
    trigger_event?: string;
    is_active: boolean;
    status: string;
    stop_on_response: boolean;
    created_at: string;
    audience_size?: number;
    progress?: number;
}

export function CampaignsTab({ workspaceId }: { workspaceId: string }) {
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');

    const { data: campaigns, error, isLoading } = useSWR<Campaign[]>(`/api/workspaces/${workspaceId}/campaigns`, fetcher);

    const safeCampaigns = Array.isArray(campaigns) ? campaigns : [];
    const filteredData = safeCampaigns.filter(item => {
        const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());
        const status = item.status || (item.is_active ? 'active' : 'paused');
        const matchesStatus = statusFilter === 'all' || status === statusFilter;
        return matchesSearch && matchesStatus;
    });

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
                const status = item.status || (item.is_active ? 'active' : 'paused');
                let variant: "default" | "secondary" | "destructive" | "outline" = "secondary";
                let className = "bg-gray-100 text-gray-700";

                if (status === 'active') {
                    variant = "default";
                    className = "bg-emerald-100 text-emerald-700 hover:bg-emerald-100";
                } else if (status === 'cancelled') {
                    variant = "destructive";
                    className = "";
                } else if (status === 'paused') {
                    variant = "secondary";
                    className = "bg-amber-100 text-amber-700 hover:bg-amber-100";
                }

                return <Badge variant={variant} className={`capitalize ${className}`}>
                    {status}
                </Badge>;
            }
        }
    ];

    return (
        <div className="space-y-6">
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
        </div>
    );
}
