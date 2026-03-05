import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { ArrowDown, ArrowUp, LucideIcon } from 'lucide-react';

interface StatsCardProps {
    title: string;
    value: string | number;
    trend?: {
        value: number;
        label?: string; // e.g., "vs last 30 days"
        direction: 'up' | 'down' | 'neutral';
    };
    icon?: LucideIcon;
    iconClassName?: string;
    className?: string;
    description?: string;
}

export function StatsCard({
    title,
    value,
    trend,
    icon: Icon,
    iconClassName,
    className,
    description,
}: StatsCardProps) {
    return (
        <Card className={cn('overflow-hidden', className)}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    {title}
                </CardTitle>
                {Icon && (
                    <div className={cn('p-2 rounded-full bg-muted', iconClassName)}>
                        <Icon className="h-4 w-4" />
                    </div>
                )}
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold">{value}</div>
                {(description && !trend) && (
                    <p className="text-xs text-muted-foreground mt-1">{description}</p>
                )}
                {trend && (
                    <p className="text-xs text-muted-foreground mt-1 flex items-center">
                        <span
                            className={cn(
                                'inline-flex items-center font-medium mr-2',
                                trend.direction === 'up' && 'text-emerald-600',
                                trend.direction === 'down' && 'text-rose-600',
                                trend.direction === 'neutral' && 'text-muted-foreground'
                            )}
                        >
                            {trend.direction === 'up' && <ArrowUp className="mr-1 h-3 w-3" />}
                            {trend.direction === 'down' && <ArrowDown className="mr-1 h-3 w-3" />}
                            {Math.abs(trend.value)}%
                        </span>
                        {trend.label}
                    </p>
                )}
            </CardContent>
        </Card>
    );
}
