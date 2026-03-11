"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import useSWR, { mutate } from "swr";
import {
    Loader2, Hammer, Search, Briefcase, FileText, Users, Clock, Package,
    CreditCard, Monitor, Shuffle, Database, FileSearch, Shield, HeartCrack,
    Languages, Lock, Mail, MessageSquare, Map, Plane, Cloud, Bot, AlertCircle,
    Globe, UserSearch, TrendingUp, CalendarClock, ShieldAlert, UserCheck,
    DollarSign, UserPlus, Calendar, PenTool, HelpCircle, Presentation,
    ClipboardList, Zap, BarChart2, ArrowUpRight, PlusCircle, Activity,
    Sparkles, Wrench
} from "lucide-react";
import { AgentFormData } from "./types";
import { Input } from "@/components/ui/input";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";

interface StepCapabilitiesProps {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
}

const fetcher = (url: string) => fetch(url).then((res) => res.json());

// ─────────── SKILL ICON / COLOR MAPS ───────────

const SKILL_ICONS: Record<string, React.ReactNode> = {
    "web-research": <Globe className="h-5 w-5 text-white" />,
    "lead-research": <UserSearch className="h-5 w-5 text-white" />,
    "competitor-analysis": <Search className="h-5 w-5 text-white" />,
    "market-intelligence": <TrendingUp className="h-5 w-5 text-white" />,
    "email-composer": <Mail className="h-5 w-5 text-white" />,
    "sms-messaging": <MessageSquare className="h-5 w-5 text-white" />,
    "follow-up-scheduler": <CalendarClock className="h-5 w-5 text-white" />,
    "objection-handler": <ShieldAlert className="h-5 w-5 text-white" />,
    "multi-language": <Languages className="h-5 w-5 text-white" />,
    "lead-qualifier": <UserCheck className="h-5 w-5 text-white" />,
    "deal-manager": <DollarSign className="h-5 w-5 text-white" />,
    "customer-profiler": <UserPlus className="h-5 w-5 text-white" />,
    "appointment-booker": <Calendar className="h-5 w-5 text-white" />,
    "content-writer": <PenTool className="h-5 w-5 text-white" />,
    "document-generator": <FileText className="h-5 w-5 text-white" />,
    "faq-builder": <HelpCircle className="h-5 w-5 text-white" />,
    "presentation-creator": <Presentation className="h-5 w-5 text-white" />,
    "sop-generator": <ClipboardList className="h-5 w-5 text-white" />,
    "task-dispatcher": <Zap className="h-5 w-5 text-white" />,
    "campaign-manager": <BarChart2 className="h-5 w-5 text-white" />,
    "data-entry": <Database className="h-5 w-5 text-white" />,
    "escalation-router": <ArrowUpRight className="h-5 w-5 text-white" />,
    "custom-skill-creator": <PlusCircle className="h-5 w-5 text-white" />,
    "event-triggers": <Activity className="h-5 w-5 text-white" />,
    "default": <Sparkles className="h-5 w-5 text-white" />,
};

const SKILL_COLORS: Record<string, string> = {
    "Research": "bg-blue-600",
    "Communication": "bg-violet-600",
    "Sales": "bg-emerald-600",
    "Content": "bg-amber-600",
    "Workflow": "bg-rose-600",
    "Custom": "bg-gray-600",
    "default": "bg-slate-500",
};

const CATEGORY_ICONS: Record<string, string> = {
    "Research": "🔍",
    "Communication": "💬",
    "Sales": "📊",
    "Content": "📄",
    "Workflow": "🛠️",
    "Custom": "✨",
};

// ─────────── WORKER ICON / COLOR MAPS (existing) ───────────

