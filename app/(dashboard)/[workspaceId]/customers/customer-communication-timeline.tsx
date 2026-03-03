'use client';

import { formatDateTime } from '@/lib/utils/date';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Phone, MessageSquare, Mail, Clock, ChevronLeft, ChevronRight, Video } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

interface Communication {
    id: string;
    type: string;
    channel?: string; // Added channel
    direction: string;
    status: string;
    duration?: number;
    summary?: string;
    started_at: string;
}

interface CustomerCommunicationTimelineProps {
    communications: Communication[];
    total: number;
    page: number;
    limit: number;
    pages: number;
    isLoading?: boolean;
    onPageChange: (page: number) => void;
}

export function CustomerCommunicationTimeline({
    communications,
    total,
    page,
    limit,
    pages,
    isLoading,
    onPageChange
}: CustomerCommunicationTimelineProps) {
    const getTypeIcon = (comm: Communication) => {
        if (comm.channel === 'video_avatar') return <Video className="h-4 w-4" />;

        switch (comm.type) {
            case 'call':
                return <Phone className="h-4 w-4" />;
            case 'chat':
                return <MessageSquare className="h-4 w-4" />;
            case 'email':
                return <Mail className="h-4 w-4" />;
            default:
                return <MessageSquare className="h-4 w-4" />;
        }
    };

    const getStatusVariant = (status: string) => {
        switch (status) {
            case 'completed':
                return 'default';
            case 'ongoing':
                return 'secondary';
            case 'failed':
                return 'destructive';
            default:
                return 'outline';
        }
    };

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Communication History</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {[...Array(3)].map((_, i) => (
                            <div key={i} className="flex space-x-4">
                                <Skeleton className="h-10 w-10 rounded-full" />
                                <div className="space-y-2 flex-1">
                                    <Skeleton className="h-4 w-3/4" />
                                    <Skeleton className="h-3 w-1/2" />
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    const startItem = (page - 1) * limit + 1;
    const endItem = Math.min(page * limit, total);

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle>Communication History</CardTitle>
                    {total > 0 && (
                        <span className="text-sm text-muted-foreground">
                            Showing {startItem}-{endItem} of {total}
                        </span>
                    )}
                </div>
            </CardHeader>
            <CardContent>
                {communications.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">
                        No communications yet
                    </p>
                ) : (
                    <>
                        <div className="space-y-4">
                            {communications.map((comm) => (
                                <div key={comm.id} className="flex space-x-4 pb-4 border-b last:border-0">
                                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                                        {getTypeIcon(comm)}
                                    </div>
                                    <div className="flex-1 space-y-1">
                                        <div className="flex items-center justify-between">
                                            <p className="text-sm font-medium capitalize">
                                                {comm.channel === 'video_avatar' ? 'Avatar Video' :
                                                    comm.channel === 'whatsapp' ? 'WhatsApp' :
                                                        comm.channel === 'web' ? 'Chatbot' :
                                                            comm.type === 'call' ? 'Voice Call' : comm.type} - {comm.direction}
                                            </p>
                                            <Badge variant={getStatusVariant(comm.status)} className="text-xs">
                                                {comm.status}
                                            </Badge>
                                        </div>
                                        {comm.summary && (
                                            <p className="text-sm text-muted-foreground line-clamp-2">
                                                {comm.summary}
                                            </p>
                                        )}
                                        <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                                            <span>{formatDateTime(comm.started_at)}</span>
                                            {comm.duration && (
                                                <span className="flex items-center">
                                                    <Clock className="h-3 w-3 mr-1" />
                                                    {comm.duration}s
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Pagination Controls */}
                        {pages > 1 && (
                            <div className="flex items-center justify-between mt-6 pt-4 border-t">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => onPageChange(page - 1)}
                                    disabled={page === 1}
                                >
                                    <ChevronLeft className="h-4 w-4 mr-1" />
                                    Previous
                                </Button>

                                <div className="flex items-center gap-2">
                                    {Array.from({ length: Math.min(pages, 5) }, (_, i) => {
                                        let pageNum;
                                        if (pages <= 5) {
                                            pageNum = i + 1;
                                        } else if (page <= 3) {
                                            pageNum = i + 1;
                                        } else if (page >= pages - 2) {
                                            pageNum = pages - 4 + i;
                                        } else {
                                            pageNum = page - 2 + i;
                                        }

                                        return (
                                            <Button
                                                key={pageNum}
                                                variant={page === pageNum ? "default" : "outline"}
                                                size="sm"
                                                onClick={() => onPageChange(pageNum)}
                                                className="w-8 h-8 p-0"
                                            >
                                                {pageNum}
                                            </Button>
                                        );
                                    })}
                                </div>

                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => onPageChange(page + 1)}
                                    disabled={page === pages}
                                >
                                    Next
                                    <ChevronRight className="h-4 w-4 ml-1" />
                                </Button>
                            </div>
                        )}
                    </>
                )}
            </CardContent>
        </Card>
    );
}
