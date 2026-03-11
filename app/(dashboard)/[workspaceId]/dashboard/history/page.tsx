'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { CallDetailDialog } from '@/components/dashboard/call-detail-dialog';
import { formatDateTime } from '@/lib/utils/date';

// --- Types ---
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

// --- Fetcher ---
const fetcher = (url: string) => fetch(url).then((res) => {
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
});

// Helper to format duration
const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
};

import { useParams } from 'next/navigation';

export default function CallActivityPage() {
    const params = useParams();
    const workspaceId = params.workspaceId as string;
    const [search, setSearch] = useState('');
    const [selectedCall, setSelectedCall] = useState<Communication | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(50);
    const [filters, setFilters] = useState({
        timeRange: '7d',
        type: 'all',
        agent: 'all'
    });

    // Sanitize filters: 'all' should be empty string to avoid filtering on backend
    const typeParam = filters.type === 'all' ? '' : filters.type;
    const agentParam = filters.agent === 'all' ? '' : filters.agent;

    const { data, error, isLoading } = useSWR(
        `/api/communications?search=${search}&timeRange=${filters.timeRange}&type=${typeParam}&agent=${agentParam}&limit=${pageSize}&offset=${(currentPage - 1) * pageSize}&workspaceId=${workspaceId}`,
        fetcher,
        { refreshInterval: 5000 }
    );

    const communications: Communication[] = data?.items || [];

    // Fetch analytics summary for all stats (ensures consistency with Analytics page)
    const { data: analyticsData } = useSWR(`/api/analytics/summary?workspaceId=${workspaceId}`, fetcher);

    // Calculate filtered stats from communications (for the current time range view)
    const callsOnly = communications.filter(c => c.type === 'call');
    const filteredTotalCalls = callsOnly.length;
    const filteredTotalDuration = callsOnly.reduce((sum, call) => sum + (call.duration || 0), 0);
    const filteredAvgDuration = filteredTotalCalls > 0 ? filteredTotalDuration / filteredTotalCalls : 0;
    const outboundCount = callsOnly.filter(c => c.direction === 'outbound').length;

    // Stats from analytics API (these are all-time stats for consistency)
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
            cell: (item) => {
                let label: string = item.type;
                let variant: "default" | "secondary" | "destructive" | "outline" = "outline";
                let icon = null;

                if (item.type === 'call') {
                    if (item.channel === 'video_avatar') {
                        label = 'Avatar Video';
                        variant = "outline"; // Purple style handled via class
                    } else {
                        label = 'Voice Call';
                    }
                } else if (item.type === 'chat') {
                    if (item.channel === 'whatsapp') {
                        label = 'WhatsApp';
                    } else if (item.channel === 'web') {
                        label = 'Chatbot';
                    }
                }

                return (
                    <Badge
                        variant={variant}
                        className={`capitalize whitespace-nowrap ${item.channel === 'video_avatar' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                            item.channel === 'whatsapp' ? 'bg-green-50 text-green-700 border-green-200' : ''
                            }`}
                    >
                        {label}
                    </Badge>
                );
            },
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

        {
            header: '',
            cell: () => (
                <Button variant="ghost" className="h-8 w-8 p-0">
                    <span className="sr-only">Open menu</span>
                    <MoreHorizontal className="h-4 w-4" />
                </Button>
            ),
        },
    ];

    return (
        <div className="flex-1 space-y-6 p-8 pt-6">
            <div className="flex items-center justify-between space-y-2">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Call Activity Dashboard</h2>
                    <p className="text-muted-foreground">
                        Monitor your AI assistant's voice performance across inbound and outbound channels.
                    </p>
                </div>
                <div className="flex items-center space-x-2">
                    <Button variant="outline">Export Data</Button>
                </div>
            </div>

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
                    iconClassName="text-orange-600 bg-orange-100"
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
                        className="px-6" // Add padding to align with table/card
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
                            {
                                key: 'agent',
                                label: 'Agents',
                                options: [
                                    { label: 'Jane (Sales)', value: 'jane' },
                                    { label: 'Support Bot', value: 'support' }
                                ]
                            }
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
                        onRowClick={(item) => setSelectedCall(item)}
                    />

                    {/* Pagination Controls */}
                    <div className="flex items-center justify-between px-6 py-4 border-t">
                        <div className="text-sm text-gray-500">
                            Showing {communications.length} of {data?.total || 0} communications
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                                <span className="text-sm text-gray-500">Rows per page:</span>
                                <select
                                    value={pageSize}
                                    onChange={(e) => {
                                        setPageSize(Number(e.target.value));
                                        setCurrentPage(1);
                                    }}
                                    className="border rounded px-2 py-1 text-sm"
                                >
                                    <option value={25}>25</option>
                                    <option value={50}>50</option>
                                    <option value={100}>100</option>
                                </select>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-sm text-gray-500">
                                    Page {currentPage} of {data?.total_pages || 1}
                                </span>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setCurrentPage(p => p - 1)}
                                    disabled={!data?.has_prev}
                                >
                                    Previous
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setCurrentPage(p => p + 1)}
                                    disabled={!data?.has_next}
                                >
                                    Next
                                </Button>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <CallDetailDialog
                open={!!selectedCall}
                onOpenChange={(open) => !open && setSelectedCall(null)}
                communication={selectedCall}
            />
        </div>
    );
}


