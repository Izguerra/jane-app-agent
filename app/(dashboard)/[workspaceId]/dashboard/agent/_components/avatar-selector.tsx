"use client";

import { useEffect, useState, useRef } from "react";
import useSWR from "swr";
import { AgentFormData } from "./types";
import { Switch } from "@/components/ui/switch";
import { Info, AlertTriangle, Loader2, User, Play, Square } from "lucide-react";
import { cn } from "@/lib/utils";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface AvatarSelectorProps {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
    showTitle?: boolean;
}

const fetcher = (url: string) => fetch(url).then(res => res.json());

const VOICE_GENDERS: Record<string, 'male' | 'female' | 'neutral'> = {
    alloy: 'female',
    echo: 'male',
    shimmer: 'female',
    ash: 'male',
    ballad: 'neutral',
    coral: 'female',
    sage: 'female',
    verse: 'male',
    nova: 'female',
    onyx: 'male',
    fable: 'male',
    Rachel: 'female',
    Adam: 'male',
    Bella: 'female',
    Chris: 'male',
    Emily: 'female',
    Josh: 'male',
    Leo: 'male',
    Matilda: 'female',
    Nicole: 'female',
    Sam: 'male',
};

const DEPRECATED_AVATARS = ['Destiny', 'Steph - Selfie', 'Deprecated', '(Deprecated)'];

const getAvatarGender = (name: string): 'male' | 'female' | 'neutral' => {
    const n = name.toLowerCase();

    // Specific Name Lists (Precise mapping)
    const femaleNames = [
        'female', 'woman', 'girl', 'lady', // explicit gender labels
        'sarah', 'emily', 'jessica', 'linda', 'olivia', 'sophia', 'mia', 'isabella',
        'charlotte', 'amelia', 'harper', 'evelyn', 'abigail', 'steph', 'lily', 'grace',
        'chloe', 'victoria', 'madison', 'scarlett', 'ariana', 'penelope', 'layla',
        'rachel', 'bella', 'matilda', 'nicole', 'maya', 'rose', 'luna',
        'gloria', 'anna', 'mary', 'jackie', 'kora', 'zoe', 'ava',
        'beth', 'ruby', 'ivy', 'katya', 'gabby', 'julia', 'samantha'
    ];

    const maleNames = [
        'male', 'man', 'boy', 'gentleman', // explicit gender labels
        'james', 'john', 'robert', 'michael', 'william', 'david', 'richard', 'joseph',
        'thomas', 'charles', 'christopher', 'daniel', 'matthew', 'anthony', 'mark',
        'donald', 'steven', 'paul', 'andrew', 'joshua', 'kenneth', 'kevin', 'brian',
        'george', 'timothy', 'ronald', 'edward', 'jason', 'jeffrey', 'charlie',
        'adam', 'chris', 'josh', 'leo', 'sam', 'marc', 'benjamin', 'damon', 'eric', 'patrick',
        'diego', 'santa', 'danny', 'carter', 'liam', 'jakey', 'kai', 'owen', 'zane',
        'raj', 'nathan'
    ];

    // Check specific names first (word boundary safety)
    // We check if the name string *contains* the name as a distinct word or start/end
    // But since these are mostly distinct names, 'includes' is okay IF we avoided short pronouns like 'she'
    // "Bookshelf" was triggering 'she'. 'she' is removed from the list above.

    if (femaleNames.some(p => n.includes(p))) return 'female';
    if (maleNames.some(p => n.includes(p))) return 'male';

    return 'neutral';
};

