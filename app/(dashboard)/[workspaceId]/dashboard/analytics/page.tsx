"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import useSWR from 'swr';
import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Phone, MessageSquare, ArrowDownLeft, ArrowUpRight, Clock, Bot } from "lucide-react";

const fetcher = async (url: string) => {
    const res = await fetch(url);
    if (!res.ok) {
        throw new Error('Failed to fetch');
    }
    return res.json();
};

import { useParams } from 'next/navigation';

export default function AnalyticsPage() {
    const params = useParams();
    const workspaceId = params.workspaceId as string;

    const [page, setPage] = useState(1);
    const [isMounted, setIsMounted] = useState(false);
    const limit = 10;

    // Prevent hydration mismatch for Recharts
    useEffect(() => {
        setIsMounted(true);
    }, []);

    // Refresh analytics every 5 seconds for "real-time" feel
    const { data: summary, error: summaryError } = useSWR(`/api/analytics/summary?workspaceId=${workspaceId}`, fetcher, { refreshInterval: 5000 });
    const { data: history, error: historyError } = useSWR(`/api/analytics/history?workspaceId=${workspaceId}`, fetcher, { refreshInterval: 5000 });
    const { data: logsData, error: logsError } = useSWR(`/api/analytics/logs?page=${page}&limit=${limit}&workspaceId=${workspaceId}`, fetcher, { refreshInterval: 5000 });

    // Show loading state
    if (!summary && !summaryError) return <div className="p-8">Loading analytics...</div>;

    // Handle errors - show empty state
    const hasError = summaryError || historyError || logsError;
    const safeSummary = summary || {
        total_conversations: 0, avg_duration: 0, successful_conversations: 0,
        total_minutes: 0, total_agents: 0, total_messages: 0,
        minutes_limit: 100, agents_limit: 1, conversations_limit: 1000
    };
    const safeHistory = history || [];
    const safeLogsData = logsData || { items: [], total: 0 };

    // Helper to format limits (handle infinity)
    const formatLimit = (value: number) => {
        if (!isFinite(value) || value > 999999) return '∞';
        return value.toString();
    };

    const totalPages = Math.ceil(safeLogsData.total / limit);

    return (
        <div className="max-w-6xl mx-auto py-8 space-y-6">
            <h1 className="text-2xl font-bold mb-6">Analytics</h1>

            {hasError && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
                    <p className="text-sm text-yellow-800 dark:text-yellow-200">
                        Unable to load analytics data. This may be because the backend is not running or there's no data yet.
                    </p>
                </div>
            )}

            {!hasError && safeSummary.total_conversations === 0 && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                        No analytics data available yet. Start making calls or sending messages to see your analytics here.
                    </p>
                </div>
            )}

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                            <Phone className="h-4 w-4" />
                            Total Calls
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{safeSummary.total_conversations ?? 0}<span className="text-sm text-muted-foreground font-normal">/{formatLimit(safeSummary.conversations_limit ?? 1000)}</span></div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                            <Clock className="h-4 w-4" />
                            Total Minutes
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{safeSummary.total_minutes ?? 0}<span className="text-sm text-muted-foreground font-normal">/{formatLimit(safeSummary.minutes_limit ?? 100)}</span></div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                            <MessageSquare className="h-4 w-4" />
                            Total Messages
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{safeSummary.total_messages ?? 0}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                            <Bot className="h-4 w-4" />
                            Agents
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{safeSummary.total_agents ?? 0}<span className="text-sm text-muted-foreground font-normal">/{formatLimit(safeSummary.agents_limit ?? 1)}</span></div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            Avg Duration
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {Math.round(safeSummary.avg_duration / 60)}m {Math.round(safeSummary.avg_duration % 60)}s
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            Success Rate
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {safeSummary.total_conversations > 0
                                ? Math.round((safeSummary.successful_conversations / safeSummary.total_conversations) * 100)
                                : 0}%
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card className="col-span-2 md:col-span-3 lg:col-span-6">
                <CardHeader>
                    <CardTitle>Conversation Volume</CardTitle>
                </CardHeader>
                <CardContent className="pl-2">
                    <div className="w-full h-[300px]">
                        {isMounted && (
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={safeHistory}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                    <XAxis
                                        dataKey="date"
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={(value) => new Date(value).toLocaleDateString()}
                                    />
                                    <YAxis
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <Tooltip
                                        labelFormatter={(value) => new Date(value).toLocaleDateString()}
                                    />
                                    <Bar
                                        dataKey="count"
                                        fill="currentColor"
                                        radius={[4, 4, 0, 0]}
                                        className="fill-primary"
                                    />
                                </BarChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </CardContent>
            </Card>

            {/* Call History Table */}
            <Card>
                <CardHeader>
                    <CardTitle>Call History</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="rounded-md border">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-muted/50 text-muted-foreground">
                                <tr>
                                    <th className="px-4 py-3 font-medium">Type</th>
                                    <th className="px-4 py-3 font-medium">Date/Time</th>
                                    <th className="px-4 py-3 font-medium">Direction</th>
                                    <th className="px-4 py-3 font-medium">Duration</th>
                                    <th className="px-4 py-3 font-medium">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {safeLogsData.items.map((log: any) => (
                                    <tr key={log.id} className="hover:bg-muted/50 transition-colors">
                                        <td className="px-4 py-3 flex items-center gap-2">
                                            {log.type === 'call' ? <Phone className="h-4 w-4 text-blue-500" /> : <MessageSquare className="h-4 w-4 text-green-500" />}
                                            <span className="capitalize">{log.type}</span>
                                        </td>
                                        <td className="px-4 py-3">
                                            {new Date(log.started_at).toLocaleString('en-US', {
                                                timeZone: 'America/New_York',
                                                month: '2-digit',
                                                day: '2-digit',
                                                year: 'numeric',
                                                hour: '2-digit',
                                                minute: '2-digit',
                                                hour12: true
                                            })}
                                        </td>
                                        <td className="px-4 py-3">
                                            <div className="flex items-center gap-1 capitalize">
                                                {log.direction === 'inbound' ? <ArrowDownLeft className="h-3 w-3 text-green-500" /> : <ArrowUpRight className="h-3 w-3 text-blue-500" />}
                                                {log.direction}
                                            </div>
                                        </td>
                                        <td className="px-4 py-3">
                                            {log.duration > 0 ? `${Math.floor(log.duration / 60)}m ${log.duration % 60}s` : '-'}
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${log.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                                                log.status === 'missed' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                                                    'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                                                }`}>
                                                {log.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    <div className="flex items-center justify-end space-x-2 py-4">
                        <div className="text-sm text-muted-foreground mr-4">
                            Page {page} of {totalPages}
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                        >
                            <ChevronLeft className="h-4 w-4" />
                            Previous
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                            disabled={page === totalPages}
                        >
                            Next
                            <ChevronRight className="h-4 w-4" />
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
