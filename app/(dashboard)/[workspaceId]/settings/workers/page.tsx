"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Trash2, Box, Activity, Server, Link as LinkIcon, AlertCircle } from "lucide-react";
import useSWR, { mutate } from "swr";
import { toast } from "sonner";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface WorkerInstance {
    id: string;
    workspace_id: string;
    name: string;
    worker_type: string;
    status: string; // active, error, terminated
    connection_url: string;
    is_external: boolean;
    created_at: string;
    container_id?: string;
}

import { useParams, useRouter } from "next/navigation";

export default function WorkerManagementPage() {
    const params = useParams();
    const workspaceId = params?.workspaceId as string;
    const { data: instances, isLoading } = useSWR<WorkerInstance[]>(
        workspaceId ? `/api/workers/instances?workspace_id=${workspaceId}` : null,
        fetcher
    );

    const router = useRouter();
    const { data: user } = useSWR<any>('/api/user', fetcher);

    // Auto-redirect if we find instances in a different workspace
    // OR if this workspace is invalid but the user has another one
    useEffect(() => {
        if (!isLoading && (!instances || instances.length === 0) && user?.workspaceId && workspaceId !== user.workspaceId) {
            // Check if there are instances in the user's primary workspace instead
            const checkPrimary = async () => {
                const res = await fetch(`/api/workers/instances?workspace_id=${user.workspaceId}`);
                const primaryInstances = await res.json();
                if (primaryInstances && primaryInstances.length > 0) {
                    console.log(`Redirecting to primary workspace ${user.workspaceId} where workers exist`);
                    router.push(`/${user.workspaceId}/settings/workers`);
                }
            };
            checkPrimary();
        }
    }, [instances, isLoading, user, workspaceId, router]);

    // Connection State
    const [isConnectOpen, setIsConnectOpen] = useState(false);
    const [isProvisionOpen, setIsProvisionOpen] = useState(false); // Managed Flow

    const [name, setName] = useState("");
    const [url, setUrl] = useState("");
    const [apiKey, setApiKey] = useState("");
    const [tier, setTier] = useState("standard");
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Reset forms
    const resetForms = () => {
        setName("");
        setUrl("");
        setApiKey("");
        setTier("standard");
    };

    // Hydration Fix
    const [mounted, setMounted] = useState(false);
    useEffect(() => setMounted(true), []);

    const handleConnect = async (isManaged: boolean = false) => {
        // Validation
        if (!workspaceId || workspaceId === 'undefined') {
            toast.error("Workspace ID missing or invalid");
            return;
        }

        if (!isManaged && (!url || !apiKey)) {
            toast.error("URL and API Key are required for external connections");
            return;
        }

        setIsSubmitting(true);
        try {
            const payload: any = { name };
            if (isManaged) {
                // Managed Provisioning
                payload.tier = tier;
                // No connection_url -> Backend triggers provision
            } else {
                // BYO Connect
                payload.connection_url = url;
                payload.api_key = apiKey;
            }

            const res = await fetch(`/api/workers/instances?workspace_id=${workspaceId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to create worker");
            }

            toast.success(isManaged ? "Worker Provisioned Successfully" : "Worker Connected Successfully");
            mutate(`/api/workers/instances?workspace_id=${workspaceId}`);
            setIsConnectOpen(false);
            setIsProvisionOpen(false);
            resetForms();
        } catch (error: any) {
            toast.error(error.message || "Operation failed");
            console.error(error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDisconnect = async (id: string, isVirtual: boolean = false) => {
        if (!confirm(isVirtual ? "Are you sure you want to terminate this instance?" : "Are you sure you want to disconnect this worker?")) return;
        // ... (rest same)
        try {
            await fetch(`/api/workers/instances/${id}`, { method: "DELETE" });
            toast.success("Worker removed");
            mutate(`/api/workers/instances?workspace_id=${workspaceId}`);
        } catch (error) {
            toast.error("Failed to remove worker");
        }
    };

    return (
        <div className="p-8 space-y-8 max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-900">Worker Instances</h1>
                    <p className="text-slate-500 mt-2">Manage both managed and external (BYO) OpenClaw instances.</p>
                </div>
                <div className="flex gap-3">
                    {/* Managed Provision Button */}
                    {!mounted ? (
                        <Button variant="outline" className="gap-2">
                            <Plus className="h-4 w-4" />
                            Provision Managed
                        </Button>
                    ) : (
                        <Dialog open={isProvisionOpen} onOpenChange={setIsProvisionOpen}>
                            <DialogTrigger asChild>
                                <Button variant="outline" className="gap-2">
                                    <Plus className="h-4 w-4" />
                                    Provision Managed
                                </Button>
                            </DialogTrigger>
                            <DialogContent>
                                <DialogHeader>
                                    <DialogTitle>Provision Managed Worker</DialogTitle>
                                    <DialogDescription>
                                        Spin up a managed OpenClaw instance hosted by us.
                                    </DialogDescription>
                                </DialogHeader>
                                <div className="grid gap-4 py-4">
                                    <div>
                                        <Label>Name</Label>
                                        <Input value={name} onChange={e => setName(e.target.value)} placeholder="My Managed Worker" />
                                    </div>
                                    <div>
                                        <Label>Tier</Label>
                                        <div className="flex gap-4 mt-2">
                                            <div onClick={() => setTier("standard")} className={`p-4 border rounded cursor-pointer ${tier === 'standard' ? 'border-indigo-600 bg-indigo-50' : ''}`}>
                                                <div className="font-bold">Standard</div>
                                                <div className="text-xs text-slate-500">$50/mo</div>
                                            </div>
                                            <div onClick={() => setTier("performance")} className={`p-4 border rounded cursor-pointer ${tier === 'performance' ? 'border-indigo-600 bg-indigo-50' : ''}`}>
                                                <div className="font-bold">Performance</div>
                                                <div className="text-xs text-slate-500">$90/mo</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button variant="ghost" onClick={() => setIsProvisionOpen(false)}>Cancel</Button>
                                    <Button onClick={() => handleConnect(true)} disabled={isSubmitting}>
                                        {isSubmitting ? "Provisioning..." : "Provision Now"}
                                    </Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    )}

                    {/* BYO Connect Button */}
                    {!mounted ? (
                        <Button className="gap-2 bg-indigo-600 hover:bg-indigo-700 text-white">
                            <LinkIcon className="h-4 w-4" />
                            Connect External
                        </Button>
                    ) : (
                        <Dialog open={isConnectOpen} onOpenChange={setIsConnectOpen}>
                            <DialogTrigger asChild>
                                <Button className="gap-2 bg-indigo-600 hover:bg-indigo-700 text-white">
                                    <LinkIcon className="h-4 w-4" />
                                    Connect External
                                </Button>
                            </DialogTrigger>
                            <DialogContent>
                                <DialogHeader>
                                    <DialogTitle>Connect OpenClaw Instance</DialogTitle>
                                    <DialogDescription>
                                        Enter the details of your self-hosted OpenClaw instance.
                                    </DialogDescription>
                                </DialogHeader>

                                <div className="grid gap-4 py-4">
                                    {/* ... (Same BYO Fields) ... */}
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label className="text-right">Name</Label>
                                        <Input placeholder="Production Worker 1" className="col-span-3" value={name} onChange={(e) => setName(e.target.value)} />
                                    </div>
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label className="text-right">URL</Label>
                                        <Input placeholder="https://..." className="col-span-3" value={url} onChange={(e) => setUrl(e.target.value)} />
                                    </div>
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label className="text-right">API Key</Label>
                                        <Input type="password" placeholder="sk_..." className="col-span-3" value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
                                    </div>
                                </div>

                                <DialogFooter>
                                    <Button variant="outline" onClick={() => setIsConnectOpen(false)}>Cancel</Button>
                                    <Button onClick={() => handleConnect(false)} disabled={isSubmitting} className="bg-indigo-600 text-white">
                                        {isSubmitting ? "Verifying..." : "Connect"}
                                    </Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    )}
                </div>
            </div>

            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[1, 2].map((i) => (
                        <div key={i} className="h-48 rounded-xl bg-slate-100 animate-pulse" />
                    ))}
                </div>
            ) : instances && instances.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {instances.map((instance) => (
                        <Card key={instance.id} className="relative overflow-hidden transition-all hover:shadow-md border-slate-200">
                            {/* Header Status Line */}
                            <div className={`h-1.5 w-full ${instance.status === 'active' ? 'bg-green-500' : 'bg-red-500'}`} />

                            <CardHeader className="pb-3">
                                <div className="flex justify-between items-start">
                                    <div className="flex items-center gap-2">
                                        <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                                            <Box className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <CardTitle className="text-lg">{instance.name}</CardTitle>
                                            <CardDescription className="text-xs font-mono mt-1">
                                                {instance.id.slice(0, 8)}
                                            </CardDescription>
                                        </div>
                                    </div>
                                    <Badge variant={instance.status === 'active' ? 'default' : 'destructive'} className="capitalize">
                                        {instance.status}
                                    </Badge>
                                </div>
                            </CardHeader>

                            <CardContent className="space-y-4">
                                <div className="space-y-2 text-sm">
                                    {/* Instance ID */}
                                    <div className="flex justify-between py-1 border-b border-slate-50">
                                        <span className="text-slate-500 flex items-center gap-2">
                                            <Server className="h-3 w-3" />
                                            Instance ID
                                        </span>
                                        <span className="font-mono text-xs select-all text-slate-700 hover:text-indigo-600 cursor-pointer"
                                            title={instance.id}
                                            onClick={() => {
                                                navigator.clipboard.writeText(instance.id);
                                                toast.success("Instance ID copied");
                                            }}>
                                            {instance.id.slice(0, 12)}...
                                        </span>
                                    </div>

                                    {/* Container ID (if available) */}
                                    {!instance.is_external && instance.container_id && (
                                        <div className="flex justify-between py-1 border-b border-slate-50">
                                            <span className="text-slate-500 flex items-center gap-2">
                                                <Box className="h-3 w-3" />
                                                Container ID
                                            </span>
                                            <span className="font-mono text-xs select-all text-slate-700 hover:text-indigo-600 cursor-pointer"
                                                title={instance.container_id}
                                                onClick={() => {
                                                    navigator.clipboard.writeText(instance.container_id!);
                                                    toast.success("Container ID copied");
                                                }}>
                                                {instance.container_id.slice(0, 12)}...
                                            </span>
                                        </div>
                                    )}

                                    {/* Connection URL (if external) */}
                                    {instance.is_external && (
                                        <div className="flex justify-between py-1 border-b border-slate-50">
                                            <span className="text-slate-500 flex items-center gap-2">
                                                <LinkIcon className="h-3 w-3" />
                                                URL
                                            </span>
                                            <span className="font-mono text-xs truncate max-w-[150px]" title={instance.connection_url}>
                                                {instance.connection_url}
                                            </span>
                                        </div>
                                    )}

                                    <div className="flex justify-between py-1 border-b border-slate-50">
                                        <span className="text-slate-500 flex items-center gap-2">
                                            <Activity className="h-3 w-3" /> Type
                                        </span>
                                        <span className="font-medium">
                                            {instance.is_external ? "External (BYO)" : "Managed (Hosted)"}
                                        </span>
                                    </div>
                                </div>
                            </CardContent>

                            <CardFooter className="flex justify-between gap-2 pt-2 border-t bg-slate-50/50">
                                {instance.is_external ? (
                                    <Button variant="ghost" size="sm" className="text-slate-500 hover:text-slate-900"
                                        onClick={() => toast.info("Configuration is managed on your external instance.")}>
                                        <Activity className="h-4 w-4 mr-2" /> Verify
                                    </Button>
                                ) : (
                                    <Button variant="ghost" size="sm" className="text-slate-500 hover:text-slate-900">
                                        <Activity className="h-4 w-4 mr-2" /> Monitor
                                    </Button>
                                )}

                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                    onClick={() => handleDisconnect(instance.id, !instance.is_external)}
                                >
                                    <Trash2 className="h-4 w-4 mr-2" /> {instance.is_external ? "Disconnect" : "Terminate"}
                                </Button>
                            </CardFooter>
                        </Card>
                    ))}
                </div>
            ) : (
                <div className="text-center py-20 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
                    <div className="mx-auto w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-sm mb-4">
                        <Box className="h-6 w-6 text-slate-400" />
                    </div>
                    <h3 className="text-lg font-medium text-slate-900">No workers connected</h3>
                    <p className="text-slate-500 max-w-sm mx-auto mt-1 mb-6">
                        Connect your self-hosted OpenClaw instance to start running tasks.
                    </p>
                    <Button onClick={() => setIsConnectOpen(true)}>
                        <Plus className="h-4 w-4 mr-2" /> Connect Instance
                    </Button>
                </div>
            )}
        </div>
    );
}
