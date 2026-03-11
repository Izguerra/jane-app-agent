'use client';

import { useEffect, useState } from 'react';
import useSWR from 'swr';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, PhoneCall, Calendar, Users, TrendingUp, TrendingDown, DollarSign, Clock } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface IntegrationStats {
    whatsapp_agents: { count: number; growth_percentage: number };
    voice_agents: { count: number; growth_percentage: number };
    calendar_integrations: { count: number; growth_percentage: number };
    active_chats: { count: number; growth_percentage: number };
}

interface APIUsage {
    ai_llm_calls: number;
    whatsapp_messages: number;
    calendar_api_calls: number;
    voice_minutes: number;
}

interface RevenueStats {
    total_mrr: number;
    starter_count: number;
    pro_count: number;
    enterprise_count: number;
}

interface VoiceInteraction {
    date: string;
    count: number;
    is_today: boolean;
}

interface Activation {
    provider: string;
    workspace_name: string;
    time_ago: string;
}

export default function AnalyticsPage() {
    const { data: integrationStats } = useSWR<IntegrationStats>('/api/admin/analytics/integration-stats', fetcher);
    const { data: apiUsage } = useSWR<APIUsage>('/api/admin/analytics/api-usage', fetcher);
    const { data: revenue } = useSWR<RevenueStats>('/api/admin/analytics/revenue', fetcher);
    const { data: voiceData } = useSWR<{ daily_data: VoiceInteraction[] }>('/api/admin/analytics/voice-interactions', fetcher);
    const { data: activationsData } = useSWR<{ activations: Activation[] }>('/api/admin/analytics/recent-activations', fetcher);
    const { data: workspaces } = useSWR('/api/workspaces', fetcher);

    const [greeting, setGreeting] = useState('Good morning');
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        const hour = new Date().getHours();
        if (hour < 12) setGreeting('Good morning');
        else if (hour < 18) setGreeting('Good afternoon');
        else setGreeting('Good evening');
        setIsMounted(true);
    }, []);

    const isLoading = !integrationStats || !apiUsage || !revenue;

    if (isLoading) {
        return (
            <div className="p-8">
                <div className="text-muted-foreground">Loading analytics...</div>
            </div>
        );
    }

    const formatNumber = (num: number) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}k`;
        return num.toString();
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0
        }).format(amount);
    };

    const renderTrendIndicator = (percentage: number) => {
        const isPositive = percentage >= 0;
        return (
            <div className={`flex items-center gap-1 text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {isPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                <span>{Math.abs(percentage).toFixed(1)}%</span>
                <span className="text-muted-foreground">vs last month</span>
            </div>
        );
    };

    const getProviderIcon = (provider: string) => {
        const icons: Record<string, string> = {
            'whatsapp': '💬',
            'google_calendar': '📅',
            'ms_calendar': '📆',
            'twilio': '📞',
            'jane_app': '🏥'
        };
        return icons[provider] || '🔌';
    };

    const avgSessionMinutes = apiUsage.voice_minutes / (integrationStats.voice_agents.count || 1);
    const avgSessionSeconds = Math.round((avgSessionMinutes % 1) * 60);

    return (
        <div className="p-8 space-y-6">
            {/* Greeting */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold">{greeting}, Admin 👋</h2>
                    <p className="text-muted-foreground mt-1">Here's what's happening with your customers today.</p>
                </div>
                <div className="text-sm text-muted-foreground">
                    Last updated: Just now
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="border-0 shadow-sm">
                    <CardContent className="px-5 py-2.5">
                        <div className="space-y-1">
                            <div className="flex items-center justify-between">
                                <p className="text-sm font-medium text-muted-foreground">Total Revenue</p>
                                <div className="h-10 w-10 rounded-lg bg-green-50 flex items-center justify-center">
                                    <DollarSign className="h-5 w-5 text-green-600" />
                                </div>
                            </div>
                            <div>
                                <p className="text-2xl font-bold tracking-tight">{formatCurrency(revenue.total_mrr)}</p>
                                <div className="flex items-center gap-1">
                                    <TrendingUp className="h-3 w-3 text-green-600" />
                                    <span className="text-xs font-medium text-green-600">12.0%</span>
                                    <span className="text-xs text-muted-foreground">vs last month</span>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-0 shadow-sm">
                    <CardContent className="px-5 py-2.5">
                        <div className="space-y-1">
                            <div className="flex items-center justify-between">
                                <p className="text-sm font-medium text-muted-foreground">Active Voice Agents</p>
                                <div className="h-10 w-10 rounded-lg bg-blue-50 flex items-center justify-center">
                                    <PhoneCall className="h-5 w-5 text-blue-600" />
                                </div>
                            </div>
                            <div>
                                <p className="text-2xl font-bold tracking-tight">{integrationStats.voice_agents.count.toLocaleString()}</p>
                                <div className="flex items-center gap-1">
                                    {integrationStats.voice_agents.growth_percentage >= 0 ? (
                                        <>
                                            <TrendingUp className="h-3 w-3 text-green-600" />
                                            <span className="text-xs font-medium text-green-600">{integrationStats.voice_agents.growth_percentage.toFixed(1)}%</span>
                                        </>
                                    ) : (
                                        <>
                                            <TrendingDown className="h-3 w-3 text-red-600" />
                                            <span className="text-xs font-medium text-red-600">{Math.abs(integrationStats.voice_agents.growth_percentage).toFixed(1)}%</span>
                                        </>
                                    )}
                                    <span className="text-xs text-muted-foreground">vs last month</span>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-0 shadow-sm">
                    <CardContent className="px-5 py-2.5">
                        <div className="space-y-1">
                            <div className="flex items-center justify-between">
                                <p className="text-sm font-medium text-muted-foreground">Total Subscribers</p>
                                <div className="h-10 w-10 rounded-lg bg-purple-50 flex items-center justify-center">
                                    <Users className="h-5 w-5 text-purple-600" />
                                </div>
                            </div>
                            <div>
                                <p className="text-2xl font-bold tracking-tight">{(revenue.starter_count + revenue.pro_count + revenue.enterprise_count).toLocaleString()}</p>
                                <div className="flex items-center gap-1">
                                    <TrendingDown className="h-3 w-3 text-red-600" />
                                    <span className="text-xs font-medium text-red-600">2.0%</span>
                                    <span className="text-xs text-muted-foreground">vs last month</span>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-0 shadow-sm">
                    <CardContent className="px-5 py-2.5">
                        <div className="space-y-1">
                            <div className="flex items-center justify-between">
                                <p className="text-sm font-medium text-muted-foreground">Avg. Session Duration</p>
                                <div className="h-10 w-10 rounded-lg bg-blue-50 flex items-center justify-center">
                                    <Clock className="h-5 w-5 text-blue-600" />
                                </div>
                            </div>
                            <div>
                                <p className="text-2xl font-bold tracking-tight">{Math.floor(avgSessionMinutes)}m {avgSessionSeconds}s</p>
                                <div className="flex items-center gap-1">
                                    <TrendingUp className="h-3 w-3 text-green-600" />
                                    <span className="text-xs font-medium text-green-600">18.0%</span>
                                    <span className="text-xs text-muted-foreground">vs last month</span>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Voice Interaction Volume & Recent Activations */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card className="lg:col-span-2">
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <CardTitle>Voice Interaction Volume</CardTitle>
                            <span className="text-sm text-muted-foreground">Last 7 days</span>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {isMounted && (
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={voiceData?.daily_data || []}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                                    <YAxis tick={{ fontSize: 12 }} />
                                    <Tooltip />
                                    <Bar
                                        dataKey="count"
                                        fill="#3b82f6"
                                        radius={[8, 8, 0, 0]}
                                    />
                                </BarChart>
                            </ResponsiveContainer>
                        )}
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Recent Activations</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {activationsData?.activations.map((activation, index) => (
                                <div key={index} className="flex items-start gap-3">
                                    <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                                        <span className="text-lg">{getProviderIcon(activation.provider)}</span>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-sm capitalize">{activation.provider.replace('_', ' ')}</p>
                                        <p className="text-xs text-muted-foreground truncate">Integrated by {activation.workspace_name}</p>
                                    </div>
                                    <span className="text-xs text-muted-foreground whitespace-nowrap">{activation.time_ago}</span>
                                </div>
                            ))}
                            {(!activationsData || activationsData.activations.length === 0) && (
                                <p className="text-sm text-muted-foreground text-center py-4">No recent activations</p>
                            )}
                        </div>
                        <button className="w-full mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium">
                            View All Activity
                        </button>
                    </CardContent>
                </Card>
            </div>

            {/* Active Customers Table */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle>Active Customers</CardTitle>
                        <div className="flex items-center gap-2">
                            <input
                                type="text"
                                placeholder="Search customers..."
                                className="px-3 py-1.5 text-sm border rounded-md"
                            />
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b text-left text-sm text-muted-foreground">
                                    <th className="pb-3 font-medium">CUSTOMER NAME</th>
                                    <th className="pb-3 font-medium">STATUS</th>
                                    <th className="pb-3 font-medium">PLAN</th>
                                    <th className="pb-3 font-medium">USAGE (MINS)</th>
                                    <th className="pb-3 font-medium">ACTIONS</th>
                                </tr>
                            </thead>
                            <tbody>
                                {Array.isArray(workspaces) && workspaces.slice(0, 5).map((workspace: any) => (
                                    <tr key={workspace.id} className="border-b last:border-0">
                                        <td className="py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                                                    <span className="text-sm font-medium text-blue-600">
                                                        {workspace.owner_first_name?.[0] || workspace.owner_email?.[0] || '?'}
                                                    </span>
                                                </div>
                                                <span className="font-medium">{workspace.owner_first_name} {workspace.owner_last_name}</span>
                                            </div>
                                        </td>
                                        <td className="py-4">
                                            <Badge className="bg-green-100 text-green-700">Active</Badge>
                                        </td>
                                        <td className="py-4">{workspace.plan || 'Starter'}</td>
                                        <td className="py-4">
                                            <div className="flex items-center gap-2">
                                                <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                                                    <div className="h-full bg-blue-500" style={{ width: '65%' }}></div>
                                                </div>
                                                <span className="text-sm">450/1000</span>
                                            </div>
                                        </td>
                                        <td className="py-4">
                                            <button className="text-muted-foreground hover:text-foreground">⋯</button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
