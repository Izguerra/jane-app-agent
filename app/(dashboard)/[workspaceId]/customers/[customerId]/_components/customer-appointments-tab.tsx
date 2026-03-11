'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    Calendar,
    Clock,
    CheckCircle2,
    XCircle,
    ChevronRight,
} from 'lucide-react';
import { formatDateTime } from '@/lib/utils/date';
import { DataTable, Column } from '@/components/dashboard/data-table';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog";

const fetcher = (url: string) => fetch(url).then((res) => {
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
});

interface Appointment {
    id: string;
    title: string;
    appointment_date: string;
    duration_minutes: number;
    status: string;
    customer_first_name?: string;
    customer_last_name?: string;
    customer_email?: string;
    customer_phone?: string;
}

interface CustomerAppointmentsTabProps {
    customerId: string;
    workspaceId?: string;
}

export function CustomerAppointmentsTab({ customerId, workspaceId }: CustomerAppointmentsTabProps) {
    const [page, setPage] = useState(1);
    const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);

    const { data, error, isLoading, mutate } = useSWR(
        `/api/appointments?customer_id=${customerId}&page=${page}&limit=25`,
        fetcher
    );

    const appointments: Appointment[] = data?.items || data || [];

    const handleCancel = async (appointmentId: string) => {
        if (!confirm("Are you sure you want to cancel this appointment?")) return;

        try {
            const res = await fetch(`/api/appointments/${appointmentId}`, {
                method: 'DELETE',
            });

            if (res.ok) {
                mutate(); // Refresh list
                setSelectedAppointment(null);
            } else {
                alert("Failed to cancel appointment");
            }
        } catch (e) {
            console.error(e);
            alert("Error cancelling appointment");
        }
    };

    const columns: Column<Appointment>[] = [
        {
            accessorKey: 'title',
            header: 'Title',
            cell: (item) => (
                <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-blue-500" />
                    <span className="font-medium">{item.title}</span>
                </div>
            ),
        },
        {
            accessorKey: 'appointment_date',
            header: 'Date & Time',
            cell: (item) => (
                <span className="text-sm text-gray-600">
                    {item.appointment_date ? formatDateTime(item.appointment_date) : 'N/A'}
                </span>
            ),
        },
        {
            accessorKey: 'duration_minutes',
            header: 'Duration',
            cell: (item) => (
                <div className="flex items-center gap-1 text-gray-600">
                    <Clock className="h-3 w-3" />
                    {item.duration_minutes} min
                </div>
            ),
        },
        {
            accessorKey: 'status',
            header: 'Status',
            cell: (item) => {
                const statusColors: Record<string, string> = {
                    confirmed: 'bg-green-100 text-green-700',
                    pending: 'bg-yellow-100 text-yellow-700',
                    cancelled: 'bg-red-100 text-red-700',
                    completed: 'bg-blue-100 text-blue-700',
                };
                return (
                    <Badge className={statusColors[item.status] || 'bg-gray-100 text-gray-700'}>
                        {item.status}
                    </Badge>
                );
            },
        },
        {
            header: '',
            cell: (appointment) => (
                <Button
                    variant="ghost"
                    className="h-8 w-8 p-0"
                    onClick={() => setSelectedAppointment(appointment)}
                >
                    <span className="sr-only">View Details</span>
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                </Button>
            ),
        },
    ];

    if (error) {
        return (
            <Card className="border-0 shadow-none">
                <CardContent className="p-6 text-center text-gray-500">
                    Failed to load appointments.
                </CardContent>
            </Card>
        );
    }

    return (
        <>
            <Card className="border-0 shadow-none">
                <CardContent className="p-0">
                    <DataTable
                        columns={columns}
                        data={appointments}
                        isLoading={isLoading}
                    />
                </CardContent>
            </Card>

            <Dialog open={!!selectedAppointment} onOpenChange={(open) => !open && setSelectedAppointment(null)}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle>Appointment Details</DialogTitle>
                    </DialogHeader>
                    {selectedAppointment && (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div className="col-span-2">
                                    <h3 className="font-semibold text-lg">{selectedAppointment.title}</h3>
                                </div>
                                <div>
                                    <label className="text-muted-foreground block text-xs uppercase font-bold">Date & Time</label>
                                    <div className="font-medium mt-1">{formatDateTime(selectedAppointment.appointment_date)}</div>
                                </div>
                                <div>
                                    <label className="text-muted-foreground block text-xs uppercase font-bold">Duration</label>
                                    <div className="font-medium mt-1">{selectedAppointment.duration_minutes} mins</div>
                                </div>
                                <div>
                                    <label className="text-muted-foreground block text-xs uppercase font-bold">Status</label>
                                    <div className="mt-1 capitalize">{selectedAppointment.status}</div>
                                </div>
                                <div className="col-span-2">
                                    <label className="text-muted-foreground block text-xs uppercase font-bold">Customer Info</label>
                                    <div className="mt-1">
                                        {selectedAppointment.customer_first_name} {selectedAppointment.customer_last_name}
                                        <div className="text-xs text-gray-500">{selectedAppointment.customer_email}</div>
                                        <div className="text-xs text-gray-500">{selectedAppointment.customer_phone}</div>
                                    </div>
                                </div>
                            </div>

                            <DialogFooter className="gap-2 sm:gap-0">
                                <Button
                                    variant="destructive"
                                    onClick={() => handleCancel(selectedAppointment.id)}
                                    disabled={selectedAppointment.status === 'cancelled'}
                                >
                                    Cancel Appointment
                                </Button>
                                <Button variant="outline" onClick={() => setSelectedAppointment(null)}>
                                    Close
                                </Button>
                            </DialogFooter>
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </>
    );
}
