"use client";

import { useEffect, useState, useRef } from "react";
import useSWR from "swr";
import { AgentFormData } from "./types";
import { Switch } from "@/components/ui/switch";
import { Info, AlertTriangle, Loader2, User, Play, Square, Sparkles, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";

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

    const femaleNames = [
        'female', 'woman', 'girl', 'lady',
        'sarah', 'emily', 'jessica', 'linda', 'olivia', 'sophia', 'mia', 'isabella',
        'charlotte', 'amelia', 'harper', 'evelyn', 'abigail', 'steph', 'lily', 'grace',
        'chloe', 'victoria', 'madison', 'scarlett', 'ariana', 'penelope', 'layla',
        'rachel', 'bella', 'matilda', 'nicole', 'maya', 'rose', 'luna',
        'gloria', 'anna', 'mary', 'jackie', 'kora', 'zoe', 'ava',
        'beth', 'ruby', 'ivy', 'katya', 'gabby', 'julia', 'samantha'
    ];

    const maleNames = [
        'male', 'man', 'boy', 'gentleman',
        'james', 'john', 'robert', 'michael', 'william', 'david', 'richard', 'joseph',
        'thomas', 'charles', 'christopher', 'daniel', 'matthew', 'anthony', 'mark',
        'donald', 'steven', 'paul', 'andrew', 'joshua', 'kenneth', 'kevin', 'brian',
        'george', 'timothy', 'ronald', 'edward', 'jason', 'jeffrey', 'charlie',
        'adam', 'chris', 'josh', 'leo', 'sam', 'marc', 'benjamin', 'damon', 'eric', 'patrick',
        'diego', 'santa', 'danny', 'carter', 'liam', 'jakey', 'kai', 'owen', 'zane',
        'raj', 'nathan'
    ];

    if (femaleNames.some(p => n.includes(p))) return 'female';
    if (maleNames.some(p => n.includes(p))) return 'male';

    return 'neutral';
};

