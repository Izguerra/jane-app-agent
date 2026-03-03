"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ShieldAlert, Globe, Repeat, Layout } from "lucide-react";
import { AgentFormData } from "../../_components/types";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface Step6Props {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
}

export function Step6GuardrailsDeployment({ formData, setFormData }: Step6Props) {
    const handleChange = (field: keyof AgentFormData, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    return (
        <div className="space-y-8">
            {/* Browser Guardrails */}
            <div className="space-y-6">
                <div className="flex items-center gap-2">
                    <ShieldAlert className="h-5 w-5 text-red-600" />
                    <h3 className="font-semibold text-lg">Safety & Guardrails</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <Label htmlFor="domains" className="flex items-center gap-2">
                            <Globe className="h-4 w-4" /> Allowed Domains
                        </Label>
                        <CardDescription>
                            Comma-separated list of domains the agent is allowed to visit. Leave empty for unrestricted access.
                        </CardDescription>
                        <Input
                            id="domains"
                            value={formData.whitelistedDomains}
                            onChange={(e) => handleChange("whitelistedDomains", e.target.value)}
                            placeholder="e.g. google.com, amazon.com, delta.com"
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="depth" className="flex items-center gap-2">
                            <Repeat className="h-4 w-4" /> Max Navigation Depth
                        </Label>
                        <CardDescription>
                            The maximum number of sub-pages/clicks the agent can perform per task.
                        </CardDescription>
                        <Select
                            value={(formData as any).maxDepth || "10"}
                            onValueChange={(val) => handleChange("maxDepth" as any, val)}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Select depth" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="3">3 (Strict/Safe)</SelectItem>
                                <SelectItem value="5">5 (Standard)</SelectItem>
                                <SelectItem value="10">10 (Deep Research)</SelectItem>
                                <SelectItem value="20">20 (Unrestricted)</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>
            </div>

            {/* Deployment Channel */}
            <div className="space-y-6 pt-6 border-t">
                <div className="flex items-center gap-2">
                    <Layout className="h-5 w-5 text-blue-600" />
                    <h3 className="font-semibold text-lg">Deployment Channel</h3>
                </div>

                <div className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="channel">Select Primary Channel</Label>
                        <Select
                            value={formData.deploymentChannel}
                            onValueChange={(val) => handleChange("deploymentChannel", val)}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Select channel" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="web_widget">Web Widget (Dashboard or Website)</SelectItem>
                                <SelectItem value="sms">SMS / WhatsApp (Mobile Assistant)</SelectItem>
                                <SelectItem value="api">API Only (Headless)</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="handoff">Handoff Message</Label>
                        <CardDescription>
                            What should the agent say if it gets stuck or needs human intervention?
                        </CardDescription>
                        <Textarea
                            id="handoff"
                            value={formData.handoffMessage}
                            onChange={(e) => handleChange("handoffMessage", e.target.value)}
                            placeholder="I'm having trouble with this website. Would you like to take over the browser?"
                            rows={2}
                        />
                    </div>
                </div>
            </div>

            <div className="bg-slate-50 border border-slate-200 p-6 rounded-2xl">
                <h4 className="font-bold text-slate-900 mb-2 underline decoration-indigo-500 underline-offset-4">Review Complete</h4>
                <p className="text-sm text-slate-600 leading-relaxed">
                    You've configured the identity, personal context, and safety boundaries for your OpenClaw agent. Click 'Create Agent' to finalize and start browsing.
                </p>
            </div>
        </div>
    );
}
