"use client";

import { useWorkspace } from "@/hooks/use-workspace";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatDistanceToNow } from "date-fns";
import { Activity, AlertCircle, CheckCircle2, Clock, PlayCircle } from "lucide-react";
import useSWR from "swr";

interface CustomerTasksTabProps {
    customerId: string;
}

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export function CustomerTasksTab({ customerId }: CustomerTasksTabProps) {
    const { workspace } = useWorkspace();
    // Filters by workspace_id and customer_id using the correct endpoint
    const { data: tasks, isLoading } = useSWR(
        workspace ? `/api/workers/tasks?workspace_id=${workspace.id}&customer_id=${customerId}` : null,
        fetcher
    );

    if (isLoading) return <div>Loading tasks...</div>;

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-medium">Worker Activity & Tasks</h3>
                    <p className="text-sm text-muted-foreground">
                        Background jobs executed by Enterprise Workers for this customer.
                    </p>
                </div>
                <Button variant="outline" size="sm">
                    <Activity className="mr-2 h-4 w-4" />
                    Refresh
                </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
                {/* Summary Cards */}
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{tasks?.length || 0}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Completed</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-600">
                            {(Array.isArray(tasks) ? tasks : []).filter((t: any) => t.status === "completed").length || 0}
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">Active / Pending</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-blue-600">
                            {tasks?.filter((t: any) => ["running", "pending"].includes(t.status)).length || 0}
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Activity Timeline</CardTitle>
                    <CardDescription>Recent autonomous actions</CardDescription>
                </CardHeader>
                <CardContent>
                    <ScrollArea className="h-[500px] pr-4">
                        <div className="space-y-8 pl-2">
                            {tasks?.sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                                .map((task: any) => (
                                    <div key={task.id} className="relative flex gap-4 pb-4 border-l pl-6 last:border-0 border-muted">
                                        {/* Status Icon Marker */}
                                        <div className="absolute -left-[9px] top-0 bg-background">
                                            {task.status === "completed" && <CheckCircle2 className="h-5 w-5 text-green-500" />}
                                            {task.status === "running" && <PlayCircle className="h-5 w-5 text-blue-500 animate-pulse" />}
                                            {task.status === "failed" && <AlertCircle className="h-5 w-5 text-red-500" />}
                                            {task.status === "pending" && <Clock className="h-5 w-5 text-muted-foreground" />}
                                        </div>

                                        <div className="flex-1 space-y-1">
                                            <div className="flex items-center gap-2">
                                                <span className="font-semibold text-sm">{task.worker_type}</span>
                                                <Badge variant={
                                                    task.status === "completed" ? "default" :
                                                        task.status === "failed" ? "destructive" : "secondary"
                                                } className="uppercase text-[10px]">
                                                    {task.status}
                                                </Badge>
                                                <span className="text-xs text-muted-foreground ml-auto">
                                                    {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                                                </span>
                                            </div>

                                            {/* Task Details */}
                                            <div className="text-sm text-foreground bg-muted/50 p-3 rounded-md mt-2">
                                                <div className="font-medium text-xs text-muted-foreground mb-1">INPUT</div>
                                                <pre className="whitespace-pre-wrap text-xs font-mono text-muted-foreground break-all">
                                                    {JSON.stringify(task.input_data, null, 2)}
                                                </pre>

                                                {task.output_data && (
                                                    <>
                                                        <div className="font-medium text-xs text-muted-foreground mt-3 mb-1">OUTPUT</div>
                                                        <pre className="whitespace-pre-wrap text-xs font-mono text-green-700 dark:text-green-500 break-all">
                                                            {JSON.stringify(task.output_data, null, 2)}
                                                        </pre>
                                                    </>
                                                )}

                                                {task.error_message && (
                                                    <div className="text-red-500 text-xs mt-2">
                                                        Error: {task.error_message}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Step Progress */}
                                            {task.steps_total > 0 && (
                                                <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2">
                                                    <div className="h-1.5 w-24 bg-secondary rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full bg-primary transition-all duration-500"
                                                            style={{ width: `${(task.steps_completed / task.steps_total) * 100}%` }}
                                                        />
                                                    </div>
                                                    <span>{task.steps_completed} / {task.steps_total} steps</span>
                                                    {task.current_step && <span>- {task.current_step}</span>}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}

                            {!tasks?.length && (
                                <div className="text-center py-10 text-muted-foreground">
                                    No worker tasks found for this customer.
                                </div>
                            )}
                        </div>
                    </ScrollArea>
                </CardContent>
            </Card>
        </div>
    );
}
