"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Phone, MessageSquare, PhoneMissed, Clock, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";

interface AnalyticsSummary {
    total_calls: number;
    total_chats: number;
    missed_calls: number;
    avg_duration: number;
    sentiment_score: number;
}

interface CommunicationLog {
    id: number;
    type: string;
    direction: string;
    status: string;
    duration: number;
    started_at: string;
    sentiment: string;
}

export default function AnalyticsPage() {
    const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
    const [history, setHistory] = useState<CommunicationLog[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            try {
                const [summaryRes, historyRes] = await Promise.all([
                    fetch("/api/agent/analytics/summary"),
                    fetch("/api/agent/analytics/history")
                ]);
                setSummary(await summaryRes.json());
                setHistory(await historyRes.json());
            } catch (error) {
                console.error("Failed to fetch analytics", error);
            } finally {
                setIsLoading(false);
            }
        }
        fetchData();
    }, []);

    if (isLoading) {
        return <div className="p-8 text-center">Loading analytics...</div>;
    }

    return (
        <div className="max-w-6xl mx-auto py-8 space-y-8">
            <h1 className="text-2xl font-bold">Analytics & Reporting</h1>

            {/* Stats Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="card-modern">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
                        <Phone className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{summary?.total_calls}</div>
                        <p className="text-xs text-muted-foreground">+20.1% from last month</p>
                    </CardContent>
                </Card>
                <Card className="card-modern">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Chats</CardTitle>
                        <MessageSquare className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{summary?.total_chats}</div>
                        <p className="text-xs text-muted-foreground">+180.1% from last month</p>
                    </CardContent>
                </Card>
                <Card className="card-modern">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Missed Calls</CardTitle>
                        <PhoneMissed className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{summary?.missed_calls}</div>
                        <p className="text-xs text-muted-foreground">-4% from last month</p>
                    </CardContent>
                </Card>
                <Card className="card-modern">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
                        <Clock className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{summary?.avg_duration}s</div>
                        <p className="text-xs text-muted-foreground">+12s from last month</p>
                    </CardContent>
                </Card>
            </div>

            {/* Recent Activity */}
            <Card className="card-modern">
                <CardHeader>
                    <CardTitle>Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {history.map((log) => (
                            <div key={log.id} className="flex items-center justify-between p-4 rounded-lg glass bg-white/50 dark:bg-black/20">
                                <div className="flex items-center gap-4">
                                    <div className={`p-2 rounded-full ${log.type === 'call' ? 'bg-blue-100 text-blue-600' : 'bg-green-100 text-green-600'}`}>
                                        {log.type === 'call' ? <Phone className="h-4 w-4" /> : <MessageSquare className="h-4 w-4" />}
                                    </div>
                                    <div>
                                        <p className="font-medium capitalize">{log.direction} {log.type}</p>
                                        <p className="text-sm text-muted-foreground">{new Date(log.started_at).toLocaleString()}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="text-right">
                                        <p className="text-sm font-medium">{log.duration}s</p>
                                        <p className={`text-xs capitalize ${log.sentiment === 'positive' ? 'text-green-600' :
                                                log.sentiment === 'negative' ? 'text-red-600' : 'text-gray-600'
                                            }`}>
                                            {log.sentiment}
                                        </p>
                                    </div>
                                    <div className={`px-2 py-1 rounded text-xs capitalize ${log.status === 'completed' ? 'bg-green-100 text-green-700' :
                                            log.status === 'missed' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                                        }`}>
                                        {log.status}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
