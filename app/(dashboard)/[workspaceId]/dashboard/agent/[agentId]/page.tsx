
"use client";

import { Button } from "@/components/ui/button";
import { Loader2, ArrowLeft } from "lucide-react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { use, useState, useEffect } from "react";
import useSWR, { mutate } from "swr";
import { toast } from "sonner";

import { StepTypeSelection } from "./_components/step-0-type-selection";
import { Step1ConfigureAgent } from "./_components/step-1-configure";
import { StepAvatar } from "./_components/step-avatar";
import { StepCapabilities } from "./_components/step-capabilities";
import { Step2BehaviorRules } from "./_components/step-2-behavior";
import { Step3Deployment } from "./_components/step-3-deployment";
import { LivePreview } from "../_components/live-preview";
import { safeParse } from "./_components/utils";
import { AgentFormData } from "./_components/types";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface PageProps {
    params: Promise<{ workspaceId: string; agentId: string }>;
    searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default function AgentWizardPage(props: PageProps) {
    const params = use(props.params);
    const searchParams = use(props.searchParams);
    
    const router = useRouter();
    const workspaceId = params.workspaceId;
    const agentId = params.agentId;
    const isNew = agentId === "new";
    const agentType = typeof searchParams.type === 'string' ? searchParams.type : undefined;

    const [isMounted, setIsMounted] = useState(false);
    const [currentStep, setCurrentStep] = useState(isNew ? 0 : 1);
    const [isSaving, setIsSaving] = useState(false);

    // Voice token state - generated after save to ensure correct context
    const [voiceToken, setVoiceToken] = useState<{ token: string; url: string } | null>(null);

    // Form state for all steps
    const [formData, setFormData] = useState<AgentFormData>({
        // Step 1: Configure Your Agent
        name: "",
        voice_id: "alloy",  // Default voice
        language: "en",
        avatar: "HB",
        avatarUrl: "",
        avatarFile: null,
        primaryFunction: "",
        conversationStyle: "professional",
        welcomeGreeting: "",
        businessName: "",
        websiteUrl: "",
        businessDescription: "",
        email: "",
        phone: "",
        address: "",
        services: "",
        hoursOfOperation: "",
        faqItems: [],
        refUrls: [],
        kbFiles: [],

        // Step 2: Capabilities
        allowedWorkerTypes: [],
        enabledSkillIds: [],

        // Step 1 additions: Avatar
        anamPersonaId: "",
        tavusReplicaId: "",
        avatarProvider: undefined,

        // Step 3: Behavior & Rules
        soul: "",
        creativityLevel: 50,
        responseLength: 50,
        proactiveFollowups: true,
        intentRules: [],
        handoffMessage: "",
        notificationEmail: "",
        slackWebhook: "",
        autoEscalate: false,

        // Step 4: Integration & Deployment
        deploymentChannel: "web_widget",
        accentColor: "#3B82F6",
        widgetIcon: "chat",
        widgetIconUrl: "",
        widgetIconFile: null,
        widgetPosition: "bottom_right",
        removeBranding: false,
        whitelistedDomains: "",
        isActive: true,
        existingKbUrls: [],
        useTavusAvatar: false,
        avatarVoiceId: "alloy",
        // Agent Type (default to business for existing agents)
        agentType: undefined,
    });

    useEffect(() => {
        setIsMounted(true);
    }, []);

    const { data: agent, isLoading } = useSWR(
        isMounted && !isNew ? `/api/agents/${agentId}?workspaceId=${workspaceId}` : null,
        fetcher,
        {
            revalidateOnFocus: false, // Don't refetch on window focus
            revalidateOnReconnect: false, // Don't refetch on reconnect
        }
    );

    // Workspace correction: If the URL workspace doesn't match the agent's real workspace, redirect
    useEffect(() => {
        if (agent && agent.workspace_id && agent.workspace_id !== workspaceId) {
            console.log(`REDIRECT: Agent belongs to ${agent.workspace_id}, but URL has ${workspaceId}. Redirecting...`);
            router.replace(`/${agent.workspace_id}/dashboard/agent/${agentId}`);
        }
    }, [agent, workspaceId, agentId, router]);

    // Track if we've already initialized from server data
    const [hasInitialized, setHasInitialized] = useState(false);

    // Fetch skills for initialization
    const { data: agentSkills } = useSWR(
        isMounted && !isNew ? `/api/skills/agent/${agentId}` : null,
        fetcher
    );

    // Fetch workspace settings for new agents
    const { data: workspaceSettings } = useSWR(
        isMounted && isNew ? `/api/agent-settings` : null,
        fetcher
    );

    useEffect(() => {
        // Option 1: Load Existing Agent (only once on initial load)
        if (agent && !isNew && !hasInitialized && agentSkills !== undefined) {
            // Loading agent data silently
            setFormData(prev => ({
                ...prev,
                name: agent.name || "",
                language: agent.language || "en",
                voice_id: agent.voice_id || "alloy",
                welcomeGreeting: agent.welcome_message || "",
                // Core & Settings Mapping
                primaryFunction: agent.primary_function || "",
                conversationStyle: agent.conversation_style || "professional",
                businessName: agent.business_name || "",
                websiteUrl: agent.website_url || "",
                businessDescription: agent.description || "",
                email: agent.email || "",
                phone: agent.phone || "",
                address: agent.address || "",
                services: typeof agent.services === 'object' ? JSON.stringify(agent.services, null, 2) : (agent.services || ""),
                hoursOfOperation: typeof agent.hours_of_operation === 'object' ? JSON.stringify(agent.hours_of_operation, null, 2) : (agent.hours_of_operation || ""),
                faqItems: safeParse(agent.faq, []),
                refUrls: safeParse(agent.reference_urls, []),
                existingKbUrls: agent.kb_documents_urls || [],

                // Capabilities
                allowedWorkerTypes: agent.allowed_worker_types || [],

                // Rules
                soul: agent.soul || "",
                creativityLevel: agent.creativity_level ?? 50,
                responseLength: agent.response_length ?? 50,
                proactiveFollowups: agent.proactive_followups ?? true,
                intentRules: safeParse(agent.intent_rules, []),
                handoffMessage: agent.handoff_message || "",
                notificationEmail: agent.notification_email || "",
                slackWebhook: agent.slack_webhook || "",
                autoEscalate: agent.auto_escalate ?? false,

                // Widget
                deploymentChannel: agent.deployment_channel || "web_widget",
                accentColor: agent.accent_color || "#3B82F6",
                widgetIcon: agent.widget_icon || "chat",
                widgetIconUrl: agent.widget_icon_url || "",
                widgetPosition: agent.widget_position || "bottom_right",
                removeBranding: agent.remove_branding ?? false,
                whitelistedDomains: agent.whitelisted_domains || "",
                avatarUrl: agent.avatar || "",
                isActive: agent.is_active,
                // Map settings - check both root and settings object for compatibility
                tavusReplicaId: agent.tavus_replica_id || agent.settings?.tavus_replica_id,
                anamPersonaId: agent.anam_persona_id || agent.settings?.anam_persona_id,
                avatarProvider: agent.avatar_provider || agent.settings?.avatar_provider || (agent.tavus_replica_id ? 'tavus' : (agent.anam_persona_id ? 'anam' : undefined)),
                avatarVoiceId: agent.avatar_voice_id || agent.settings?.avatar_voice_id || "alloy",
                useTavusAvatar: agent.use_tavus_avatar !== undefined
                    ? agent.use_tavus_avatar
                    : (agent.settings?.use_tavus_avatar !== undefined
                        ? agent.settings.use_tavus_avatar
                        : !!(agent.tavus_replica_id || agent.settings?.tavus_replica_id || agent.anam_persona_id || agent.settings?.anam_persona_id)),
                openClawInstanceId: agent.open_claw_instance_id || agent.settings?.open_claw_instance_id,
                // Agent Type & Personal Profile
                agentType: agent.agent_type || agent.settings?.agent_type || "business",
                ownerName: agent.owner_name || agent.settings?.owner_name || "",
                location: agent.personal_location || agent.settings?.personal_location || "",
                timezone: agent.personal_timezone || agent.settings?.personal_timezone || "",
                favoriteFoods: agent.favorite_foods || agent.settings?.favorite_foods || "",
                favoriteRestaurants: agent.favorite_restaurants || agent.settings?.favorite_restaurants || "",
                favoriteMusic: agent.favorite_music || agent.settings?.favorite_music || "",
                favoriteActivities: agent.favorite_activities || agent.settings?.favorite_activities || "",
                otherInterests: agent.other_interests || agent.settings?.other_interests || "",
                likes: agent.personal_likes || agent.settings?.personal_likes || "",
                dislikes: agent.personal_dislikes || agent.settings?.personal_dislikes || "",
                // Initialize skills from separate fetch
                enabledSkillIds: agentSkills?.map((s: any) => s.id) || [],
            }));
            setHasInitialized(true);
        }
        // Option 2: Pre-fill New Agent with Workspace Settings
        else if (workspaceSettings && isNew && !hasInitialized) {
            console.log("DEBUG: Pre-filling workspace settings", workspaceSettings);
            setFormData(prev => ({
                ...prev,
                businessName: workspaceSettings.business_name || "",
                websiteUrl: workspaceSettings.website_url || "",
                businessDescription: workspaceSettings.description || "",
                email: workspaceSettings.email || "",
                phone: workspaceSettings.phone || "",
                address: workspaceSettings.address || "",
                services: workspaceSettings.services || "",
                hoursOfOperation: workspaceSettings.hours_of_operation || "",
                // Pre-configure Humanoid specific settings if requested
                ...(agentType === "humanoid" ? {
                    useTavusAvatar: true,
                    name: "Humanoid Assistant",
                    primaryFunction: "Interactive Video Assistant"
                } : {})
            }));
            setHasInitialized(true);
        }
    }, [agent, workspaceSettings, agentSkills, isNew, hasInitialized]);

    const TOTAL_STEPS = (isNew && currentStep === 0) ? 6 : 5;
    const displayStep = currentStep === 0 ? 0 : currentStep;

    const handleNext = async () => {
        // Auto-save draft before moving to next step (skip token fetch for speed)
        try {
            await saveAgent(false, false, true);
            if (currentStep < TOTAL_STEPS) setCurrentStep(currentStep + 1);
        } catch (error) {
            // Error is handled in saveAgent, but we prevent step change
            console.error("Failed to save before next step:", error);
        }
    };

    const handleBack = async () => {
        // Auto-save draft before moving back (skip token fetch for speed)
        try {
            await saveAgent(false, false, true);
            if (currentStep > 1) setCurrentStep(currentStep - 1);
        } catch (error) {
            console.error("Failed to save before back step:", error);
            // We allow going back even if save fails
            if (currentStep > 1) setCurrentStep(currentStep - 1);
        }
    };

    const saveAgent = async (redirectToList: boolean = true, shouldPublish: boolean = false, skipTokenFetch: boolean = false) => {
        if (!workspaceId || workspaceId === "undefined") {
            toast.error("System Error: Workspace ID is missing. Please refresh.");
            return;
        }

        setIsSaving(true);
        try {
            // Helper to upload file (Calls Backend for Vectorization)
            const uploadFile = async (file: File) => {
                const fd = new FormData();
                fd.append('file', file);
                // Use backend endpoint to trigger immediate indexing
                // Note: /api/ prefix is rewritten to backend URL by next.config.ts if strictly /api/
                // But here we want to hit the backend router at: /api/workspaces/{id}/knowledge-base/upload
                // (Prefix in router is empty for this endpoint? No, we added @router.post("/{workspace_id}...") in knowledge_base.py)
                // knowledge_base.py has prefix="/api/workspaces" on the router itself.
                // So Full URL: /api/workspaces/${workspaceId}/knowledge-base/upload
                const res = await fetch(`/api/workspaces/${workspaceId}/knowledge-base/upload`, { method: 'POST', body: fd });
                if (!res.ok) throw new Error('Upload & Indexing failed');
                const data = await res.json();
                return data.url;
            };

            // 1. Upload Avatar if new file exists
            let finalAvatarUrl = formData.avatarUrl;
            if (formData.avatarFile) {
                try {
                    finalAvatarUrl = await uploadFile(formData.avatarFile);
                } catch (e) {
                    toast.error("Failed to upload avatar");
                    console.error(e);
                }
            }

            // 2. Upload Widget Icon if new file exists
            let finalWidgetIconUrl = formData.widgetIconUrl;
            if (formData.widgetIconFile) {
                try {
                    finalWidgetIconUrl = await uploadFile(formData.widgetIconFile);
                } catch (e) {
                    toast.error("Failed to upload widget icon");
                    console.error(e);
                }
            }

            // 3. Upload KB Documents
            const kbDocUrls: string[] = [];
            if (formData.kbFiles.length > 0) {
                try {
                    const uploads = await Promise.all(
                        formData.kbFiles.map(file => uploadFile(file))
                    );
                    kbDocUrls.push(...uploads);
                } catch (e) {
                    toast.error("Failed to upload documents");
                    console.error(e);
                }
            }

            // 4. Construct Payload
            const data = {
                // Core
                name: formData.name,
                description: formData.businessDescription, // Map to description
                voice_id: formData.voice_id || "alloy",
                language: formData.language,
                allowed_worker_types: formData.allowedWorkerTypes,
                prompt_template: `You are ${formData.name}, a ${formData.conversationStyle} assistant. ${formData.businessDescription}`,
                welcome_message: formData.welcomeGreeting,
                // Preserve existing is_active status, only force to true when explicitly publishing
                is_active: shouldPublish ? true : formData.isActive,

                agent_type: formData.agentType || (isNew ? (agentType || "standard") : undefined),

                // Personal Agent Profile (stored in settings JSON)
                owner_name: formData.ownerName || undefined,
                personal_location: formData.location || undefined,
                personal_timezone: formData.timezone || undefined,
                favorite_foods: formData.favoriteFoods || undefined,
                favorite_restaurants: formData.favoriteRestaurants || undefined,
                favorite_music: formData.favoriteMusic || undefined,
                favorite_activities: formData.favoriteActivities || undefined,
                other_interests: formData.otherInterests || undefined,
                personal_likes: formData.likes || undefined,
                personal_dislikes: formData.dislikes || undefined,
                tavus_replica_id: formData.tavusReplicaId,
                anam_persona_id: formData.anamPersonaId,
                avatar_provider: formData.avatarProvider,
                avatar_voice_id: formData.avatarVoiceId,
                use_tavus_avatar: formData.useTavusAvatar,
                open_claw_instance_id: formData.openClawInstanceId,

                // Extended Fields (Settings)
                avatar: finalAvatarUrl || formData.avatar,

                primary_function: formData.primaryFunction,
                conversation_style: formData.conversationStyle,
                creativity_level: Number(formData.creativityLevel || 50),
                response_length: Number(formData.responseLength || 50),
                proactive_followups: Boolean(formData.proactiveFollowups),

                // KB
                business_name: formData.businessName || "",
                website_url: formData.websiteUrl || "",
                email: formData.email || "",
                phone: formData.phone || "",
                address: formData.address || "",
                services: formData.services || "",
                hours_of_operation: formData.hoursOfOperation || "",
                faq: JSON.stringify(formData.faqItems || []),
                reference_urls: JSON.stringify(formData.refUrls || []),
                kb_documents_urls: [...(formData.existingKbUrls || []), ...kbDocUrls],

                // Rules
                soul: formData.soul || "",
                intent_rules: JSON.stringify(formData.intentRules || []),
                handoff_message: formData.handoffMessage || "",
                notification_email: formData.notificationEmail || "",
                slack_webhook: formData.slackWebhook || "",
                auto_escalate: Boolean(formData.autoEscalate),

                // Widget
                deployment_channel: formData.deploymentChannel || "web_widget",
                accent_color: formData.accentColor || "#3B82F6",
                widget_icon: formData.widgetIcon,
                widget_icon_url: finalWidgetIconUrl,
                widget_position: formData.widgetPosition,
                remove_branding: formData.removeBranding,
                whitelisted_domains: formData.whitelistedDomains,
            };

            const response = await fetch(isNew ? "/api/agents" : `/api/agents/${agentId}`, {
                method: isNew ? "POST" : "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error("Save Agent Failed:", response.status, errorText);
                throw new Error(`Failed to save agent: ${response.status} ${errorText}`);
            }

            const savedAgent = await response.json();
            // Precisely mutate the singular agent key to trigger revalidation
            await mutate(`/api/agents/${agentId}?workspaceId=${workspaceId}`);
            // Also mutate the plural key just in case other pages need it
            await mutate(`/api/agents?workspace_id=${workspaceId}`);

            // Clear uploaded files from state to prevent duplicates on subsequent saves
            setFormData(prev => ({
                ...prev,
                kbFiles: [],
                avatarFile: null,
                widgetIconFile: null
            }));

            // Removed eager voice token fetching to prevent creating false "call" logs
            // The LivePreview component handles fetching its own token when switched to voice mode.

            // Bulk sync skills for the agent
            const finalAgentId = savedAgent.id || agentId;
            if (hasInitialized && finalAgentId && formData.enabledSkillIds) {
                try {
                    await fetch(`/api/skills/agent/${finalAgentId}/bulk?workspaceId=${workspaceId}`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ enabled_skill_ids: formData.enabledSkillIds })
                    });
                    mutate(`/api/skills/agent/${finalAgentId}`);
                } catch (e) {
                    console.error("Failed to bulk sync skills:", e);
                }
            }

            if (redirectToList) {
                toast.success("Agent deployed successfully!");
                router.push(`/${workspaceId}/dashboard/agent`);
            } else {
                toast.success("Draft saved successfully!");
                if (isNew && savedAgent.id) {
                    router.push(`/${workspaceId}/dashboard/agent/${savedAgent.id}`);
                } else {
                    // Just refresh data without page reload if existing
                    await mutate(isNew ? "/api/agents" : `/api/agents/${agentId}`);
                }
            }
        } catch (error) {
            toast.error("Failed to save agent");
            console.error(error);
        } finally {
            setIsSaving(false);
        }
    };
    if (!isMounted || (!isNew && isLoading)) {
        return (
            <div className="max-w-7xl mx-auto py-8 flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    const progress = currentStep === 0 ? 0 : (currentStep / 5) * 100;

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white border-b px-8 py-4">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="icon" asChild>
                            <Link href={`/${workspaceId}/dashboard/agent`}>
                                <ArrowLeft className="h-4 w-4" />
                            </Link>
                        </Button>
                        <div>
                            <div className="text-sm text-muted-foreground">{currentStep === 0 ? "GET STARTED" : `STEP ${currentStep} OF 5`}</div>
                            <h1 className="text-2xl font-bold">
                                {currentStep === 0 && "Choose Agent Type"}
                                {currentStep === 1 && "Configure Your Agent"}
                                {currentStep === 2 && "Visual Identity (Avatar)"}
                                {currentStep === 3 && "Agent Capabilities"}
                                {currentStep === 4 && "Behavior & Rules"}
                                {currentStep === 5 && "Integration & Deployment"}
                            </h1>
                            <p className="text-sm text-muted-foreground mt-1">
                                {currentStep === 0 && "Select the type of agent you want to build."}
                                {currentStep === 1 && (formData.agentType === "personal" ? "Tell us about yourself so your agent can serve you better." : "Name your agent, define its identity, and set up your knowledge base.")}
                                {currentStep === 2 && "Choose a video avatar for face-to-face interactions."}
                                {currentStep === 3 && "Select the specialized AI tools this agent is authorized to use."}
                                {currentStep === 4 && "Define how your agent handles complex conversations and specific intents."}
                                {currentStep === 5 && "Choose where your agent lives and how it looks to your users."}
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-sm text-muted-foreground mr-2">{Math.round(progress)}% Completed</div>

                        {/* Top Actions */}
                        {currentStep < 5 ? (
                            <div className="flex gap-2">
                                <Button variant="outline" size="sm" onClick={() => saveAgent(false, false)} disabled={isSaving}>
                                    {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                    Save Draft
                                </Button>
                                <Button size="sm" onClick={handleNext}>
                                    Next Step →
                                </Button>
                            </div>
                        ) : (
                            <div className="flex gap-2">
                                <Button variant="outline" size="sm" onClick={() => saveAgent(false, false)} disabled={isSaving}>
                                    {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                    Save Draft
                                </Button>
                                <Button size="sm" onClick={() => saveAgent(true, true)} disabled={isSaving}>
                                    {isSaving ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Deploying...
                                        </>
                                    ) : (
                                        "Deploy Agent"
                                    )}
                                </Button>
                            </div>
                        )}
                    </div>
                </div>
                {/* Progress Bar */}
                <div className="max-w-7xl mx-auto mt-4">
                    <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-blue-600 transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto py-8 px-8">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left: Form Content */}
                    <div className="lg:col-span-2 space-y-6">
                        {currentStep === 0 && (
                            <StepTypeSelection formData={formData} setFormData={setFormData} onSelect={() => setCurrentStep(1)} />
                        )}
                        {currentStep === 1 && (
                            <Step1ConfigureAgent formData={formData} setFormData={setFormData} workspaceId={workspaceId} />
                        )}
                        {currentStep === 2 && (
                            <StepAvatar formData={formData} setFormData={setFormData} />
                        )}
                        {currentStep === 3 && (
                            <StepCapabilities formData={formData} setFormData={setFormData} />
                        )}
                        {currentStep === 4 && (
                            <Step2BehaviorRules formData={formData} setFormData={setFormData} />
                        )}
                        {currentStep === 5 && (
                            <Step3Deployment formData={formData} setFormData={setFormData} agentId={!isNew ? agentId : undefined} />
                        )}
                    </div>

                    {/* Right: Live Preview */}
                    <div className="lg:col-span-1">
                        <LivePreview formData={formData} agentId={!isNew ? agentId : undefined} workspaceId={workspaceId} voiceToken={voiceToken} setFormData={setFormData} />
                    </div>
                </div>

                {/* Navigation */}
                <div className="max-w-7xl mx-auto mt-8 flex justify-between">
                    <Button
                        variant="outline"
                        onClick={handleBack}
                        disabled={currentStep <= 1}
                    >
                        Back
                    </Button>
                    {currentStep < 5 ? (
                        <div className="flex gap-2">
                            <Button variant="outline" onClick={() => saveAgent(false, false)} disabled={isSaving}>
                                {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                Save Draft
                            </Button>
                            <Button onClick={handleNext}>
                                Next Step →
                            </Button>
                        </div>
                    ) : (
                        <div className="flex gap-2">
                            <Button variant="outline" onClick={() => saveAgent(false, false)} disabled={isSaving}>
                                {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                Save Draft
                            </Button>
                            <Button onClick={() => saveAgent(true, true)} disabled={isSaving}>
                                {isSaving ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Deploying...
                                    </>
                                ) : (
                                    "Deploy Agent"
                                )}
                            </Button>
                        </div>
                    )}
                </div>
            </div>
        </div >
    );
}
