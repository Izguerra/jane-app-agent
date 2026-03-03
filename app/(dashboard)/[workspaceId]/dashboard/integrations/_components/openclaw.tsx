"use client";

import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Bot, Plus, Server } from "lucide-react";

interface OpenClawProps {
    integrations: any[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

interface WorkerInstance {
    id: string;
    name: string;
    type: "byo" | "managed";
    status: "active" | "offline" | "provisioning";
    url?: string;
}

export function OpenClawIntegration({ integrations, expanded, onToggleExpand }: OpenClawProps) {
    const params = useParams();
    const workspaceId = params?.workspaceId as string;
    const router = useRouter();

    const integration = integrations?.find((i: any) => i.provider === 'openclaw');
    const isActive = integration?.is_active ?? false;

    const handleManage = () => {
        // Redirect to AI Workers page for all infrastructure management
        router.push(`/${workspaceId}/settings/workers`);
    };

    return (
        <Card className={isActive ? "border-green-200 bg-green-50/10" : ""}>
            <CardContent className="p-6">
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-indigo-100 rounded-lg">
                            <Bot className="w-6 h-6 text-indigo-600" />
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <h3 className="text-lg font-semibold text-slate-900">OpenClaw Browser Agent</h3>
                                {isActive && (
                                    <span className="flex items-center gap-1.5 px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                                        <div className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
                                        Active
                                    </span>
                                )}
                            </div>
                            <p className="text-sm text-slate-500 mt-1">
                                Connect local machines or rent secure cloud workers for autonomous browsing tasks.
                            </p>
                        </div>
                    </div>

                    <Button
                        variant={isActive ? "outline" : "default"}
                        className={isActive ? "border-indigo-200 text-indigo-700 hover:bg-indigo-50" : "bg-indigo-600 hover:bg-indigo-700"}
                        onClick={handleManage}
                    >
                        {isActive ? (
                            <>
                                <Server className="w-4 h-4 mr-2" />
                                Manage Workers
                            </>
                        ) : (
                            <>
                                <Plus className="w-4 h-4 mr-2" />
                                Connect Worker
                            </>
                        )}
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
