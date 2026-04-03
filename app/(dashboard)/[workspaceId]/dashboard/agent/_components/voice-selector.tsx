"use client";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Play, Square, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface VoiceSelectorProps {
    voiceId: string;
    onVoiceChange: (voiceId: string) => void;
    disabled?: boolean;
}

export function VoiceSelector({ voiceId, onVoiceChange, disabled }: VoiceSelectorProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoadingPreview, setIsLoadingPreview] = useState(false);

    const handlePreview = async () => {
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
            const currentVoiceId = voiceId || 'alloy';
            let provider = 'openai';

            // Provider detection logic
            const grokVoices = ["ara", "eve", "leo", "rex", "sal"];
            const elevenVoices = ["Rachel", "Adam", "Bella", "Chris", "Emily", "Josh", "Leo", "Matilda", "Nicole", "Sam"];
            const geminiVoices = ["Aoede", "Kore", "Puck", "Charon", "Fenrir"];

            if (geminiVoices.includes(currentVoiceId)) {
                throw new Error("Gemini Live voices are generated natively in real-time and cannot be previewed.");
            }

            if (grokVoices.includes(currentVoiceId.toLowerCase())) provider = 'grok';
            else if (elevenVoices.includes(currentVoiceId) || (currentVoiceId === 'Leo' && !grokVoices.includes('leo'))) provider = 'elevenlabs';

            // Handle specific case for 'Leo' (ElevenLabs) vs 'leo' (Grok)
            if (currentVoiceId === 'Leo') provider = 'elevenlabs';
            if (currentVoiceId === 'leo') provider = 'grok';

            const res = await fetch('/api/voice/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider, voiceId: currentVoiceId })
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
    };

    return (
        <div className="flex gap-2">
            <Select
                value={voiceId}
                onValueChange={onVoiceChange}
                disabled={disabled}
            >
                <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Select a voice" />
                </SelectTrigger>
                <SelectContent>
                    {/* OpenAI Voices */}
                    <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">OpenAI</div>
                    <SelectItem value="alloy">Alloy (OpenAI)</SelectItem>
                    <SelectItem value="echo">Echo (OpenAI)</SelectItem>
                    <SelectItem value="shimmer">Shimmer (OpenAI)</SelectItem>
                    <SelectItem value="ash">Ash (OpenAI)</SelectItem>
                    <SelectItem value="ballad">Ballad (OpenAI)</SelectItem>
                    <SelectItem value="coral">Coral (OpenAI)</SelectItem>
                    <SelectItem value="sage">Sage (OpenAI)</SelectItem>
                    <SelectItem value="verse">Verse (OpenAI)</SelectItem>
                    <SelectItem value="nova">Nova (OpenAI)</SelectItem>
                    <SelectItem value="onyx">Onyx (OpenAI)</SelectItem>
                    <SelectItem value="fable">Fable (OpenAI)</SelectItem>

                    {/* Gemini Live Voices */}
                    <div className="border-t my-2" />
                    <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Gemini Live</div>
                    <SelectItem value="Aoede">Aoede (Gemini/Female)</SelectItem>
                    <SelectItem value="Kore">Kore (Gemini/Female)</SelectItem>
                    <SelectItem value="Puck">Puck (Gemini/Male)</SelectItem>
                    <SelectItem value="Charon">Charon (Gemini/Male)</SelectItem>
                    <SelectItem value="Fenrir">Fenrir (Gemini/Male)</SelectItem>

                    {/* Grok Voices */}
                    <div className="border-t my-2" />
                    <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Grok (xAI)</div>
                    <SelectItem value="ara">Ara (Grok)</SelectItem>
                    <SelectItem value="eve">Eve (Grok)</SelectItem>
                    <SelectItem value="leo">Leo (Grok)</SelectItem>
                    <SelectItem value="rex">Rex (Grok)</SelectItem>
                    <SelectItem value="sal">Sal (Grok)</SelectItem>

                    {/* ElevenLabs Voices */}
                    <div className="border-t my-2" />
                    <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">ElevenLabs</div>
                    <SelectItem value="Rachel">Rachel (ElevenLabs)</SelectItem>
                    <SelectItem value="Adam">Adam (ElevenLabs)</SelectItem>
                    <SelectItem value="Bella">Bella (ElevenLabs)</SelectItem>
                    <SelectItem value="Chris">Chris (ElevenLabs)</SelectItem>
                    <SelectItem value="Emily">Emily (ElevenLabs)</SelectItem>
                    <SelectItem value="Josh">Josh (ElevenLabs)</SelectItem>
                    <SelectItem value="Leo">Leo (ElevenLabs)</SelectItem>
                    <SelectItem value="Matilda">Matilda (ElevenLabs)</SelectItem>
                    <SelectItem value="Nicole">Nicole (ElevenLabs)</SelectItem>
                    <SelectItem value="Sam">Sam (ElevenLabs)</SelectItem>
                </SelectContent>
            </Select>

            <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={handlePreview}
                disabled={isLoadingPreview || disabled}
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
    );
}
