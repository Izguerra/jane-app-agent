"use client";

import { useState } from "react";
import useSWR, { mutate } from "swr";
import { toast } from "sonner";
import {
    Plug, Plus, Trash2, RefreshCw, CheckCircle2, XCircle, Clock,
    Wrench, ExternalLink, ChevronDown, ChevronUp, Loader2, Shield
} from "lucide-react";

const fetcher = (url: string) =>
    fetch(url, { credentials: 'include' }).then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    });

// Popular MCP presets
const MCP_PRESETS = [
    { name: "Zapier", url: "https://mcp.zapier.com/sse", description: "8,000+ app automations", icon: "⚡" },
    { name: "GitHub", url: "https://mcp.github.com/sse", description: "Repos, issues, PRs, and code search", icon: "🐙" },
    { name: "Notion", url: "https://mcp.notion.so/sse", description: "Pages, databases, and workspaces", icon: "📝" },
    { name: "Slack", url: "https://mcp.slack.com/sse", description: "Messages, channels, and users", icon: "💬" },
    { name: "Google Calendar", url: "https://mcp.google.com/calendar/sse", description: "Events and scheduling", icon: "📅" },
    { name: "Brave Search", url: "https://mcp.brave.com/sse", description: "Private web search", icon: "🔍" },
    { name: "Supabase", url: "https://mcp.supabase.com/sse", description: "Database queries and management", icon: "⚡" },
    { name: "Stripe", url: "https://mcp.stripe.com/sse", description: "Payments and subscriptions", icon: "💳" },
    { name: "PostgreSQL", url: "", description: "Query custom databases", icon: "🐘" },
];

const STATUS_BADGES: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
    connected: { color: "bg-green-100 text-green-700", icon: <CheckCircle2 className="h-3 w-3" />, label: "Connected" },
    error: { color: "bg-red-100 text-red-700", icon: <XCircle className="h-3 w-3" />, label: "Error" },
    pending: { color: "bg-yellow-100 text-yellow-700", icon: <Clock className="h-3 w-3" />, label: "Pending" },
};

interface AddModalProps {
    onClose: () => void;
}

