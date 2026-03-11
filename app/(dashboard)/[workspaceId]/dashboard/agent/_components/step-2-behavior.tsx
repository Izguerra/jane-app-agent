
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Trash2, Plus, ShieldCheck, Sparkles, Loader2 } from "lucide-react";
import { AgentFormData } from "./types";

interface StepProps {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
}

export function Step2BehaviorRules({ formData, setFormData }: StepProps) {
    const [isEnhancing, setIsEnhancing] = useState(false);

    const handleChange = (field: keyof AgentFormData, value: any) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
    };

    const handleEnhance = async () => {
        if (!formData.soul || formData.soul.trim() === "") return;

        setIsEnhancing(true);
        try {
            const response = await fetch("/api/agents/enhance-soul", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ current_soul: formData.soul })
            });

            if (response.ok) {
                const data = await response.json();
                handleChange("soul", data.enhanced_soul);
            } else {
                console.error("Failed to enhance soul");
            }
        } catch (error) {
            console.error("Error enhancing soul:", error);
        } finally {
            setIsEnhancing(false);
        }
    };

    return (
        <>
            {/* Core Identity & Guardrails */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center">
                            <ShieldCheck className="w-5 h-5 text-indigo-600" />
                        </div>
                        <CardTitle>Core Identity & Guardrails</CardTitle>
                    </div>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Agent Soul Input */}
                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <div>
                                <Label className="text-base">Agent Soul (User-Defined Boundaries)</Label>
                                <p className="text-sm text-muted-foreground">Define what the agent *is*, its ultimate goals, and what it *must never do*. This is inserted at the highest priority in the prompt.</p>
                            </div>
                            <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={handleEnhance}
                                disabled={!formData.soul || formData.soul.trim() === "" || isEnhancing}
                                className="bg-indigo-50 text-indigo-600 hover:bg-indigo-100 border-indigo-200"
                            >
                                {isEnhancing ? (
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                ) : (
                                    <Sparkles className="w-4 h-4 mr-2" />
                                )}
                                {isEnhancing ? "Enhancing..." : "Enhance with AI"}
                            </Button>
                        </div>
                        <Textarea
                            placeholder="e.g., 'You are a high-energy sales assistant. Your main priority is to book demos. Never discuss technical implementation details.'"
                            value={formData.soul || ""}
                            onChange={(e) => handleChange("soul", e.target.value)}
                            className="min-h-[120px]"
                        />
                    </div>

                    {/* System Guardrails Read-only */}
                    <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 mt-4">
                        <div className="flex items-center gap-2 mb-3">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-lock text-slate-500"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                            <h4 className="text-sm font-semibold text-slate-700">Locked System Guardrails</h4>
                        </div>
                        <p className="text-xs text-slate-500 mb-3">These enterprise-grade security rules are permanently enforced on all SupaAgent models to protect your business.</p>
                        <ul className="text-xs text-slate-600 space-y-2 list-disc pl-4">
                            <li><strong>Prompt Injection & Hijacking Protection:</strong> Agent will reject commands like "Ignore previous instructions".</li>
                            <li><strong>Jailbreak & Hypothetical Evasion:</strong> Agent will refuse to roleplay unrestricted AI models (e.g., DAN).</li>
                            <li><strong>Tool & RBAC Enforcement:</strong> Agent operates strictly within authorized tool boundaries.</li>
                            <li><strong>PII & PCI Protection:</strong> Agent will not store or repeat sensitive financial or medical data.</li>
                            <li><strong>Access Control Verification:</strong> Real-world actions require explicit identity verification.</li>
                            <li><strong>Phishing Prevention & Data Minimization:</strong> Malicious link generation and unnecessary data collection are blocked.</li>
                            <li><strong>Internal Data Isolation:</strong> Internal metrics like Customer Lifetime Value are hidden from the user.</li>
                        </ul>
                    </div>
                </CardContent>
            </Card>

            {/* Conversation Logic */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
                            <span className="text-blue-600 text-lg">🎯</span>
                        </div>
                        <CardTitle>Conversation Logic</CardTitle>
                    </div>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Creativity Level */}
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <Label>Creativity Level</Label>
                            <span className="text-sm text-muted-foreground">
                                {formData.creativityLevel < 33 ? "Precise" : formData.creativityLevel < 66 ? "Balanced" : "Creative"}
                            </span>
                        </div>
                        <input
                            type="range"
                            min="0"
                            max="100"
                            value={formData.creativityLevel}
                            onChange={(e) => setFormData({ ...formData, creativityLevel: parseInt(e.target.value) })}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                        />
                        <div className="flex justify-between text-xs text-muted-foreground">
                            <span>Precise</span>
                            <span>Creative</span>
                        </div>
                    </div>

                    {/* Response Length */}
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <Label>Response Length</Label>
                            <span className="text-sm text-muted-foreground">
                                {formData.responseLength < 33 ? "Brief" : formData.responseLength < 66 ? "Concise" : "Detailed"}
                            </span>
                        </div>
                        <input
                            type="range"
                            min="0"
                            max="100"
                            value={formData.responseLength}
                            onChange={(e) => setFormData({ ...formData, responseLength: parseInt(e.target.value) })}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                        />
                        <div className="flex justify-between text-xs text-muted-foreground">
                            <span>Brief</span>
                            <span>Detailed</span>
                        </div>
                    </div>

                    {/* Proactive Follow-ups */}
                    <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="space-y-0.5">
                            <Label className="text-base">Proactive Follow-ups</Label>
                            <p className="text-sm text-muted-foreground">
                                Allow the agent to ask clarifying questions when information is missing.
                            </p>
                        </div>
                        <Switch
                            checked={formData.proactiveFollowups}
                            onCheckedChange={(checked) => setFormData({ ...formData, proactiveFollowups: checked })}
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Intent Routing */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center">
                            <span className="text-purple-600 text-lg">🔀</span>
                        </div>
                        <CardTitle>Intent Routing</CardTitle>
                    </div>
                    <CardDescription>Define special actions for specific user intents.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {formData.intentRules.map((rule, index) => (
                        <div key={index} className="p-4 border rounded-lg space-y-3 bg-gray-50">
                            <div className="flex items-start justify-between gap-2">
                                <div className="flex-1 space-y-3">
                                    <div className="flex items-center gap-2">
                                        <div className="w-6 h-6 rounded bg-green-100 flex items-center justify-center flex-shrink-0">
                                            <span className="text-green-600 text-sm">$</span>
                                        </div>
                                        <div className="flex-1 flex items-center gap-2">
                                            <span className="text-sm font-medium">IF INTENT IS</span>
                                            <Input
                                                value={rule.intent}
                                                onChange={(e) => {
                                                    const newRules = [...formData.intentRules];
                                                    newRules[index].intent = e.target.value;
                                                    setFormData({ ...formData, intentRules: newRules });
                                                }}
                                                placeholder="Pricing Inquiry"
                                                className="flex-1"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 pl-8">
                                        <span className="text-sm font-medium">THEN</span>
                                        <Input
                                            value={rule.action}
                                            onChange={(e) => {
                                                const newRules = [...formData.intentRules];
                                                newRules[index].action = e.target.value;
                                                setFormData({ ...formData, intentRules: newRules });
                                            }}
                                            placeholder="Show pricing card component"
                                            className="flex-1"
                                        />
                                    </div>
                                </div>
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setFormData({
                                        ...formData,
                                        intentRules: formData.intentRules.filter((_, i) => i !== index)
                                    })}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                    ))}

                    <Button
                        type="button"
                        variant="outline"
                        onClick={() => setFormData({
                            ...formData,
                            intentRules: [...formData.intentRules, { intent: "", action: "" }]
                        })}
                        className="w-full"
                    >
                        <Plus className="h-4 w-4 mr-2" />
                        Create New Routing Rule
                    </Button>
                </CardContent>
            </Card>

            {/* Escalation & Handoff */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-orange-100 flex items-center justify-center">
                            <span className="text-orange-600 text-lg">🆘</span>
                        </div>
                        <CardTitle>Escalation & Handoff</CardTitle>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="handoffMessage">Handoff Message</Label>
                        <Textarea
                            id="handoffMessage"
                            value={formData.handoffMessage}
                            onChange={(e) => setFormData({ ...formData, handoffMessage: e.target.value })}
                            placeholder="What the bot says when connecting to a human."
                            rows={3}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="notificationEmail">Notification Email</Label>
                            <Input
                                id="notificationEmail"
                                type="email"
                                value={formData.notificationEmail}
                                onChange={(e) => setFormData({ ...formData, notificationEmail: e.target.value })}
                                placeholder="support@supaagent.com"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="slackWebhook">Slack Webhook URL</Label>
                            <Input
                                id="slackWebhook"
                                type="password"
                                value={formData.slackWebhook}
                                onChange={(e) => setFormData({ ...formData, slackWebhook: e.target.value })}
                                placeholder="••••••••••••••••••"
                            />
                        </div>
                    </div>

                    <div className="flex items-center space-x-2">
                        <input
                            type="checkbox"
                            id="autoEscalate"
                            checked={formData.autoEscalate}
                            onChange={(e) => setFormData({ ...formData, autoEscalate: e.target.checked })}
                            className="h-4 w-4 rounded border-gray-300"
                        />
                        <Label htmlFor="autoEscalate" className="text-sm font-normal cursor-pointer">
                            Auto-escalate after 2 consecutive fallback responses
                        </Label>
                    </div>
                </CardContent>
            </Card>
        </>
    );
}
