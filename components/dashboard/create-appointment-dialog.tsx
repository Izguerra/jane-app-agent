"use client";

import { useState } from 'react';
import useSWR from 'swr';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';

interface CreateAppointmentDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

interface Customer {
    id: string;
    first_name: string;
    last_name: string;
    email: string;
    phone: string;
}

interface CustomersResponse {
    items: Customer[];
    total: number;
}

const fetcher = async (url: string) => {
    const res = await fetch(url + '?limit=100'); // Fetch more customers for the dropdown
    if (!res.ok) throw new Error('Failed to fetch data');
    return res.json();
};

export function CreateAppointmentDialog({ open, onOpenChange, onSuccess }: CreateAppointmentDialogProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [formData, setFormData] = useState({
        title: '',
        customer_id: '',
        date: '',
        time: '',
        duration: '60',
        notes: ''
    });

    const { data: customersData, error } = useSWR<CustomersResponse>('/api/customers', fetcher);
    const customers = customersData?.items || [];

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);

        if (!formData.customer_id) {
            toast.error("Please select a customer");
            return;
        }

        try {
            const [year, month, day] = formData.date.split('-').map(Number);
            const [hours, minutes] = formData.time.split(':').map(Number);

            const appointmentDate = new Date();
            appointmentDate.setFullYear(year, month - 1, day);
            appointmentDate.setHours(hours, minutes, 0, 0);

            const response = await fetch('/api/appointments', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: formData.title,
                    customer_id: formData.customer_id,
                    appointment_date: appointmentDate.toISOString(),
                    duration_minutes: parseInt(formData.duration),
                    notes: formData.notes,
                    status: 'confirmed'
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.detail || 'Failed to create appointment';
                toast.error(errorMessage);
                throw new Error("HANDLED");
            }

            toast.success('Appointment created successfully');
            onSuccess();
            onOpenChange(false);
            setFormData({
                title: '',
                customer_id: '',
                date: '',
                time: '',
                duration: '60',
                notes: ''
            });
        } catch (error) {
            console.error('Error creating appointment:', error);
            if (error instanceof Error && error.message === "HANDLED") return;
            toast.error('Failed to create appointment');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-md">
                <DialogHeader>
                    <DialogTitle>Add Manual Appointment</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="title">Title/Service</Label>
                        <Input
                            id="title"
                            placeholder="e.g. Consultation, Tattoo Session"
                            required
                            value={formData.title}
                            onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="customer">Customer</Label>
                        <Select
                            value={formData.customer_id}
                            onValueChange={(val) => setFormData(prev => ({ ...prev, customer_id: val }))}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Select a customer" />
                            </SelectTrigger>
                            <SelectContent className="max-h-[200px]">
                                {customers.map((customer) => (
                                    <SelectItem key={customer.id} value={customer.id}>
                                        {customer.first_name} {customer.last_name} ({customer.email || customer.phone})
                                    </SelectItem>
                                ))}
                                {customers.length === 0 && (
                                    <div className="p-2 text-sm text-muted-foreground text-center">
                                        No customers found. Add a customer first.
                                    </div>
                                )}
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="date">Date</Label>
                            <Input
                                id="date"
                                type="date"
                                required
                                value={formData.date}
                                onChange={(e) => setFormData(prev => ({ ...prev, date: e.target.value }))}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="time">Time</Label>
                            <Input
                                id="time"
                                type="time"
                                required
                                value={formData.time}
                                onChange={(e) => setFormData(prev => ({ ...prev, time: e.target.value }))}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="duration">Duration (minutes)</Label>
                        <Select
                            value={formData.duration}
                            onValueChange={(val) => setFormData(prev => ({ ...prev, duration: val }))}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Select duration" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="15">15 mins</SelectItem>
                                <SelectItem value="30">30 mins</SelectItem>
                                <SelectItem value="45">45 mins</SelectItem>
                                <SelectItem value="60">1 hour</SelectItem>
                                <SelectItem value="90">1.5 hours</SelectItem>
                                <SelectItem value="120">2 hours</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="notes">Notes</Label>
                        <Textarea
                            id="notes"
                            value={formData.notes}
                            onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                        />
                    </div>

                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={isLoading}>
                            {isLoading ? 'Creating...' : 'Create Appointment'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
