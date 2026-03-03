"use client";

import { useState, useEffect } from "react";
import useSWR from "swr";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AgentFormData } from "../../_components/types";
import { Step1Identity } from "../_components/step-1-identity";
import { Step2Context } from "../_components/step-2-context";
import { Step3Avatar } from "../_components/step-3-avatar";
import { Step4BrowserConnection } from "../_components/step-4-browser-connection";
import { Step5BrowserCapabilities } from "../_components/step-5-browser-capabilities";
import { Step6GuardrailsDeployment } from "../_components/step-6-guardrails-deployment";
import { toast } from "sonner";
import { Bot, ArrowLeft, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

import { LivePreview } from "../../_components/live-preview";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function OpenClawAgentWizardPage() {
    const params = useParams();
    const router = useRouter();
    const workspaceId = params?.workspaceId as string;
    const agentId = params?.agentId as string;
    const isNew = agentId === "new";

    const [isSaving, setIsSaving] = useState(false);
    const [currentStep, setCurrentStep] = useState(1);
    const [voiceToken, setVoiceToken] = useState<{ token: string; url: string } | null>(null);

    const [formData, setFormData] = useState<AgentFormData>({
        name: "My Browser agent",
        language: "en",
        voice_id: "alloy",
        avatar: "",
        avatarUrl: "",
        avatarFile: null,
        primaryFunction: "",
        conversationStyle: "helpful",
        welcomeGreeting: "I'm ready to help you browse the web. What task should I perform?",
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
        existingKbUrls: [],
        useTavusAvatar: false,
        allowedWorkerTypes: ["openclaw"],
        creativityLevel: 50,
        responseLength: 50,
        proactiveFollowups: true,
        intentRules: [],
        handoffMessage: "I'm having trouble with this task. Can you help me?",
        notificationEmail: "",
        slackWebhook: "",
        autoEscalate: false,
        deploymentChannel: "web_widget",
        accentColor: "#3B82F6",
        widgetIcon: "chat",
        widgetIconUrl: "",
        widgetIconFile: null,
        widgetPosition: "bottom_right",
        removeBranding: false,
        whitelistedDomains: "",
        isActive: false,
        personalPreferences: "",
        user_email: "",
        user_phone: ""
    });

    const { data: agent, isLoading } = useSWR(
        !isNew ? [`/api/agents?workspace_id=${workspaceId}`, agentId] : null,
        async ([url, id]) => {
            const res = await fetch(url);
            const agents = await res.json();
            return agents.find((a: any) => a.id === id);
        },
        {
            revalidateOnFocus: false, // Don't refetch on window focus
            revalidateOnReconnect: false, // Don't refetch on reconnect
        }
    );

    // Workspace correction: If the URL workspace doesn't match the agent's real workspace, redirect
    useEffect(() => {
        if (agent && agent.workspace_id && agent.workspace_id !== workspaceId) {
            console.log(`REDIRECT: Agent belongs to ${agent.workspace_id}, but URL has ${workspaceId}. Redirecting...`);
            router.replace(`/${agent.workspace_id}/dashboard/agent/open-claw/${agentId}`);
        }
    }, [agent, workspaceId, agentId, router]);

    // Track if we've already initialized from server data
    const [hasInitialized, setHasInitialized] = useState(false);

    useEffect(() => {
        // Only populate form data once on initial load, not on every SWR revalidation
        if (agent && !isNew && !hasInitialized) {
            setFormData(prev => ({
                ...prev,
                name: agent.name || "",
                language: agent.language || "en",
                voice_id: agent.voice_id || "alloy",
                welcomeGreeting: agent.welcome_message || "",
                primaryFunction: agent.primary_function || "",
                conversationStyle: agent.conversation_style || "helpful",
                businessName: agent.business_name || "",
                websiteUrl: agent.website_url || "",
                businessDescription: agent.description || "",
                email: agent.email || "",
                phone: agent.phone || "",
                address: agent.address || "",
                allowedWorkerTypes: agent.allowed_worker_types || ["openclaw"],
                whitelistedDomains: agent.whitelisted_domains || "",
                isActive: agent.is_active,
                // OpenClaw specific fields from settings
                personalPreferences: agent.personal_preferences || agent.personalPreferences || "",
                user_email: agent.user_email || "",
                user_phone: agent.user_phone || "",
                openClawInstanceId: agent.open_claw_instance_id || agent.openClawInstanceId,
                tavusReplicaId: agent.tavus_replica_id,
                useTavusAvatar: !!agent.tavus_replica_id,
                avatarVoiceId: agent.avatar_voice_id || "alloy",
            }));
            setHasInitialized(true);
        }
    }, [agent, isNew, hasInitialized]);





    const handleNext = () => {
        if (currentStep < 6) setCurrentStep(currentStep + 1);
    };

    const handleBack = () => {
        if (currentStep > 1) setCurrentStep(currentStep - 1);
    };

    const handleSave = async (redirect = true) => {
        setIsSaving(true);
        try {
            const updatedWorkerTypes = Array.from(new Set([...formData.allowedWorkerTypes, "openclaw"]));

            const payload = {
                name: formData.name,
                voice_id: formData.voice_id,
                language: formData.language,
                welcome_message: formData.welcomeGreeting,
                description: formData.businessDescription,
                is_active: formData.isActive,
                allowed_worker_types: updatedWorkerTypes,

                // Personalization
                business_name: formData.businessName,
                email: formData.email,
                phone: formData.phone,
                address: formData.address,
                services: formData.services,
                personal_preferences: formData.personalPreferences,
                user_email: formData.user_email,
                user_phone: formData.user_phone,

                // OpenClaw specific
                open_claw_instance_id: formData.openClawInstanceId,
                tavus_replica_id: formData.tavusReplicaId,
                avatar_voice_id: formData.avatarVoiceId || formData.voice_id || "alloy",
                use_tavus_avatar: formData.useTavusAvatar,

                // Guardrails & Deployment
                whitelisted_domains: formData.whitelistedDomains,
                handoff_message: formData.handoffMessage,
                deployment_channel: formData.deploymentChannel,
                max_depth: parseInt((formData as any).maxDepth || "10", 10),

                // Other fields from AgentUpdate
                workspace_id: workspaceId,
                agent_type: "openclaw",
            };

            const res = await fetch(isNew ? "/api/agents" : `/api/agents/${agentId}`, {
                method: isNew ? "POST" : "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error(`Failed to ${isNew ? "create" : "update"} agent`);

            toast.success(`OpenClaw Agent ${isNew ? "created" : "updated"} successfully!`);
            if (redirect) router.push(`/${workspaceId}/dashboard/agent`);
        } catch (e: any) {
            toast.error(e.message || "An error occurred");
        } finally {
            setIsSaving(false);
        }
    };

    if (isLoading && !isNew) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
            </div>
        );
    }

    const TOTAL_STEPS = 6;
    const progress = (currentStep / TOTAL_STEPS) * 100;

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
                            <div className="text-sm text-muted-foreground">STEP {currentStep} OF {TOTAL_STEPS}</div>
                            <h1 className="text-2xl font-bold">
                                {currentStep === 1 && "Identity & Branding"}
                                {currentStep === 2 && "Job Context"}
                                {currentStep === 3 && "Browser Connection"}
                                {currentStep === 4 && "Browser Skills"}
                                {currentStep === 5 && "Guardrails & Safety"}
                                {currentStep === 6 && "Visual Identity (Avatar)"}
                            </h1>
                            <p className="text-sm text-muted-foreground mt-1">
                                {currentStep === 1 && "Name your agent, define its identity, and set up your knowledge base."}
                                {currentStep === 2 && "Define the context and rules for the browser agent."}
                                {currentStep === 3 && "Connect to a browser session."}
                                {currentStep === 4 && "Define what skills the agent has access to."}
                                {currentStep === 5 && "Set up guardrails and deployment settings."}
                                {currentStep === 6 && "Review and customize the avatar."}
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-sm text-muted-foreground mr-2">{Math.round(progress)}% Completed</div>

                        {/* Top Actions */}
                        {currentStep < 6 ? (
                            <div className="flex gap-2">
                                <Button variant="outline" size="sm" onClick={() => handleSave(false)} disabled={isSaving}>
                                    {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                    Save Draft
                                </Button>
                                <Button size="sm" onClick={handleNext}>
                                    Next Step →
                                </Button>
                            </div>
                        ) : (
                            <div className="flex gap-2">
                                <Button variant="outline" size="sm" onClick={() => handleSave(false)} disabled={isSaving}>
                                    {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                    Save Draft
                                </Button>
                                <Button size="sm" onClick={() => handleSave(true)} disabled={isSaving}>
                                    {isSaving ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Active & Deploying...
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
                        <Card className="border-none shadow-xl bg-white/80 backdrop-blur-sm rounded-3xl overflow-hidden min-h-[500px]">
                            <CardContent className="p-8">
                                {currentStep === 1 && <Step1Identity formData={formData} setFormData={setFormData} agentId={!isNew ? agentId : undefined} />}
                                {currentStep === 2 && <Step2Context formData={formData} setFormData={setFormData} />}
                                {currentStep === 3 && <Step4BrowserConnection formData={formData} setFormData={setFormData} />}
                                {currentStep === 4 && <Step5BrowserCapabilities formData={formData} setFormData={setFormData} />}
                                {currentStep === 5 && <Step6GuardrailsDeployment formData={formData} setFormData={setFormData} />}
                                {currentStep === 6 && <Step3Avatar formData={formData} setFormData={setFormData} />}
                            </CardContent>
                        </Card>
                    </div>

                    <div className="lg:col-span-1">
                        <LivePreview
                            formData={formData}
                            agentId={!isNew ? agentId : undefined}
                            workspaceId={workspaceId}
                            voiceToken={voiceToken}
                            setFormData={setFormData}
                            unavailable={currentStep !== 6}
                        />
                        {/* Live Preview Rendered */}
                    </div>
                </div>

                {/* Footer Navigation */}
                <div className="max-w-7xl mx-auto mt-8 flex justify-between">
                    <Button
                        variant="outline"
                        onClick={handleBack}
                        disabled={currentStep === 1}
                    >
                        Back
                    </Button>
                    {currentStep < 6 ? (
                        <div className="flex gap-2">
                            <Button variant="outline" onClick={() => handleSave(false)} disabled={isSaving}>
                                {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                Save Draft
                            </Button>
                            <Button onClick={handleNext}>
                                Next Step →
                            </Button>
                        </div>
                    ) : (
                        <div className="flex gap-2">
                            <Button variant="outline" onClick={() => handleSave(false)} disabled={isSaving}>
                                {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                Save Draft
                            </Button>
                            <Button onClick={() => handleSave(true)} disabled={isSaving}>
                                {isSaving ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Active & Deploying...
                                    </>
                                ) : (
                                    "Deploy Agent"
                                )}
                            </Button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
