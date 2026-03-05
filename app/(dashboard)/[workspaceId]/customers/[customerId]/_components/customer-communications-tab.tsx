import { useState } from 'react';
import useSWR from 'swr';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    ArrowUpRight,
    ArrowDownLeft,
    Clock,
    CheckCircle2,
    XCircle,
    MoreHorizontal,
    Video
} from 'lucide-react';
import { formatDateTime } from '@/lib/utils/date';
import { DataTable, Column } from '@/components/dashboard/data-table';
import { CallDetailDialog } from '@/components/dashboard/call-detail-dialog';

const fetcher = (url: string) => fetch(url).then((res) => {
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
});

// Helper to format duration
const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
};

interface Communication {
    id: number;
    type: 'call' | 'chat';
    channel?: string;
    direction: string;
    status: string;
    duration: number;
    started_at: string;
    user_identifier?: string;
    call_intent?: string;
    call_outcome?: string;
}

interface CustomerCommunicationsTabProps {
    customerId: string;
    type?: 'call' | 'chat';
}

export function CustomerCommunicationsTab({ customerId, type }: CustomerCommunicationsTabProps) {
    const [page, setPage] = useState(1);
    const [selectedCall, setSelectedCall] = useState<Communication | null>(null);

    // Reuse the main communications endpoint with customer_id filter
    // Append type if provided
    const typeParam = type ? `&type=${type}` : '';
    const { data, error, isLoading } = useSWR(
        `/api/communications?customer_id=${customerId}&page=${page}&limit=25${typeParam}`,
        fetcher
    );

    const communications: Communication[] = data?.items || [];

    const columns: Column<Communication>[] = [
        {
            accessorKey: 'type',
            header: 'Type',
            cell: (item) => {
                let label: string = item.type;
                let className = "";
                let icon = null;

                if (item.type === 'call') {
                    if (item.channel === 'video_avatar') {
                        label = 'Avatar Video';
                        className = "bg-purple-50 text-purple-700 border-purple-200 gap-1 pr-3";
                        icon = <Video className="h-3 w-3" />;
                    } else {
                        label = 'Voice Call';
                    }
                } else if (item.type === 'chat') {
                    if (item.channel === 'whatsapp') {
                        label = 'WhatsApp';
                        className = "bg-green-50 text-green-700 border-green-200";
                    } else if (item.channel === 'web') {
                        label = 'Chatbot';
                    }
                }

                return (
                    <div className="flex items-center gap-2">
                        <Badge variant="outline" className={`capitalize whitespace-nowrap ${className}`}>
                            {icon}
                            {label}
                        </Badge>
                    </div>
                );
            },
        },
        {
            accessorKey: 'direction',
            header: 'Direction',
            cell: (item) => (
                <div className="flex items-center gap-1">
                    {item.direction === 'inbound' ? (
                        <ArrowDownLeft className="h-3 w-3 text-green-500" />
                    ) : (
                        <ArrowUpRight className="h-3 w-3 text-red-500" />
                    )}
                    <span className="capitalize">{item.direction}</span>
                </div>
            ),
        },
        {
            accessorKey: 'duration',
            header: 'Duration',
            cell: (item) => (
                <div className="flex items-center gap-1 text-gray-600">
                    <Clock className="h-3 w-3" />
                    {formatDuration(item.duration)}
                </div>
            ),
        },
        {
            accessorKey: 'status',
            header: 'Status',
            cell: (item) => (
                <div className="flex items-center gap-1">
                    {item.status === 'completed' ? (
                        <CheckCircle2 className="h-3 w-3 text-green-500" />
                    ) : (
                        item.status === 'missed' ? (
                            <XCircle className="h-3 w-3 text-red-500" />
                        ) : (
                            <span className="capitalize text-gray-500">{item.status}</span>
                        )
                    )}
                </div>
            ),
        },
        {
            accessorKey: 'call_intent',
            header: 'Intent',
            cell: (item) => (
                <Badge variant="secondary" className="capitalize">
                    {item.call_intent || 'N/A'}
                </Badge>
            ),
        },
        {
            accessorKey: 'call_outcome',
            header: 'Outcome',
            cell: (item) => (
                <Badge variant="secondary" className="capitalize">
                    {item.call_outcome || 'N/A'}
                </Badge>
            ),
        },
        {
            accessorKey: 'started_at',
            header: <div className="text-right font-medium">Time</div>,
            className: 'w-[140px]',
            cell: (item) => (
                <div className="text-right">
                    <span className="text-sm text-gray-500 whitespace-nowrap">
                        {item.started_at ? formatDateTime(item.started_at) : 'N/A'}
                    </span>
                </div>
            ),
        },
        {
            header: '',
            cell: () => (
                <Button variant="ghost" className="h-8 w-8 p-0">
                    <span className="sr-only">Open menu</span>
                    <MoreHorizontal className="h-4 w-4" />
                </Button>
            ),
        },
    ];

    return (
        <Card className="border-0 shadow-none">
            <CardContent className="p-0">
                <DataTable
                    columns={columns}
                    data={communications}
                    isLoading={isLoading}
                    onRowClick={(item) => setSelectedCall(item)}
                />
            </CardContent>
            <CallDetailDialog
                open={!!selectedCall}
                onOpenChange={(open) => !open && setSelectedCall(null)}
                communication={selectedCall}
            />
        </Card>
    );
}
