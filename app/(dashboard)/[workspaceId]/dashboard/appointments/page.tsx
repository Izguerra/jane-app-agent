'use client';

import { useState } from 'react';
import { formatDateTime } from '@/lib/utils/date';
import useSWR from 'swr';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Plus, Calendar, Clock, MapPin, User, CheckCircle, AlertCircle, Trash2, Edit } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useParams } from 'next/navigation';
import { StatsCard } from '@/components/dashboard/stats-card';
import { FilterBar } from '@/components/dashboard/filter-bar';
import { DataTable, Column } from '@/components/dashboard/data-table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { CreateAppointmentDialog } from '@/components/dashboard/create-appointment-dialog';

const fetcher = (url: string) => fetch(url, { credentials: 'include' }).then((res) => res.json());

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

export default function AppointmentsPage() {
    const params = useParams();
    const [page, setPage] = useState(1);
    const [statusFilter, setStatusFilter] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm] = useState<any>({});
    const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

    // Fetch data
    const query = new URLSearchParams({
        page: page.toString(),
        limit: '20',
        ...(statusFilter !== 'all' && { status: statusFilter }),
    });

    const { data, error, isLoading, mutate } = useSWR(
        `/api/appointments?${query.toString()}`,
        fetcher
    );

    // Stats (Mocked or derived)
    const totalBookings = data?.total || 0;

    const getStatusBadge = (status: string) => {
        const variants: Record<string, string> = {
            'scheduled': "bg-blue-100 text-blue-700 hover:bg-blue-100",
            'confirmed': "bg-emerald-100 text-emerald-700 hover:bg-emerald-100",
            'completed': "bg-gray-100 text-gray-700 hover:bg-gray-100",
            'cancelled': "bg-rose-100 text-rose-700 hover:bg-rose-100",
            'no_show': "bg-blue-100 text-blue-700 hover:bg-blue-100"
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
        },
        {
            header: "Action",
            className: "text-right",
            cell: (item) => (
                <Button variant="ghost" size="sm" onClick={(e) => {
                    e.stopPropagation();
                    setSelectedAppointment(item);
                }}>
                    View
                </Button>
            )
        }
    ];

    return (
        <div className="space-y-6 p-8 pt-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Appointment Booked Overview</h2>
                    <p className="text-muted-foreground">Manage and track all appointments scheduled by your AI agents.</p>
                </div>
                <Button onClick={() => setIsCreateDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Manual Appointment
                </Button>
            </div>

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
                                    { label: 'Pending', value: 'scheduled' }, // Mapping 'scheduled' to 'Pending' per UI
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
                    onRowClick={(item) => setSelectedAppointment(item)}
                    emptyMessage="No appointments found."
                />
            </div>

            {/* Edit/View Modal */}
            <Dialog open={!!selectedAppointment} onOpenChange={(open) => !open && setSelectedAppointment(null)}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle>{isEditing ? 'Edit Appointment' : selectedAppointment?.title}</DialogTitle>
                    </DialogHeader>
                    {selectedAppointment && (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <label className="text-muted-foreground">Customer</label>
                                    <div className="font-medium">{selectedAppointment.customer_first_name} {selectedAppointment.customer_last_name}</div>
                                    <div className="text-muted-foreground">{selectedAppointment.customer_phone}</div>
                                </div>
                                <div>
                                    <label className="text-muted-foreground">Date</label>
                                    <div className="font-medium">{formatDateTime(selectedAppointment.appointment_date)}</div>
                                </div>
                                <div>
                                    <label className="text-muted-foreground">Status</label>
                                    <div>{getStatusBadge(selectedAppointment.status)}</div>
                                </div>
                                <div>
                                    <label className="text-muted-foreground">Location</label>
                                    <div>{selectedAppointment.location || 'N/A'}</div>
                                </div>
                                <div className="col-span-2">
                                    <label className="text-muted-foreground">Notes</label>
                                    <p className="mt-1">{selectedAppointment.notes || 'No notes.'}</p>
                                </div>
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => setSelectedAppointment(null)}>Close</Button>
                            </DialogFooter>
                        </div>
                    )}
                </DialogContent>
            </Dialog>

            {/* Create Appointment Dialog */}
            <CreateAppointmentDialog
                open={isCreateDialogOpen}
                onOpenChange={setIsCreateDialogOpen}
                onSuccess={() => mutate()}
            />
        </div >
    );
}
