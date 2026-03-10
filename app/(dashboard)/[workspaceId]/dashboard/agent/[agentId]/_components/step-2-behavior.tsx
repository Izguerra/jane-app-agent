
"use client";

import { useState } from "react";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ShieldCheck, Sparkles, Loader2 } from "lucide-react";
import { AgentFormData } from "./types";

interface Step2Props {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
}

export function Step2BehaviorRules({ formData, setFormData }: Step2Props) {
    const [isEnhancing, setIsEnhancing] = useState(false);

    const handleChange = (field: keyof AgentFormData, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
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
        <div className="space-y-8">
            <div className="space-y-4">
                <div className="flex items-center gap-2 text-indigo-600 mb-2">
                    <ShieldCheck className="w-5 h-5" />
                    <h3 className="text-lg font-semibold">Core Identity & Guardrails</h3>
                </div>

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
            </div>

            <div className="space-y-4 pt-4 border-t">
                <div className="flex items-center justify-between">
                    <div>
                        <Label className="text-base">Creativity Level</Label>
                        <p className="text-sm text-muted-foreground">Adjust how creative vs. factual the agent should be.</p>
                    </div>
                    <span className="text-sm font-medium">{formData.creativityLevel}%</span>
                </div>
                <Slider
                    value={[formData.creativityLevel]}
                    onValueChange={(val) => handleChange("creativityLevel", val[0])}
                    max={100}
                    step={1}
                />
            </div>

            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <div>
                        <Label className="text-base">Response Length</Label>
                        <p className="text-sm text-muted-foreground">Concise vs. Detailed responses.</p>
                    </div>
                    <span className="text-sm font-medium">{formData.responseLength}%</span>
                </div>
                <Slider
                    value={[formData.responseLength]}
                    onValueChange={(val) => handleChange("responseLength", val[0])}
                    max={100}
                    step={1}
                />
            </div>

            <div className="space-y-4">
                <div>
                    <Label className="text-base mb-2 block">Conversation Style</Label>
                    <Select
                        value={formData.conversationStyle}
                        onValueChange={(val) => handleChange("conversationStyle", val)}
                    >
                        <SelectTrigger>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="professional">Professional & Formal</SelectItem>
                            <SelectItem value="friendly">Friendly & Casual</SelectItem>
                            <SelectItem value="empathetic">Empathetic & Supportive</SelectItem>
                            <SelectItem value="enthusiastic">Enthusiastic & High Energy</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <div className="flex items-center justify-between py-4 border-t">
                <div>
                    <Label className="text-base">Proactive Follow-ups</Label>
                    <p className="text-sm text-muted-foreground">Allow the agent to ask clarifying questions.</p>
                </div>
                <Switch
                    checked={formData.proactiveFollowups}
                    onCheckedChange={(val) => handleChange("proactiveFollowups", val)}
                />
            </div>

            <div className="space-y-4 py-4 border-t">
                <div className="flex items-center justify-between">
                    <div>
                        <Label className="text-base">Custom Behavior Rules</Label>
                        <p className="text-sm text-muted-foreground">Define specific actions for keywords or sentiments.</p>
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                            const newRules = [...(formData.intentRules || []), { intent: '', action: '' }];
                            handleChange("intentRules", newRules);
                        }}
                    >
                        + Add Rule
                    </Button>
                </div>

                <div className="space-y-3">
                    {(formData.intentRules || []).map((rule, idx) => (
                        <div key={idx} className="flex gap-2 items-start p-3 bg-gray-50 rounded-lg border">
                            <div className="grid gap-2 flex-1">
                                <div className="flex gap-2">
                                    <Input
                                        value={rule.intent}
                                        onChange={(e) => {
                                            const newRules = [...(formData.intentRules || [])];
                                            newRules[idx].intent = e.target.value;
                                            handleChange("intentRules", newRules);
                                        }}
                                        placeholder="e.g. 'refund', 'cancel'"
                                        className="flex-1"
                                    />
                                </div>
                                <Input
                                    value={rule.action}
                                    onChange={(e) => {
                                        const newRules = [...(formData.intentRules || [])];
                                        newRules[idx].action = e.target.value;
                                        handleChange("intentRules", newRules);
                                    }}
                                    placeholder="Instruction for agent (e.g. 'Transfer to human')"
                                />
                            </div>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-muted-foreground hover:text-destructive"
                                onClick={() => {
                                    const newRules = (formData.intentRules || []).filter((_, i) => i !== idx);
                                    handleChange("intentRules", newRules);
                                }}
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-trash-2 h-4 w-4"><path d="M3 6h18" /><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" /><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" /><line x1="10" x2="10" y1="11" y2="17" /><line x1="14" x2="14" y1="11" y2="17" /></svg>
                            </Button>
                        </div>
                    ))}
                    {(formData.intentRules || []).length === 0 && (
                        <div className="text-center py-4 text-sm text-muted-foreground border-2 border-dashed rounded-lg">
                            No rules defined. Click "Add Rule" to handle specific scenarios.
                        </div>
                    )}
                </div>
            </div>

            <div className="flex items-center justify-between py-4 border-t">
                <div>
                    <Label className="text-base">Auto-Escalate to Human</Label>
                    <p className="text-sm text-muted-foreground">Automatically transfer if sentiment is negative.</p>
                </div>
                <Switch
                    checked={formData.autoEscalate}
                    onCheckedChange={(val) => handleChange("autoEscalate", val)}
                />
            </div>

            {formData.autoEscalate && (
                <div className="space-y-4 pl-4 border-l-2 border-blue-100">
                    <div className="space-y-2">
                        <Label>Handoff Message</Label>
                        <Input
                            value={formData.handoffMessage}
                            onChange={(e) => handleChange("handoffMessage", e.target.value)}
                            placeholder="I'll connect you with a human agent..."
                        />
                    </div>
                    <div className="space-y-2">
                        <Label>Notification Email</Label>
                        <Input
                            value={formData.notificationEmail}
                            onChange={(e) => handleChange("notificationEmail", e.target.value)}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
