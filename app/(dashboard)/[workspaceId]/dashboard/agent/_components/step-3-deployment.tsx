
"use client";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { validateImageFile } from "./utils";
import { AgentFormData } from "./types";

interface StepProps {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
}

export function Step3Deployment({ formData, setFormData }: StepProps) {
    // Dynamic embed code based on settings
    const widgetConfig = {
        id: "agent_123xyz",
        accentColor: formData.accentColor,
        icon: formData.widgetIcon,
        position: formData.widgetPosition,
        ...(formData.removeBranding && { branding: false })
    };

    const embedCode = `<script
  src="https://cdn.supaagent.com/widget.js">
</script>
<script>
  SupaAgent.init(${JSON.stringify(widgetConfig, null, 2)});
</script>`;

    return (
        <>
            {/* Deployment Channels */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
                            <span className="text-blue-600 text-lg">🚀</span>
                        </div>
                        <CardTitle>Deployment Channels</CardTitle>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-3 gap-4">
                        {/* Web Widget */}
                        <button
                            type="button"
                            onClick={() => setFormData({ ...formData, deploymentChannel: "web_widget" })}
                            className={`p-6 border-2 rounded-lg text-center transition-all ${formData.deploymentChannel === "web_widget"
                                ? "border-blue-600 bg-blue-50"
                                : "border-gray-200 hover:border-gray-300"
                                }`}
                        >
                            <div className="w-12 h-12 mx-auto mb-3 bg-blue-100 rounded-lg flex items-center justify-center">
                                <span className="text-2xl">💬</span>
                            </div>
                            <div className="font-medium">Web Widget</div>
                            <div className="text-xs text-muted-foreground mt-1">Embed on your website via snippet.</div>
                            {formData.deploymentChannel === "web_widget" && (
                                <div className="mt-2">
                                    <div className="w-5 h-5 mx-auto bg-blue-600 rounded-full flex items-center justify-center">
                                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                    </div>
                                </div>
                            )}
                        </button>

                        {/* Slack App */}
                        <button
                            type="button"
                            onClick={() => setFormData({ ...formData, deploymentChannel: "slack" })}
                            className={`p-6 border-2 rounded-lg text-center transition-all ${formData.deploymentChannel === "slack"
                                ? "border-blue-600 bg-blue-50"
                                : "border-gray-200 hover:border-gray-300"
                                }`}
                        >
                            <div className="w-12 h-12 mx-auto mb-3 bg-purple-100 rounded-lg flex items-center justify-center">
                                <span className="text-2xl">💼</span>
                            </div>
                            <div className="font-medium">Slack App</div>
                            <div className="text-xs text-muted-foreground mt-1">Connect to internal workspace.</div>
                        </button>

                        {/* WhatsApp */}
                        <button
                            type="button"
                            onClick={() => setFormData({ ...formData, deploymentChannel: "whatsapp" })}
                            className={`p-6 border-2 rounded-lg text-center transition-all ${formData.deploymentChannel === "whatsapp"
                                ? "border-blue-600 bg-blue-50"
                                : "border-gray-200 hover:border-gray-300"
                                }`}
                        >
                            <div className="w-12 h-12 mx-auto mb-3 bg-green-100 rounded-lg flex items-center justify-center">
                                <span className="text-2xl">📱</span>
                            </div>
                            <div className="font-medium">WhatsApp</div>
                            <div className="text-xs text-muted-foreground mt-1">Direct messaging pod.</div>
                        </button>
                    </div>
                </CardContent>
            </Card>

            {/* Widget Appearance - Only show for Web Widget */}
            {formData.deploymentChannel === "web_widget" && (
                <Card>
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center">
                                <span className="text-2xl">🎨</span>
                            </div>
                            <CardTitle>Widget Appearance</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-8">
                        {/* Avatar Settings */}
                        <div className="space-y-3">
                            <Label className="text-base font-semibold">Agent Avatar</Label>
                            <div className="flex items-center gap-4 p-4 border rounded-lg bg-gray-50/50">
                                {/* Avatar Preview */}
                                <div className="w-16 h-16 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold text-xl overflow-hidden shrink-0">
                                    {formData.avatarUrl ? (
                                        <img src={formData.avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
                                    ) : (
                                        formData.avatar
                                    )}
                                </div>

                                <div className="flex-1 space-y-2">
                                    {/* Initials Input */}
                                    <div className="flex items-center gap-2">
                                        <Input
                                            value={formData.avatar}
                                            onChange={(e) => setFormData({ ...formData, avatar: e.target.value.slice(0, 2).toUpperCase() })}
                                            placeholder="HB"
                                            className="w-20 bg-white"
                                            maxLength={2}
                                        />
                                        <span className="text-sm text-muted-foreground">or</span>

                                        {/* Image Upload */}
                                        <label className="cursor-pointer">
                                            <div className="px-4 py-2 border-2 border-dashed bg-white rounded-lg hover:border-blue-600 transition-colors text-sm text-center whitespace-nowrap">
                                                <Upload className="h-4 w-4 inline mr-2" />
                                                Upload Image
                                            </div>
                                            <input
                                                type="file"
                                                accept="image/png,image/jpeg,image/svg+xml"
                                                className="hidden"
                                                onChange={async (e) => {
                                                    const file = e.target.files?.[0];
                                                    if (file) {
                                                        const validation = await validateImageFile(file, {
                                                            maxSizeMB: 2,
                                                            allowedTypes: ['image/png', 'image/jpeg', 'image/svg+xml'],
                                                            recommendedWidth: 200,
                                                            recommendedHeight: 200
                                                        });

                                                        if (!validation.valid) {
                                                            toast.error(validation.error!);
                                                            e.target.value = ''; // Reset input
                                                            return;
                                                        }

                                                        if (validation.warning) {
                                                            toast.warning(validation.warning);
                                                        }

                                                        // Create preview URL
                                                        const url = URL.createObjectURL(file);
                                                        setFormData({ ...formData, avatarUrl: url, avatarFile: file });
                                                    }
                                                }}
                                            />
                                        </label>

                                        {formData.avatarUrl && (
                                            <Button
                                                type="button"
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => setFormData({ ...formData, avatarUrl: "", avatarFile: null })}
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        )}
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        This avatar will be displayed in the chat header and messages.
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-8">
                            {/* Accent Color */}
                            <div className="space-y-3">
                                <Label className="text-base font-semibold">Accent Color</Label>
                                <div className="flex gap-3">
                                    {["#3B82F6", "#8B5CF6", "#10B981", "#000000"].map((color) => (
                                        <button
                                            key={color}
                                            type="button"
                                            onClick={() => setFormData({ ...formData, accentColor: color })}
                                            className={`w-14 h-14 rounded-2xl border-4 transition-all hover:scale-105 ${formData.accentColor === color
                                                ? "border-gray-900 shadow-lg"
                                                : "border-gray-200 hover:border-gray-300"
                                                }`}
                                            style={{ backgroundColor: color }}
                                        />
                                    ))}
                                    <label className="w-14 h-14 rounded-2xl border-4 border-gray-200 hover:border-gray-300 cursor-pointer transition-all hover:scale-105 overflow-hidden">
                                        <input
                                            type="color"
                                            value={formData.accentColor}
                                            onChange={(e) => setFormData({ ...formData, accentColor: e.target.value })}
                                            className="w-full h-full cursor-pointer"
                                            style={{ border: 'none', padding: 0 }}
                                        />
                                    </label>
                                </div>
                            </div>

                            {/* Widget Icon */}
                            <div className="space-y-3">
                                <Label className="text-base font-semibold">Widget Icon</Label>
                                <div className="flex gap-3 flex-wrap">
                                    {[
                                        { id: "chat", icon: "💬" },
                                        { id: "robot", icon: "🤖" },
                                        { id: "support", icon: "🎧" },
                                    ].map((item) => (
                                        <button
                                            key={item.id}
                                            type="button"
                                            onClick={() => setFormData({ ...formData, widgetIcon: item.id, widgetIconUrl: "" })}
                                            className={`w-14 h-14 rounded-2xl border-4 flex items-center justify-center text-2xl transition-all hover:scale-105 ${formData.widgetIcon === item.id && !formData.widgetIconUrl
                                                ? "border-blue-600 bg-blue-50 shadow-lg"
                                                : "border-gray-200 bg-white hover:border-gray-300"
                                                }`}
                                        >
                                            {item.icon}
                                        </button>
                                    ))}

                                    {/* Custom Icon Upload */}
                                    <label className="cursor-pointer">
                                        <div className={`w-14 h-14 rounded-2xl border-4 flex items-center justify-center transition-all hover:scale-105 overflow-hidden ${formData.widgetIconUrl
                                            ? "border-blue-600 bg-blue-50 shadow-lg"
                                            : "border-dashed border-gray-300 hover:border-blue-600"
                                            }`}>
                                            {formData.widgetIconUrl ? (
                                                <img src={formData.widgetIconUrl} alt="Custom icon" className="w-full h-full object-cover" />
                                            ) : (
                                                <Upload className="h-5 w-5 text-gray-400" />
                                            )}
                                        </div>
                                        <input
                                            type="file"
                                            accept="image/png,image/jpeg,image/svg+xml"
                                            className="hidden"
                                            onChange={async (e) => {
                                                const file = e.target.files?.[0];
                                                if (file) {
                                                    const validation = await validateImageFile(file, {
                                                        maxSizeMB: 1,
                                                        allowedTypes: ['image/png', 'image/jpeg', 'image/svg+xml'],
                                                        recommendedWidth: 64,
                                                        recommendedHeight: 64
                                                    });

                                                    if (!validation.valid) {
                                                        toast.error(validation.error!);
                                                        e.target.value = ''; // Reset input
                                                        return;
                                                    }

                                                    if (validation.warning) {
                                                        toast.warning(validation.warning);
                                                    }

                                                    // Create preview URL
                                                    const url = URL.createObjectURL(file);
                                                    setFormData({ ...formData, widgetIconUrl: url, widgetIconFile: file, widgetIcon: "custom" });
                                                }
                                            }}
                                        />
                                    </label>

                                    {formData.widgetIconUrl && (
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => setFormData({ ...formData, widgetIconUrl: "", widgetIconFile: null, widgetIcon: "chat" })}
                                            className="self-center"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    )}
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    Choose an emoji or upload custom icon (PNG, JPG, SVG. Max 1MB. Recommended: 64x64px)
                                </p>
                            </div>
                        </div>

                        {/* Widget Position */}
                        <div className="space-y-3">
                            <Label className="text-base font-semibold">Widget Position</Label>
                            <div className="grid grid-cols-2 gap-3">
                                <button
                                    type="button"
                                    onClick={() => setFormData({ ...formData, widgetPosition: "bottom_right" })}
                                    className={`px-6 py-4 border-4 rounded-2xl text-base font-semibold transition-all ${formData.widgetPosition === "bottom_right"
                                        ? "border-blue-600 bg-blue-50 text-blue-600 shadow-md"
                                        : "border-gray-200 bg-white hover:border-gray-300"
                                        }`}
                                >
                                    Bottom Right
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setFormData({ ...formData, widgetPosition: "bottom_left" })}
                                    className={`px-6 py-4 border-4 rounded-2xl text-base font-semibold transition-all ${formData.widgetPosition === "bottom_left"
                                        ? "border-blue-600 bg-blue-50 text-blue-600 shadow-md"
                                        : "border-gray-200 bg-white hover:border-gray-300"
                                        }`}
                                >
                                    Bottom Left
                                </button>
                            </div>
                        </div>

                        {/* Remove Branding */}
                        <div className="flex items-center justify-between p-6 border-2 rounded-2xl bg-gray-50">
                            <div className="space-y-1">
                                <Label className="text-base font-semibold">Remove "Powered by SupaAgent"</Label>
                                <p className="text-sm text-muted-foreground">
                                    Toggle to remove our branding from the widget.
                                </p>
                            </div>
                            <Switch
                                checked={formData.removeBranding}
                                onCheckedChange={(checked: boolean) => setFormData({ ...formData, removeBranding: checked })}
                            />
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Security & Access */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-orange-100 flex items-center justify-center">
                            <span className="text-orange-600 text-lg">🔒</span>
                        </div>
                        <CardTitle>Security & Access</CardTitle>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="whitelistedDomains">Whitelisted Domains</Label>
                        <Input
                            id="whitelistedDomains"
                            value={formData.whitelistedDomains}
                            onChange={(e) => setFormData({ ...formData, whitelistedDomains: e.target.value })}
                            placeholder="example.com, mysite.org"
                        />
                        <p className="text-xs text-muted-foreground">
                            Only allow the agent to be loaded on these domains. Leave empty to allow all.
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* Embed Code - Only show for Web Widget */}
            {formData.deploymentChannel === "web_widget" && (
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <CardTitle>EMBED CODE</CardTitle>
                            <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                    navigator.clipboard.writeText(embedCode);
                                    toast.success("Copied to clipboard!");
                                }}
                            >
                                Copy
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm font-mono">
                            {embedCode}
                        </pre>
                        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-2">
                            <div className="text-blue-600 mt-0.5">ℹ️</div>
                            <p className="text-sm text-blue-900">
                                Changes to appearance will be reflected immediately on your live widget.
                            </p>
                        </div>
                    </CardContent>
                </Card>
            )}
        </>
    );
}
