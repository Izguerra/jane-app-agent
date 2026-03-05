
"use client";

import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Upload, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AgentFormData } from "./types";

interface Step3Props {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
    agentId?: string;
}

export function Step3Deployment({ formData, setFormData, agentId }: Step3Props) {
    const handleChange = (field: keyof AgentFormData, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    return (
        <div className="space-y-8">
            <div className="space-y-2">
                <Label>Deployment Channel</Label>
                <Select
                    value={formData.deploymentChannel}
                    onValueChange={(val) => handleChange("deploymentChannel", val)}
                >
                    <SelectTrigger>
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="web_widget">Web Widget</SelectItem>
                        <SelectItem value="whatsapp">WhatsApp (Coming Soon)</SelectItem>
                        <SelectItem value="instagram">Instagram (Coming Soon)</SelectItem>
                    </SelectContent>
                </Select>
            </div>



            <div className="space-y-4">
                <Label className="text-base font-semibold">Widget Customization</Label>

                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Label>Accent Color</Label>
                        <div className="flex gap-2">
                            <Input
                                type="color"
                                className="w-12 h-10 p-1"
                                value={formData.accentColor}
                                onChange={(e) => handleChange("accentColor", e.target.value)}
                            />
                            <Input
                                value={formData.accentColor}
                                onChange={(e) => handleChange("accentColor", e.target.value)}
                            />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label>Widget Position</Label>
                        <Select
                            value={formData.widgetPosition}
                            onValueChange={(val) => handleChange("widgetPosition", val)}
                        >
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="bottom_right">Bottom Right</SelectItem>
                                <SelectItem value="bottom_left">Bottom Left</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="col-span-2 space-y-2">
                        <Label>Widget Icon</Label>
                        <div className="flex items-center gap-4">
                            <div className="h-12 w-12 rounded-full border flex items-center justify-center overflow-hidden bg-white">
                                {formData.widgetIconUrl ? (
                                    <img src={formData.widgetIconUrl} alt="Icon" className="h-full w-full object-contain" />
                                ) : (
                                    <div className="text-muted-foreground text-xs text-center p-1">No Icon</div>
                                )}
                            </div>
                            <div className="flex-1">
                                <Input
                                    type="file"
                                    accept="image/*"
                                    onChange={(e) => {
                                        if (e.target.files?.[0]) {
                                            const file = e.target.files[0];
                                            const url = URL.createObjectURL(file);
                                            setFormData(prev => ({
                                                ...prev,
                                                widgetIconFile: file,
                                                widgetIconUrl: url
                                            }));
                                        }
                                    }}
                                />
                                <p className="text-xs text-muted-foreground mt-1">
                                    Upload a custom icon for the chat bubble (SVG or PNG recommended).
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex items-center justify-between py-4 border-t">
                <div>
                    <Label className="text-base">Remove Branding</Label>
                    <p className="text-sm text-muted-foreground">Hide "Powered by SupaAgent"</p>
                </div>
                <Switch
                    checked={formData.removeBranding}
                    onCheckedChange={(val) => handleChange("removeBranding", val)}
                />
            </div>

            <div className="space-y-2">
                <Label>Whitelisted Domains</Label>
                <Input
                    value={formData.whitelistedDomains}
                    onChange={(e) => handleChange("whitelistedDomains", e.target.value)}
                    placeholder="example.com, mybusiness.com"
                />
                <p className="text-xs text-muted-foreground">Comma separated list of domains where the widget is allowed to load.</p>
            </div>

            <div className="space-y-4 py-4 border-t">
                <Label className="text-base font-semibold">Embed Code</Label>
                <p className="text-sm text-muted-foreground">Copy and paste this code into your website's HTML body.</p>
                <div className="bg-slate-950 text-slate-50 p-4 rounded-lg font-mono text-sm overflow-x-auto relative group">
                    <code className="whitespace-pre-wrap">
                        {`<script
  src="https://cdn.supaagent.com/widget.js"
  data-agent-id="${agentId || 'YOUR_AGENT_ID'}"
  data-accent-color="${formData.accentColor}"
  data-position="${formData.widgetPosition}"
  ${formData.removeBranding ? 'data-remove-branding="true"' : ''}
></script>`}
                    </code>
                </div>
                {!agentId && (
                    <p className="text-xs text-yellow-600 bg-yellow-50 p-2 rounded border border-yellow-200">
                        Note: Save your agent to generate a valid Agent ID for this code.
                    </p>
                )}
            </div>

        </div>
    );
}