const WORKER_ICONS: Record<string, React.ReactNode> = {
    "job-search": <Briefcase className="h-5 w-5 text-white" />,
    "lead-research": <Users className="h-5 w-5 text-white" />,
    "content-writer": <FileText className="h-5 w-5 text-white" />,
    "sales-outreach": <Users className="h-5 w-5 text-white" />,
    "faq-resolution": <MessageSquare className="h-5 w-5 text-white" />,
    "meeting-coordination": <Clock className="h-5 w-5 text-white" />,
    "hr-onboarding": <Users className="h-5 w-5 text-white" />,
    "order-status": <Package className="h-5 w-5 text-white" />,
    "payment-billing": <CreditCard className="h-5 w-5 text-white" />,
    "it-support": <Monitor className="h-5 w-5 text-white" />,
    "intelligent-routing": <Shuffle className="h-5 w-5 text-white" />,
    "data-entry": <Database className="h-5 w-5 text-white" />,
    "document-processing": <FileSearch className="h-5 w-5 text-white" />,
    "content-moderation": <Shield className="h-5 w-5 text-white" />,
    "sentiment-escalation": <HeartCrack className="h-5 w-5 text-white" />,
    "translation-localization": <Languages className="h-5 w-5 text-white" />,
    "compliance-risk": <Lock className="h-5 w-5 text-white" />,
    "email-worker": <Mail className="h-5 w-5 text-white" />,
    "weather-worker": <Cloud className="h-5 w-5 text-white" />,
    "map-worker": <Map className="h-5 w-5 text-white" />,
    "sms-messaging": <MessageSquare className="h-5 w-5 text-white" />,
    "flight-tracker": <Plane className="h-5 w-5 text-white" />,
    "openclaw": <Bot className="h-5 w-5 text-white" />,
    "default": <Hammer className="h-5 w-5 text-white" />,
};

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
    "map-worker": "bg-emerald-500",
    "openclaw": "bg-indigo-600",
    "default": "bg-gray-500",
};


// ─────────── OPENCLAW INSTANCE SELECTOR ───────────

