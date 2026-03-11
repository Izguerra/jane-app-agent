'use client';

import { useEffect, useState } from 'react';
import useSWR from 'swr';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Search, Filter, Eye, TrendingUp, Users, CreditCard } from 'lucide-react';
import Link from 'next/link';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface Workspace {
    id: string;
    name: string;
    owner_email: string;
    owner_name: string;
    owner_first_name: string;
    owner_last_name: string;
    plan: string;
    status: string;
    agent_count: number;
    phone_count: number;
    monthly_calls: number;
    monthly_chats: number;
    created_at: string;
    mrr: number;
}

export default function AdminWorkspacesPage() {
    const { data, error, isLoading } = useSWR<{ items: Workspace[]; total: number }>('/api/workspaces', fetcher);
    const [search, setSearch] = useState('');

    const workspaces = data?.items || [];
    const total = data?.total || 0;

    // Filter workspaces by search
    const filteredWorkspaces = workspaces.filter((ws) =>
        ws.name.toLowerCase().includes(search.toLowerCase()) ||
        ws.owner_email.toLowerCase().includes(search.toLowerCase()) ||
        ws.owner_name.toLowerCase().includes(search.toLowerCase())
    );

    // Calculate stats
    const stats = {
        totalWorkspaces: total,
        activeSubscriptions: workspaces.filter(ws => ws.status === 'active').length,
        totalMRR: workspaces.reduce((sum, ws) => sum + ws.mrr, 0),
    };

    const getInitials = (name: string) => {
        const parts = name.split(' ');
        if (parts.length >= 2) {
            return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    };

    const getAvatarColor = (name: string) => {
        const colors = [
            'bg-blue-500',
            'bg-purple-500',
            'bg-pink-500',
            'bg-green-500',
            'bg-blue-500',
        ];
        const index = name.charCodeAt(0) % colors.length;
        return colors[index];
    };

    const getPlanBadge = (plan: string, status: string) => {
        if (status === 'trialing') {
            return <Badge variant="secondary">Trialing</Badge>;
        }
        if (status === 'churned' || status === 'canceled') {
            return <Badge variant="destructive">Churned</Badge>;
        }
        if (plan === 'Enterprise') {
            return <Badge>Active • Enterprise</Badge>;
        }
        if (plan === 'Professional' || plan === 'Pro') {
            return <Badge>Active • Pro Plan</Badge>;
        }
        return <Badge variant="secondary">Trialing</Badge>;
    };

    return (
        <div className="p-8 space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Total Workspaces</p>
                                <p className="text-3xl font-bold mt-2">{stats.totalWorkspaces}</p>
                                <p className="text-sm text-green-600 mt-1 flex items-center gap-1">
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
                                <p className="text-sm text-muted-foreground">Active Subscriptions</p>
                                <p className="text-3xl font-bold mt-2">{stats.activeSubscriptions}</p>
                                <p className="text-sm text-muted-foreground mt-1">
                                    {total > 0 ? Math.round((stats.activeSubscriptions / total) * 100) : 0}% conversion rate
                                </p>
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
                                <p className="text-sm text-muted-foreground">Total MRR</p>
                                <p className="text-3xl font-bold mt-2">${stats.totalMRR.toLocaleString()}</p>
                                <p className="text-sm text-green-600 mt-1 flex items-center gap-1">
                                    <TrendingUp className="h-3 w-3" />
                                    8.2% vs last month
                                </p>
                            </div>
                            <div className="h-12 w-12 rounded-full bg-purple-100 flex items-center justify-center">
                                <CreditCard className="h-6 w-6 text-purple-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Search and Actions */}
            <div className="flex items-center gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search workspaces..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="pl-10"
                    />
                </div>
                <Button variant="outline">
                    <Filter className="h-4 w-4 mr-2" />
                    Filter
                </Button>
            </div>

            {/* Workspaces Table */}
            <Card>
                <CardContent className="p-0">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="border-b">
                                <tr>
                                    <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Workspace</th>
                                    <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Owner</th>
                                    <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Resources</th>
                                    <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Joined</th>
                                    <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {isLoading && (
                                    <tr>
                                        <td colSpan={5} className="p-8 text-center text-muted-foreground">
                                            Loading...
                                        </td>
                                    </tr>
                                )}
                                {!isLoading && filteredWorkspaces.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="p-8 text-center text-muted-foreground">
                                            No workspaces found
                                        </td>
                                    </tr>
                                )}
                                {filteredWorkspaces.map((workspace) => (
                                    <tr key={workspace.id} className="border-b hover:bg-muted/50">
                                        <td className="p-4">
                                            <div className="font-medium">{workspace.name}</div>
                                            <div className="text-sm text-muted-foreground">{workspace.id}</div>
                                            <div className="mt-1">{getPlanBadge(workspace.plan, workspace.status)}</div>
                                        </td>
                                        <td className="p-4">
                                            <div className="flex items-center gap-3">
                                                <Avatar className={`h-8 w-8 ${getAvatarColor(workspace.owner_name)}`}>
                                                    <AvatarFallback className="text-white text-xs">
                                                        {getInitials(workspace.owner_name)}
                                                    </AvatarFallback>
                                                </Avatar>
                                                <div>
                                                    <div className="text-sm font-medium">
                                                        {workspace.owner_first_name} {workspace.owner_last_name}
                                                    </div>
                                                    <div className="text-xs text-muted-foreground">{workspace.owner_email}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <div className="text-sm">
                                                <div>{workspace.agent_count} agents</div>
                                                <div className="text-muted-foreground">{workspace.phone_count} phone numbers</div>
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <div className="text-sm">
                                                {workspace.created_at ? new Date(workspace.created_at).toLocaleDateString('en-US', {
                                                    month: 'short',
                                                    day: 'numeric',
                                                    year: 'numeric'
                                                }) : '-'}
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <Button variant="ghost" size="sm" asChild>
                                                <Link href={`/admin/workspaces/${workspace.id}`}>
                                                    <Eye className="h-4 w-4" />
                                                </Link>
                                            </Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            {/* Pagination */}
            <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                    Showing 1 to {filteredWorkspaces.length} of {filteredWorkspaces.length} results
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled>
                        Previous
                    </Button>
                    <Button variant="outline" size="sm" disabled>
                        Next
                    </Button>
                </div>
            </div>
        </div>
    );
}
