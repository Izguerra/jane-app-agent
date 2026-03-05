"use client";

import { ArrowLeft, Clock, CheckCircle2, XCircle, AlertCircle, Star } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import useSWR, { mutate } from "swr";
import { useState } from "react";
import { toast } from "sonner";
import { ResultTable } from "./_components/result-table";
import { ResultCard } from "./_components/result-card";

const fetcher = (url: string) => fetch(url).then(res => res.json());

// Status badge mapping
const STATUS_CONFIG: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
    pending: { color: "bg-yellow-100 text-yellow-800", icon: <Clock className="h-4 w-4" />, label: "Pending" },
    running: { color: "bg-blue-100 text-blue-800", icon: <AlertCircle className="h-4 w-4 animate-pulse" />, label: "Running" },
    completed: { color: "bg-green-100 text-green-800", icon: <CheckCircle2 className="h-4 w-4" />, label: "Completed" },
    failed: { color: "bg-red-100 text-red-800", icon: <XCircle className="h-4 w-4" />, label: "Failed" },
    cancelled: { color: "bg-gray-100 text-gray-800", icon: <XCircle className="h-4 w-4" />, label: "Cancelled" }
};

export default function TaskDetailPage() {
    const params = useParams();
    const router = useRouter();
    const workspaceId = params?.workspaceId as string;
    const taskId = params?.taskId as string;

    const [rating, setRating] = useState(0);
    const [hoverRating, setHoverRating] = useState(0);
    const [feedback, setFeedback] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Fetch task details
    const { data: task, isLoading } = useSWR(
        taskId ? `/api/workers/tasks/${taskId}` : null,
        fetcher,
        { refreshInterval: 5000 } // Poll every 5s for running tasks
    );

    const handleRate = async () => {
        if (rating === 0) {
            toast.error("Please select a rating");
            return;
        }

        setIsSubmitting(true);
        try {
            const res = await fetch(`/api/workers/tasks/${taskId}/rate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ rating, feedback })
            });

            if (!res.ok) throw new Error("Failed to submit rating");

            toast.success("Rating submitted successfully!");
            mutate(`/api/workers/tasks/${taskId}`);
        } catch (error) {
            toast.error("Failed to submit rating");
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-16">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    if (!task) {
        return (
            <div className="text-center py-16">
                <p className="text-muted-foreground">Task not found</p>
                <Link href={`/${workspaceId}/dashboard/workforce`}>
                    <Button variant="outline" className="mt-4">Back to Workforce</Button>
                </Link>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Link href={`/${workspaceId}/dashboard/workforce`}>
                    <Button variant="ghost" size="icon">
                        <ArrowLeft className="h-4 w-4" />
                    </Button>
                </Link>
                <div>
                    <h1 className="text-2xl font-bold capitalize">
                        {(task as any).worker_name || task.worker_type.replace("-", " ")}
                    </h1>
                    <p className="text-sm text-muted-foreground">Task ID: {task.id}</p>
                </div>
                <Badge className={`ml-auto ${STATUS_CONFIG[task.status]?.color}`}>
                    <span className="flex items-center gap-1">
                        {STATUS_CONFIG[task.status]?.icon}
                        {STATUS_CONFIG[task.status]?.label}
                    </span>
                </Badge>
            </div>

            {/* Progress */}
            {task.steps_total && (
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-lg">Progress</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span>{task.current_step || "Initializing..."}</span>
                                <span>{task.steps_completed || 0} / {task.steps_total}</span>
                            </div>
                            <div className="h-2 bg-muted rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-primary transition-all"
                                    style={{ width: `${((task.steps_completed || 0) / task.steps_total) * 100}%` }}
                                />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Input Parameters */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">Input Parameters</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(task.input_data || {}).map(([key, value]) => (
                            <div key={key} className="flex flex-col space-y-1 p-3 bg-muted/50 rounded-lg border">
                                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                    {key.replace(/_/g, " ")}
                                </span>
                                <span className="text-sm font-medium break-words">
                                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </span>
                            </div>
                        ))}
                        {Object.keys(task.input_data || {}).length === 0 && (
                            <p className="text-sm text-muted-foreground italic">No input parameters provided</p>
                        )}
                    </div>
                </CardContent>
            </Card>

            {/* Output / Results */}
            {task.output_data && (
                <div className="space-y-6">
                    <ResultCard data={task.output_data} status={task.status} />
                </div>
            )}

            {/* Error Message */}
            {task.error_message && (
                <Card className="border-red-200 bg-red-50">
                    <CardHeader>
                        <CardTitle className="text-lg text-red-800">Error</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <pre className="text-red-700 text-sm whitespace-pre-wrap">
                            {task.error_message}
                        </pre>
                    </CardContent>
                </Card>
            )}

            {/* Rating Section - Only show for completed tasks without rating */}
            {task.status === "completed" && !task.rating && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">Rate this result</CardTitle>
                        <CardDescription>
                            Your feedback helps improve worker performance
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* Star Rating */}
                        <div className="flex gap-2">
                            {[1, 2, 3, 4, 5].map((star) => (
                                <button
                                    key={star}
                                    onClick={() => setRating(star)}
                                    onMouseEnter={() => setHoverRating(star)}
                                    onMouseLeave={() => setHoverRating(0)}
                                    className="focus:outline-none"
                                >
                                    <Star
                                        className={`h-8 w-8 transition-colors ${star <= (hoverRating || rating)
                                            ? "fill-yellow-400 text-yellow-400"
                                            : "text-gray-300"
                                            }`}
                                    />
                                </button>
                            ))}
                            <span className="ml-2 text-sm text-muted-foreground self-center">
                                {rating > 0 && (
                                    rating <= 2 ? "Below expectations" :
                                        rating === 3 ? "Met expectations" :
                                            rating === 4 ? "Good" : "Excellent!"
                                )}
                            </span>
                        </div>

                        {/* Feedback */}
                        <Textarea
                            placeholder="Optional feedback..."
                            value={feedback}
                            onChange={(e) => setFeedback(e.target.value)}
                            rows={3}
                        />

                        <Button onClick={handleRate} disabled={isSubmitting}>
                            {isSubmitting ? "Submitting..." : "Submit Rating"}
                        </Button>
                    </CardContent>
                </Card>
            )}

            {/* Existing Rating Display */}
            {task.rating && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">Rating</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex gap-1">
                            {[1, 2, 3, 4, 5].map((star) => (
                                <Star
                                    key={star}
                                    className={`h-6 w-6 ${star <= task.rating
                                        ? "fill-yellow-400 text-yellow-400"
                                        : "text-gray-300"
                                        }`}
                                />
                            ))}
                            <span className="ml-2 text-muted-foreground">
                                {task.rating}/5
                            </span>
                        </div>
                        {task.rating_feedback && (
                            <p className="mt-2 text-sm text-muted-foreground">
                                &quot;{task.rating_feedback}&quot;
                            </p>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Timing Info */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">Timing</CardTitle>
                </CardHeader>
                <CardContent>
                    <dl className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <dt className="text-muted-foreground">Created</dt>
                            <dd>{new Date(task.created_at).toLocaleString()}</dd>
                        </div>
                        {task.started_at && (
                            <div>
                                <dt className="text-muted-foreground">Started</dt>
                                <dd>{new Date(task.started_at).toLocaleString()}</dd>
                            </div>
                        )}
                        {task.completed_at && (
                            <div>
                                <dt className="text-muted-foreground">Completed</dt>
                                <dd>{new Date(task.completed_at).toLocaleString()}</dd>
                            </div>
                        )}
                        <div>
                            <dt className="text-muted-foreground">Tokens Used</dt>
                            <dd>{task.tokens_used?.toLocaleString() || 0}</dd>
                        </div>
                    </dl>
                </CardContent>
            </Card>
        </div>
    );
}
