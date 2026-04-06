
"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AgentFormData } from "./types";
import { Upload, Plus, Trash2, Play, Square, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { toast } from "sonner";

interface Step1Props {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
    workspaceId: string;
}

import { useParams } from "next/navigation";
import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export function Step1ConfigureAgent({ formData, setFormData, workspaceId }: Step1Props) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoadingPreview, setIsLoadingPreview] = useState(false);

    // const params = useParams(); // Using prop instead for reliability
    // const workspaceId = params?.workspaceId as string;

    // Fetch Sources to map URLs to Source IDs for deletion
    const { data: sources, mutate } = useSWR(
        workspaceId && workspaceId !== "undefined" ? `/api/workspaces/${workspaceId}/knowledge-base/sources` : null,
        fetcher
    );

    const handleChange = (field: keyof AgentFormData, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, field: 'avatarFile' | 'kbFiles') => {
        if (e.target.files && e.target.files.length > 0) {
            if (field === 'avatarFile') {
                const file = e.target.files[0];
                setFormData(prev => ({
                    ...prev,
                    avatarFile: file,
                    avatarUrl: URL.createObjectURL(file)
                }));
            } else {
                setFormData(prev => ({
                    ...prev,
                    kbFiles: Array.from(e.target.files || [])
                }));
            }
        }
    };

    const handleDeleteExistingFile = async (url: string) => {
        const filename = url.split('/').pop();
        if (!filename) return;

        // Optimistically remove from UI
        setFormData(prev => ({
            ...prev,
            existingKbUrls: prev.existingKbUrls.filter(u => u !== url)
        }));

        // Find source ID matching this file
        if (sources && Array.isArray(sources)) {
            const source = sources.find((s: any) =>
                s.source_type === 'file_upload' &&
                (s.name === filename || (s.config?.file_path && s.config.file_path.endsWith(filename)))
            );

            if (source) {
                try {
                    await fetch(`/api/workspaces/${workspaceId}/knowledge-base/sources/${source.id}`, {
                        method: 'DELETE'
                    });
                    mutate(); // Refresh sources list
                } catch (e) {
                    console.error("Failed to delete source", e);
                }
            }
        }
    };

    return (
        <div className="space-y-6">
            <div className="space-y-4">
                <div className="space-y-2">
                    <Label htmlFor="name">Agent Name</Label>
                    <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => handleChange("name", e.target.value)}
                        placeholder="e.g. Sarah"
                    />
                </div>

                <div className="space-y-2">
                    <Label htmlFor="voice_id">Agent Voice</Label>
                    <div className="flex gap-2">
                        <Select
                            value={formData.voice_id}
                            onValueChange={(val) => handleChange("voice_id", val)}
                        >
                            <SelectTrigger className="flex-1">
                                <SelectValue placeholder="Select a voice" />
                            </SelectTrigger>
                            <SelectContent>
                                {/* Gemini Live Voices Only */}
                                <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Gemini Live (Native Audio)</div>
                                <SelectItem value="Aoede">Aoede (Gemini/Female)</SelectItem>
                                <SelectItem value="Kore">Kore (Gemini/Female)</SelectItem>
                                <SelectItem value="Puck">Puck (Gemini/Male)</SelectItem>
                                <SelectItem value="Charon">Charon (Gemini/Male)</SelectItem>
                                <SelectItem value="Fenrir">Fenrir (Gemini/Male)</SelectItem>
                            </SelectContent>
                        </Select>

                        <Button
                            type="button"
                            variant="outline"
                            size="icon"
                            onClick={async () => {
                                if (isPlaying) {
                                    window.speechSynthesis.cancel();
                                    const audio = document.getElementById('voice-preview-audio') as HTMLAudioElement;
                                    if (audio) {
                                        audio.pause();
                                        audio.currentTime = 0;
                                    }
                                    setIsPlaying(false);
                                    return;
                                }

                                setIsLoadingPreview(true);
                                try {
                                    const voiceId = formData.voice_id || 'alloy';
                                    let provider = 'openai';

                                    const grokVoices = ["ara", "eve", "leo", "rex", "sal"];
                                    const elevenVoices = ["Rachel", "Adam", "Bella", "Chris", "Emily", "Josh", "Leo", "Matilda", "Nicole", "Sam"];
                                    const geminiVoices = ["Aoede", "Kore", "Puck", "Charon", "Fenrir"];

                                    if (geminiVoices.includes(voiceId)) {
                                        throw new Error("Gemini Live voices are generated natively in real-time and cannot be previewed.");
                                    }

                                    if (grokVoices.includes(voiceId.toLowerCase())) provider = 'grok';
                                    else if (elevenVoices.includes(voiceId) || (voiceId === 'Leo' && !grokVoices.includes('leo'))) provider = 'elevenlabs';
                                    if (voiceId === 'Leo') provider = 'elevenlabs';
                                    if (voiceId === 'leo') provider = 'grok';

                                    const res = await fetch('/api/voice/preview', {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ provider, voiceId })
                                    });

                                    if (!res.ok) {
                                        const err = await res.json();
                                        if (provider === 'grok') throw new Error("Preview not supported for Grok voices yet.");
                                        throw new Error(err.error || "Failed to fetch preview");
                                    }

                                    const blob = await res.blob();
                                    const url = URL.createObjectURL(blob);
                                    const audio = new Audio(url);
                                    audio.id = 'voice-preview-audio';

                                    audio.onended = () => setIsPlaying(false);
                                    audio.onerror = () => {
                                        toast.error("Error playing audio");
                                        setIsPlaying(false);
                                    };

                                    await audio.play();
                                    setIsPlaying(true);
                                } catch (e: any) {
                                    toast.error(e.message);
                                } finally {
                                    setIsLoadingPreview(false);
                                }
                            }}
                            disabled={isLoadingPreview}
                        >
                            {isLoadingPreview ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : isPlaying ? (
                                <Square className="h-4 w-4 fill-current" />
                            ) : (
                                <Play className="h-4 w-4" />
                            )}
                        </Button>
                    </div>


                </div>

                <div className="space-y-2">
                    <Label htmlFor="language">Language</Label>
                    {(() => {
                        // Detect voice provider based on selected voice
                        const voiceId = formData.voice_id || 'alloy';
                        const grokVoices = ['ara', 'eve', 'leo', 'rex', 'sal'];
                        const elevenLabsVoices = ['Rachel', 'Adam', 'Bella', 'Chris', 'Emily', 'Josh', 'Leo', 'Matilda', 'Nicole', 'Sam'];

                        let provider: 'openai' | 'grok' | 'elevenlabs' = 'openai';
                        if (grokVoices.includes(voiceId.toLowerCase())) {
                            provider = 'grok';
                        } else if (elevenLabsVoices.includes(voiceId) || (voiceId === 'Leo')) {
                            // Capital "Leo" is ElevenLabs
                            provider = 'elevenlabs';
                        }

                        // Language support by provider
                        // Based on official documentation:
                        // - OpenAI: 50+ languages (most comprehensive)
                        // - ElevenLabs: 29 languages
                        // - Grok/xAI: ~10 core languages
                        const LANGUAGES = [
                            // Universal (all providers)
                            { code: 'en', name: 'English', openai: true, elevenlabs: true, grok: true },
                            { code: 'es', name: 'Spanish', openai: true, elevenlabs: true, grok: true },
                            { code: 'fr', name: 'French', openai: true, elevenlabs: true, grok: true },
                            { code: 'de', name: 'German', openai: true, elevenlabs: true, grok: true },
                            { code: 'it', name: 'Italian', openai: true, elevenlabs: true, grok: true },
                            { code: 'pt', name: 'Portuguese', openai: true, elevenlabs: true, grok: true },
                            { code: 'ja', name: 'Japanese', openai: true, elevenlabs: true, grok: true },
                            { code: 'ko', name: 'Korean', openai: true, elevenlabs: true, grok: true },
                            { code: 'zh', name: 'Chinese (Mandarin)', openai: true, elevenlabs: true, grok: true },
                            { code: 'ar', name: 'Arabic', openai: true, elevenlabs: true, grok: true },
                            // OpenAI + ElevenLabs
                            { code: 'nl', name: 'Dutch', openai: true, elevenlabs: true, grok: false },
                            { code: 'pl', name: 'Polish', openai: true, elevenlabs: true, grok: false },
                            { code: 'ru', name: 'Russian', openai: true, elevenlabs: true, grok: false },
                            { code: 'tr', name: 'Turkish', openai: true, elevenlabs: true, grok: false },
                            { code: 'sv', name: 'Swedish', openai: true, elevenlabs: true, grok: false },
                            { code: 'da', name: 'Danish', openai: true, elevenlabs: false, grok: false },
                            { code: 'fi', name: 'Finnish', openai: true, elevenlabs: true, grok: false },
                            { code: 'no', name: 'Norwegian', openai: true, elevenlabs: true, grok: false },
                            { code: 'cs', name: 'Czech', openai: true, elevenlabs: true, grok: false },
                            { code: 'el', name: 'Greek', openai: true, elevenlabs: true, grok: false },
                            { code: 'he', name: 'Hebrew', openai: true, elevenlabs: true, grok: false },
                            { code: 'hu', name: 'Hungarian', openai: true, elevenlabs: true, grok: false },
                            { code: 'id', name: 'Indonesian', openai: true, elevenlabs: true, grok: false },
                            { code: 'hi', name: 'Hindi', openai: true, elevenlabs: true, grok: false },
                            { code: 'uk', name: 'Ukrainian', openai: true, elevenlabs: true, grok: false },
                            { code: 'vi', name: 'Vietnamese', openai: true, elevenlabs: true, grok: false },
                            { code: 'th', name: 'Thai', openai: true, elevenlabs: false, grok: false },
                            { code: 'ms', name: 'Malay', openai: true, elevenlabs: true, grok: false },
                            { code: 'ro', name: 'Romanian', openai: true, elevenlabs: true, grok: false },
                            { code: 'sk', name: 'Slovak', openai: true, elevenlabs: true, grok: false },
                            { code: 'bg', name: 'Bulgarian', openai: true, elevenlabs: true, grok: false },
                            { code: 'hr', name: 'Croatian', openai: true, elevenlabs: true, grok: false },
                            // OpenAI Only
                            { code: 'af', name: 'Afrikaans', openai: true, elevenlabs: false, grok: false },
                            { code: 'bn', name: 'Bengali', openai: true, elevenlabs: false, grok: false },
                            { code: 'ta', name: 'Tamil', openai: true, elevenlabs: true, grok: false },
                            { code: 'te', name: 'Telugu', openai: true, elevenlabs: false, grok: false },
                            { code: 'ur', name: 'Urdu', openai: true, elevenlabs: false, grok: false },
                            { code: 'sw', name: 'Swahili', openai: true, elevenlabs: false, grok: false },
                        ];

                        // Filter languages based on provider
                        const supportedLanguages = LANGUAGES.filter(lang => lang[provider]);

                        return (
                            <Select
                                key={`lang-${formData.voice_id}`}
                                value={formData.language}
                                onValueChange={(val) => handleChange("language", val)}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select language" />
                                </SelectTrigger>
                                <SelectContent className="max-h-[300px]">
                                    <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                                        {provider === 'grok' ? '🔴 Grok/xAI Languages' :
                                            provider === 'elevenlabs' ? '🟣 ElevenLabs Languages' :
                                                '🟢 OpenAI Languages'}
                                    </div>
                                    {supportedLanguages.map(lang => (
                                        <SelectItem key={lang.code} value={lang.code}>{lang.name}</SelectItem>
                                    ))}
                                    {provider !== 'openai' && (
                                        <div className="px-2 py-1.5 text-xs text-muted-foreground border-t mt-2 pt-2">
                                            💡 Switch to an OpenAI voice for 50+ languages
                                        </div>
                                    )}
                                </SelectContent>
                            </Select>
                        );
                    })()}
                </div>
            </div>



            <div className="space-y-2">
                <Label htmlFor="role">Primary Function</Label>
                <Input
                    id="role"
                    value={formData.primaryFunction}
                    onChange={(e) => handleChange("primaryFunction", e.target.value)}
                    placeholder="e.g. Booking appointments, answering FAQs"
                />
            </div>

            <div className="space-y-2">
                <Label htmlFor="greeting">Welcome Greeting</Label>
                <Textarea
                    id="greeting"
                    value={formData.welcomeGreeting}
                    onChange={(e) => handleChange("welcomeGreeting", e.target.value)}
                    placeholder="Hello! How can I help you today?"
                    rows={3}
                />
            </div>

            {/* ==== CONDITIONAL FORM: BUSINESS vs PERSONAL ==== */}
            {formData.agentType === "personal" ? (
                <>
                    {/* ---- PERSONAL AGENT PROFILE ---- */}
                    <div className="border-t pt-4">
                        <h3 className="font-semibold mb-1">👤 Personal Profile</h3>
                        <p className="text-sm text-gray-500 mb-4">Tell your agent about yourself so it can assist you better.</p>
                        <div className="grid grid-cols-2 gap-4 mb-4">
                            <div className="space-y-2">
                                <Label htmlFor="owner-name">Your Name</Label>
                                <Input
                                    id="owner-name"
                                    value={formData.ownerName || ""}
                                    onChange={(e) => handleChange("ownerName", e.target.value)}
                                    placeholder="e.g. Randy"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="location">Location / City</Label>
                                <Input
                                    id="location"
                                    value={formData.location || ""}
                                    onChange={(e) => handleChange("location", e.target.value)}
                                    placeholder="e.g. Toronto, ON"
                                />
                            </div>
                        </div>
                        <div className="space-y-2 mb-4">
                            <Label htmlFor="timezone">Timezone</Label>
                            <Select
                                value={formData.timezone || ""}
                                onValueChange={(val) => handleChange("timezone", val)}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select timezone" />
                                </SelectTrigger>
                                <SelectContent className="max-h-[250px]">
                                    <SelectItem value="America/New_York">Eastern (ET)</SelectItem>
                                    <SelectItem value="America/Chicago">Central (CT)</SelectItem>
                                    <SelectItem value="America/Denver">Mountain (MT)</SelectItem>
                                    <SelectItem value="America/Los_Angeles">Pacific (PT)</SelectItem>
                                    <SelectItem value="America/Toronto">Toronto (ET)</SelectItem>
                                    <SelectItem value="America/Vancouver">Vancouver (PT)</SelectItem>
                                    <SelectItem value="Europe/London">London (GMT)</SelectItem>
                                    <SelectItem value="Europe/Paris">Paris (CET)</SelectItem>
                                    <SelectItem value="Asia/Tokyo">Tokyo (JST)</SelectItem>
                                    <SelectItem value="Asia/Dubai">Dubai (GST)</SelectItem>
                                    <SelectItem value="Australia/Sydney">Sydney (AEST)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <div className="border-t pt-4">
                        <h3 className="font-semibold mb-1">⭐ Preferences</h3>
                        <p className="text-sm text-gray-500 mb-4">Your agent will use these to personalize recommendations and conversations.</p>
                        <div className="grid grid-cols-2 gap-4 mb-4">
                            <div className="space-y-2">
                                <Label htmlFor="fav-foods">Favorite Foods</Label>
                                <Textarea
                                    id="fav-foods"
                                    value={formData.favoriteFoods || ""}
                                    onChange={(e) => handleChange("favoriteFoods", e.target.value)}
                                    placeholder="e.g. Sushi, Tacos, Italian pasta"
                                    rows={2}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="fav-restaurants">Favorite Restaurants</Label>
                                <Textarea
                                    id="fav-restaurants"
                                    value={formData.favoriteRestaurants || ""}
                                    onChange={(e) => handleChange("favoriteRestaurants", e.target.value)}
                                    placeholder="e.g. Joe's Pizza, Nobu, Chipotle"
                                    rows={2}
                                />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4 mb-4">
                            <div className="space-y-2">
                                <Label htmlFor="fav-music">Favorite Music / Artists</Label>
                                <Textarea
                                    id="fav-music"
                                    value={formData.favoriteMusic || ""}
                                    onChange={(e) => handleChange("favoriteMusic", e.target.value)}
                                    placeholder="e.g. Drake, The Weeknd, Jazz"
                                    rows={2}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="fav-activities">Activities / Hobbies</Label>
                                <Textarea
                                    id="fav-activities"
                                    value={formData.favoriteActivities || ""}
                                    onChange={(e) => handleChange("favoriteActivities", e.target.value)}
                                    placeholder="e.g. Hiking, Gaming, Photography"
                                    rows={2}
                                />
                            </div>
                        </div>
                        <div className="space-y-2 mb-4">
                            <Label htmlFor="other-interests">Other Interests</Label>
                            <Textarea
                                id="other-interests"
                                value={formData.otherInterests || ""}
                                onChange={(e) => handleChange("otherInterests", e.target.value)}
                                placeholder="e.g. AI, Startups, Travel, Crypto"
                                rows={2}
                            />
                        </div>
                    </div>

                    <div className="border-t pt-4">
                        <h3 className="font-semibold mb-1">👍 Likes & Dislikes</h3>
                        <p className="text-sm text-gray-500 mb-4">Help your agent recommend the right things and avoid what you don&apos;t like.</p>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="likes">Things I Like</Label>
                                <Textarea
                                    id="likes"
                                    value={formData.likes || ""}
                                    onChange={(e) => handleChange("likes", e.target.value)}
                                    placeholder="e.g. Warm weather, spicy food, early mornings"
                                    rows={3}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="dislikes">Things I Dislike / Avoid</Label>
                                <Textarea
                                    id="dislikes"
                                    value={formData.dislikes || ""}
                                    onChange={(e) => handleChange("dislikes", e.target.value)}
                                    placeholder="e.g. Crowded places, seafood, cold weather"
                                    rows={3}
                                />
                            </div>
                        </div>
                    </div>
                </>
            ) : (
                <>
                    {/* ---- BUSINESS AGENT KNOWLEDGE BASE (CURRENT) ---- */}
                    <div className="border-t pt-4">
                        <h3 className="font-semibold mb-4">Knowledge Base</h3>
                        <div className="grid grid-cols-2 gap-4 mb-4">
                            <div className="space-y-2">
                                <Label htmlFor="biz-name">Business Name</Label>
                                <Input
                                    id="biz-name"
                                    value={formData.businessName}
                                    onChange={(e) => handleChange("businessName", e.target.value)}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="website">Website URL</Label>
                                <Input
                                    id="website"
                                    value={formData.websiteUrl}
                                    onChange={(e) => handleChange("websiteUrl", e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="space-y-2 mb-4">
                            <Label htmlFor="desc">Business Description</Label>
                            <Textarea
                                id="desc"
                                value={formData.businessDescription}
                                onChange={(e) => handleChange("businessDescription", e.target.value)}
                                rows={3}
                            />
                        </div>

                        <div className="space-y-4 mb-4">
                            <div className="space-y-2">
                                <Label htmlFor="hours">Business Hours (JSON Format or Text)</Label>
                                <Textarea
                                    id="hours"
                                    value={formData.hoursOfOperation}
                                    onChange={(e) => handleChange("hoursOfOperation", e.target.value)}
                                    placeholder='e.g. {"Mon": "9-5", "Tue": "9-5"} or "Mon-Fri 9am-5pm"'
                                    rows={3}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="services">Services</Label>
                                <Textarea
                                    id="services"
                                    value={formData.services}
                                    onChange={(e) => handleChange("services", e.target.value)}
                                    placeholder="e.g. Consulting, Support, Development"
                                    rows={3}
                                />
                            </div>
                        </div>

                        <div className="space-y-4 mb-4">
                            <div className="flex items-center justify-between">
                                <Label>FAQ Items</Label>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                        setFormData(prev => ({
                                            ...prev,
                                            faqItems: [...prev.faqItems, { question: "", answer: "" }]
                                        }));
                                    }}
                                >
                                    <Plus className="h-4 w-4 mr-2" />
                                    Add FAQ
                                </Button>
                            </div>

                            <div className="space-y-4">
                                {(formData.faqItems || []).map((item, index) => (
                                    <div key={index} className="flex gap-4 items-start p-4 border rounded-lg bg-gray-50">
                                        <div className="flex-1 space-y-3">
                                            <div>
                                                <Label className="text-xs text-muted-foreground">Question</Label>
                                                <Input
                                                    value={item.question}
                                                    onChange={(e) => {
                                                        const newFaq = [...formData.faqItems];
                                                        newFaq[index].question = e.target.value;
                                                        setFormData(prev => ({ ...prev, faqItems: newFaq }));
                                                    }}
                                                    placeholder="What is your return policy?"
                                                />
                                            </div>
                                            <div>
                                                <Label className="text-xs text-muted-foreground">Answer</Label>
                                                <Textarea
                                                    value={item.answer}
                                                    onChange={(e) => {
                                                        const newFaq = [...formData.faqItems];
                                                        newFaq[index].answer = e.target.value;
                                                        setFormData(prev => ({ ...prev, faqItems: newFaq }));
                                                    }}
                                                    placeholder="We offer a 30-day return policy..."
                                                    rows={2}
                                                />
                                            </div>
                                        </div>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                            onClick={() => {
                                                const newFaq = formData.faqItems.filter((_, i) => i !== index);
                                                setFormData(prev => ({ ...prev, faqItems: newFaq }));
                                            }}
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                ))}
                                {formData.faqItems.length === 0 && (
                                    <p className="text-sm text-gray-500 italic text-center py-4">No FAQ items added yet.</p>
                                )}
                            </div>
                        </div>
                    </div>
                </>
            )}

            {/* ==== SHARED: KB File Upload ==== */}
            <div className="border-t pt-4">
                <div className="space-y-2">
                    <Label htmlFor="kb-upload">{formData.agentType === "personal" ? "Upload Personal Documents (PDF, TXT)" : "Upload Knowledge Documents (PDF, TXT)"}</Label>
                    <div className="border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center text-center">
                        <Upload className="h-8 w-8 text-gray-400 mb-2" />
                        <p className="text-sm text-gray-500 mb-2">Drag & drop files here or click to browse</p>
                        <Input
                            type="file"
                            id="kb-upload"
                            multiple
                            className="hidden"
                            onChange={(e) => handleFileChange(e, 'kbFiles')}
                        />
                        <Button variant="secondary" size="sm" asChild>
                            <Label htmlFor="kb-upload" className="cursor-pointer">Browse Files</Label>
                        </Button>
                        {formData.kbFiles.length > 0 && (
                            <div className="mt-4 w-full text-left">
                                <p className="text-xs font-semibold mb-1">Selected Files:</p>
                                <ul className="text-xs text-gray-600 list-disc pl-4">
                                    {(formData.kbFiles || []).map((f, i) => (
                                        <li key={i}>{f.name}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        {formData.existingKbUrls.length > 0 && (
                            <div className="mt-4 w-full text-left">
                                <p className="text-xs font-semibold mb-1">Existing Files:</p>
                                <div className="space-y-1">
                                    {(formData.existingKbUrls || []).map((url, i) => (
                                        <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded text-xs border">
                                            <span className="truncate flex-1" title={url}>{url.split('/').pop()}</span>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-6 w-6 ml-2 text-red-500 hover:text-red-700 hover:bg-red-50"
                                                onClick={() => handleDeleteExistingFile(url)}
                                            >
                                                <Trash2 className="h-3 w-3" />
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
