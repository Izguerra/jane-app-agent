"use client";

import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Bot, Mic, MoreVertical, Edit, PhoneCall, Globe, Search, Trash2 } from "lucide-react";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { useState, useEffect } from "react";
import useSWR from "swr";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    Pagination,
    PaginationContent,
    PaginationEllipsis,
    PaginationItem,
    PaginationLink,
    PaginationNext,
    PaginationPrevious,
} from "@/components/ui/pagination";
import { Input } from "@/components/ui/input";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface Agent {
    id: string;
    name: string;
    description: string;
    voice_id: string;
    language: string;
    is_active: boolean;
    is_orchestrator: boolean;
    updated_at: string;
    created_at?: string;
    phone_numbers?: { id: string; phone_number: string }[];
    agent_type?: string;
    allowed_worker_types?: string[];
}

export default function AgentsListPage() {
    const params = useParams();
    const workspaceId = params?.workspaceId as string;
    const [isMounted, setIsMounted] = useState(false);
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");
    const limit = 10;

    useEffect(() => {
        setIsMounted(true);
    }, []);

    const { data: agents, error, isLoading, mutate } = useSWR<Agent[]>(
        isMounted ? `/api/agents?workspace_id=${workspaceId}` : null,
        fetcher
    );

    const { data: workspace } = useSWR(
        isMounted ? `/api/workspaces/${workspaceId}` : null,
        fetcher
    );

    const [agentToDelete, setAgentToDelete] = useState<Agent | null>(null);

    const handleDelete = async () => {
        if (!agentToDelete) return;

        try {
            const res = await fetch(`/api/agents/${agentToDelete.id}`, {
                method: "DELETE"
            });

            if (!res.ok) throw new Error("Failed to delete");

            mutate(); // Refresh list
            setAgentToDelete(null);
            toast.success("Agent deleted successfully");
        } catch (e) {
            console.error("Delete failed", e);
            toast.error("Failed to delete agent");
        }
    };

    const handleToggleStatus = async (agent: Agent) => {
        try {
            const res = await fetch(`/api/agents/${agent.id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ is_active: !agent.is_active })
            });

            if (!res.ok) throw new Error("Failed to update status");

            mutate();
            toast.success(agent.is_active ? "Agent unpublished (Draft)" : "Agent published");
        } catch (e) {
            console.error("Status update failed", e);
            toast.error("Failed to update agent status");
        }
    };

    if (!isMounted) {
        return <AgentsSkeleton />;
    }

    if (error) {
        return <div className="p-8 text-red-500">Failed to load agents.</div>;
    }

    // Client-side filtering and pagination
    const safeAgents = Array.isArray(agents) ? agents : [];
    const filteredAgents = safeAgents.filter(agent =>
        agent.name.toLowerCase().includes(search.toLowerCase()) ||
        agent.description?.toLowerCase().includes(search.toLowerCase())
    );

    const totalPages = Math.ceil(filteredAgents.length / limit);
    const paginatedAgents = filteredAgents.slice((page - 1) * limit, page * limit);



    // Use dynamic limits from backend if available, fallback to safe defaults
    const agentLimit = workspace?.limits?.agents || (workspace?.custom_agent_limit) || 3;
    const currentCount = agents?.length || 0;
    const remaining = Math.max(0, agentLimit - currentCount);
    const isLimitReached = currentCount >= agentLimit;

    return (
        <div className="max-w-5xl mx-auto py-8 px-4">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 gap-4">
                <div>
                    <p className="text-muted-foreground mt-1">
                        Manage your AI workforce. Create specialized agents for different tasks.
                    </p>
                </div>
                <div className="flex flex-col items-end gap-1">
                    {isLimitReached ? (
                        <div className={cn(buttonVariants({ variant: "default" }), "opacity-50 cursor-not-allowed")}>
                            <Plus className="mr-2 h-4 w-4" />
                            Create Agent
                        </div>
                    ) : (
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button className="shadow-sm">
                                    <Plus className="mr-2 h-4 w-4" />
                                    Create Agent
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-56">
                                <DropdownMenuLabel>Choose Agent Type</DropdownMenuLabel>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem asChild>
                                    <Link href={`/${workspaceId}/dashboard/agent/new`} className="cursor-pointer" prefetch={false}>
                                        <div className="flex flex-col">
                                            <span className="font-semibold">Standard Agent</span>
                                            <span className="text-[10px] text-muted-foreground whitespace-normal leading-tight">
                                                Versatile assistant for FAQs, booking, and CRM tasks.
                                            </span>
                                        </div>
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem asChild>
                                    <Link href={`/${workspaceId}/dashboard/agent/new?type=humanoid`} className="cursor-pointer bg-fuchsia-50/50" prefetch={false}>
                                        <div className="flex flex-col">
                                            <span className="font-semibold text-fuchsia-700 underline decoration-fuchsia-300 decoration-2 underline-offset-4">Multimodal Humanoid Agent</span>
                                            <span className="text-[10px] text-fuchsia-600/70 whitespace-normal leading-tight">
                                                Interactive video avatar for face-to-face AI communication and real-time vision.
                                            </span>
                                        </div>
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem asChild>
                                    <Link href={`/${workspaceId}/dashboard/agent/open-claw/new`} className="cursor-pointer bg-indigo-50/50" prefetch={false}>
                                        <div className="flex flex-col">
                                            <span className="font-semibold text-indigo-700">OpenClaw Browser Agent</span>
                                            <span className="text-[10px] text-indigo-600/70 whitespace-normal leading-tight">
                                                Advanced browsing, research, and automated web tasks.
                                            </span>
                                        </div>
                                    </Link>
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    )}
                    <p className="text-xs text-muted-foreground">
                        {currentCount} / {agentLimit} Agents Used
                    </p>
                </div>
            </div>

            <div className="space-y-4">
                <div className="flex items-center gap-2 max-w-sm">
                    <div className="relative flex-1">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search agents..."
                            className="pl-8"
                            value={search}
                            onChange={(e) => {
                                setSearch(e.target.value);
                                setPage(1); // Reset to first page on search
                            }}
                        />
                    </div>
                </div>

                <div className="border rounded-lg bg-white overflow-hidden">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-[50px]"></TableHead>
                                <TableHead>Name</TableHead>
                                <TableHead>Phone Number</TableHead>
                                <TableHead>Agent Type</TableHead>
                                <TableHead>Created</TableHead>
                                <TableHead>Description</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading ? (
                                <TableRow>
                                    <TableCell colSpan={8} className="h-24 text-center">
                                        Loading...
                                    </TableCell>
                                </TableRow>
                            ) : paginatedAgents.length > 0 ? (
                                paginatedAgents.map((agent) => (
                                    <TableRow key={agent.id} className="group hover:bg-muted/50 transition-colors">
                                        <TableCell>
                                            <div className={`p-2 rounded-lg inline-flex items-center justify-center ${agent.is_orchestrator ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}>
                                                {agent.is_orchestrator ? <Globe className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                                            </div>
                                        </TableCell>
                                        <TableCell className="font-medium">
                                            {agent.name}
                                            <div className="text-xs text-muted-foreground font-normal mt-0.5">
                                                {agent.language.toUpperCase()} • {agent.voice_id}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            {agent.phone_numbers && agent.phone_numbers.length > 0 ? (
                                                <div className="flex flex-col gap-1">
                                                    {agent.phone_numbers.map((pn) => (
                                                        <span key={pn.id} className="text-xs font-mono bg-secondary px-1.5 py-0.5 rounded w-fit">
                                                            {pn.phone_number}
                                                        </span>
                                                    ))}
                                                </div>
                                            ) : (
                                                <span className="text-xs text-muted-foreground">-</span>
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex flex-col gap-1.5">
                                                <div className="flex items-center gap-2">
                                                    {agent.agent_type === 'openclaw' ? (
                                                        <Badge variant="outline" className="bg-indigo-50 text-indigo-700 border-indigo-200">OpenClaw</Badge>
                                                    ) : agent.agent_type === 'humanoid' || (agent as any).use_tavus_avatar || (agent as any).useTavusAvatar || (agent as any).settings?.use_tavus_avatar ? (
                                                        <Badge variant="outline" className="bg-fuchsia-50 text-fuchsia-700 border-fuchsia-200">Humanoid</Badge>
                                                    ) : (
                                                        <Badge variant="outline" className="bg-slate-50 text-slate-700 border-slate-200">Standard</Badge>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-1.5 px-0.5">
                                                    {agent.agent_type === 'personal' ? (
                                                        <div className="flex items-center gap-1">
                                                            <div className="h-1.5 w-1.5 rounded-full bg-blue-500" />
                                                            <span className="text-[10px] font-medium text-blue-600 uppercase tracking-wider">Personal Assistant</span>
                                                        </div>
                                                    ) : (
                                                        <div className="flex items-center gap-1">
                                                            <div className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                                                            <span className="text-[10px] font-medium text-amber-600 uppercase tracking-wider">Business Intelligence</span>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-xs text-muted-foreground">
                                            {agent.created_at ? new Date(agent.created_at).toLocaleDateString() : "-"}
                                        </TableCell>
                                        <TableCell className="max-w-[200px] truncate text-muted-foreground">
                                            {agent.description || "-"}
                                        </TableCell>
                                        <TableCell>
                                            {agent.is_active ? (
                                                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 hover:bg-green-50">Live</Badge>
                                            ) : (
                                                <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200 hover:bg-yellow-50">Draft</Badge>
                                            )}
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="icon" className="h-8 w-8">
                                                        <MoreVertical className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuItem asChild>
                                                        <Link href={
                                                            agent.agent_type === 'openclaw'
                                                                ? `/${workspaceId}/dashboard/agent/open-claw/${agent.id}`
                                                                : `/${workspaceId}/dashboard/agent/${agent.id}`
                                                        } prefetch={false}>
                                                            Manage Agent
                                                        </Link>
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem onClick={() => handleToggleStatus(agent)}>
                                                        {agent.is_active ? "Unpublish Agent" : "Publish Agent"}
                                                    </DropdownMenuItem>
                                                    <DropdownMenuSeparator />
                                                    <DropdownMenuItem
                                                        onClick={() => setAgentToDelete(agent)}
                                                        className="text-destructive focus:text-destructive"
                                                    >
                                                        Delete Agent
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    </TableRow>
                                ))
                            ) : (
                                <TableRow>
                                    <TableCell colSpan={8} className="h-32 text-center text-muted-foreground">
                                        No agents found.
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </div>

                {filteredAgents.length > limit && (
                    <Pagination className="justify-end">
                        <PaginationContent>
                            <PaginationItem>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                >
                                    Previous
                                </Button>
                            </PaginationItem>
                            <PaginationItem>
                                <span className="text-sm text-muted-foreground px-2">
                                    Page {page} of {totalPages}
                                </span>
                            </PaginationItem>
                            <PaginationItem>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                    disabled={page === totalPages}
                                >
                                    Next
                                </Button>
                            </PaginationItem>
                        </PaginationContent>
                    </Pagination>
                )}
            </div>

            <AlertDialog open={!!agentToDelete} onOpenChange={(open) => !open && setAgentToDelete(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This will permanently delete the agent "{agentToDelete?.name}". This action cannot be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div >
    );
}

function AgentsSkeleton() {
    return (
        <div className="max-w-5xl mx-auto py-8 px-4">
            <div className="flex justify-between items-center mb-8">
                <div className="space-y-2">
                    <Skeleton className="h-8 w-48" />
                    <Skeleton className="h-4 w-96" />
                </div>
                <Skeleton className="h-10 w-32" />
            </div>
            <div className="space-y-4">
                <Skeleton className="h-10 w-full max-w-sm" />
                <div className="border rounded-lg overflow-hidden">
                    <div className="space-y-2 p-4">
                        {[1, 2, 3, 4, 5].map((i) => (
                            <Skeleton key={i} className="h-12 w-full" />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
