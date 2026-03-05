'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import useSWR, { mutate } from 'swr';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
    ArrowLeft,
    Download,
    DollarSign,
    Users,
    AlertCircle,
    TrendingUp,
    Search,
    Filter
} from 'lucide-react';
import Link from 'next/link';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface Invoice {
    id: string;
    invoice_number: string;
    customer_name: string;
    plan: string;
    date: string;
    amount: number;
    status: 'paid' | 'pending' | 'failed' | 'refunded';
    invoice_pdf?: string | null;
    hosted_invoice_url?: string | null;
}

interface BillingStats {
    total_revenue: number;
    revenue_change: number;
    active_subscribers: number;
    subscriber_change: number;
    pending_amount: number;
    pending_count: number;
    failed_payments: number;
}

export default function PaymentHistoryPage() {
    const params = useParams();
    const router = useRouter();
    const workspaceId = params?.workspaceId as string;

    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [timeRange, setTimeRange] = useState('30');

    // Fetch billing stats from API
    const { data: statsData, isLoading: statsLoading } = useSWR<BillingStats>(
        `/api/workspaces/${workspaceId}/billing/stats?time_range=${timeRange}`,
        fetcher
    );

    // Fetch invoices from API
    const { data: invoicesData, isLoading: invoicesLoading } = useSWR<{ invoices: Invoice[]; total: number; has_more: boolean }>(
        `/api/workspaces/${workspaceId}/billing/invoices?status=${statusFilter}`,
        fetcher
    );

    const stats: BillingStats = statsData || {
        total_revenue: 0,
        revenue_change: 0,
        active_subscribers: 0,
        subscriber_change: 0,
        pending_amount: 0,
        pending_count: 0,
        failed_payments: 0,
    };

    const invoices = invoicesData?.invoices || [];

    if (statsLoading || invoicesLoading) {
        return (
            <div className="p-8">
                <div className="text-muted-foreground">Loading workspace billing data...</div>
            </div>
        );
    }

    const handleRetryPayment = async (invoiceId: string) => {
        try {
            // Note: Retrying often remains global or needs specific endpoint. 
            // For now assuming existing global retry or needing update. 
            // Let's assume global admin billing retry is fine or update if needed. 
            // Actually, best to use the same pattern.
            // But we didn't add POST to the new route. 
            // Let's stick to global for retry for now as it takes invoice ID, 
            // OR update it. The implementation plan didn't specify retry update, 
            // but for consistency we should probably use the old one or add POST.
            // Let's use the old one for ACTIONs for now as it's safe.
            const response = await fetch(`/api/billing/admin?action=retry&invoice_id=${invoiceId}`, {
                method: 'POST',
            });

            if (response.ok) {
                toast.success('Payment retry initiated');
                mutate(`/api/workspaces/${workspaceId}/billing?type=invoices&status=${statusFilter}`);
            } else {
                toast.error('Failed to retry payment');
            }
        } catch (error) {
            toast.error('An error occurred');
        }
    };

    const handleDownloadInvoice = (invoice: Invoice) => {
        if (invoice.invoice_pdf) {
            window.open(invoice.invoice_pdf, '_blank');
        } else if (invoice.hosted_invoice_url) {
            window.open(invoice.hosted_invoice_url, '_blank');
        } else {
            toast.error('Invoice PDF not available');
        }
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'paid':
                return <Badge className="bg-green-100 text-green-700">Paid</Badge>;
            case 'pending':
                return <Badge className="bg-yellow-100 text-yellow-700">Pending</Badge>;
            case 'failed':
                return <Badge className="bg-red-100 text-red-700">Failed</Badge>;
            case 'refunded':
                return <Badge className="bg-gray-100 text-gray-700">Refunded</Badge>;
            default:
                return <Badge variant="outline">{status}</Badge>;
        }
    };

    const filteredInvoices = invoices.filter((invoice) => {
        const matchesSearch =
            invoice.customer_name.toLowerCase().includes(search.toLowerCase()) ||
            invoice.invoice_number.toLowerCase().includes(search.toLowerCase()) ||
            invoice.plan.toLowerCase().includes(search.toLowerCase());

        const matchesStatus = statusFilter === 'all' || invoice.status === statusFilter;

        return matchesSearch && matchesStatus;
    });

    return (
        <div className="p-8 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex flex-row items-center gap-2 flex-nowrap">
                    <Button variant="ghost" size="sm" asChild>
                        <Link href={`/admin/workspaces/${workspaceId}`} className="flex items-center gap-2">
                            <ArrowLeft className="h-4 w-4" />
                            <span>Back to Details</span>
                        </Link>
                    </Button>
                </div>
                <Button>
                    <Download className="h-4 w-4 mr-2" />
                    Export Report
                </Button>
            </div>

            {/* Title */}
            <div>
                <h1 className="text-3xl font-bold">Workspace Billing & Payments</h1>
                <p className="text-muted-foreground mt-1">
                    Manage revenue, track transactions, and download invoices.
                </p>
            </div>

            {/* Time Range Selector */}
            <div className="flex items-center gap-2">
                <Select value={timeRange} onValueChange={setTimeRange}>
                    <SelectTrigger className="w-[180px]">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="7">Last 7 Days</SelectItem>
                        <SelectItem value="30">Last 30 Days</SelectItem>
                        <SelectItem value="90">Last 90 Days</SelectItem>
                        <SelectItem value="365">Last Year</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Total Revenue</p>
                                <p className="text-3xl font-bold mt-2">${(stats?.total_revenue ?? 0).toLocaleString()}</p>
                                <p className="text-sm text-green-600 mt-1">
                                    +{stats?.revenue_change ?? 0}% from last month
                                </p>
                            </div>
                            <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
                                <DollarSign className="h-6 w-6 text-green-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Active Subscri...</p>
                                <p className="text-3xl font-bold mt-2">{(stats?.active_subscribers ?? 0).toLocaleString()}</p>
                                <p className="text-sm text-green-600 mt-1">
                                    +{stats?.subscriber_change ?? 0}% new customers
                                </p>
                            </div>
                            <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                                <Users className="h-6 w-6 text-blue-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Pending Amount</p>
                                <p className="text-3xl font-bold mt-2">${(stats?.pending_amount ?? 0).toLocaleString()}</p>
                                <p className="text-sm text-muted-foreground mt-1">
                                    Across {stats?.pending_count ?? 0} invoices
                                </p>
                            </div>
                            <div className="h-12 w-12 rounded-full bg-yellow-100 flex items-center justify-center">
                                <TrendingUp className="h-6 w-6 text-yellow-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Failed Payments</p>
                                <p className="text-3xl font-bold mt-2">{stats?.failed_payments ?? 0}</p>
                                <p className="text-sm text-red-600 mt-1">
                                    Requires attention
                                </p>
                            </div>
                            <div className="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center">
                                <AlertCircle className="h-6 w-6 text-red-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Transaction History */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle>Transaction History</CardTitle>
                        <div className="flex items-center gap-2">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Search customer..."
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                    className="pl-9 w-[250px]"
                                />
                            </div>
                            <Select value={statusFilter} onValueChange={setStatusFilter}>
                                <SelectTrigger className="w-[150px]">
                                    <SelectValue placeholder="All Statuses" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Statuses</SelectItem>
                                    <SelectItem value="paid">Paid</SelectItem>
                                    <SelectItem value="pending">Pending</SelectItem>
                                    <SelectItem value="failed">Failed</SelectItem>
                                    <SelectItem value="refunded">Refunded</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <table className="w-full">
                        <thead className="border-b">
                            <tr>
                                <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">
                                    Invoice ID
                                </th>
                                <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">
                                    Customer / Plan
                                </th>
                                <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">
                                    Date
                                </th>
                                <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">
                                    Amount
                                </th>
                                <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">
                                    Status
                                </th>
                                <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">
                                    Action
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredInvoices.map((invoice) => (
                                <tr key={invoice.id} className="border-b hover:bg-muted/50">
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <div className="h-8 w-8 rounded bg-orange-100 flex items-center justify-center">
                                                <span className="text-xs font-bold text-orange-600">
                                                    {(() => {
                                                        const parts = invoice.invoice_number.split('-');
                                                        if (parts.length >= 3) return parts[2].substring(0, 2);
                                                        if (parts.length >= 2) return parts[1].substring(0, 2);
                                                        return invoice.invoice_number.substring(0, 2);
                                                    })()}
                                                </span>
                                            </div>
                                            <span className="font-medium text-orange-600">{invoice.invoice_number}</span>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div>
                                            <div className="font-medium">{invoice.customer_name}</div>
                                            <div className="text-sm text-muted-foreground">{invoice.plan}</div>
                                        </div>
                                    </td>
                                    <td className="p-4 text-sm">{invoice.date}</td>
                                    <td className="p-4 font-medium">${invoice.amount.toFixed(2)}</td>
                                    <td className="p-4">{getStatusBadge(invoice.status)}</td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => handleDownloadInvoice(invoice)}
                                            >
                                                <Download className="h-4 w-4" />
                                            </Button>
                                            {invoice.status === 'failed' && (
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    className="text-orange-600"
                                                    onClick={() => handleRetryPayment(invoice.id)}
                                                >
                                                    Retry
                                                </Button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    {/* Pagination */}
                    <div className="flex items-center justify-between mt-4">
                        <p className="text-sm text-muted-foreground">
                            Showing 1 to 5 of 42 results
                        </p>
                        <div className="flex items-center gap-2">
                            <Button variant="outline" size="sm" disabled>
                                Previous
                            </Button>
                            <Button variant="outline" size="sm" className="bg-orange-600 text-white">
                                1
                            </Button>
                            <Button variant="outline" size="sm">
                                2
                            </Button>
                            <Button variant="outline" size="sm">
                                3
                            </Button>
                            <span className="px-2">...</span>
                            <Button variant="outline" size="sm">
                                Next
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
