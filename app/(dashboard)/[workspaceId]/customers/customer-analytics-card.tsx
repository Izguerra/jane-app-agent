'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Calendar, MessageSquare, Phone, CheckCircle, XCircle, Clock, TrendingUp, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import useSWR from 'swr';
import { Skeleton } from '@/components/ui/skeleton';

const fetcher = (url: string) => fetch(url, { credentials: 'include' }).then((res) => res.json());

interface CustomerAnalyticsCardProps {
    customerId: string;
}

export function CustomerAnalyticsCard({ customerId }: CustomerAnalyticsCardProps) {
    const currentDate = new Date();
    const currentMonth = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}`;
    const currentYear = String(currentDate.getFullYear());

    const [periodType, setPeriodType] = useState<'month' | 'year'>('month');
    const [periodValue, setPeriodValue] = useState(currentMonth);
    const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());

    // Generate last 12 months
    const monthOptions = [];
    for (let i = 0; i < 12; i++) {
        const date = new Date(currentDate.getFullYear(), currentDate.getMonth() - i, 1);
        const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        const label = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        monthOptions.push({ value, label });
    }

    // Generate last 3 years
    const yearOptions = [];
    for (let i = 0; i < 3; i++) {
        const year = currentDate.getFullYear() - i;
        yearOptions.push({ value: String(year), label: String(year) });
    }

    const { data: analytics, isLoading } = useSWR(
        `/api/customers/${customerId}/analytics?period_type=${periodType}&period_value=${periodValue}`,
        fetcher
    );

    const toggleAgent = (agentId: string) => {
        const newExpanded = new Set(expandedAgents);
        if (newExpanded.has(agentId)) {
            newExpanded.delete(agentId);
        } else {
            newExpanded.add(agentId);
        }
        setExpandedAgents(newExpanded);
    };

    const handlePeriodTypeChange = (type: 'month' | 'year') => {
        setPeriodType(type);
        setPeriodValue(type === 'month' ? currentMonth : currentYear);
    };

    const renderAgentStats = (agent: any, isPrimary: boolean = false) => {
        const stats = agent.stats;
        const isExpanded = expandedAgents.has(agent.agent_id) || isPrimary;

        return (
            <div key={agent.agent_id} className={`${!isPrimary ? 'border-t pt-4 mt-4' : ''}`}>
                <div
                    className={`flex items-center justify-between ${!isPrimary ? 'cursor-pointer' : ''}`}
                    onClick={() => !isPrimary && toggleAgent(agent.agent_id)}
                >
                    <div className="flex items-center gap-3">
                        {agent.avatar_url ? (
                            <img src={agent.avatar_url} alt={agent.agent_name} className="w-10 h-10 rounded-full" />
                        ) : (
                            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                                <span className="text-sm font-medium">{agent.agent_name[0]}</span>
                            </div>
                        )}
                        <div>
                            <h4 className="font-medium">{agent.agent_name}</h4>
                            {isPrimary && <Badge variant="secondary" className="text-xs">Primary Agent</Badge>}
                        </div>
                    </div>
                    {!isPrimary && (
                        <Button variant="ghost" size="sm">
                            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        </Button>
                    )}
                </div>

                {isExpanded && (
                    <div className="mt-4 space-y-4">
                        {/* Chat Stats */}
                        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
                            <div className="space-y-1">
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <MessageSquare className="h-4 w-4" />
                                    <span>Total Messages</span>
                                </div>
                                <p className="text-2xl font-bold">{stats.chat.total_messages}</p>
                                <p className="text-xs text-muted-foreground">
                                    {stats.chat.total_conversations} conversations
                                </p>
                            </div>

                            <div className="space-y-1">
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <Clock className="h-4 w-4" />
                                    <span>Avg Response</span>
                                </div>
                                <p className="text-2xl font-bold">{stats.chat.avg_response_time_seconds}s</p>
                                <div className="flex items-center gap-1">
                                    <span className="text-yellow-500">★</span>
                                    <span className="text-sm font-medium">{stats.chat.satisfaction_rating}</span>
                                </div>
                            </div>

                            <div className="space-y-1">
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <Phone className="h-4 w-4" />
                                    <span>Phone Calls</span>
                                </div>
                                <p className="text-2xl font-bold">{stats.phone.total_calls}</p>
                                <p className="text-xs text-muted-foreground">
                                    {Math.floor(stats.phone.avg_duration_seconds / 60)}m avg
                                </p>
                            </div>

                            <div className="space-y-1">
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <Calendar className="h-4 w-4" />
                                    <span>Appointments</span>
                                </div>
                                <p className="text-2xl font-bold">{stats.appointments.total_booked}</p>
                                <p className="text-xs text-muted-foreground">
                                    {stats.appointments.upcoming} upcoming
                                </p>
                            </div>
                        </div>

                        {/* Sentiment Analysis */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="border rounded-lg p-4">
                                <h5 className="font-medium mb-2">Chat Sentiment</h5>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-green-600">Positive</span>
                                        <span className="font-medium">{stats.chat.sentiment.positive}%</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-gray-600">Neutral</span>
                                        <span className="font-medium">{stats.chat.sentiment.neutral}%</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-red-600">Negative</span>
                                        <span className="font-medium">{stats.chat.sentiment.negative}%</span>
                                    </div>
                                </div>
                            </div>

                            <div className="border rounded-lg p-4">
                                <h5 className="font-medium mb-2">Status Breakdown</h5>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="flex items-center gap-1">
                                            <CheckCircle className="h-3 w-3 text-green-600" />
                                            Completed
                                        </span>
                                        <span className="font-medium">{stats.status_breakdown.completed}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="flex items-center gap-1">
                                            <XCircle className="h-3 w-3 text-red-600" />
                                            Failed
                                        </span>
                                        <span className="font-medium">{stats.status_breakdown.failed}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="flex items-center gap-1">
                                            <Clock className="h-3 w-3 text-yellow-600" />
                                            Ongoing
                                        </span>
                                        <span className="font-medium">{stats.status_breakdown.ongoing}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Analytics</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        <Skeleton className="h-10 w-full" />
                        <Skeleton className="h-32 w-full" />
                        <Skeleton className="h-32 w-full" />
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardHeader>
                    <div className="flex flex-col gap-4">
                        <div className="flex items-center justify-between">
                            <CardTitle>Analytics</CardTitle>
                        </div>
                        <div className="flex flex-wrap items-center gap-2 bg-muted/30 p-2 rounded-lg w-full sm:w-auto mt-2 sm:mt-0">
                            <span className="text-sm font-medium text-muted-foreground whitespace-nowrap">Analytics for:</span>
                            <div className="flex flex-wrap items-center gap-2 flex-1">
                                {periodType === 'month' ? (
                                    <Select value={periodValue} onValueChange={setPeriodValue}>
                                        <SelectTrigger className="w-[140px]">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {monthOptions.map((option) => (
                                                <SelectItem key={option.value} value={option.value}>
                                                    {option.label}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                ) : (
                                    <Select value={periodValue} onValueChange={setPeriodValue}>
                                        <SelectTrigger className="w-[100px]">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {yearOptions.map((option) => (
                                                <SelectItem key={option.value} value={option.value}>
                                                    {option.label}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                )}
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handlePeriodTypeChange(periodType === 'month' ? 'year' : 'month')}
                                    className="whitespace-nowrap"
                                >
                                    <Calendar className="h-4 w-4 mr-2" />
                                    <span>{periodType === 'month' ? 'Year' : 'Month'}</span>
                                </Button>
                            </div>
                        </div>
                    </div>
                </CardHeader>
            </CardHeader>
            <CardContent>
                {analytics?.primary_agent ? (
                    <div className="space-y-4">
                        {renderAgentStats(analytics.primary_agent, true)}
                        {analytics.additional_agents?.map((agent: any) => renderAgentStats(agent, false))}
                    </div>
                ) : (
                    <p className="text-center text-muted-foreground py-8">No analytics data available for this period</p>
                )}
            </CardContent>
        </Card>
    );
}