export function AvatarSelector({ formData, setFormData, showTitle = true }: AvatarSelectorProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoadingPreview, setIsLoadingPreview] = useState(false);

    // Auto-detect active avatar provider from integrations
    const { data: integrations } = useSWR("/api/agent/integrations", fetcher);
    const activeProvider: 'tavus' | 'anam' | null = (() => {
        if (!integrations || !Array.isArray(integrations)) return null;
        const anam = integrations.find((i: any) => i.provider === 'anam' && i.is_active);
        if (anam) return 'anam';
        const tavus = integrations.find((i: any) => i.provider === 'tavus' && i.is_active);
        if (tavus) return 'tavus';
        return null;
    })();

    // Fetch avatars from active provider
    const { data: tavusReplicas, isLoading: tavusLoading } = useSWR(
        activeProvider === 'tavus' ? "/api/integrations/tavus/replicas" : null,
        fetcher
    );
    const { data: anamAvatars, isLoading: anamLoading } = useSWR(
        activeProvider === 'anam' ? "/api/integrations/anam/avatars" : null,
        fetcher
    );

    const isLoading = tavusLoading || anamLoading;

    // Normalize avatars to a common format
    const avatars = activeProvider === 'anam'
        ? (anamAvatars || []).map((p: any) => ({
            id: p.id,
            name: p.displayName || p.name || "Unnamed",
            thumbnail_image_url: p.imageUrl || p.avatarImageUrl || p.thumbnail_image_url || null,
            thumbnail_video_url: p.videoUrl || p.avatarVideoUrl || p.thumbnail_video_url || null,
            provider: 'anam' as const,
            raw: p,
        }))
        : (tavusReplicas || [])
            .filter((r: any) => !DEPRECATED_AVATARS.some(d => (r.replica_name || "").includes(d)))
            .map((r: any) => ({
                id: r.replica_id,
                name: r.replica_name || "Unnamed",
                thumbnail_image_url: r.thumbnail_image_url,
                thumbnail_video_url: r.thumbnail_video_url,
                provider: 'tavus' as const,
                raw: r,
            }));

    const selectedVoiceGender = formData.avatarVoiceId ? VOICE_GENDERS[formData.avatarVoiceId] || 'neutral' : 'neutral';

    const filteredAvatars = avatars.filter((a: any) => {
        if (!formData.avatarVoiceId) return true;
        if (selectedVoiceGender === 'neutral') return true;

        const avatarGender = getAvatarGender(a.name);
        if (selectedVoiceGender === 'male' && avatarGender === 'female') return false;
        if (selectedVoiceGender === 'female' && avatarGender === 'male') return false;
        return true;
    });

    const selectedAvatarId = activeProvider === 'anam' ? formData.anamPersonaId : formData.tavusReplicaId;

    const handleToggle = (checked: boolean) => {
        setFormData((prev: AgentFormData) => ({
            ...prev,
            useTavusAvatar: checked,
            avatarProvider: activeProvider || undefined,
            tavusReplicaId: checked ? prev.tavusReplicaId : undefined,
            anamPersonaId: checked ? prev.anamPersonaId : undefined,
        }));
    };

    const handleSelect = (avatar: any) => {
        if (avatar.provider === 'anam') {
            setFormData((prev: AgentFormData) => ({
                ...prev,
                anamPersonaId: avatar.id,
                avatarProvider: 'anam',
                tavusReplicaId: undefined,
                avatarUrl: avatar.thumbnail_video_url || avatar.thumbnail_image_url || prev.avatarUrl,
            }));
        } else {
            setFormData((prev: AgentFormData) => ({
                ...prev,
                tavusReplicaId: avatar.id,
                avatarProvider: 'tavus',
                anamPersonaId: undefined,
                avatarUrl: avatar.thumbnail_video_url || prev.avatarUrl,
            }));
        }
    };

    if (!activeProvider) {
        return (
            <div className="p-4 rounded-lg border border-amber-200 bg-amber-50 text-amber-800 flex gap-3">
                <AlertTriangle className="h-5 w-5 shrink-0" />
                <div>
                    <h5 className="font-medium mb-1">No Avatar Provider Connected</h5>
                    <p className="text-sm">
                        Please go to Integrations → AI & Avatars and enable either <strong>Tavus</strong> or <strong>Anam.ai</strong>.
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
                    {/* Provider indicator */}
                    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-50 border border-slate-200">
                        {activeProvider === 'anam' ? (
                            <Sparkles className="h-4 w-4 text-cyan-600" />
                        ) : (
                            <Bot className="h-4 w-4 text-purple-600" />
                        )}
                        <span className="text-sm font-medium text-slate-600">
                            Provider: {activeProvider === 'anam' ? 'Anam.ai' : 'Tavus'}
                        </span>
                        <Badge variant="outline" className="ml-auto text-xs">Active</Badge>
                    </div>

                    {/* Voice selector */}
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

                    {/* Avatar Grid */}
                    <div className="space-y-4">
                        <Label className="text-base font-medium">Choose Your Avatar</Label>
                        {isLoading ? (
                            <div className="flex items-center justify-center p-8">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : filteredAvatars.length > 0 ? (
                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                                {filteredAvatars.map((avatar: any) => (
                                    <AvatarCard
                                        key={avatar.id}
                                        avatar={avatar}
                                        isSelected={selectedAvatarId === avatar.id}
                                        onSelect={() => handleSelect(avatar)}
                                    />
                                ))}
                            </div>
                        ) : (
                            <div className="p-8 rounded-xl border-2 border-dashed bg-muted/20 flex flex-col items-center justify-center text-center">
                                <Info className="h-8 w-8 text-slate-300 mb-2" />
                                <h5 className="font-medium text-slate-600">No Matching Avatars</h5>
                                <p className="text-sm text-slate-500">
                                    We filtered out avatars that don&apos;t match the selected voice gender ({selectedVoiceGender}).
                                    <br />Try selecting a different voice or a &apos;Neutral&apos; one.
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

function AvatarCard({ avatar, isSelected, onSelect }: { avatar: any, isSelected: boolean, onSelect: () => void }) {
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
        if (videoRef.current && avatar.thumbnail_video_url && isVisible) {
            if (isHovered) {
                videoRef.current.play().catch(() => { });
            } else {
                videoRef.current.pause();
                videoRef.current.currentTime = 0;
            }
        }
    }, [isHovered, avatar.thumbnail_video_url, isVisible]);

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
                {isVisible && avatar.thumbnail_video_url ? (
                    <video
                        ref={videoRef}
                        src={`${avatar.thumbnail_video_url}#t=0.1`}
                        poster={avatar.thumbnail_image_url}
                        className="object-cover w-full h-full bg-slate-200"
                        loop
                        muted
                        playsInline
                        preload="metadata"
                    />
                ) : isVisible && avatar.thumbnail_image_url ? (
                    <img
                        src={avatar.thumbnail_image_url}
                        alt={avatar.name}
                        className="object-cover w-full h-full bg-slate-200"
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center">
                        <Loader2 className="h-5 w-5 animate-spin text-slate-300" />
                    </div>
                )}

                {/* Provider badge */}
                <div className="absolute top-2 left-2 z-10">
                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0.5 bg-white/80 backdrop-blur-sm">
                        {avatar.provider === 'anam' ? '✨ Anam' : '🟣 Tavus'}
                    </Badge>
                </div>

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
                    {avatar.name}
                    <span className="text-muted-foreground font-normal ml-1 opacity-70 capitalize">
                        ({getAvatarGender(avatar.name)})
                    </span>
                </p>
            </div>
        </div>
    );
}