function OpenClawInstanceSelector({ formData, setFormData }: StepCapabilitiesProps) {
    const { data: integrations } = useSWR("/api/agent/integrations", fetcher);
    const openClawIntegration = integrations?.find((i: any) => i.provider === 'openclaw');

    const params = useParams();
    const workspaceId = params?.workspaceId as string;

    const { data: instances } = useSWR(
        workspaceId ? `/api/workers/instances?workspace_id=${workspaceId}` : null,
        fetcher
    );

    if (!openClawIntegration || !openClawIntegration.is_active) {
        return (
            <div className="text-sm text-red-600 bg-red-50 p-3 rounded border border-red-200">
                OpenClaw integration is not active. Please enable it in the Integrations page first.
            </div>
        );
    }

    if (!instances || !Array.isArray(instances) || instances.length === 0) {
        return (
            <div className="text-sm text-yellow-700 bg-yellow-50 p-3 rounded border border-yellow-200">
                No OpenClaw instances found. Please provision a worker in Settings &apos;AI Workers&apos;.
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {instances.map((instance: any) => (
                    <div
                        key={instance.id}
                        onClick={() => setFormData(prev => ({ ...prev, openClawInstanceId: instance.id }))}
                        className={`
                            cursor-pointer p-3 rounded-lg border flex flex-col gap-1 transition-all
                            ${formData.openClawInstanceId === instance.id
                                ? 'bg-indigo-100 border-indigo-500 ring-1 ring-indigo-500'
                                : 'bg-white border-indigo-100 hover:border-indigo-300'
                            }
                        `}
                    >
                        <div className="font-semibold text-sm text-indigo-950 flex justify-between items-center gap-2 min-w-0">
                            <span className="truncate">{instance.name}</span>
                            {!instance.is_external && <span className="text-[10px] bg-purple-100 text-purple-700 px-1.5 rounded shrink-0">Cloud</span>}
                        </div>
                        <div className="text-xs text-indigo-600/80 truncate">
                            {instance.status}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}


// ─────────── SKILLS TAB ───────────

function SkillsTab({ formData, setFormData }: StepCapabilitiesProps) {
    const params = useParams();
    const agentId = params?.agentId as string;
    const { data: skills, isLoading } = useSWR("/api/skills", fetcher);
    // Use agentId from params for consistent fetching
    const { data: agentSkills } = useSWR(
        agentId && agentId !== "new" ? `/api/skills/agent/${agentId}` : null,
        fetcher
    );
    const [searchQuery, setSearchQuery] = useState("");
    const [hasInitialized, setHasInitialized] = useState(false);

    const workspaceId = params?.workspaceId as string;

    // Initialize enabledSkillIds from agent's existing skills
    useEffect(() => {
        // We only initialize once from the server to avoid overwriting user's local selections
        if (agentSkills && Array.isArray(agentSkills) && !hasInitialized) {
            const ids = agentSkills.map((s: any) => s.id);
            setFormData(prev => {
                // If the user hasn't made any selections yet (empty array or undefined)
                // or if we are just loading the existing agent for the first time
                if (!prev.enabledSkillIds || prev.enabledSkillIds.length === 0) {
                    return { ...prev, enabledSkillIds: ids };
                }
                return prev;
            });
            setHasInitialized(true);
        }
    }, [agentSkills, hasInitialized, setFormData]);

    const handleToggleSkill = (skillId: string) => {
        setFormData(prev => {
            const current = new Set(prev.enabledSkillIds || []);
            if (current.has(skillId)) {
                current.delete(skillId);
            } else {
                current.add(skillId);
            }
            return { ...prev, enabledSkillIds: Array.from(current) };
        });

        // Persist toggle to backend if editing existing agent
        if (agentId && agentId !== "new") {
            const isEnabled = !(formData.enabledSkillIds || []).includes(skillId);
            fetch(`/api/skills/agent/${agentId}/toggle/${skillId}?enabled=${isEnabled}&workspaceId=${workspaceId}`, {
                method: "POST",
            }).catch(console.error);
        }
    };

    const handleSelectAllCategory = (categorySkills: any[]) => {
        setFormData(prev => {
            const current = new Set(prev.enabledSkillIds || []);
            const allSelected = categorySkills.every(s => current.has(s.id));
            if (allSelected) {
                categorySkills.forEach(s => current.delete(s.id));
            } else {
                categorySkills.forEach(s => current.add(s.id));
            }
            return { ...prev, enabledSkillIds: Array.from(current) };
        });
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    const safeSkills = Array.isArray(skills) ? skills : [];
    const filteredSkills = safeSkills.filter((s: any) =>
        s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.description?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Group by category
    const grouped = filteredSkills.reduce((acc: any, s: any) => {
        const cat = s.category || "Custom";
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(s);
        return acc;
    }, {});

    // Sort categories in preferred order
    const categoryOrder = ["Research", "Communication", "Sales", "Content", "Workflow", "Custom"];
    const sortedCategories = Object.keys(grouped).sort(
        (a, b) => (categoryOrder.indexOf(a) === -1 ? 99 : categoryOrder.indexOf(a)) -
            (categoryOrder.indexOf(b) === -1 ? 99 : categoryOrder.indexOf(b))
    );

    return (
        <div className="space-y-5">
            {/* Search */}
            <div className="flex items-center justify-between gap-4">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search skills..."
                        className="pl-9"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <div className="text-sm text-muted-foreground">
                    {formData.enabledSkillIds?.length || 0} of {safeSkills.length} enabled
                </div>
            </div>

            <ScrollArea className="h-[550px] pr-4">
                <div className="space-y-6">
                    {sortedCategories.map(category => {
                        const items = grouped[category];
                        const emoji = CATEGORY_ICONS[category] || "📦";
                        const allSelected = items.every((s: any) => formData.enabledSkillIds?.includes(s.id));
                        const colorClass = SKILL_COLORS[category] || SKILL_COLORS["default"];

                        return (
                            <div key={category} className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <h3 className="font-semibold text-primary flex items-center gap-2">
                                        <span>{emoji}</span> {category}
                                        <Badge variant="outline" className="text-[10px] ml-1">{items.length}</Badge>
                                    </h3>
                                    <button
                                        onClick={() => handleSelectAllCategory(items)}
                                        className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                                    >
                                        {allSelected ? "Disable All" : "Enable All"}
                                    </button>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                    {items.map((skill: any) => {
                                        const isSelected = formData.enabledSkillIds?.includes(skill.id);
                                        const icon = SKILL_ICONS[skill.slug] || SKILL_ICONS["default"];

                                        return (
                                            <div
                                                key={skill.id}
                                                onClick={() => handleToggleSkill(skill.id)}
                                                className={`
                                                    relative p-4 rounded-xl border transition-all cursor-pointer
                                                    hover:shadow-md hover:border-slate-300
                                                    ${isSelected
                                                        ? 'border-green-500 bg-green-50/50 shadow-sm ring-1 ring-green-500/50'
                                                        : 'border-slate-100 bg-white shadow-sm'
                                                    }
                                                `}
                                            >
                                                {isSelected && (
                                                    <div className="absolute top-2 right-2 text-green-700 bg-green-100 px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase">
                                                        On
                                                    </div>
                                                )}
                                                <div className="flex items-center gap-2.5 mb-2">
                                                    <div className={`p-2 rounded-lg shrink-0 ${colorClass}`}>
                                                        {icon}
                                                    </div>
                                                    <h4 className="font-semibold text-sm text-slate-900 leading-tight">
                                                        {skill.name}
                                                    </h4>
                                                </div>
                                                <p className="text-xs text-slate-500 leading-relaxed line-clamp-2">
                                                    {skill.description}
                                                </p>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </ScrollArea>
        </div>
    );
}


// ─────────── WORKERS TAB (existing logic) ───────────

function WorkersTab({ formData, setFormData }: StepCapabilitiesProps) {
    const { data: templates, isLoading } = useSWR("/api/workers/templates", fetcher);
    const [searchQuery, setSearchQuery] = useState("");

    const handleToggleWorker = (slug: string) => {
        setFormData(prev => {
            const current = new Set(prev.allowedWorkerTypes || []);
            if (current.has(slug)) {
                current.delete(slug);
            } else {
                current.add(slug);
            }
            return { ...prev, allowedWorkerTypes: Array.from(current) };
        });
    };

    const handleSelectAll = (category?: string) => {
        if (!templates) return;
        setFormData(prev => {
            const current = new Set(prev.allowedWorkerTypes || []);
            const targets = templates.filter((t: any) => !category || t.category === category);
            const allSelected = targets.every((t: any) => current.has(t.slug));
            if (allSelected) {
                targets.forEach((t: any) => current.delete(t.slug));
            } else {
                targets.forEach((t: any) => current.add(t.slug));
            }
            return { ...prev, allowedWorkerTypes: Array.from(current) };
        });
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    const safeTemplates = Array.isArray(templates) ? templates : [];
    const filteredTemplates = safeTemplates.filter((t: any) =>
        t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.description?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const groupedTemplates = filteredTemplates.reduce((acc: any, t: any) => {
        const cat = t.category || "General";
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(t);
        return acc;
    }, {});

    return (
        <div className="space-y-5">
            <div className="flex items-center justify-between gap-4">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search workers..."
                        className="pl-9"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <div className="text-sm text-muted-foreground">
                    {formData.allowedWorkerTypes?.length || 0} enabled
                </div>
            </div>

            <ScrollArea className="h-[550px] pr-4">
                <div className="space-y-6">
                    {Object.entries(groupedTemplates).map(([category, items]: [string, any]) => (
                        <div key={category} className="space-y-3">
                            <div className="flex items-center justify-between">
                                <h3 className="font-semibold capitalize text-primary">
                                    {category} Agents
                                </h3>
                                <button
                                    onClick={() => handleSelectAll(category)}
                                    className="text-xs text-blue-600 hover:text-blue-800"
                                >
                                    {items.every((t: any) => formData.allowedWorkerTypes?.includes(t.slug)) ? 'Disable All' : 'Enable All'}
                                </button>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {items.map((template: any) => {
                                    const isSelected = formData.allowedWorkerTypes?.includes(template.slug);
                                    const icon = WORKER_ICONS[template.slug] || WORKER_ICONS["default"];
                                    const colorClass = WORKER_COLORS[template.slug] || WORKER_COLORS["default"];

                                    return (
                                        <div
                                            key={template.id}
                                            onClick={() => handleToggleWorker(template.slug)}
                                            className={`
                                                relative p-5 rounded-2xl border transition-all cursor-pointer
                                                hover:shadow-lg hover:border-slate-300
                                                ${isSelected
                                                    ? 'border-green-500 bg-white shadow-md ring-1 ring-green-500'
                                                    : 'border-slate-100 bg-white shadow-sm'
                                                }
                                                ${template.slug === 'openclaw' ? 'md:col-span-2' : ''}
                                            `}
                                        >
                                            {isSelected && (
                                                <div className="absolute bottom-3 right-3 text-green-700 bg-green-100 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase">
                                                    Enabled
                                                </div>
                                            )}
                                            <div className="flex items-center gap-3 mb-3">
                                                <div className={`p-2.5 rounded-xl shrink-0 ${colorClass}`}>
                                                    {icon}
                                                </div>
                                                <div className="min-w-0">
                                                    <h4 className="font-bold text-base text-slate-900 leading-tight">
                                                        {template.name}
                                                    </h4>
                                                    <Badge variant="secondary" className="mt-1 text-[10px] font-normal text-slate-500 bg-slate-100 border-0">
                                                        {category}
                                                    </Badge>
                                                </div>
                                            </div>
                                            <p className="text-sm text-slate-500 leading-relaxed line-clamp-2 mb-3">
                                                {template.description}
                                            </p>
                                            <div className="pt-3 border-t border-slate-50">
                                                <p className="text-[11px] text-slate-400">
                                                    Dispatch: <span className="italic">&quot;Help me with...&quot;</span>
                                                </p>
                                            </div>
                                            {/* OPENCLAW CONFIGURATION */}
                                            {template.slug === 'openclaw' && isSelected && (
                                                <div className="mt-4 pt-4 border-t border-slate-100" onClick={(e) => e.stopPropagation()}>
                                                    <div className="bg-indigo-50/50 rounded-lg p-3 border border-indigo-100">
                                                        <h5 className="text-xs font-semibold text-indigo-900 mb-2 flex items-center gap-1">
                                                            <Bot className="h-3 w-3" /> Worker Instance
                                                        </h5>
                                                        <OpenClawInstanceSelector formData={formData} setFormData={setFormData} />
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            </ScrollArea>
        </div>
    );
}


// ─────────── MAIN COMPONENT ───────────

export function StepCapabilities({ formData, setFormData }: StepCapabilitiesProps) {
    const [activeTab, setActiveTab] = useState<"skills" | "workers">("skills");

    const tabs = [
        { id: "skills" as const, label: "Skills", icon: <Sparkles className="h-4 w-4" />, count: formData.enabledSkillIds?.length || 0 },
        { id: "workers" as const, label: "AI Workers", icon: <Wrench className="h-4 w-4" />, count: formData.allowedWorkerTypes?.length || 0 },
    ];

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader className="pb-4">
                    <CardTitle className="flex items-center gap-2">
                        <Hammer className="h-5 w-5 text-blue-600" />
                        Agent Capabilities
                    </CardTitle>
                    <CardDescription>
                        {formData.agentType === "personal"
                            ? "All capabilities are enabled by default for personal agents. You can still customize below."
                            : "Configure which skills and AI tools this agent can use."
                        }
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {formData.agentType === "personal" && (
                        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 flex items-start gap-3">
                            <Sparkles className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0" />
                            <div>
                                <h4 className="text-sm font-semibold text-purple-900 mb-1">Personal Agent — All Capabilities Active</h4>
                                <p className="text-sm text-purple-700">
                                    Your personal agent has web browsing, weather, flights, maps, and all other tools enabled by default.
                                    You can disable specific ones below if you prefer.
                                </p>
                            </div>
                        </div>
                    )}
                    {/* Tab Bar */}
                    <div className="flex gap-1 p-1 bg-slate-100 rounded-lg">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`
                                    flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-md
                                    text-sm font-medium transition-all
                                    ${activeTab === tab.id
                                        ? 'bg-white text-slate-900 shadow-sm'
                                        : 'text-slate-500 hover:text-slate-700'
                                    }
                                `}
                            >
                                {tab.icon}
                                {tab.label}
                                {tab.count > 0 && (
                                    <Badge variant="secondary" className="ml-1 text-[10px] h-5 min-w-[20px] justify-center bg-blue-100 text-blue-700 border-0">
                                        {tab.count}
                                    </Badge>
                                )}
                            </button>
                        ))}
                    </div>

                    {/* Tab Content */}
                    {activeTab === "skills" && <SkillsTab formData={formData} setFormData={setFormData} />}
                    {activeTab === "workers" && <WorkersTab formData={formData} setFormData={setFormData} />}
                </CardContent>
            </Card>

            <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-blue-900 mb-1">💡 Pro Tip</h4>
                <p className="text-sm text-blue-700">
                    {activeTab === "skills"
                        ? "Skills define what this agent knows how to do during conversations — like booking appointments, researching leads, or drafting emails."
                        : "AI Workers are background agents that handle tasks independently. Only enable the ones relevant to this agent's role."
                    }
                </p>
            </div>
        </div>
    );
}
