"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from '@/components/ui/table';
import {
    Loader2,
    RefreshCw,
    Bot,
    CheckCircle,
    XCircle,
    Clock,
    PlayCircle
} from 'lucide-react';
import useSWR from 'swr';
import Link from 'next/link';

// Fetcher function
const fetcher = (url: string) => fetch(url).then((res) => res.json());

function timeAgo(dateString: string) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + " years ago";
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + " months ago";
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + " days ago";
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + " hours ago";
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + " minutes ago";
    return Math.floor(seconds) + " seconds ago";
}

export default function AdminWorkforcePage() {
    // Admin fetch (admin=true)
    const { data: tasksData, error, isLoading, mutate } = useSWR(
        '/api/workers/tasks?admin=true',
        fetcher,
        { refreshInterval: 5000 } // Auto-refresh every 5s
    );

    // Fetch global stats specifically
    const { data: statsData } = useSWR(
        '/api/workers/stats?admin=true',
        fetcher,
        { refreshInterval: 5000 }
    );

    const tasks = tasksData?.tasks || [];
    const stats = statsData || {
        running_tasks: 0,
        completed_tasks: 0,
        failed_tasks: 0,
        total_tasks: 0,
        available_types: 3
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'completed':
                return <Badge className="bg-green-500 hover:bg-green-600"><CheckCircle className="w-3 h-3 mr-1" /> Completed</Badge>;
            case 'failed':
                return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" /> Failed</Badge>;
            case 'running':
                return <Badge className="bg-blue-500 hover:bg-blue-600"><Loader2 className="w-3 h-3 mr-1 animate-spin" /> Running</Badge>;
            default:
                return <Badge variant="outline"><Clock className="w-3 h-3 mr-1" /> Pending</Badge>;
        }
    };

    return (
        <div className="space-y-6 p-8 pt-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Global Workforce Monitor</h1>
                    <p className="text-muted-foreground mt-2">
                        Monitor active worker agents across all workspaces.
                    </p>
                </div>
                <Button onClick={() => mutate()} variant="outline" size="sm">
                    <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                    Refresh
                </Button>
            </div>

            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
                        <PlayCircle className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {stats.running_tasks}
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Completed</CardTitle>
                        <CheckCircle className="h-4 w-4 text-green-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {stats.completed_tasks}
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Failed</CardTitle>
                        <XCircle className="h-4 w-4 text-red-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {stats.failed_tasks}
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
                        <Bot className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">3</div>
                        <p className="text-xs text-muted-foreground">Available types</p>
                    </CardContent>
                </Card>
            </div>

            {/* Tasks Table */}
            <Card>
                <CardHeader>
                    <CardTitle>Recent Activity</CardTitle>
                    <CardDescription>
                        Real-time log of worker agent tasks.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="rounded-md border">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Task ID</TableHead>
                                    <TableHead>Type</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Progress</TableHead>
                                    <TableHead>Dispatched By</TableHead>
                                    <TableHead>Started</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {isLoading && tasks.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={7} className="h-24 text-center">
                                            <Loader2 className="w-6 h-6 animate-spin mx-auto text-muted-foreground" />
                                        </TableCell>
                                    </TableRow>
                                ) : tasks.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                                            No recent worker activity found.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    tasks.map((task: any) => (
                                        <TableRow key={task.id}>
                                            <TableCell className="font-mono text-xs text-muted-foreground">
                                                {task.id.substring(0, 8)}...
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex items-center gap-2">
                                                    <Badge variant="outline" className="capitalize">
                                                        {task.worker_type}
                                                    </Badge>
                                                </div>
                                            </TableCell>
                                            <TableCell>{getStatusBadge(task.status)}</TableCell>
                                            <TableCell>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs text-muted-foreground">
                                                        {task.steps_completed}/{task.steps_total || '?'}
                                                    </span>
                                                    {task.current_step && (
                                                        <span className="text-xs truncate max-w-[150px] text-muted-foreground" title={task.current_step}>
                                                            - {task.current_step}
                                                        </span>
                                                    )}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex flex-col">
                                                    {task.dispatched_by_agent_id ? (
                                                        <span className="text-xs font-medium text-purple-600 dark:text-purple-400">
                                                            🤖 Agent {task.dispatched_by_agent_id.substring(0, 6)}
                                                        </span>
                                                    ) : (
                                                        <span className="text-xs text-muted-foreground">👤 User</span>
                                                    )}
                                                    <span className="text-[10px] text-muted-foreground truncate max-w-[100px]" title={task.workspace_id}>
                                                        {task.workspace_id}
                                                    </span>
                                                </div>
                                            </TableCell>
                                            <TableCell className="text-xs text-muted-foreground">
                                                {timeAgo(task.created_at)}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <Button variant="ghost" size="sm" asChild>
                                                    <Link href={`/admin/workforce/${task.id}`}>
                                                        View
                                                    </Link>
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
