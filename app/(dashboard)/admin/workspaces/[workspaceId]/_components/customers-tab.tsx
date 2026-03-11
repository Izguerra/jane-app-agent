'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search, Filter, Download, TrendingUp, TrendingDown, Users, CreditCard, UserMinus } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export function CustomersTab({ workspaceId }: { workspaceId: string }) {
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');

    const { data, error, isLoading } = useSWR(
        `/api/workspaces/${workspaceId}/customers?page=${page}&limit=10${search ? `&search=${search}` : ''}`,
        fetcher
    );

    // Mock stats - replace with real data from API if available or derive
    const stats = {
        totalCustomers: data?.total || 0,
        activeSubscriptions: Math.floor((data?.total || 0) * 0.78),
        churnRate: 2.4,
        churnChange: -0.5
    };

    const getInitials = (firstName: string, lastName: string) => {
        return `${firstName?.[0] || ''}${lastName?.[0] || ''}`.toUpperCase();
    };

    const getAvatarColor = (name: string) => {
        const colors = [
            'bg-blue-100 text-blue-600',
            'bg-purple-100 text-purple-600',
            'bg-pink-100 text-pink-600',
            'bg-green-100 text-green-600',
            'bg-blue-100 text-blue-600',
        ];
        const index = (name?.charCodeAt(0) || 0) % colors.length;
        return colors[index];
    };

    return (
        <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-3">
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-muted-foreground">Total Customers</p>
                                <p className="text-3xl font-bold mt-2">{stats.totalCustomers.toLocaleString()}</p>
                                <p className="text-xs text-green-600 mt-2 flex items-center gap-1">
                                    <TrendingUp className="h-3 w-3" />
                                    12% vs last month
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
                                <p className="text-sm font-medium text-muted-foreground">Active Subscriptions</p>
                                <p className="text-3xl font-bold mt-2">{stats.activeSubscriptions}</p>
                                <p className="text-xs text-muted-foreground mt-2">78% conversion rate</p>
                            </div>
                            <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
                                <CreditCard className="h-6 w-6 text-green-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-muted-foreground">Churn Rate</p>
                                <p className="text-3xl font-bold mt-2">{stats.churnRate}%</p>
                                <p className="text-xs text-green-600 mt-2 flex items-center gap-1">
                                    <TrendingDown className="h-3 w-3" />
                                    {Math.abs(stats.churnChange)}% vs last month
                                </p>
                            </div>
                            <div className="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center">
                                <UserMinus className="h-6 w-6 text-red-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Search and Actions */}
            <div className="flex items-center justify-between gap-4">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        type="search"
                        placeholder="Search customers..."
                        className="pl-9"
                        value={search}
                        onChange={(e) => {
                            setSearch(e.target.value);
                            setPage(1);
                        }}
                    />
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                        <Filter className="h-4 w-4 mr-2" />
                        Filter
                    </Button>
                    <Button variant="outline" size="sm">
                        <Download className="h-4 w-4 mr-2" />
                        Export
                    </Button>
                </div>
            </div>

            {/* Customer Table */}
            <Card>
                <CardContent className="p-0">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="border-b bg-muted/50">
                                <tr>
                                    <th className="text-left p-4 text-sm font-medium text-muted-foreground w-[30%]">CUSTOMER NAME</th>
                                    <th className="text-left p-4 text-sm font-medium text-muted-foreground w-[25%]">BUSINESS PROFILE</th>
                                    <th className="text-left p-4 text-sm font-medium text-muted-foreground w-[20%]">JOINED DATE</th>
                                    <th className="text-left p-4 text-sm font-medium text-muted-foreground w-[25%]">LAST ACTIVE</th>
                                </tr>
                            </thead>
                            <tbody>
                                {isLoading ? (
                                    <tr>
                                        <td colSpan={4} className="p-8 text-center text-muted-foreground">
                                            Loading...
                                        </td>
                                    </tr>
                                ) : data?.items?.length === 0 ? (
                                    <tr>
                                        <td colSpan={4} className="p-8 text-center text-muted-foreground">
                                            No customers found.
                                        </td>
                                    </tr>
                                ) : (
                                    data?.items?.map((customer: any) => (
                                        <tr key={customer.id} className="border-b hover:bg-muted/50 transition-colors">
                                            <td className="p-4">
                                                <div className="flex items-center gap-3">
                                                    <Avatar className={`h-10 w-10 ${getAvatarColor(customer.first_name)}`}>
                                                        <AvatarFallback>
                                                            {getInitials(customer.first_name, customer.last_name)}
                                                        </AvatarFallback>
                                                    </Avatar>
                                                    <div>
                                                        <p className="font-medium">{customer.first_name} {customer.last_name}</p>
                                                        <p className="text-sm text-muted-foreground">{customer.email}</p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="p-4">
                                                <div className="flex items-center gap-2">
                                                    <div className="h-8 w-8 rounded bg-muted flex items-center justify-center">
                                                        <span className="text-xs">🏢</span>
                                                    </div>
                                                    <span className="text-sm font-medium">{customer.company_name || 'No Company'}</span>
                                                </div>
                                            </td>
                                            <td className="p-4">
                                                <p className="text-sm text-muted-foreground">
                                                    {new Date(customer.created_at || Date.now()).toLocaleDateString('en-US', {
                                                        month: 'short',
                                                        day: 'numeric',
                                                        year: 'numeric'
                                                    })}
                                                </p>
                                            </td>
                                            <td className="p-4">
                                                <div className="flex items-center gap-2">
                                                    <div className={`h-2 w-2 rounded-full ${customer.status === 'active' ? 'bg-green-500' : 'bg-gray-300'}`} />
                                                    <span className="text-sm text-muted-foreground">
                                                        {customer.last_contact_date ? new Date(customer.last_contact_date).toLocaleDateString('en-US', {
                                                            month: 'short',
                                                            day: 'numeric',
                                                            year: 'numeric'
                                                        }) : (customer.updated_at ? new Date(customer.updated_at).toLocaleDateString('en-US', {
                                                            month: 'short',
                                                            day: 'numeric',
                                                            year: 'numeric'
                                                        }) : 'Never')}
                                                    </span>
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    {data?.items?.length > 0 && (
                        <div className="flex items-center justify-between p-4 border-t">
                            <p className="text-sm text-muted-foreground">
                                Showing {((page - 1) * 10) + 1} to {Math.min(page * 10, data?.total || 0)} of {data?.total || 0} results
                            </p>
                            <div className="flex items-center gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                                    disabled={page === 1 || isLoading}
                                >
                                    Previous
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setPage((p) => p + 1)}
                                    disabled={!data || !data.items || data.items.length < 10 || isLoading}
                                >
                                    Next
                                </Button>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
