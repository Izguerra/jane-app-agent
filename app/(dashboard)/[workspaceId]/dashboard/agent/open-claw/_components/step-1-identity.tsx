"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AgentFormData } from "../../_components/types";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { toast } from "sonner";
import { VoiceSelector } from "../../_components/voice-selector";

interface Step1Props {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
    agentId?: string;
}

export function Step1Identity({ formData, setFormData, agentId }: Step1Props) {
    const handleChange = (field: keyof AgentFormData, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const embedCode = `<script
  src="https://cdn.supaagent.com/widget.js"
  data-agent-id="${agentId || 'YOUR_AGENT_ID'}"
  data-accent-color="${formData.accentColor || '#3B82F6'}"
  data-position="bottom_right"
></script>`;

    return (
        <div className="space-y-6">
            <div className="space-y-4">
                <div className="space-y-2">
                    <Label htmlFor="name">Agent Name</Label>
                    <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => handleChange("name", e.target.value)}
                        placeholder="e.g. Browser Pro"
                    />
                </div>

                <div className="space-y-2">
                    <Label htmlFor="voice_id">Agent Voice</Label>
                    <VoiceSelector
                        voiceId={formData.voice_id}
                        onVoiceChange={(val) => handleChange("voice_id", val)}
                    />
                </div>

                <div className="space-y-2">
                    <Label htmlFor="language">Language</Label>
                    <Select
                        value={formData.language}
                        onValueChange={(val) => handleChange("language", val)}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder="Select language" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="en">English</SelectItem>
                            <SelectItem value="es">Spanish</SelectItem>
                            <SelectItem value="fr">French</SelectItem>
                            <SelectItem value="de">German</SelectItem>
                            <SelectItem value="it">Italian</SelectItem>
                            <SelectItem value="pt">Portuguese</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                {/* Branding Section */}
                <div className="space-y-4 pt-4 border-t">
                    <h3 className="text-sm font-medium text-slate-900">Widget Branding</h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="accentColor">Accent Color</Label>
                            <div className="flex gap-2">
                                <Input
                                    id="accentColor"
                                    type="color"
                                    className="w-12 h-10 p-1 cursor-pointer"
                                    value={formData.accentColor}
                                    onChange={(e) => handleChange("accentColor", e.target.value)}
                                />
                                <Input
                                    value={formData.accentColor}
                                    onChange={(e) => handleChange("accentColor", e.target.value)}
                                    placeholder="#3B82F6"
                                    className="flex-1 font-mono"
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="widgetIcon">Widget Icon</Label>
                            <Select
                                value={formData.widgetIcon}
                                onValueChange={(val) => handleChange("widgetIcon", val)}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select icon" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="chat">Chat Bubble</SelectItem>
                                    <SelectItem value="bot">Robot Head</SelectItem>
                                    <SelectItem value="sparkles">Sparkles</SelectItem>
                                    <SelectItem value="user">User</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="branding">Branding</Label>
                        <div className="flex items-center space-x-2 border p-3 rounded-lg bg-slate-50">
                            <input
                                type="checkbox"
                                id="removeBranding"
                                checked={formData.removeBranding}
                                onChange={(e) => handleChange("removeBranding", e.target.checked)}
                                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-600"
                            />
                            <Label htmlFor="removeBranding" className="font-normal cursor-pointer">
                                Remove "Powered by SupaAgent" branding (Pro)
                            </Label>
                        </div>
                    </div>
                </div>

                {/* Embed Code Section */}
                <div className="space-y-4 pt-4 border-t">
                    <h3 className="text-sm font-medium text-slate-900">Embed Code</h3>
                    <p className="text-sm text-muted-foreground">Copy and paste this code into your website's HTML body.</p>
                    <div className="relative">
                        <pre className="p-4 rounded-lg bg-slate-950 text-slate-50 overflow-x-auto text-xs">
                            <code>{embedCode}</code>
                        </pre>
                    </div>
                </div>
            </div>

            <div className="space-y-2 pt-4 border-t">
                <Label htmlFor="persona">Browsing Persona & Primary Goal</Label>
                <CardDescription className="mb-2">
                    Describe the main purpose of this agent. This will be the foundational instruction for all browser tasks.
                </CardDescription>
                <Textarea
                    id="persona"
                    value={formData.primaryFunction}
                    onChange={(e) => handleChange("primaryFunction", e.target.value)}
                    placeholder="e.g. Always look for the cheapest flights on Expedia and Kayak, then summarize the top 3 options."
                    rows={4}
                />
            </div>
        </div>
    );
}
