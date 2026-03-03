"use client";

import { Bot, Briefcase, FileText, Users, Clock, CheckCircle2, XCircle, AlertCircle, ArrowRight, Plane, Cloud, Map, Languages } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useParams } from "next/navigation";
import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then(res => res.json());

// Icon mapping for worker types
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
    "map-worker": <Map className="h-6 w-6" />,
    "default": <Bot className="h-6 w-6" />
};

// Color mapping
const WORKER_COLORS: Record<string, string> = {
    "job-search": "bg-blue-500",
    "lead-research": "bg-green-500",
    "content-writer": "bg-purple-500",
    "sales-outreach": "bg-blue-600",
    "faq-resolution": "bg-green-600",
    "meeting-coordination": "bg-orange-500",
    "hr-onboarding": "bg-purple-600",
    "order-status": "bg-yellow-500",
    "payment-billing": "bg-red-500",
    "it-support": "bg-slate-500",
    "intelligent-routing": "bg-indigo-500",
    "data-entry": "bg-cyan-500",
    "document-processing": "bg-orange-600",
    "content-moderation": "bg-red-600",
    "sentiment-escalation": "bg-pink-500",
    "translation-localization": "bg-teal-500",
    "compliance-risk": "bg-zinc-800",
    "weather-worker": "bg-sky-500",
    "flight-tracker": "bg-blue-800",
    "map-worker": "bg-emerald-500",
    "default": "bg-gray-500"
};

// Status badge mapping
const STATUS_CONFIG: Record<string, { color: string; icon: React.ReactNode }> = {
    pending: { color: "bg-yellow-100 text-yellow-800", icon: <Clock className="h-3 w-3" /> },
    running: { color: "bg-blue-100 text-blue-800", icon: <AlertCircle className="h-3 w-3 animate-pulse" /> },
    completed: { color: "bg-green-100 text-green-800", icon: <CheckCircle2 className="h-3 w-3" /> },
    failed: { color: "bg-red-100 text-red-800", icon: <XCircle className="h-3 w-3" /> },
    cancelled: { color: "bg-gray-100 text-gray-800", icon: <XCircle className="h-3 w-3" /> }
};

export default function WorkforceDashboardPage() {
    const params = useParams();
    const workspaceId = params?.workspaceId as string;

    // Fetch worker templates
    const { data: templates, isLoading: templatesLoading } = useSWR(
        "/api/workers/templates",
        fetcher
    );

    // Fetch recent tasks
    const { data: tasksData, isLoading: tasksLoading } = useSWR(
        workspaceId ? `/api/workers/tasks?workspace_id=${workspaceId}` : null,
        fetcher
    );

    const tasks = tasksData?.tasks || [];

    // Fetch stats
    const { data: stats } = useSWR(
        workspaceId ? `/api/workers/stats?workspace_id=${workspaceId}` : null,
        fetcher
    );

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Workforce</h1>
                <p className="text-muted-foreground">
                    Manage your autonomous worker agents and monitor task progress
                </p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                    <CardHeader className="pb-2">
                        <CardDescription>Total Tasks</CardDescription>
                        <CardTitle className="text-2xl">{stats?.total_tasks || 0}</CardTitle>
                    </CardHeader>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardDescription>Running</CardDescription>
                        <CardTitle className="text-2xl text-blue-600">
                            {stats?.status_counts?.running || 0}
                        </CardTitle>
                    </CardHeader>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardDescription>Completed</CardDescription>
                        <CardTitle className="text-2xl text-green-600">
                            {stats?.status_counts?.completed || 0}
                        </CardTitle>
                    </CardHeader>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardDescription>Tokens Used</CardDescription>
                        <CardTitle className="text-2xl">{stats?.total_tokens_used?.toLocaleString() || 0}</CardTitle>
                    </CardHeader>
                </Card>
            </div>

            {/* Worker Templates */}
            <div>
                <h2 className="text-xl font-semibold mb-4">Available Workers</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {templatesLoading ? (
                        <div className="col-span-3 text-center py-8 text-muted-foreground">
                            Loading workers...
                        </div>
                    ) : !Array.isArray(templates) || templates.length === 0 ? (
                        <div className="col-span-3 text-center py-8 text-muted-foreground">
                            {Array.isArray(templates) ? "No worker templates available" : "Error loading templates"}
                        </div>
                    ) : (
                        templates.map((template: any) => (
                            <Card key={template.id} className="hover:shadow-md transition-shadow">
                                <CardHeader className="pb-2">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-lg text-white ${WORKER_COLORS[template.slug] || WORKER_COLORS.default}`}>
                                            {WORKER_ICONS[template.slug] || WORKER_ICONS.default}
                                        </div>
                                        <div>
                                            <CardTitle className="text-lg">{template.name}</CardTitle>
                                            <Badge variant="outline" className="mt-1">{template.category}</Badge>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground line-clamp-2">
                                        {template.description}
                                    </p>
                                    <p className="text-xs text-muted-foreground mt-2">
                                        Dispatch via conversation: &quot;{template.slug === "job-search" ? "Find me jobs..." :
                                            template.slug === "lead-research" ? "Research companies..." : "Write a blog post..."}&quot;
                                    </p>
                                </CardContent>
                            </Card>
                        ))
                    )}
                </div>
            </div>

            {/* Recent Tasks */}
            <div>
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-semibold">Recent Tasks</h2>
                    <Link href={`/${workspaceId}/dashboard/workforce/tasks`}>
                        <Button variant="outline" size="sm">
                            View All <ArrowRight className="h-4 w-4 ml-1" />
                        </Button>
                    </Link>
                </div>

                <Card>
                    <CardContent className="p-0">
                        {tasksLoading ? (
                            <div className="p-8 text-center text-muted-foreground">Loading tasks...</div>
                        ) : !tasks || tasks.length === 0 ? (
                            <div className="p-8 text-center text-muted-foreground">
                                No tasks yet. Ask your agent to dispatch a worker!
                            </div>
                        ) : (
                            <div className="divide-y">
                                {tasks.slice(0, 5).map((task: any) => (
                                    <Link
                                        key={task.id}
                                        href={`/${workspaceId}/dashboard/workforce/tasks/${task.id}`}
                                        className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-lg text-white ${WORKER_COLORS[task.worker_type] || WORKER_COLORS.default}`}>
                                                {WORKER_ICONS[task.worker_type] || WORKER_ICONS.default}
                                            </div>
                                            <div>
                                                <p className="font-medium capitalize">{task.worker_name || task.worker_type.replace("-", " ")}</p>
                                                <p className="text-sm text-muted-foreground">
                                                    {task.current_step || "Waiting to start..."}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            {task.steps_total && (
                                                <span className="text-sm text-muted-foreground">
                                                    {task.steps_completed || 0}/{task.steps_total} steps
                                                </span>
                                            )}
                                            <Badge className={STATUS_CONFIG[task.status]?.color}>
                                                <span className="flex items-center gap-1">
                                                    {STATUS_CONFIG[task.status]?.icon}
                                                    {task.status}
                                                </span>
                                            </Badge>
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
