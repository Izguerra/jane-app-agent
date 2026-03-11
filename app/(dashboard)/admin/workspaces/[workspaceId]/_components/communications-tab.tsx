'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    Phone,
    ArrowUpRight,
    ArrowDownLeft,
    Clock,
    CheckCircle2,
    XCircle,
    MoreHorizontal,
    PhoneCall,
    Timer,
    Activity,
    Target,
    MessageSquare,
    Bot
} from 'lucide-react';
import { StatsCard } from '@/components/dashboard/stats-card';
import { FilterBar } from '@/components/dashboard/filter-bar';
import { DataTable, Column } from '@/components/dashboard/data-table';
import { formatDateTime } from '@/lib/utils/date';

const fetcher = (url: string) => fetch(url).then((res) => {
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
});

const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
};

interface Communication {
    id: number;
    type: 'call' | 'chat';
    channel?: string;
    direction: string;
    status: string;
    duration: number;
    transcript?: string;
    summary?: string;
    sentiment?: string;
    started_at: string;
    user_identifier?: string;
    call_intent?: string;
    call_outcome?: string;
}

export function CommunicationsTab({ workspaceId }: { workspaceId: string }) {
    const [search, setSearch] = useState('');
    const [filters, setFilters] = useState({
        timeRange: '7d',
        type: 'all',
        agent: 'all'
    });

    const typeParam = filters.type === 'all' ? '' : filters.type;
    const agentParam = filters.agent === 'all' ? '' : filters.agent;

    const { data, error, isLoading } = useSWR(
        `/api/workspaces/${workspaceId}/communications?search=${search}&timeRange=${filters.timeRange}&type=${typeParam}&agent=${agentParam}`,
        fetcher
    );

    // Fetch analytics summary
    const { data: analyticsData } = useSWR(`/api/workspaces/${workspaceId}/analytics/summary`, fetcher);

    const communications: Communication[] = data?.items || [];

    // Filtered stats (client-side approximation from filtered table data)
    const callsOnly = communications.filter(c => c.type === 'call');
    const filteredTotalCalls = callsOnly.length;
    const filteredTotalDuration = callsOnly.reduce((sum, call) => sum + (call.duration || 0), 0);
    const filteredAvgDuration = filteredTotalCalls > 0 ? filteredTotalDuration / filteredTotalCalls : 0;
    const outboundCount = callsOnly.filter(c => c.direction === 'outbound').length;

    // Global Stats from API
    const totalCalls = analyticsData?.total_conversations || 0;
    const totalMinutes = analyticsData?.total_minutes || 0;
    const totalMessages = analyticsData?.total_messages || 0;
    const totalAgents = analyticsData?.total_agents || 0;
    const minutesLimit = analyticsData?.minutes_limit || 100;
    const agentsLimit = analyticsData?.agents_limit || 1;
    const conversationsLimit = analyticsData?.conversations_limit || 1000;
    const successfulConversations = analyticsData?.successful_conversations || 0;
    const successRate = totalCalls > 0 ? ((successfulConversations / totalCalls) * 100).toFixed(1) : '0.0';

    const columns: Column<Communication>[] = [
        {
            accessorKey: 'type',
            header: 'Type',
            cell: (item) => (
                <Badge variant="outline" className="capitalize">
                    {item.type}
                </Badge>
            ),
        },
        {
            accessorKey: 'direction',
            header: 'Direction',
            cell: (item) => (
                <div className="flex items-center gap-1">
                    {item.direction === 'inbound' ? (
                        <ArrowDownLeft className="h-3 w-3 text-green-500" />
                    ) : (
                        <ArrowUpRight className="h-3 w-3 text-red-500" />
                    )}
                    <span className="capitalize">{item.direction}</span>
                </div>
            ),
        },
        {
            accessorKey: 'user_identifier',
            header: 'User',
            cell: (item) => (
                <div className="font-medium text-gray-900">
                    {item.user_identifier || 'N/A'}
                </div>
            ),
        },
        {
            accessorKey: 'duration',
            header: 'Duration',
            cell: (item) => (
                <div className="flex items-center gap-1 text-gray-600">
                    <Clock className="h-3 w-3" />
                    {formatDuration(item.duration)}
                </div>
            ),
        },
        {
            accessorKey: 'status',
            header: 'Status',
            cell: (item) => (
                <div className="flex items-center gap-1">
                    {item.status === 'completed' ? (
                        <CheckCircle2 className="h-3 w-3 text-green-500" />
                    ) : (
                        <XCircle className="h-3 w-3 text-red-500" />
                    )}
                    <span className="capitalize">{item.status}</span>
                </div>
            ),
        },
        {
            accessorKey: 'call_intent',
            header: 'Intent',
            cell: (item) => (
                <Badge variant="secondary" className="capitalize">
                    {item.call_intent || 'N/A'}
                </Badge>
            ),
        },
        {
            accessorKey: 'call_outcome',
            header: 'Outcome',
            cell: (item) => (
                <Badge variant="secondary" className="capitalize">
                    {item.call_outcome || 'N/A'}
                </Badge>
            ),
        },
        {
            accessorKey: 'started_at',
            header: <div className="text-right font-medium">Time</div>,
            className: 'w-[140px]',
            cell: (item) => (
                <div className="text-right">
                    <span className="text-sm text-gray-500 whitespace-nowrap">
                        {item.started_at ? formatDateTime(item.started_at) : 'N/A'}
                    </span>
                </div>
            ),
        },
    ];

    return (
        <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <StatsCard
                    title="Total Calls"
                    value={`${totalCalls.toLocaleString()}/${conversationsLimit.toLocaleString()}`}
                    icon={PhoneCall}
                    trend={{ value: 5, direction: 'up', label: 'vs last 30 days' }}
                />
                <StatsCard
                    title="Total Minutes"
                    value={`${totalMinutes.toLocaleString()}/${minutesLimit}`}
                    icon={Timer}
                    trend={{ value: 2, direction: 'up', label: 'Voice usage' }}
                    iconClassName="text-purple-600 bg-purple-100"
                />
                <StatsCard
                    title="Total Messages"
                    value={totalMessages.toLocaleString()}
                    icon={MessageSquare}
                    trend={{ value: 3, direction: 'up', label: 'Chat messages' }}
                    iconClassName="text-indigo-600 bg-indigo-100"
                />
                <StatsCard
                    title="Agents"
                    value={`${totalAgents}/${agentsLimit}`}
                    icon={Bot}
                    iconClassName="text-gray-600 bg-gray-100"
                />
                <StatsCard
                    title="Avg. Handle Time"
                    value={formatDuration(filteredAvgDuration)}
                    icon={Clock}
                    trend={{ value: 1.2, direction: 'down', label: 'vs last 30 days' }}
                    iconClassName="text-blue-600 bg-blue-100"
                />
                <StatsCard
                    title="Outbound Reach"
                    value={outboundCount.toLocaleString()}
                    icon={Activity}
                    trend={{ value: 2, direction: 'down', label: 'Unique customers' }}
                    iconClassName="text-blue-600 bg-blue-100"
                />
                <StatsCard
                    title="Success Rate"
                    value={`${successRate}%`}
                    icon={Target}
                    trend={{ value: successfulConversations, direction: 'up', label: `${successfulConversations} successful calls` }}
                    iconClassName="text-emerald-600 bg-emerald-100"
                />
            </div>

            {/* Main Content */}
            <Card>
                <CardHeader className="p-0 border-b">
                    <FilterBar
                        className="px-6"
                        searchPlaceholder="Search calls, numbers..."
                        searchValue={search}
                        onSearchChange={setSearch}
                        filters={[
                            {
                                key: 'timeRange',
                                label: 'Time Range',
                                options: [
                                    { label: 'Last 24 Hours', value: '24h' },
                                    { label: 'Last 7 Days', value: '7d' },
                                    { label: 'Last 30 Days', value: '30d' }
                                ]
                            },
                            {
                                key: 'type',
                                label: 'Call Type',
                                options: [
                                    { label: 'Inbound', value: 'inbound' },
                                    { label: 'Outbound', value: 'outbound' }
                                ]
                            },
                        ]}
                        activeFilters={filters}
                        onFilterChange={(key, val) => setFilters(prev => ({ ...prev, [key]: val }))}
                    />
                </CardHeader>
                <CardContent className="p-0">
                    <DataTable
                        columns={columns}
                        data={communications || []}
                        isLoading={isLoading}
                        emptyMessage="No communications found."
                    />
                </CardContent>
            </Card>
        </div>
    );
}
