"use client";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useState, useEffect } from "react";
import useSWR, { mutate } from "swr";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface VoiceOption {
    id: string;
    name: string;
}

interface LanguageOption {
    id: string;
    name: string;
}

interface AgentOptions {
    voices: VoiceOption[];
    languages: LanguageOption[];
}

export default function AgentSettingsPage() {
    // 1. Force client-side rendering only
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
    }, []);

    // 2. Fetch data only when mounted
    const { data: settings, error: settingsError } = useSWR(
        isMounted ? "/api/agent/settings" : null,
        fetcher,
        {
            revalidateOnFocus: false,
            suspense: false // Explicitly disable suspense
        }
    );

    const { data: options, error: optionsError } = useSWR<AgentOptions>(
        isMounted ? "/api/agent/settings/options" : null,
        fetcher,
        {
            revalidateOnFocus: false,
            suspense: false
        }
    );

    const [isSaving, setIsSaving] = useState(false);

    async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsSaving(true);

        const formData = new FormData(event.currentTarget);
        const data = {
            voice_id: formData.get("voice_id"),
            language: formData.get("language"),
            prompt_template: formData.get("prompt_template"),
            is_active: formData.get("is_active") === "on",
        };

        try {
            const response = await fetch("/api/agent/settings", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                throw new Error("Failed to update agent settings");
            }

            await mutate("/api/agent/settings");
            toast.success("Agent settings updated successfully", {
                duration: 2000,
            });
        } catch (error) {
            toast.error("Failed to update agent settings");
            console.error(error);
        } finally {
            setIsSaving(false);
        }
    }

    // 3. Return generic loading state during SSR or hydration
    if (!isMounted) {
        return (
            <div className="max-w-2xl mx-auto py-8 flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (settingsError || optionsError) {
        return <div className="p-8 text-red-500">Failed to load agent settings.</div>;
    }

    // 4. Loading state for data fetching
    if (!settings || !options) {
        return (
            <div className="max-w-2xl mx-auto py-8">
                <div className="animate-pulse space-y-6">
                    <div className="h-8 bg-muted rounded w-1/4"></div>
                    <div className="h-[400px] bg-muted rounded-xl"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-2xl mx-auto py-8">
            <h1 className="text-2xl font-bold mb-6">Agent Settings</h1>

            <Card className="card-modern">
                <CardHeader>
                    <CardTitle>Voice & Personality</CardTitle>
                    <CardDescription>Customize how your agent sounds and behaves.</CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={onSubmit} className="space-y-6">

                        <div className="flex items-center justify-between p-4 rounded-lg glass">
                            <div className="space-y-0.5">
                                <Label className="text-base">Agent Active</Label>
                                <p className="text-sm text-muted-foreground">Enable or disable the AI agent.</p>
                            </div>
                            <Switch name="is_active" defaultChecked={settings.is_active} />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Voice</Label>
                                <Select name="voice_id" defaultValue={settings.voice_id || "alloy"}>
                                    <SelectTrigger className="">
                                        <SelectValue placeholder="Select a voice" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {options.voices?.map((voice) => (
                                            <SelectItem key={voice.id} value={voice.id}>
                                                {voice.name}
                                            </SelectItem>
                                        )) || <SelectItem value="alloy">Alloy (Default)</SelectItem>}
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <Label>Language</Label>
                                <Select name="language" defaultValue={settings.language || "en"}>
                                    <SelectTrigger className="">
                                        <SelectValue placeholder="Select language" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {options.languages?.map((lang) => (
                                            <SelectItem key={lang.id} value={lang.id}>
                                                {lang.name}
                                            </SelectItem>
                                        )) || <SelectItem value="en">English (Default)</SelectItem>}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="prompt_template">System Prompt</Label>
                            <Textarea
                                id="prompt_template"
                                name="prompt_template"
                                placeholder="You are a helpful assistant..."
                                className=" min-h-[150px]"
                                defaultValue={settings.prompt_template || "You are Jane, an AI assistant for a healthcare practice. You help staff with scheduling, patient inquiries, and general information."}
                            />
                            <p className="text-xs text-muted-foreground">
                                Instructions for the AI on how to behave and what information to prioritize.
                            </p>
                        </div>

                        <div className="pt-4">
                            <Button
                                type="submit"
                                className=" w-full sm:w-auto"
                                disabled={isSaving}
                            >
                                {isSaving ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Saving...
                                    </>
                                ) : "Save Configuration"}
                            </Button>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
