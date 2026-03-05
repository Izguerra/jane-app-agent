"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { AnalyticsHistoryItem } from "@/types/analytics";
import { useEffect, useState } from "react";

interface ConversationVolumeChartProps {
    data: AnalyticsHistoryItem[];
    className?: string;
}

export function ConversationVolumeChart({ data, className }: ConversationVolumeChartProps) {
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
    }, []);

    return (
        <Card className={className}>
            <CardHeader>
                <CardTitle>Conversation Volume</CardTitle>
            </CardHeader>
            <CardContent className="pl-2">
                <div className="w-full h-[300px]">
                    {isMounted && (
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={data}>
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
    );
}
