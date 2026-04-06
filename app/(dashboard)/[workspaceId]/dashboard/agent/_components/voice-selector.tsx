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
            /* 
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
            */

            const geminiVoices = ["Aoede", "Kore", "Puck", "Charon", "Fenrir"];
            if (geminiVoices.includes(currentVoiceId)) {
                throw new Error("Gemini Live voices are generated natively in real-time and cannot be previewed.");
            }
            
            // Default to openai for now if somehow we get here, but the UI should prevent it.
            provider = 'openai';

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
                    {/* Gemini Live Voices */}
                    <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Gemini Live</div>
                    <SelectItem value="Aoede">Aoede (Gemini/Female)</SelectItem>
                    <SelectItem value="Kore">Kore (Gemini/Female)</SelectItem>
                    <SelectItem value="Puck">Puck (Gemini/Male)</SelectItem>
                    <SelectItem value="Charon">Charon (Gemini/Male)</SelectItem>
                    <SelectItem value="Fenrir">Fenrir (Gemini/Male)</SelectItem>

                    {/* Other providers temporarily disabled to ensure Gemini Live stability */}
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
