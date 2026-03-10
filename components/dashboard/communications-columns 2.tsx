"use client";

import { Column } from "@/components/dashboard/data-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    ArrowUpRight,
    ArrowDownLeft,
    Clock,
    CheckCircle2,
    XCircle,
    MoreHorizontal,
    PhoneCall,
    MessageSquare
} from 'lucide-react';
import { formatDateTime } from '@/lib/utils/date';

// Helper to format duration
const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
};

// Define a common interface that covers both Communication and CommunicationLogResponse
export interface UnifiedCommunication {
    id: string | number;
    type: string;
    direction: string;
    status: string;
    duration: number;
    started_at: string;
    user_identifier?: string;
    call_intent?: string;
    call_outcome?: string;
    channel?: string;
    // ... add others as needed
}

export const communicationColumns: Column<UnifiedCommunication>[] = [
    {
        accessorKey: 'type',
        header: 'Type',
        cell: (item) => (
            <div className="flex items-center gap-2">
                {item.type === 'call' ? <PhoneCall className="h-4 w-4 text-blue-500" /> : <MessageSquare className="h-4 w-4 text-green-500" />}
                <Badge variant="outline" className="capitalize">
                    {item.type}
                </Badge>
            </div>
        ),
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
        accessorKey: 'user_identifier',
        header: 'User',
        cell: (item) => (
            <div className="font-medium text-gray-900">
                {item.user_identifier || 'N/A'}
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
                    <XCircle className="h-3 w-3 text-red-500" />
                )}
                <span className="capitalize">{item.status}</span>
            </div>
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