export function AvatarSelector({ formData, setFormData, showTitle = true }: AvatarSelectorProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoadingPreview, setIsLoadingPreview] = useState(false);

    const { data: replicas, error, isLoading } = useSWR("/api/integrations/tavus/replicas", fetcher);
    useEffect(() => {
        // Tavus Replicas loaded
    }, [replicas]);

    // Helper functions lifted to module scope

    const selectedVoiceGender = formData.avatarVoiceId ? VOICE_GENDERS[formData.avatarVoiceId] || 'neutral' : 'neutral';

    const filteredReplicas = replicas ? replicas.filter((r: any) => {
        const name = r.replica_name || "";

        // 1. Filter out Deprecated
        if (DEPRECATED_AVATARS.some(deprecated => name.includes(deprecated))) return false;

        // 2. Gender Filtering
        if (!formData.avatarVoiceId) return true;
        if (selectedVoiceGender === 'neutral') return true;

        const avatarGender = getAvatarGender(name);

        // Strict Filtering: If voice is Male, ONLY show Male. If Female, ONLY show Female.
        // Neutral avatars are usually safe to show for both, BUT user said:
        // "let's just have male and female avatars for now" and "neutral avatars... that should be female"
        // So we try to match strictly if possible.
        // If the avatar is explicitly Neutral, we show it (fallback). 
        // But if it's Male, don't show on Female voice.

        if (selectedVoiceGender === 'male' && avatarGender === 'female') return false;
        if (selectedVoiceGender === 'female' && avatarGender === 'male') return false;

        return true;
    }) : [];

    const handleToggle = (checked: boolean) => {
        setFormData((prev: AgentFormData) => ({
            ...prev,
            useTavusAvatar: checked,
            tavusReplicaId: checked ? prev.tavusReplicaId : undefined
        }));
    };

    const handleSelect = (replica: any) => {
        setFormData((prev: AgentFormData) => ({
            ...prev,
            tavusReplicaId: replica.replica_id,
            avatarUrl: replica.thumbnail_video_url || prev.avatarUrl
        }));
    };

    if (error) {
        return (
            <div className="p-4 rounded-lg border border-destructive/50 bg-destructive/10 text-destructive flex gap-3">
                <AlertTriangle className="h-5 w-5 shrink-0" />
                <div>
                    <h5 className="font-medium mb-1">Integration Error</h5>
                    <p className="text-sm">
                        Could not load Tavus Avatars. Please ensure the integration is connected.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {showTitle && (
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-lg font-medium">Visual Presence</h2>
                        <p className="text-sm text-muted-foreground">
                            Enable a video avatar so you can watch the agent work in real-time.
                        </p>
                    </div>
                    <Switch checked={formData.useTavusAvatar} onCheckedChange={handleToggle} />
                </div>
            )}

            {formData.useTavusAvatar && (
                <div className="space-y-6 animate-in fade-in slide-in-from-top-4 duration-300">
                    <div className="space-y-3 p-4 bg-slate-50 rounded-xl border border-slate-200">
                        <Label className="text-base font-medium">Select Avatar Voice</Label>
                        <div className="flex gap-2">
                            <Select
                                value={formData.avatarVoiceId}
                                onValueChange={(val) => setFormData((prev: AgentFormData) => ({ ...prev, avatarVoiceId: val }))}
                            >
                                <SelectTrigger className="flex-1 bg-white">
                                    <SelectValue placeholder="Select a voice" />
                                </SelectTrigger>
                                <SelectContent>
                                    <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">OpenAI</div>
                                    <SelectItem value="alloy">Alloy (Female)</SelectItem>
                                    <SelectItem value="echo">Echo (Male)</SelectItem>
                                    <SelectItem value="shimmer">Shimmer (Female)</SelectItem>
                                    <SelectItem value="ash">Ash (Male)</SelectItem>
                                    <SelectItem value="ballad">Ballad (Neutral)</SelectItem>
                                    <SelectItem value="coral">Coral (Female)</SelectItem>
                                    <SelectItem value="sage">Sage (Female)</SelectItem>
                                    <SelectItem value="verse">Verse (Male)</SelectItem>
                                    <SelectItem value="nova">Nova (Female)</SelectItem>
                                    <SelectItem value="onyx">Onyx (Male)</SelectItem>
                                    <SelectItem value="fable">Fable (Male)</SelectItem>

                                    <div className="border-t my-2" />
                                    <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">ElevenLabs</div>
                                    <SelectItem value="Rachel">Rachel (Female)</SelectItem>
                                    <SelectItem value="Adam">Adam (Male)</SelectItem>
                                    <SelectItem value="Bella">Bella (Female)</SelectItem>
                                    <SelectItem value="Chris">Chris (Male)</SelectItem>
                                    <SelectItem value="Emily">Emily (Female)</SelectItem>
                                    <SelectItem value="Josh">Josh (Male)</SelectItem>
                                    <SelectItem value="Leo">Leo (Male)</SelectItem>
                                    <SelectItem value="Matilda">Matilda (Female)</SelectItem>
                                    <SelectItem value="Nicole">Nicole (Female)</SelectItem>
                                    <SelectItem value="Sam">Sam (Male)</SelectItem>
                                </SelectContent>
                            </Select>

                            <Button
                                type="button"
                                variant="outline"
                                size="icon"
                                className="bg-white"
                                onClick={async () => {
                                    if (isPlaying) {
                                        setIsPlaying(false);
                                        return;
                                    }
                                    setIsLoadingPreview(true);
                                    try {
                                        const res = await fetch('/api/voice/preview', {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({
                                                provider: (['Rachel', 'Adam', 'Bella', 'Chris', 'Emily', 'Josh', 'Leo', 'Matilda', 'Nicole', 'Sam'].includes(formData.avatarVoiceId || '')) ? 'elevenlabs' : 'openai',
                                                voiceId: formData.avatarVoiceId || 'alloy'
                                            })
                                        });
                                        if (!res.ok) throw new Error("Failed to fetch preview");
                                        const blob = await res.blob();
                                        const audio = new Audio(URL.createObjectURL(blob));
                                        audio.onended = () => setIsPlaying(false);
                                        await audio.play();
                                        setIsPlaying(true);
                                    } catch (e: any) {
                                        toast.error(e.message);
                                    } finally {
                                        setIsLoadingPreview(false);
                                    }
                                }}
                                disabled={isLoadingPreview || !formData.avatarVoiceId}
                            >
                                {isLoadingPreview ? <Loader2 className="h-4 w-4 animate-spin" /> : isPlaying ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                            </Button>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <Label className="text-base font-medium">Choose Your Avatar</Label>
                        {isLoading ? (
                            <div className="flex items-center justify-center p-8">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : filteredReplicas.length > 0 ? (
                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                                {filteredReplicas.map((replica: any) => (
                                    <ReplicaCard
                                        key={replica.replica_id}
                                        replica={replica}
                                        isSelected={formData.tavusReplicaId === replica.replica_id}
                                        onSelect={() => handleSelect(replica)}
                                    />
                                ))}
                            </div>
                        ) : (
                            <div className="p-8 rounded-xl border-2 border-dashed bg-muted/20 flex flex-col items-center justify-center text-center">
                                <Info className="h-8 w-8 text-slate-300 mb-2" />
                                <h5 className="font-medium text-slate-600">No Matching Avatars</h5>
                                <p className="text-sm text-slate-500">
                                    We filtered out avatars that don't match the selected voice gender ({selectedVoiceGender}).
                                    <br />Try selecting a different voice or a 'Neutral' one.
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

function ReplicaCard({ replica, isSelected, onSelect }: { replica: any, isSelected: boolean, onSelect: () => void }) {
    const [isHovered, setIsHovered] = useState(false);
    const [isVisible, setIsVisible] = useState(false);
    const videoRef = useRef<HTMLVideoElement>(null);
    const cardRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const observer = new IntersectionObserver(([entry]) => {
            if (entry.isIntersecting) {
                setIsVisible(true);
                observer.disconnect();
            }
        }, { threshold: 0.01, rootMargin: '200px' });

        if (cardRef.current) {
            observer.observe(cardRef.current);
        }
        return () => observer.disconnect();
    }, []);

    useEffect(() => {
        if (videoRef.current && replica.thumbnail_video_url && isVisible) {
            if (isHovered) {
                videoRef.current.play().catch(() => { });
            } else {
                videoRef.current.pause();
                videoRef.current.currentTime = 0; // Reset to frame 0
            }
        }
    }, [isHovered, replica.thumbnail_video_url, isVisible]);

    return (
        <div
            ref={cardRef}
            className={cn(
                "cursor-pointer group relative rounded-xl border-2 overflow-hidden transition-all hover:border-primary/50 bg-white",
                isSelected ? "border-primary ring-2 ring-primary/10" : "border-slate-200"
            )}
            onClick={onSelect}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            <div className="aspect-[3/4] bg-slate-100 relative overflow-hidden">
                {/* 
                    Always use the video tag if visible. 
                    If not visible yet, we show nothing (or just the bgColor from bg-slate-100) 
                    to save bandwidth. Tavus's thumbnail_image_url is sometimes slow or broken.
                */}
                {isVisible && replica.thumbnail_video_url ? (
                    <video
                        ref={videoRef}
                        src={`${replica.thumbnail_video_url}#t=0.1`}
                        poster={replica.thumbnail_image_url}
                        className="object-cover w-full h-full bg-slate-200"
                        loop
                        muted
                        playsInline
                        preload="metadata"
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center">
                        <Loader2 className="h-5 w-5 animate-spin text-slate-300" />
                    </div>
                )}

                {isSelected && (
                    <div className="absolute top-2 right-2 z-10">
                        <div className="bg-primary text-white rounded-full p-1 shadow-lg">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                    </div>
                )}
            </div>
            <div className="p-2 bg-white border-t text-center">
                <p className="font-semibold text-xs truncate text-slate-700">
                    {replica.replica_name || "Unnamed Avatar"}
                    <span className="text-muted-foreground font-normal ml-1 opacity-70 capitalize">
                        ({getAvatarGender(replica.replica_name || "")})
                    </span>
                </p>
            </div>
        </div>
    );
}

