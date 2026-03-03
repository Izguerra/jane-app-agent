'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Phone, TrendingUp, Clock, MessageSquare } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

interface CustomerAnalyticsProps {
    customerId: string;
    isLoading?: boolean;
}

export function CustomerAnalytics({ customerId, isLoading }: CustomerAnalyticsProps) {
    // Mock data - in real implementation, fetch from API
    const stats = {
        totalCalls: 24,
        totalDuration: 3420, // seconds
        avgDuration: 142.5, // seconds
        lastContact: '2 days ago',
    };

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Customer Analytics</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {[...Array(4)].map((_, i) => (
                            <Skeleton key={i} className="h-16 w-full" />
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Customer Analytics</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                        <div className="flex items-center space-x-3">
                            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                                <Phone className="h-5 w-5 text-primary" />
                            </div>
                            <div>
                                <p className="text-sm font-medium">Total Calls</p>
                                <p className="text-xs text-muted-foreground">All time</p>
                            </div>
                        </div>
                        <p className="text-2xl font-bold">{stats.totalCalls}</p>
                    </div>

                    <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                        <div className="flex items-center space-x-3">
                            <div className="h-10 w-10 rounded-full bg-green-500/10 flex items-center justify-center">
                                <Clock className="h-5 w-5 text-green-500" />
                            </div>
                            <div>
                                <p className="text-sm font-medium">Total Duration</p>
                                <p className="text-xs text-muted-foreground">All time</p>
                            </div>
                        </div>
                        <p className="text-2xl font-bold">{Math.floor(stats.totalDuration / 60)}m</p>
                    </div>

                    <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                        <div className="flex items-center space-x-3">
                            <div className="h-10 w-10 rounded-full bg-blue-500/10 flex items-center justify-center">
                                <TrendingUp className="h-5 w-5 text-blue-500" />
                            </div>
                            <div>
                                <p className="text-sm font-medium">Avg Duration</p>
                                <p className="text-xs text-muted-foreground">Per call</p>
                            </div>
                        </div>
                        <p className="text-2xl font-bold">{Math.floor(stats.avgDuration)}s</p>
                    </div>

                    <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                        <div className="flex items-center space-x-3">
                            <div className="h-10 w-10 rounded-full bg-purple-500/10 flex items-center justify-center">
                                <MessageSquare className="h-5 w-5 text-purple-500" />
                            </div>
                            <div>
                                <p className="text-sm font-medium">Last Contact</p>
                                <p className="text-xs text-muted-foreground">Most recent</p>
                            </div>
                        </div>
                        <p className="text-sm font-medium">{stats.lastContact}</p>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
