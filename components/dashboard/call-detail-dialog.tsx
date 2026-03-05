"use client";

import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Play, FileText, User, Calendar, Clock, BarChart3, Sparkles } from "lucide-react";
import useSWR from 'swr';

interface CallDetailDialogProps {
    communication: any | null; // Typed loosely for now or import Communication type
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

const fetcher = (url: string) => fetch(url).then((res) => {
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
});

export function CallDetailDialog({
    communication: initialCommunication,
    open,
    onOpenChange,
}: CallDetailDialogProps) {
    // Only fetch if we have an ID and the dialog is open
    const shouldFetch = open && initialCommunication?.id;
    const { data: fullDetails, isLoading } = useSWR(
        shouldFetch ? `/api/communications/${initialCommunication.id}` : null,
        fetcher
    );

    // Use full details if available, otherwise fallback to initial prop (which has basic info but no transcript)
    const communication = fullDetails || initialCommunication;

    if (!communication) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-3xl h-[80vh] flex flex-col">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-xl">
                        {communication.direction === 'inbound' ? 'Inbound' : 'Outbound'} Call Details
                        <Badge variant="outline" className="ml-2 font-normal">
                            {communication.status}
                        </Badge>
                    </DialogTitle>
                    <div className="text-sm text-muted-foreground flex items-center gap-4 mt-1">
                        <span className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            {communication.user_identifier || 'Unknown User'}
                        </span>
                        <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {new Date(communication.started_at).toLocaleString()}
                        </span>
                        <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {Math.floor(communication.duration / 60)}m {communication.duration % 60}s
                        </span>
                    </div>
                </DialogHeader>

                <Separator className="my-2" />

                <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-6 overflow-hidden">
                    {/* Left Column: Recording & Metadata */}
                    <div className="space-y-6 md:col-span-1 border-r pr-4">
                        {/* Audio Player */}
                        {communication.recording_url ? (
                            <div className="bg-muted p-4 rounded-lg">
                                <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
                                    <Play className="h-4 w-4" /> Recording
                                </h4>
                                <audio controls className="w-full">
                                    <source src={communication.recording_url} type="audio/wav" />
                                    Your browser does not support the audio element.
                                </audio>
                            </div>
                        ) : (
                            <div className="bg-muted/50 p-4 rounded-lg text-center text-sm text-muted-foreground">
                                No recording available.
                            </div>
                        )}

                        {/* Analysis / Metadata */}
                        <div>
                            <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
                                <BarChart3 className="h-4 w-4" /> Analysis
                            </h4>
                            <div className="space-y-3">
                                <div>
                                    <span className="text-xs text-muted-foreground uppercase">Sentiment</span>
                                    <div className="font-medium capitalize">{communication.sentiment || 'N/A'}</div>
                                </div>
                                <div>
                                    <span className="text-xs text-muted-foreground uppercase">Intent</span>
                                    <div className="font-medium capitalize">{communication.call_intent || 'N/A'}</div>
                                </div>
                                <div>
                                    <span className="text-xs text-muted-foreground uppercase">Outcome</span>
                                    <div className="font-medium capitalize">{communication.call_outcome || 'N/A'}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Transcript */}
                    <div className="md:col-span-2 flex flex-col h-full overflow-hidden">

                        {/* AI Summary Section */}
                        {communication.summary && (
                            <div className="mb-4 bg-purple-50 p-4 rounded-md border border-purple-100">
                                <div className="flex items-center gap-2 mb-2">
                                    <Sparkles className="h-4 w-4 text-purple-600" />
                                    <span className="text-sm font-semibold text-purple-900 uppercase">AI Summary</span>
                                </div>
                                <p className="text-sm text-purple-800 leading-relaxed">{communication.summary}</p>
                            </div>
                        )}

                        <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
                            <FileText className="h-4 w-4" /> Transcript
                        </h4>
                        <ScrollArea className="flex-1 border rounded-md p-4 bg-muted/20">
                            {isLoading && !fullDetails ? (
                                <div className="flex items-center justify-center py-8">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                                </div>
                            ) : communication.transcript ? (
                                <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700">
                                    {communication.transcript}
                                </div>
                            ) : (
                                <div className="text-center text-muted-foreground py-8">
                                    Transcript processing or not available.
                                </div>
                            )}
                        </ScrollArea>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
