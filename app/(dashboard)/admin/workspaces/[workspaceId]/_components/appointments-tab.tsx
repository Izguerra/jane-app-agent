'use client';

import { useState } from 'react';
import { formatDateTime } from '@/lib/utils/date';
import useSWR from 'swr';
import { Badge } from '@/components/ui/badge';
import { StatsCard } from '@/components/dashboard/stats-card';
import { FilterBar } from '@/components/dashboard/filter-bar';
import { DataTable, Column } from '@/components/dashboard/data-table';
import { Button } from '@/components/ui/button';
import { Plus, Calendar, Clock, User, CheckCircle } from 'lucide-react';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface Appointment {
    id: number;
    title: string;
    customer_first_name?: string;
    customer_last_name?: string;
    customer_email?: string;
    customer_phone?: string;
    appointment_date: string;
    duration_minutes: number;
    status: string;
    location?: string;
    description?: string;
    notes?: string;
}

export function AppointmentsTab({ workspaceId }: { workspaceId: string }) {
    const [page, setPage] = useState(1);
    const [statusFilter, setStatusFilter] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');

    const query = new URLSearchParams({
        page: page.toString(),
        limit: '20',
        ...(statusFilter !== 'all' && { status: statusFilter }),
    });

    const { data, error, isLoading } = useSWR(
        `/api/workspaces/${workspaceId}/appointments?${query.toString()}`,
        fetcher
    );

    const getStatusBadge = (status: string) => {
        const variants: Record<string, string> = {
            'scheduled': "bg-blue-100 text-blue-700 hover:bg-blue-100",
            'confirmed': "bg-emerald-100 text-emerald-700 hover:bg-emerald-100",
            'completed': "bg-gray-100 text-gray-700 hover:bg-gray-100",
            'cancelled': "bg-rose-100 text-rose-700 hover:bg-rose-100",
            'no_show': "bg-orange-100 text-orange-700 hover:bg-orange-100"
        };
        return <Badge variant="secondary" className={`capitalize ${variants[status] || ''}`}>{status.replace('_', ' ')}</Badge>;
    };

    const columns: Column<Appointment>[] = [
        {
            header: "Customer",
            cell: (item) => (
                <div className="flex items-center gap-3">
                    <div className="bg-primary/10 p-2 rounded-full">
                        <User className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                        <div className="font-medium text-sm">
                            {item.customer_first_name} {item.customer_last_name}
                        </div>
                        <div className="text-xs text-muted-foreground">{item.customer_email || item.customer_phone}</div>
                    </div>
                </div>
            )
        },
        {
            header: "Date & Time",
            cell: (item) => (
                <div className="flex flex-col text-sm">
                    <span className="font-medium">{formatDateTime(item.appointment_date)}</span>
                    <span className="text-xs text-muted-foreground">{item.duration_minutes} mins</span>
                </div>
            )
        },
        {
            header: "Service",
            accessorKey: "title",
            cell: (item) => <Badge variant="outline">{item.title}</Badge>
        },
        {
            header: "Status",
            cell: (item) => getStatusBadge(item.status)
        }
    ];

    return (
        <div className="space-y-6">
            {/* Stats Row */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <StatsCard
                    title="Total Bookings Today"
                    value={data?.total?.toString() || "0"}
                    trend={{ value: 12, direction: 'up' }}
                    icon={Calendar}
                />
                <StatsCard
                    title="Upcoming (7 Days)"
                    value={data?.upcoming_7_days?.toString() || "0"}
                    trend={{ value: 5, direction: 'up' }}
                    icon={Clock}
                />
                <StatsCard
                    title="Completion Rate"
                    value={`${data?.completion_rate || 0}%`}
                    trend={{ value: 0, direction: 'neutral', label: 'vs 86% avg' }}
                    icon={CheckCircle}
                />
            </div>

            {/* Filter & Table */}
            <div className="space-y-4">
                <div className="bg-white p-1 rounded-lg border">
                    <FilterBar
                        className="px-6"
                        searchValue={searchTerm}
                        onSearchChange={setSearchTerm}
                        searchPlaceholder="Search customers..."
                        filters={[
                            {
                                key: 'status',
                                label: 'Status',
                                options: [
                                    { label: 'Confirmed', value: 'confirmed' },
                                    { label: 'Pending', value: 'scheduled' },
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
                    data={data?.items || []}
                    isLoading={isLoading}
                    emptyMessage="No appointments found."
                />
            </div>
        </div>
    );
}
