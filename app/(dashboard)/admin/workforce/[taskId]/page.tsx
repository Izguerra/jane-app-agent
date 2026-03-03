"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    Loader2,
    ArrowLeft,
    CheckCircle,
    XCircle,
    Clock,
    PlayCircle,
    FileText,
    TerminalSquare
} from 'lucide-react';
import useSWR from 'swr';
import Link from 'next/link';
import { useParams } from 'next/navigation';

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

export default function AdminTaskDetailsPage() {
    const params = useParams();
    const taskId = params.taskId as string;

    // Admin fetch (scope=global if needed, but endpoint handles it)
    const { data: task, error, isLoading } = useSWR(
        taskId ? `/api/workers/tasks/${taskId}` : null,
        fetcher,
        { refreshInterval: 3000 }
    );

    if (isLoading) return (
        <div className="flex items-center justify-center p-20">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
    );

    if (error || !task) return (
        <div className="container mx-auto py-10">
            <div className="flex flex-col items-center justify-center gap-4 text-center">
                <XCircle className="w-12 h-12 text-red-500" />
                <h2 className="text-xl font-semibold">Task Not Found</h2>
                <p className="text-muted-foreground">The requested worker task could not be found.</p>
                <Button asChild variant="outline">
                    <Link href="/admin/workforce">Back to Workforce</Link>
                </Button>
            </div>
        </div>
    );

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'completed': return <Badge className="bg-green-500">Completed</Badge>;
            case 'failed': return <Badge variant="destructive">Failed</Badge>;
            case 'running': return <Badge className="bg-blue-500 animate-pulse">Running</Badge>;
            default: return <Badge variant="outline">Pending</Badge>;
        }
    };

    return (
        <div className="container mx-auto py-10 space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" asChild>
                        <Link href="/admin/workforce"><ArrowLeft className="w-4 h-4" /></Link>
                    </Button>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                            {task.worker_type} <span className="text-muted-foreground font-normal text-lg">#{task.id.slice(0, 8)}</span>
                        </h1>
                        <p className="text-muted-foreground text-sm flex items-center gap-2 mt-1">
                            Created {timeAgo(task.created_at)}
                            {' '}&bull;{' '}
                            {new Date(task.created_at).toLocaleString()}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {getStatusBadge(task.status)}
                    {task.dispatched_by_agent_id && (
                        <Badge variant="outline" className="border-purple-200 bg-purple-50 text-purple-700 dark:bg-purple-900/20 dark:text-purple-300 dark:border-purple-800">
                            🤖 Agent {task.dispatched_by_agent_id.slice(0, 6)}
                        </Badge>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Main Content */}
                <div className="md:col-span-2 space-y-6">
                    {/* Progress */}
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium uppercase text-muted-foreground">Progress Monitor</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex flex-col gap-4">
                                <div className="flex items-center justify-between text-sm">
                                    <span>{task.current_step || 'Initializing...'}</span>
                                    <span className="font-mono text-muted-foreground">
                                        {task.steps_completed} / {task.steps_total || '?'}
                                    </span>
                                </div>
                                <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-primary transition-all duration-500 ease-in-out"
                                        style={{ width: `${Math.min(100, (task.steps_completed / (task.steps_total || 1)) * 100)}%` }}
                                    />
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Output / Result */}
                    {task.output_data && (
                        <Card>
                            <CardHeader className="pb-3">
                                <CardTitle className="text-sm font-medium uppercase text-muted-foreground">Result Output</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="bg-muted/50 p-4 rounded-md font-mono text-xs overflow-auto max-h-[400px]">
                                    <pre>{JSON.stringify(task.output_data, null, 2)}</pre>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Error */}
                    {task.error_message && (
                        <Card className="border-red-200 bg-red-50 dark:bg-red-900/10 dark:border-red-900">
                            <CardHeader className="pb-3">
                                <CardTitle className="text-sm font-medium uppercase text-red-600 dark:text-red-400">Error Details</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-sm text-red-600 dark:text-red-400">{task.error_message}</p>
                            </CardContent>
                        </Card>
                    )}

                    {/* Logs */}
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium uppercase text-muted-foreground">Execution Logs</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                {task.logs && task.logs.length > 0 ? (
                                    task.logs.map((log: any, i: number) => (
                                        <div key={i} className="flex gap-3 text-sm border-b last:border-0 pb-2 last:pb-0">
                                            <span className="text-muted-foreground font-mono text-xs whitespace-nowrap pt-0.5">
                                                {new Date(log.timestamp).toLocaleTimeString()}
                                            </span>
                                            <span className={`${log.level === 'error' ? 'text-red-500' : ''}`}>
                                                {log.message}
                                            </span>
                                        </div>
                                    ))
                                ) : (
                                    <div className="text-center py-8 text-muted-foreground text-sm">No logs available.</div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium uppercase text-muted-foreground">Task Details</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <p className="text-muted-foreground text-xs">Worker Type</p>
                                    <p className="font-medium capitalize">{task.worker_type}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground text-xs">Customer ID</p>
                                    <p className="font-mono">{task.customer_id ? task.customer_id.slice(0, 8) + '...' : 'N/A'}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground text-xs">Workspace</p>
                                    <p className="font-mono text-xs truncate" title={task.workspace_id}>{task.workspace_id}</p>
                                </div>
                                <div>
                                    <p className="text-muted-foreground text-xs">Created By</p>
                                    <p className="font-mono text-xs">{task.created_by_user_id || 'System'}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium uppercase text-muted-foreground">Input Parameters</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="bg-muted p-3 rounded-md font-mono text-xs overflow-auto max-h-[200px]">
                                <pre>{JSON.stringify(task.input_data, null, 2)}</pre>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
