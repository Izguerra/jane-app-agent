"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ReactNode } from "react";

interface UsageProgressProps {
    title: string;
    icon: ReactNode;
    used: number;
    limit: number;
    unit?: string;
    color?: string; // e.g. "bg-blue-500"
}

export function UsageProgress({ title, icon, used, limit, unit = "", color = "bg-primary" }: UsageProgressProps) {
    // Calculate percentage, max 100
    const isUnlimited = limit > 999999 || limit === Infinity;
    const percentage = (!isUnlimited && limit > 0) ? Math.min(100, (used / limit) * 100) : 0;

    const formattedLimit = isUnlimited ? "∞" : limit.toLocaleString();
    const formattedUsed = used.toLocaleString();

    return (
        <Card>
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        {icon}
                        {title}
                    </div>
                    <span className="text-xs font-normal">
                        {formattedUsed} / {formattedLimit} {unit}
                    </span>
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-2">
                    <div className="text-2xl font-bold">
                        {isUnlimited ? formattedUsed : `${Math.round(percentage)}%`}
                    </div>
                    {!isUnlimited && (
                        <Progress value={percentage} className={`h-2 [&>div]:${color}`} />
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