function AddMCPServerModal({ onClose }: AddModalProps) {
    const [name, setName] = useState("");
    const [url, setUrl] = useState("");
    const [transport, setTransport] = useState("sse");
    const [authType, setAuthType] = useState("none");
    const [authValue, setAuthValue] = useState("");
    const [loading, setLoading] = useState(false);
    const [showPresets, setShowPresets] = useState(true);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim() || !url.trim()) return;

        setLoading(true);
        try {
            const res = await fetch("/api/mcp-servers", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({
                    name: name.trim(),
                    url: url.trim(),
                    transport,
                    auth_type: authType,
                    auth_value: authValue || null,
                }),
            });

            if (!res.ok) throw new Error(await res.text());

            toast.success("MCP server added successfully");
            mutate("/api/mcp-servers");
            onClose();
        } catch (err: any) {
            toast.error("Failed to add MCP server: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    const applyPreset = (preset: typeof MCP_PRESETS[0]) => {
        setName(preset.name);
        setUrl(preset.url);
        setShowPresets(false);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                <div className="p-6">
                    <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2 mb-1">
                        <Plug className="h-5 w-5 text-violet-600" />
                        Add MCP Server
                    </h2>
                    <p className="text-sm text-slate-500 mb-5">
                        Connect an external MCP server to expand your agent&apos;s capabilities.
                    </p>

                    {/* Popular Presets */}
                    {showPresets && (
                        <div className="mb-5">
                            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Popular Integrations</h3>
                            <div className="grid grid-cols-3 gap-2">
                                {MCP_PRESETS.map((preset) => (
                                    <button
                                        key={preset.name}
                                        onClick={() => applyPreset(preset)}
                                        className="p-2.5 rounded-lg border border-slate-200 hover:border-violet-300 hover:bg-violet-50/50 text-center transition-all"
                                    >
                                        <span className="text-lg">{preset.icon}</span>
                                        <p className="text-xs font-medium text-slate-700 mt-1">{preset.name}</p>
                                    </button>
                                ))}
                                <button
                                    onClick={() => setShowPresets(false)}
                                    className="p-2.5 rounded-lg border border-dashed border-slate-300 hover:border-violet-400 text-center transition-all"
                                >
                                    <Plus className="h-5 w-5 text-slate-400 mx-auto" />
                                    <p className="text-xs font-medium text-slate-500 mt-1">Custom</p>
                                </button>
                            </div>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="text-xs font-medium text-slate-700 mb-1 block">Server Name</label>
                            <input
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="My MCP Server"
                                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 focus:border-violet-500 outline-none"
                                required
                            />
                        </div>
                        <div>
                            <label className="text-xs font-medium text-slate-700 mb-1 block">Server URL</label>
                            <input
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="https://mcp.example.com/sse"
                                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 focus:border-violet-500 outline-none"
                                required
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="text-xs font-medium text-slate-700 mb-1 block">Transport</label>
                                <select
                                    value={transport}
                                    onChange={(e) => setTransport(e.target.value)}
                                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white focus:ring-2 focus:ring-violet-500 outline-none"
                                >
                                    <option value="sse">SSE (Server-Sent Events)</option>
                                    <option value="stdio">Stdio (Local Process)</option>
                                </select>
                            </div>
                            <div>
                                <label className="text-xs font-medium text-slate-700 mb-1 block">Authentication</label>
                                <select
                                    value={authType}
                                    onChange={(e) => setAuthType(e.target.value)}
                                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white focus:ring-2 focus:ring-violet-500 outline-none"
                                >
                                    <option value="none">None</option>
                                    <option value="api_key">API Key</option>
                                    <option value="bearer">Bearer Token</option>
                                </select>
                            </div>
                        </div>
                        {authType !== "none" && (
                            <div>
                                <label className="text-xs font-medium text-slate-700 mb-1 block flex items-center gap-1">
                                    <Shield className="h-3 w-3" />
                                    {authType === "api_key" ? "API Key" : "Bearer Token"}
                                </label>
                                <input
                                    value={authValue}
                                    onChange={(e) => setAuthValue(e.target.value)}
                                    type="password"
                                    placeholder="Enter your key..."
                                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 focus:border-violet-500 outline-none"
                                />
                            </div>
                        )}
                        <div className="flex gap-3 pt-2">
                            <button
                                type="button"
                                onClick={onClose}
                                className="flex-1 px-4 py-2.5 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={loading || !name.trim() || !url.trim()}
                                className="flex-1 px-4 py-2.5 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                            >
                                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                                Add Server
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}


// ─────────── MCP Server Card ───────────

function MCPServerCard({ server }: { server: any }) {
    const [expanded, setExpanded] = useState(false);
    const [testing, setTesting] = useState(false);

    const handleTest = async (e: React.MouseEvent) => {
        e.stopPropagation();
        setTesting(true);
        try {
            const res = await fetch(`/api/mcp-servers/${server.id}/test`, {
                method: "POST",
                credentials: "include",
            });
            const data = await res.json();
            if (data.status === "connected") {
                toast.success(`Connected! ${data.tools_count || 0} tools found.`);
            } else {
                toast.error(`Connection failed: ${data.error || "Unknown error"}`);
            }
            mutate("/api/mcp-servers");
        } catch (err: any) {
            toast.error("Test failed: " + err.message);
        } finally {
            setTesting(false);
        }
    };

    const handleDelete = async (e: React.MouseEvent) => {
        e.stopPropagation();
        if (!confirm(`Remove "${server.name}"?`)) return;

        try {
            await fetch(`/api/mcp-servers/${server.id}`, {
                method: "DELETE",
                credentials: "include",
            });
            toast.success("MCP server removed");
            mutate("/api/mcp-servers");
        } catch (err: any) {
            toast.error("Failed to remove: " + err.message);
        }
    };

    const badge = STATUS_BADGES[server.status] || STATUS_BADGES.pending;
    const toolsCount = server.tools_cache?.length || 0;

    return (
        <div className="border border-slate-200 rounded-xl bg-white overflow-hidden">
            <div
                className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50/50 transition-colors"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center gap-3 min-w-0">
                    <div className="p-2 bg-violet-100 rounded-lg shrink-0">
                        <Plug className="h-5 w-5 text-violet-600" />
                    </div>
                    <div className="min-w-0">
                        <h4 className="font-semibold text-sm text-slate-900">{server.name}</h4>
                        <p className="text-xs text-slate-400 truncate">{server.url}</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${badge.color}`}>
                        {badge.icon} {badge.label}
                    </span>
                    {toolsCount > 0 && (
                        <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                            {toolsCount} tools
                        </span>
                    )}
                    {expanded ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
                </div>
            </div>

            {expanded && (
                <div className="px-4 pb-4 pt-0 border-t border-slate-100">
                    <div className="flex items-center gap-2 mb-3 pt-3">
                        <span className="text-xs text-slate-500">Transport: <strong>{server.transport?.toUpperCase()}</strong></span>
                        <span className="text-slate-300">•</span>
                        <span className="text-xs text-slate-500">Auth: <strong>{server.auth_type || "none"}</strong></span>
                    </div>

                    {/* Tools List */}
                    {toolsCount > 0 && (
                        <div className="mb-3">
                            <h5 className="text-xs font-semibold text-slate-600 mb-1.5 flex items-center gap-1">
                                <Wrench className="h-3 w-3" /> Available Tools
                            </h5>
                            <div className="flex flex-wrap gap-1.5">
                                {server.tools_cache.map((tool: any, i: number) => (
                                    <span key={i} className="px-2 py-1 bg-slate-50 border border-slate-200 rounded text-[11px] text-slate-600">
                                        {tool.name}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="flex gap-2">
                        <button
                            onClick={handleTest}
                            disabled={testing}
                            className="flex items-center gap-1.5 px-3 py-1.5 border border-violet-200 text-violet-700 rounded-lg text-xs font-medium hover:bg-violet-50 disabled:opacity-50 transition-colors"
                        >
                            {testing ? <Loader2 className="h-3 w-3 animate-spin" /> : <RefreshCw className="h-3 w-3" />}
                            Test Connection
                        </button>
                        <button
                            onClick={handleDelete}
                            className="flex items-center gap-1.5 px-3 py-1.5 border border-red-200 text-red-600 rounded-lg text-xs font-medium hover:bg-red-50 transition-colors"
                        >
                            <Trash2 className="h-3 w-3" />
                            Remove
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}


// ─────────── MAIN EXPORT ───────────

export function MCPServersSection() {
    const { data: servers, isLoading } = useSWR("/api/mcp-servers", fetcher);
    const [showAddModal, setShowAddModal] = useState(false);

    const safeServers = Array.isArray(servers) ? servers : [];
    const connectedCount = safeServers.filter(s => s.status === "connected").length;

    return (
        <section>
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h2 className="text-lg font-semibold text-muted-foreground flex items-center gap-2">
                        🔌 MCP Servers
                    </h2>
                    <p className="text-xs text-slate-400 mt-0.5">
                        Connect external tools via Model Context Protocol. {connectedCount > 0 && `${connectedCount} connected.`}
                    </p>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-1.5 px-4 py-2 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-700 transition-colors shadow-sm"
                >
                    <Plus className="h-4 w-4" />
                    Add MCP Server
                </button>
            </div>

            {isLoading ? (
                <div className="flex items-center justify-center p-8">
                    <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
                </div>
            ) : safeServers.length === 0 ? (
                <div className="border border-dashed border-slate-200 rounded-xl p-8 text-center">
                    <Plug className="h-10 w-10 text-slate-300 mx-auto mb-3" />
                    <h3 className="text-sm font-semibold text-slate-600 mb-1">No MCP servers connected</h3>
                    <p className="text-xs text-slate-400 mb-3 max-w-sm mx-auto">
                        Connect to MCP servers like Zapier, GitHub, Notion, or create a custom connection to extend your agents&apos; capabilities.
                    </p>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="inline-flex items-center gap-1.5 px-4 py-2 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-700 transition-colors"
                    >
                        <Plus className="h-4 w-4" />
                        Add Your First MCP Server
                    </button>
                </div>
            ) : (
                <div className="grid gap-3">
                    {safeServers.map((server: any) => (
                        <MCPServerCard key={server.id} server={server} />
                    ))}
                </div>
            )}

            {showAddModal && <AddMCPServerModal onClose={() => setShowAddModal(false)} />}
        </section>
    );
}
