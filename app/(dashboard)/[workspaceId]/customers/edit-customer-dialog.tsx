'use client';

import { useState } from 'react';
import { useSWRConfig } from 'swr';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';

interface Customer {
    id: string;
    first_name: string;
    last_name: string;
    email: string;
    phone: string;
    plan: string;
    status: string;
    customer_type?: string;
    lifecycle_stage?: string;
    crm_status?: string;
    company_name?: string;
}

interface EditCustomerDialogProps {
    customer: Customer;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function EditCustomerDialog({ customer, open, onOpenChange }: EditCustomerDialogProps) {
    const [loading, setLoading] = useState(false);
    const { mutate } = useSWRConfig();

    async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setLoading(true);

        const formData = new FormData(e.currentTarget);
        const data = {
            first_name: formData.get('first_name'),
            last_name: formData.get('last_name'),
            email: formData.get('email'),
            phone: formData.get('phone'),
            company_name: formData.get('company_name'),
            status: formData.get('status'),
            customer_type: formData.get('customer_type'),
            lifecycle_stage: formData.get('lifecycle_stage'),
            crm_status: formData.get('crm_status'),
        };

        try {
            const res = await fetch(`/api/customers/${customer.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
                credentials: 'include',
            });

            if (!res.ok) throw new Error('Failed to update customer');

            toast.success('Customer updated successfully');
            mutate(`/api/customers/${customer.id}`);
            mutate((key: string) => typeof key === 'string' && key.startsWith('/api/customers'));
            onOpenChange(false);
        } catch (error) {
            toast.error('Failed to update customer');
        } finally {
            setLoading(false);
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <form onSubmit={onSubmit}>
                    <DialogHeader>
                        <DialogTitle>Edit Customer</DialogTitle>
                        <DialogDescription>
                            Update customer information.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                            <Label htmlFor="company_name">Company Name</Label>
                            <Input
                                id="company_name"
                                name="company_name"
                                defaultValue={customer.company_name}
                                placeholder="Acme Corp"
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="grid gap-2">
                                <Label htmlFor="first_name">First Name</Label>
                                <Input
                                    id="first_name"
                                    name="first_name"
                                    defaultValue={customer.first_name}
                                    required
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="last_name">Last Name</Label>
                                <Input
                                    id="last_name"
                                    name="last_name"
                                    defaultValue={customer.last_name}
                                    required
                                />
                            </div>
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="email">Email</Label>
                            <Input
                                id="email"
                                name="email"
                                type="email"
                                defaultValue={customer.email}
                                required
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="phone">Phone</Label>
                            <Input
                                id="phone"
                                name="phone"
                                defaultValue={customer.phone}
                                placeholder="+1..."
                            />
                        </div>
                        {/* CRM Fields */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="grid gap-2">
                                <Label htmlFor="customer_type">Type</Label>
                                <Select name="customer_type" defaultValue={customer.customer_type?.toLowerCase()}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select type" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="b2b">B2B</SelectItem>
                                        <SelectItem value="b2c">B2C</SelectItem>
                                        <SelectItem value="partner">Partner</SelectItem>
                                        <SelectItem value="wholesale">Wholesale</SelectItem>
                                        <SelectItem value="vip">VIP</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="lifecycle_stage">Lifecycle Stage</Label>
                                <Select name="lifecycle_stage" defaultValue={customer.lifecycle_stage?.toLowerCase()}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select stage" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="subscriber">Subscriber</SelectItem>
                                        <SelectItem value="lead">Lead</SelectItem>
                                        <SelectItem value="mql">MQL</SelectItem>
                                        <SelectItem value="sql">SQL</SelectItem>
                                        <SelectItem value="opportunity">Opportunity</SelectItem>
                                        <SelectItem value="customer">Customer</SelectItem>
                                        <SelectItem value="evangelist">Evangelist</SelectItem>
                                        <SelectItem value="other">Other</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        <div className="grid gap-2">
                            <Label htmlFor="crm_status">CRM Status</Label>
                            <Select name="crm_status" defaultValue={customer.crm_status?.toLowerCase()}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select status" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="new">New/Raw</SelectItem>
                                    <SelectItem value="attempted_contact">Attempted to Contact</SelectItem>
                                    <SelectItem value="working">Working/Contacted</SelectItem>
                                    <SelectItem value="nurture">Nurture</SelectItem>
                                    <SelectItem value="bad_fit">Bad Fit</SelectItem>
                                    <SelectItem value="disqualified">Disqualified</SelectItem>
                                    <SelectItem value="active">Active</SelectItem>
                                    <SelectItem value="onboarding">Onboarding</SelectItem>
                                    <SelectItem value="at_risk">At Risk</SelectItem>
                                    <SelectItem value="churned">Churned</SelectItem>
                                    <SelectItem value="lapsed">Lapsed</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="grid gap-2">
                            <Label htmlFor="status">Account Status</Label>
                            <Select name="status" defaultValue={customer.status}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="active">Active</SelectItem>
                                    <SelectItem value="trialing">Trialing</SelectItem>
                                    <SelectItem value="past_due">Past Due</SelectItem>
                                    <SelectItem value="churned">Churned</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div >
                    <DialogFooter>
                        <Button type="submit" disabled={loading}>
                            {loading ? 'Updating...' : 'Update Customer'}
                        </Button>
                    </DialogFooter>
                </form >
            </DialogContent >
        </Dialog >
    );
}
