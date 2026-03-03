'use client';

import { use } from 'react';
import { useState } from 'react';
import useSWR from 'swr';
import { useParams, useRouter } from 'next/navigation';
import { CustomerProfileCard } from '../customer-profile-card';
import { CustomerAnalyticsCard } from '../customer-analytics-card';
import { EditCustomerDialog } from '../edit-customer-dialog';
import { CustomerTabs } from './customer-tabs';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';

const fetcher = (url: string) => fetch(url, { credentials: 'include' }).then((res) => res.json());

export default function CustomerDetailPage() {
    const params = useParams();
    const router = useRouter();
    const workspaceId = params?.workspaceId as string;
    const customerId = params?.customerId as string;
    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [commsPage, setCommsPage] = useState(1);

    const { data: customer, error: customerError, isLoading: customerLoading } = useSWR(
        `/api/customers/${customerId}`,
        fetcher
    );

    // Debug logging
    console.log('Customer detail page - customerId:', customerId);
    console.log('Customer detail page - customer data:', customer);
    console.log('Customer detail page - error:', customerError);

    const { data: commsData, error: commsError, isLoading: commsLoading, mutate: mutateComms } = useSWR(
        `/api/customers/${customerId}/communications?page=${commsPage}&limit=25`,
        fetcher
    );

    const handleEdit = () => {
        setEditDialogOpen(true);
    };

    const handleDelete = async () => {
        if (!confirm('Are you sure you want to delete this customer? This action cannot be undone.')) return;

        try {
            const res = await fetch(`/api/customers/${customerId}`, {
                method: 'DELETE',
                credentials: 'include',
            });

            if (!res.ok) throw new Error('Failed to delete customer');

            toast.success('Customer deleted successfully');
            router.push(`/${workspaceId}/customers`);
        } catch (error) {
            toast.error('Failed to delete customer');
        }
    };

    const handlePageChange = (newPage: number) => {
        setCommsPage(newPage);
        mutateComms();
    };

    if (customerLoading) {
        return (
            <div className="space-y-6">
                <div className="flex items-center space-x-4">
                    <Skeleton className="h-10 w-10" />
                    <Skeleton className="h-8 w-64" />
                </div>
                <div className="grid gap-6 lg:grid-cols-[1fr_400px]">
                    <Skeleton className="h-[400px]" />
                    <Skeleton className="h-[400px]" />
                </div>
                <Skeleton className="h-[500px] w-full" />
            </div>
        );
    }

    if (customerError || !customer) {
        return (
            <div className="flex flex-col items-center justify-center h-[400px] space-y-4">
                <p className="text-lg text-muted-foreground">Customer not found</p>
                <Button onClick={() => router.push(`/${workspaceId}/customers`)}>
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Customers
                </Button>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center space-x-4">
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => router.push(`/${workspaceId}/customers`)}
                >
                    <ArrowLeft className="h-4 w-4" />
                </Button>
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">
                        {customer.first_name} {customer.last_name}
                    </h2>
                    <p className="text-muted-foreground">Customer Details</p>
                </div>
            </div>

            {/* Analytics and Profile - 2 Column Grid */}
            <div className="grid gap-6 lg:grid-cols-[6fr_4fr]">
                {/* Analytics - Left */}
                <CustomerAnalyticsCard customerId={customerId} />

                {/* Profile - Right Sidebar */}
                <CustomerProfileCard
                    customer={customer}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                />
            </div>

            {/* Tabbed Interface - Full Width */}
            <CustomerTabs customerId={customerId} workspaceId={workspaceId} />

            {/* Edit Dialog */}
            {customer && (
                <EditCustomerDialog
                    customer={customer}
                    open={editDialogOpen}
                    onOpenChange={setEditDialogOpen}
                />
            )}
        </div>
    );
}
