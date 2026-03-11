"use client";

import { useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import useSWR from "swr";
import Link from "next/link";
import {
    AlertCircle,
    ArrowLeft,
    ArrowRight,
    Bot,
    Briefcase,
    CheckCircle2,
    ChevronLeft,
    ChevronRight,
    Clock,
    Cloud,
    FileText,
    Map as MapIcon,
    Plane,
    Users,
    XCircle,
    Languages,
    Filter
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

const fetcher = (url: string) => fetch(url).then(res => res.json());

// Icon mapping (duplicate from dashboard for consistency)
const WORKER_ICONS: Record<string, React.ReactNode> = {
    "job-search": <Briefcase className="h-6 w-6" />,
    "lead-research": <Users className="h-6 w-6" />,
    "content-writer": <FileText className="h-6 w-6" />,
    "sales-outreach": <Users className="h-6 w-6" />,
    "faq-resolution": <Users className="h-6 w-6" />,
    "meeting-coordination": <Clock className="h-6 w-6" />,
    "hr-onboarding": <Users className="h-6 w-6" />,
    "order-status": <CheckCircle2 className="h-6 w-6" />,
    "payment-billing": <CheckCircle2 className="h-6 w-6" />,
    "it-support": <Bot className="h-6 w-6" />,
    "intelligent-routing": <Bot className="h-6 w-6" />,
    "data-entry": <FileText className="h-6 w-6" />,
    "document-processing": <FileText className="h-6 w-6" />,
    "content-moderation": <AlertCircle className="h-6 w-6" />,
    "sentiment-escalation": <AlertCircle className="h-6 w-6" />,
    "translation-localization": <Languages className="h-6 w-6" />,
    "compliance-risk": <AlertCircle className="h-6 w-6" />,
    "weather-worker": <Cloud className="h-6 w-6" />,
    "flight-tracker": <Plane className="h-6 w-6" />,
    "map-worker": <MapIcon className="h-6 w-6" />,
    "default": <Bot className="h-6 w-6" />
};

const WORKER_COLORS: Record<string, string> = {
    "job-search": "bg-blue-500",
    "lead-research": "bg-green-500",
    "content-writer": "bg-purple-500",
    "sales-outreach": "bg-blue-600",
    "faq-resolution": "bg-green-600",
    "meeting-coordination": "bg-blue-500",
    "hr-onboarding": "bg-purple-600",
    "order-status": "bg-yellow-500",
    "payment-billing": "bg-red-500",
    "it-support": "bg-slate-500",
    "intelligent-routing": "bg-indigo-500",
    "data-entry": "bg-cyan-500",
    "document-processing": "bg-blue-600",
    "content-moderation": "bg-red-600",
    "sentiment-escalation": "bg-pink-500",
    "translation-localization": "bg-teal-500",
    "compliance-risk": "bg-zinc-800",
    "weather-worker": "bg-sky-500",
    "flight-tracker": "bg-blue-800",
    "map-worker": "bg-emerald-500",
    "default": "bg-gray-500"
};

const STATUS_CONFIG: Record<string, { color: string; icon: React.ReactNode }> = {
    pending: { color: "bg-yellow-100 text-yellow-800", icon: <Clock className="h-3 w-3" /> },
    running: { color: "bg-blue-100 text-blue-800", icon: <AlertCircle className="h-3 w-3 animate-pulse" /> },
    completed: { color: "bg-green-100 text-green-800", icon: <CheckCircle2 className="h-3 w-3" /> },
    failed: { color: "bg-red-100 text-red-800", icon: <XCircle className="h-3 w-3" /> },
    cancelled: { color: "bg-gray-100 text-gray-800", icon: <XCircle className="h-3 w-3" /> }
};

export default function TasksPage() {
    const params = useParams();
    const router = useRouter();
    const searchParams = useSearchParams();
    const workspaceId = params?.workspaceId as string;

    const page = parseInt(searchParams?.get("page") || "1");
    const statusFilter = searchParams?.get("status") || "all";
    const limit = 10;
    const offset = (page - 1) * limit;

    const { data: tasksData, isLoading, mutate } = useSWR(
        workspaceId ? `/api/workers/tasks?workspace_id=${workspaceId}&limit=${limit}&offset=${offset}${statusFilter !== "all" ? `&status=${statusFilter}` : ""}` : null,
        fetcher
    );

    const tasks = tasksData?.tasks || [];
    // If we request 'limit', and we get < limit, we are at the end. 
    // Ideally the API would return total count, but routers/workers.py currently returns { tasks: [] }.
    // We can guess "Next" availability if data.length === limit.
    const hasMore = tasks.length === limit;

    const handlePageChange = (newPage: number) => {
        const query = new URLSearchParams(searchParams?.toString());
        query.set("page", newPage.toString());
        router.push(`/${workspaceId}/dashboard/workforce/tasks?${query.toString()}`);
    };

    const handleStatusChange = (newStatus: string) => {
        const query = new URLSearchParams(searchParams?.toString());
        query.set("status", newStatus);
        query.set("page", "1"); // Reset to page 1
        router.push(`/${workspaceId}/dashboard/workforce/tasks?${query.toString()}`);
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Link href={`/${workspaceId}/dashboard/workforce`}>
                        <Button variant="ghost" size="icon">
                            <ArrowLeft className="h-4 w-4" />
                        </Button>
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Worker Tasks</h1>
                        <p className="text-muted-foreground">View all autonomous worker history</p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <Select value={statusFilter} onValueChange={handleStatusChange}>
                        <SelectTrigger className="w-[180px]">
                            <Filter className="mr-2 h-4 w-4" />
                            <SelectValue placeholder="Filter by status" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All Statuses</SelectItem>
                            <SelectItem value="running">Running</SelectItem>
                            <SelectItem value="completed">Completed</SelectItem>
                            <SelectItem value="failed">Failed</SelectItem>
                            <SelectItem value="pending">Pending</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <Card>
                <CardContent className="p-0">
                    {isLoading ? (
                        <div className="p-12 text-center text-muted-foreground">Loading tasks...</div>
                    ) : !tasks || tasks.length === 0 ? (
                        <div className="p-12 text-center text-muted-foreground">
                            {statusFilter !== "all" ? "No tasks found matching filter." : "No worker tasks found."}
                        </div>
                    ) : (
                        <div className="divide-y">
                            {tasks.map((task: any) => (
                                <Link
                                    key={task.id}
                                    href={`/${workspaceId}/dashboard/workforce/tasks/${task.id}`}
                                    className="flex flex-col sm:flex-row sm:items-center justify-between p-4 hover:bg-muted/50 transition-colors gap-4"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-lg text-white ${WORKER_COLORS[task.worker_type] || WORKER_COLORS.default}`}>
                                            {WORKER_ICONS[task.worker_type] || WORKER_ICONS.default}
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <p className="font-medium capitalize">{task.worker_name || task.worker_type.replace("-", " ")}</p>
                                                <span className="text-xs text-muted-foreground hidden sm:inline-block">
                                                    • {new Date(task.created_at).toLocaleString()}
                                                </span>
                                            </div>
                                            <p className="text-sm text-muted-foreground">
                                                {task.current_step || "Processing..."}
                                            </p>
                                            <span className="text-xs text-muted-foreground sm:hidden">
                                                {new Date(task.created_at).toLocaleString()}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4 justify-between sm:justify-end">
                                        {task.status === "failed" && task.error_message && (
                                            <p className="text-xs text-red-500 max-w-[200px] truncate" title={task.error_message}>
                                                {task.error_message}
                                            </p>
                                        )}
                                        <Badge className={STATUS_CONFIG[task.status]?.color}>
                                            <span className="flex items-center gap-1">
                                                {STATUS_CONFIG[task.status]?.icon}
                                                {task.status}
                                            </span>
                                        </Badge>
                                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                                    </div>
                                </Link>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Pagination Controls */}
            <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                    Page {page}
                </p>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(page - 1)}
                        disabled={page <= 1 || isLoading}
                    >
                        <ChevronLeft className="h-4 w-4 mr-1" /> Previous
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(page + 1)}
                        disabled={!hasMore || isLoading}
                    >
                        Next <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                </div>
            </div>
        </div>
    );
}
