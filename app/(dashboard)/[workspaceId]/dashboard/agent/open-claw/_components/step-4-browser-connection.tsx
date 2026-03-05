"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Bot, Globe, ShieldCheck, AlertCircle } from "lucide-react";
import useSWR from "swr";
import { useParams } from "next/navigation";
import { AgentFormData } from "../../_components/types";

interface Step4Props {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
}

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export function Step4BrowserConnection({ formData, setFormData }: Step4Props) {
    const params = useParams();
    const workspaceId = params?.workspaceId as string;

    const { data: instances, isLoading, error } = useSWR(
        workspaceId ? `/api/workers/instances?workspace_id=${workspaceId}` : null,
        fetcher
    );

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-8 text-center bg-red-50 rounded-xl border border-red-100">
                <AlertCircle className="h-10 w-10 text-red-500 mx-auto mb-3" />
                <h3 className="text-lg font-semibold text-red-900">Failed to load instances</h3>
                <p className="text-red-600 mt-1">Please ensure your workers are properly configured in Settings.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <Card className="border-indigo-100 shadow-sm">
                <CardHeader>
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-100 rounded-lg">
                            <Bot className="h-5 w-5 text-indigo-600" />
                        </div>
                        <div>
                            <CardTitle>Browser Instance Connection</CardTitle>
                            <CardDescription>
                                Select the OpenClaw worker where this agent's browsing session will live.
                            </CardDescription>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="space-y-6">
                    {instances && Array.isArray(instances) && instances.length > 0 ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {instances.map((instance: any) => (
                                <div
                                    key={instance.id}
                                    onClick={() => setFormData(prev => ({ ...prev, openClawInstanceId: instance.id }))}
                                    className={`
                                        cursor-pointer p-4 rounded-xl border-2 transition-all relative overflow-hidden
                                        ${formData.openClawInstanceId === instance.id
                                            ? 'bg-indigo-50 border-indigo-500 ring-2 ring-indigo-500/20'
                                            : 'bg-white border-slate-100 hover:border-indigo-200'
                                        }
                                    `}
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="font-bold text-slate-900 truncate pr-4">{instance.name}</div>
                                        {instance.status === 'online' ? (
                                            <span className="flex h-2 w-2 rounded-full bg-green-500" />
                                        ) : (
                                            <span className="flex h-2 w-2 rounded-full bg-slate-300" />
                                        )}
                                    </div>

                                    <div className="flex items-center gap-2 text-xs text-slate-500 mb-3">
                                        {instance.is_external ? (
                                            <span className="flex items-center gap-1">
                                                <Globe className="h-3 w-3" /> External
                                            </span>
                                        ) : (
                                            <span className="flex items-center gap-1 text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">
                                                <ShieldCheck className="h-3 w-3" /> Managed Cloud
                                            </span>
                                        )}
                                        <span className="text-slate-300">•</span>
                                        <span className="capitalize">{instance.status}</span>
                                    </div>

                                    <div className="text-[10px] font-mono text-slate-400 bg-slate-50 p-1.5 rounded truncate">
                                        {instance.id}
                                    </div>

                                    {formData.openClawInstanceId === instance.id && (
                                        <div className="absolute -right-2 -bottom-2 bg-indigo-500 text-white p-2 rounded-tl-xl">
                                            <Bot className="h-4 w-4" />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
                            <Bot className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                            <h4 className="font-medium text-slate-900">No Instances Found</h4>
                            <p className="text-sm text-slate-500 mt-1 max-w-xs mx-auto">
                                You need at least one OpenClaw worker enabled to create a browser agent.
                            </p>
                        </div>
                    )}
                </CardContent>
            </Card>

            <div className="bg-amber-50 border border-amber-100 p-4 rounded-xl flex gap-3">
                <AlertCircle className="h-5 w-5 text-amber-600 shrink-0" />
                <p className="text-xs text-amber-800 leading-relaxed">
                    <strong>Note:</strong> Each agent session requires a separate worker instance for optimal performance. You can provision more workers in the 'AI Workers' settings.
                </p>
            </div>
        </div>
    );
}
