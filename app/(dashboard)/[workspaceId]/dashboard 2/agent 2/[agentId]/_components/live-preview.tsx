
"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AgentFormData } from "./types";
import { Send, User as UserIcon, Bot as BotIcon, X, Phone, Video, Bot, Camera, CameraOff } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Maximize2, Minimize2, Settings2, Layout, Monitor, Square, Layers, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import {
    LiveKitRoom,
    RoomAudioRenderer,
    BarVisualizer,
    useVoiceAssistant,
    useConnectionState,
    useLocalParticipant,
    useTracks,
    VideoTrack,
    useTranscriptions,
} from "@livekit/components-react";
import { Track } from "livekit-client";
import "@livekit/components-styles";
import { Mic, MicOff } from "lucide-react";
import { cn } from "@/lib/utils";

interface LivePreviewProps {
    formData: AgentFormData;
    agentId?: string;
    workspaceId?: string;
    voiceToken?: { token: string; url: string } | null;  // Pre-generated token from parent
    setFormData?: React.Dispatch<React.SetStateAction<AgentFormData>>;
}

export function LivePreview({ formData, agentId, workspaceId, voiceToken, setFormData }: LivePreviewProps) {
    const [mode, setMode] = useState<'chat' | 'voice' | 'avatar'>('chat');
    const [messages, setMessages] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [input, setInput] = useState("");
    const scrollRef = useRef<HTMLDivElement>(null);

    // LiveKit State
    const [token, setToken] = useState("");
    const [url, setUrl] = useState("");
    const [isConnecting, setIsConnecting] = useState(false);
    const [error, setError] = useState("");
    const [imgError, setImgError] = useState(false);
    const isReconnecting = useRef(false);

    // UI Enhancements (Phase 5)
    const [isTheaterMode, setIsTheaterMode] = useState(false);
    const [pipSize, setPipSize] = useState<'sm' | 'md' | 'lg'>('sm');

    useEffect(() => {
        setImgError(false);
    }, [formData.avatarUrl, formData.widgetIconUrl]);

    // Auto-scroll to bottom when messages change
    // Auto-scroll to bottom when messages change
    useEffect(() => {
        if (scrollRef.current) {
            const { scrollHeight, clientHeight } = scrollRef.current; // Get the values from the current scrollRef
            // Only scroll if the content is taller than the container
            if (scrollHeight > clientHeight) {
                scrollRef.current.scrollTo({
                    top: scrollHeight - clientHeight,
                    behavior: "smooth"
                });
            }
        }
    }, [messages]);

    // Update messages when welcome greeting changes
    // Update messages when welcome greeting or language changes
    useEffect(() => {
        const updateGreeting = async () => {
            let greeting = formData.welcomeGreeting || "Hello! How can I help you?";

            if (formData.language && formData.language !== 'en') {
                try {
                    const res = await fetch('/api/settings/translate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            text: greeting,
                            target_language: formData.language
                        })
                    });
                    if (res.ok) {
                        const data = await res.json();
                        greeting = data.translated_text;
                    }
                } catch (e) {
                    console.error("Translation failed", e);
                }
            }

            setMessages([
                { role: 'assistant', content: greeting }
            ]);
        };

        // Debounce to prevent too many API calls while typing
        const timer = setTimeout(updateGreeting, 1000);
        return () => clearTimeout(timer);

    }, [formData.welcomeGreeting, formData.language]);

    // Helper to construct agent config from form data
    const getAgentConfig = () => ({
        name: formData.name,
        voice_id: formData.voice_id || "alloy",
        language: formData.language,
        // Reconstruct prompt logic to match backend/page.tsx logic
        prompt_template: `You are ${formData.name}, a ${formData.conversationStyle} assistant. ${formData.businessDescription}`,
        welcome_message: formData.welcomeGreeting,
        creativity_level: Number(formData.creativityLevel || 50),
        response_length: Number(formData.responseLength || 50),
        intent_rules: JSON.stringify(formData.intentRules || []),
        allowed_worker_types: formData.allowedWorkerTypes || [],

        // Avatar Context
        tavus_replica_id: formData.tavusReplicaId,
        tavus_persona_id: formData.tavusPersonaId,
        avatar_voice_id: formData.avatarVoiceId,
        use_tavus_avatar: formData.useTavusAvatar,

        // KB Context
        business_name: formData.businessName,
        website_url: formData.websiteUrl,
        email: formData.email,
        phone: formData.phone,
        address: formData.address,
        services: formData.services,
        hours_of_operation: formData.hoursOfOperation,
        faq: JSON.stringify(formData.faqItems || []),
        accent_color: formData.accentColor,
        mode: mode
    });

    // Clear token ONLY when settings relevant to the current mode change
    const lastConfig = useRef({ voice_id: "", avatarVoiceId: "", replicaId: "", mode: mode });
    useEffect(() => {
        // Force refresh for Turbopack stability
        const currentVoiceId = formData.voice_id || "";
        const currentAvatarVoiceId = formData.avatarVoiceId || "";
        const currentReplicaId = formData.tavusReplicaId || "";

        // Helper to compare loosely (treat null/undefined/"" as same)
        const isDifferent = (a: any, b: any) => {
            const valA = a || "";
            const valB = b || "";
            return valA !== valB;
        };

        const isModeSwitchToInactive = lastConfig.current.mode !== 'chat' && mode === 'chat';
        const isVoiceUpdateWhileActive = mode === 'voice' && isDifferent(lastConfig.current.voice_id, currentVoiceId);

        // Only trigger update if we were ALREADY on avatar mode and something changed
        // Switching TO avatar mode should be handled by the initial connection logic, not this cleaner
        const isAvatarUpdateWhileActive = mode === 'avatar' && lastConfig.current.mode === 'avatar' && (
            isDifferent(lastConfig.current.avatarVoiceId, currentAvatarVoiceId) ||
            isDifferent(lastConfig.current.replicaId, currentReplicaId)
        );

        const isMediaModeSwitch = lastConfig.current.mode !== mode && (mode === 'voice' || mode === 'avatar') && (lastConfig.current.mode === 'voice' || lastConfig.current.mode === 'avatar');

        if (token && (isModeSwitchToInactive || isVoiceUpdateWhileActive || isAvatarUpdateWhileActive || isMediaModeSwitch)) {
            // SAFEGUARD: If we are using the prop-token (saved state), and the config "drift" is minor, ignore it.
            // This prevents race conditions where initial hydration differs slightly from saved state.
            if (voiceToken && token === voiceToken.token) {
                console.log("DEBUG: Config change detected but ignored because using validated saved token.");
                // Update ref to match current state so future real changes trigger
                lastConfig.current = {
                    voice_id: currentVoiceId,
                    avatarVoiceId: currentAvatarVoiceId,
                    replicaId: currentReplicaId,
                    mode: mode
                };
                return;
            }

            console.warn("DEBUG: Config change detected, BUT IGNORING auto-disconnect to prevent loop.", {
                mode,
                old_mode: lastConfig.current.mode,
                isMediaModeSwitch,
                isVoiceUpdateWhileActive,
                isAvatarUpdateWhileActive,
                reason: isModeSwitchToInactive ? "Mode Inactive" : isVoiceUpdateWhileActive ? "Voice Changed" : isAvatarUpdateWhileActive ? "Avatar Config Changed" : "Media Mode Switch",
            });
            // isReconnecting.current = true;
            // setToken("");
            // setUrl("");
            // setError("");
        }
        // Update tracking ref ALWAYS
        lastConfig.current = {
            voice_id: currentVoiceId,
            avatarVoiceId: currentAvatarVoiceId,
            replicaId: currentReplicaId,
            mode: mode
        };
    }, [formData.voice_id, formData.avatarVoiceId, formData.tavusReplicaId, mode]);

    // Fetch Token on Voice Mode - Use pre-generated token if available
    useEffect(() => {
        if ((mode === 'voice' || mode === 'avatar') && !token) {
            // Priority 1: Use pre-generated token from parent (after save)
            // parent now generates tokens with correct mode if useTavusAvatar is set
            if (voiceToken) {
                // Determine if parent's token matches our current mode intent
                // We don't have the mode in the tokenData object itself usually, 
                // but we can assume if useTavusAvatar is true, we want avatar mode.
                const parentMode = formData.useTavusAvatar ? 'avatar' : 'voice';
                if (mode === parentMode) {
                    setToken(voiceToken.token);
                    setUrl(voiceToken.url);
                    console.log(`DEBUG: Using pre-generated ${mode} token from save`);
                    return;
                }
            }

            // Priority 2: Fallback to on-demand fetch if no pre-generated token
            // This is for cases where user hasn't saved yet but wants to preview
            if (!agentId) {
                setError("Please save the agent first to enable voice/video preview");
                return;
            }

            if (mode === 'avatar' && !formData.tavusReplicaId) {
                // Do not connect if no avatar is selected
                setError("Please select an avatar to start.");
                setIsConnecting(false);
                return;
            }

            setIsConnecting(true);
            setError("");
            (async () => {
                try {
                    // Only send agent_id and workspace_id - let backend use saved DB data
                    const resp = await fetch("/api/voice/token", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            agent_id: agentId,
                            workspace_id: workspaceId,
                            agent_config: getAgentConfig(), // Use current wizard data
                            mode: mode
                        })
                    });

                    if (!resp.ok) {
                        const err = await resp.json();
                        throw new Error(err.detail || "Failed to get token");
                    }
                    const data = await resp.json();
                    setToken(data.token);
                    setUrl(data.url);
                    isReconnecting.current = false;
                } catch (e) {
                    console.error(e);
                    setError("Failed to connect to voice service");
                } finally {
                    setIsConnecting(false);
                }
            })();
        }
    }, [mode, agentId, token, voiceToken, workspaceId, formData.tavusReplicaId]); // Added formData.tavusReplicaId dependency
    // Removed formData dependency - token should use saved data, not form state 
    // But token is state. If token exists, it won't fetch. So we need to clear token if formData changes?
    // For now, let's keep it simple: It fetches when entering voice mode.

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = { role: 'user' as const, content: input };
        const newMsgs = [...messages, userMessage];
        setMessages(newMsgs);
        setInput("");
        setIsLoading(true);

        // 1. Check client-side matches for instant feedback on simple fields
        const lowerInput = input.toLowerCase();
        let clientResponse = null;

        if ((lowerInput.includes("hours") || lowerInput.includes("open")) && formData.hoursOfOperation) {
            clientResponse = `Our hours are: ${formData.hoursOfOperation}`;
        } else if ((lowerInput.includes("service") || lowerInput.includes("offer")) && formData.services) {
            clientResponse = `We offer the following services: ${formData.services}`;
        } else if ((lowerInput.includes("who") || lowerInput.includes("name")) && formData.businessName) {
            clientResponse = `I am ${formData.name}, an assistant for ${formData.businessName}.`;
        } else {
            // Check FAQ items
            const faqMatch = formData.faqItems.find(item => {
                if (!item.question?.trim()) return false;
                const qLower = item.question.toLowerCase();
                return lowerInput.includes(qLower) || qLower.includes(lowerInput);
            });

            if (faqMatch) {
                clientResponse = faqMatch.answer;
            }
        }

        if (clientResponse) {
            setMessages(prev => [...prev, { role: 'assistant', content: clientResponse! }]);
            setIsLoading(false);
            return;
        }

        // 2. Call Real API for complex reasoning / unsaved settings
        try {
            // Construct agent config override from formData
            const agentConfig = getAgentConfig();

            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: input,
                    agent_id: agentId, // Optional, enables DB fallback
                    agent_config: agentConfig, // Override with current form data
                    history: newMsgs.map(m => ({ role: m.role, content: m.content }))
                })
            });

            if (!response.ok) throw new Error("Failed to get response");

            const data = await response.json();
            setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
        } catch (e) {
            setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I'm having trouble connecting to the preview server." }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={cn(
            "flex flex-col bg-white border rounded-lg overflow-hidden shadow-sm transition-all duration-500 ease-in-out",
            isTheaterMode ? "fixed inset-4 z-[100] h-auto" : "h-[600px]"
        )}>
            {/* Header */}
            <div
                className="p-4 flex items-center justify-between text-white shrink-0"
                style={{ backgroundColor: formData.accentColor }}
            >
                <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-full bg-white flex items-center justify-center overflow-hidden border border-white/20">
                        {formData.useTavusAvatar && (formData.avatarUrl || formData.widgetIconUrl) && !imgError ? (
                            (formData.widgetIconUrl || formData.avatarUrl) && (formData.widgetIconUrl || formData.avatarUrl).endsWith('.mp4') ? (
                                <video
                                    src={formData.widgetIconUrl || formData.avatarUrl}
                                    className="h-full w-full object-cover"
                                    autoPlay
                                    loop
                                    muted
                                    playsInline
                                    onError={(e) => {
                                        console.warn("Header video failed to load", e);
                                        setImgError(true);
                                    }}
                                />
                            ) : (
                                <img
                                    src={formData.widgetIconUrl || formData.avatarUrl}
                                    alt="Av"
                                    className="h-full w-full object-contain"
                                    onError={() => setImgError(true)}
                                />
                            )
                        ) : (!formData.useTavusAvatar && formData.widgetIconUrl && !imgError) ? (
                            <img
                                src={formData.widgetIconUrl}
                                alt="Widget Icon"
                                className="h-full w-full object-contain"
                                onError={() => setImgError(true)}
                            />
                        ) : (
                            <span className="text-xs font-bold text-gray-800">{formData.avatar || (formData.name ? formData.name.substring(0, 2).toUpperCase() : 'AI')}</span>
                        )}
                    </div>
                    <div>
                        <p className="font-semibold text-sm leading-none mb-1">{formData.name || "Agent"}</p>
                        <p className="text-xs opacity-90 leading-none">{formData.primaryFunction || "Assistant"}</p>
                    </div>
                </div>
                <div className="flex gap-1">
                    {mode === 'chat' && !formData.useTavusAvatar && (
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-white hover:bg-white/20 rounded-full"
                            onClick={() => setMode('voice')}
                            title="Switch to Voice"
                        >
                            <Phone className="h-4 w-4" />
                        </Button>
                    )}
                    {mode === 'chat' && formData.useTavusAvatar && (
                        <Button
                            variant="ghost"
                            size="icon"
                            className={cn(
                                "h-8 w-8 text-white rounded-full transition-all",
                                !formData.tavusReplicaId ? "opacity-40 cursor-not-allowed hover:bg-transparent" : "hover:bg-white/20"
                            )}
                            onClick={() => {
                                if (!formData.tavusReplicaId) {
                                    toast.error("Please select an avatar first");
                                    return;
                                }
                                setMode('avatar');
                            }}
                            title={!formData.tavusReplicaId ? "Select an avatar to enable video" : "Switch to Video"}
                        >
                            <Video className="h-4 w-4" />
                        </Button>
                    )}
                    {(mode === 'avatar' || (mode === 'chat' && isTheaterMode)) && (
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-white hover:bg-white/20 rounded-full"
                            onClick={() => setIsTheaterMode(!isTheaterMode)}
                            title={isTheaterMode ? "Exit Theater Mode" : "Expand Window"}
                        >
                            {isTheaterMode ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
                        </Button>
                    )}
                </div>
            </div>

            {/* Content */}
            {mode === 'chat' ? (
                <>
                    <div className="flex-1 p-4 bg-gray-50/50 overflow-y-auto" ref={scrollRef}>
                        <div className="space-y-4 max-w-3xl mx-auto">
                            {messages.map((m, i) => (
                                <div key={i} className={`flex gap-2 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    {m.role === 'assistant' && (
                                        <div className="w-8 h-8 rounded-full bg-white border flex items-center justify-center shrink-0 overflow-hidden">
                                            {formData.useTavusAvatar && formData.avatarUrl && !imgError ? (
                                                formData.avatarUrl && formData.avatarUrl.endsWith('.mp4') ? (
                                                    <video
                                                        src={formData.avatarUrl}
                                                        className="w-full h-full object-cover"
                                                        autoPlay
                                                        loop
                                                        muted
                                                        playsInline
                                                        onError={(e) => {
                                                            console.warn("Message video failed to load", e);
                                                            setImgError(true);
                                                        }}
                                                    />
                                                ) : (
                                                    <img
                                                        src={formData.avatarUrl}
                                                        alt="Bot"
                                                        className="w-full h-full object-cover"
                                                        onError={(e) => {
                                                            e.currentTarget.style.display = 'none';
                                                            setImgError(true);
                                                        }}
                                                    />
                                                )
                                            ) : (!formData.useTavusAvatar && formData.widgetIconUrl && !imgError) ? (
                                                <img
                                                    src={formData.widgetIconUrl}
                                                    alt="Bot Icon"
                                                    className="w-full h-full object-contain"
                                                    onError={(e) => {
                                                        e.currentTarget.style.display = 'none';
                                                        setImgError(true);
                                                    }}
                                                />
                                            ) : (
                                                <Bot className="h-5 w-5 text-gray-400" />
                                            )}
                                        </div>
                                    )}
                                    <div
                                        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm shadow-sm ${m.role === 'user'
                                            ? 'text-white'
                                            : 'bg-white border text-gray-800'
                                            }`}
                                        style={m.role === 'user' ? { backgroundColor: formData.accentColor } : {}}
                                    >
                                        {m.content}
                                    </div>
                                </div>
                            ))}
                            {/* Typing indicator */}
                            {isLoading && (
                                <div className="flex justify-start">
                                    <div className="bg-white border rounded-2xl px-4 py-2.5 shadow-sm">
                                        <div className="flex gap-1">
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="p-4 border-t bg-white shrink-0">
                        <form
                            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                            className="flex gap-2"
                        >
                            <Input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Type a message..."
                                className="flex-1"
                            />
                            <Button type="submit" size="icon" style={{ backgroundColor: formData.accentColor }}>
                                <Send className="h-4 w-4" />
                            </Button>
                        </form>
                        {!formData.removeBranding && (
                            <div className="text-center mt-3">
                                <span className="text-[10px] text-gray-400 font-medium">Powered by SupaAgent</span>
                            </div>
                        )}
                    </div>
                </>
            ) : (
                <div className="flex-1 bg-white relative">
                    {(token && url) ? (
                        <LiveKitRoom
                            key={`${token}-${mode}-${formData.tavusReplicaId}`}
                            token={token}
                            serverUrl={url}
                            connect={!!token}
                            audio={true}
                            video={mode === 'avatar'}
                            className="flex flex-col h-full w-full"
                            onDisconnected={() => {
                                if (!isReconnecting.current) {
                                    setMode('chat');
                                }
                            }}
                        >
                            {mode === 'avatar' ? (
                                <div className="flex-1 relative bg-slate-50 overflow-hidden group">
                                    <AvatarVideoStage
                                        formData={formData}
                                        pipSize={pipSize}
                                        setPipSize={setPipSize}
                                        onClose={() => setMode('chat')}
                                    />
                                </div>
                            ) : (
                                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center min-h-0 bg-white">
                                    <div className="flex-1 flex flex-col items-center justify-center gap-2 w-full">
                                        <div className="relative w-32 h-32 flex items-center justify-center">
                                            <div className="absolute inset-0 bg-blue-500/10 rounded-full animate-[pulse_3s_ease-in-out_infinite]" />
                                            <div className="absolute inset-4 bg-blue-500/20 rounded-full animate-[pulse_2s_ease-in-out_infinite]" />
                                            <div className="relative z-10 w-24 h-24 bg-gradient-to-b from-blue-500 to-blue-600 rounded-full shadow-xl flex items-center justify-center text-white ring-4 ring-white">
                                                <Phone className="h-10 w-10" />
                                            </div>
                                        </div>

                                        <div className="space-y-1 w-full">
                                            <VoiceStatusDisplay name={formData.name || "Agent"} />
                                        </div>

                                        <div className="h-8 w-full max-w-[200px] flex items-center justify-center">
                                            <CustomVisualizer accentColor={formData.accentColor} />
                                        </div>
                                    </div>

                                    <div className="w-full max-w-xs space-y-3 shrink-0 mb-4 z-10">
                                        <VoiceControlPanel onClose={() => setMode('chat')} />
                                    </div>
                                </div>
                            )}
                            <RoomAudioRenderer />
                            {mode === 'avatar' && <TranscriptOverlay />}
                        </LiveKitRoom>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                            {error ? (
                                <div className="text-red-500 space-y-4">
                                    <p className="font-semibold">Connection Failed</p>
                                    <p className="text-sm text-gray-500">{error}</p>
                                    <Button onClick={() => setMode('chat')} variant="outline">Go Back</Button>
                                </div>
                            ) : (
                                <div className="space-y-4 animate-pulse">
                                    <div className="h-24 w-24 rounded-full bg-gray-100 mx-auto" />
                                    <p className="text-sm text-gray-400">Connecting to voice server...</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function TranscriptOverlay() {
    const { state } = useVoiceAssistant();
    const segments = useTranscriptions();
    const [messages, setMessages] = useState<any[]>([]);

    useEffect(() => {
        if (segments && segments.length > 0) {
            setMessages(prev => {
                const newMessages = [...prev];
                (segments as any[]).forEach(seg => {
                    const existingIdx = newMessages.findIndex(m => m.id === seg.id);
                    if (existingIdx !== -1) {
                        newMessages[existingIdx] = { ...newMessages[existingIdx], text: seg.text, timestamp: Date.now() };
                    } else {
                        newMessages.push({
                            id: seg.id,
                            text: seg.text,
                            timestamp: Date.now()
                        });
                    }
                });
                // Keep only last 4 messages to avoid overcrowding
                return newMessages
                    .filter(m => Date.now() - m.timestamp < 6000)
                    .slice(-4);
            });
        }
    }, [segments]);

    // Secondary cleaner to remove stale messages
    useEffect(() => {
        const interval = setInterval(() => {
            setMessages(prev => prev.filter(m => Date.now() - m.timestamp < 6000));
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="absolute bottom-24 left-0 right-0 z-50 flex flex-col items-center justify-end px-6 pointer-events-none gap-2 overflow-hidden max-h-[40%]">
            <AnimatePresence mode="popLayout">
                {messages.map((m) => (
                    <motion.div
                        key={m.id}
                        layout
                        initial={{ opacity: 0, y: 20, scale: 0.9 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -60, scale: 0.8, transition: { duration: 0.4 } }}
                        className="bg-black/60 backdrop-blur-md px-5 py-2.5 rounded-2xl text-white text-sm md:text-base font-medium shadow-xl border border-white/10 max-w-[90%] text-center"
                    >
                        {m.text}
                    </motion.div>
                ))}
            </AnimatePresence>

            <AnimatePresence>
                {messages.length === 0 && state === 'thinking' && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        className="bg-blue-600/80 backdrop-blur-md px-4 py-1.5 rounded-full text-white text-[10px] uppercase tracking-wider font-bold shadow-lg border border-blue-400/30 mb-2"
                    >
                        Thinking...
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

function CustomControls({ onClose }: { onClose: () => void }) {
    const { localParticipant } = useLocalParticipant();
    const [isMuted, setIsMuted] = useState(false);
    const [isVideoOff, setIsVideoOff] = useState(true);

    const toggleMic = async () => {
        if (!localParticipant) return;
        const newState = !isMuted;
        await localParticipant.setMicrophoneEnabled(!newState);
        setIsMuted(newState);
    };

    const toggleCam = async () => {
        if (!localParticipant) return;
        const newState = !isVideoOff;
        await localParticipant.setCameraEnabled(!newState);
        setIsVideoOff(newState);
    };

    useEffect(() => {
        if (localParticipant) {
            setIsMuted(!localParticipant.isMicrophoneEnabled);
            setIsVideoOff(!localParticipant.isCameraEnabled);
        }
    }, [localParticipant]);

    return (
        <div className="flex items-center gap-3 p-2 rounded-full bg-white/80 dark:bg-black/60 backdrop-blur-md border border-slate-200 dark:border-white/10 shadow-2xl">
            <Button
                variant={isMuted ? "destructive" : "secondary"}
                size="icon"
                className="rounded-full h-10 w-10 shrink-0"
                onClick={toggleMic}
            >
                {isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </Button>
            <Button
                variant={isVideoOff ? "destructive" : "secondary"}
                size="icon"
                className="rounded-full h-10 w-10 shrink-0"
                onClick={toggleCam}
            >
                {isVideoOff ? <CameraOff className="h-4 w-4" /> : <Camera className="h-4 w-4" />}
            </Button>
            <div className="w-px h-6 bg-slate-200 dark:bg-white/20 mx-1" />
            <Button
                variant="destructive"
                size="icon"
                className="rounded-full h-10 w-10 shrink-0"
                onClick={onClose}
            >
                <Phone className="h-4 w-4 rotate-[135deg]" />
            </Button>
        </div>
    );
}

function VoiceStatusDisplay({ name }: { name: string }) {
    // ... (rest remains same)
    const { state } = useVoiceAssistant();
    const connectionState = useConnectionState();
    const { localParticipant } = useLocalParticipant();

    let statusText = "Connecting...";
    let statusColor = "bg-yellow-500";

    const currentRoomState = String(connectionState).toLowerCase();

    if (currentRoomState === "connected") {
        if (localParticipant && !localParticipant.isMicrophoneEnabled) {
            statusText = "Microphone Muted";
            statusColor = "bg-red-500";
        } else {
            switch (state) {
                case "connecting":
                    statusText = "Connecting...";
                    statusColor = "bg-yellow-500";
                    break;
                case "listening":
                    statusText = "Listening...";
                    statusColor = "bg-green-500";
                    break;
                case "thinking":
                    statusText = "Thinking...";
                    statusColor = "bg-purple-500";
                    break;
                case "speaking":
                    statusText = "Speaking...";
                    statusColor = "bg-blue-500";
                    break;
                default:
                    statusText = "Ready";
                    statusColor = "bg-green-500";
            }
        }
    } else if (currentRoomState === "connecting" || currentRoomState === "reconnecting") {
        statusText = "Connecting...";
        statusColor = "bg-yellow-500";
    } else {
        statusText = "Disconnected";
        statusColor = "bg-red-500";
    }

    return (
        <>
            <h3 className="font-semibold text-lg">{name}</h3>
            <div className="flex items-center gap-2 justify-center mt-1">
                <div className={cn("w-2 h-2 rounded-full animate-pulse", statusColor)} />
                <p className="text-sm text-muted-foreground transition-all duration-300">{statusText}</p>
            </div>
        </>
    );
}

function CustomVisualizer({ accentColor }: { accentColor: string }) {
    const { state, audioTrack } = useVoiceAssistant();

    return (
        <BarVisualizer
            state={state}
            barCount={5}
            trackRef={audioTrack}
            className="flex gap-1 h-full items-end justify-center w-full"
            style={{
                // @ts-ignore - LiveKit custom property for bar color if supported, otherwise handled by class
                "--lk-bar-color": accentColor
            }}
        />
    );
}

function VoiceControlPanel({ onClose, onDisconnect, isVideo }: { onClose: () => void; onDisconnect?: () => void; isVideo?: boolean }) {
    const { localParticipant } = useLocalParticipant();
    const [isMuted, setIsMuted] = useState(false);

    const toggleMute = async () => {
        if (!localParticipant) return;
        const newState = !isMuted;
        await localParticipant.setMicrophoneEnabled(!newState);
        setIsMuted(newState);
    };

    // Handle End Call - disconnect room first, then close
    const handleEndCall = async () => {
        try {
            // Stop audio tracks to immediately stop any audio
            if (localParticipant) {
                await localParticipant.setMicrophoneEnabled(false);
            }
            // Call disconnect callback if provided (uses room.disconnect())
            if (onDisconnect) {
                onDisconnect();
            }
        } catch (e) {
            console.error("Error during disconnect:", e);
        }
        // Switch to chat mode
        onClose();
    };

    // Auto-unmute on join/mount if possible
    useEffect(() => {
        if (localParticipant && !localParticipant.isMicrophoneEnabled) {
            localParticipant.setMicrophoneEnabled(true).catch(() => {
                // Autoplay policy might block this, user will have to click
                console.log("Auto-unmute blocked by browser");
            });
        }
    }, [localParticipant]);

    // Sync initial state
    useEffect(() => {
        if (localParticipant) {
            setIsMuted(!localParticipant.isMicrophoneEnabled);
        }
    }, [localParticipant]);

    return (
        <div className="flex flex-col gap-3 w-full items-center">
            <Button
                variant={isMuted ? "destructive" : "secondary"}
                className={`w-40 rounded-full shadow-md ${isMuted ? 'bg-red-100 text-red-600 hover:bg-red-200 border-red-200' : 'bg-white hover:bg-gray-100 border'}`}
                onClick={toggleMute}
            >
                {isMuted ? (
                    <>
                        <MicOff className="h-4 w-4 mr-2" />
                        Unmute
                    </>
                ) : (
                    <>
                        <Mic className="h-4 w-4 mr-2" />
                        Mute
                    </>
                )}
            </Button>
            <Button
                variant="destructive"
                className="w-40 rounded-full shadow-md"
                onClick={handleEndCall}
            >
                End Call
            </Button>

            <Button
                variant="ghost"
                size="sm"
                className="w-40 text-muted-foreground"
                onClick={onClose}
            >
                Switch to Chat
            </Button>
        </div>
    );
}

function AvatarVideoStage({ formData, onClose, pipSize, setPipSize }: { formData: any; onClose: () => void; pipSize: 'sm' | 'md' | 'lg'; setPipSize: (s: 'sm' | 'md' | 'lg') => void }) {
    const tracks = useTracks([Track.Source.Camera]);
    // Filter for remote camera (the avatar)
    const remoteTrack = tracks.find(t => t.participant.isLocal === false && t.source === Track.Source.Camera);
    // Filter for local camera (user preview)
    const localTrack = tracks.find(t => t.participant.isLocal === true && t.source === Track.Source.Camera);

    return (
        <div className="w-full h-full relative bg-slate-50 dark:bg-zinc-900 flex items-center justify-center">
            {!formData.tavusReplicaId ? (
                <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 p-8 text-center">
                    <div className="w-16 h-16 bg-amber-100 rounded-2xl flex items-center justify-center mb-4 text-amber-600">
                        <AlertTriangle className="h-8 w-8" />
                    </div>
                    <span className="text-sm font-semibold text-slate-800 mb-1">No Avatar Selected</span>
                    <p className="text-xs text-slate-500 max-w-[200px]">
                        Please select an avatar in Step 2 to enable video calls.
                    </p>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="mt-4 text-primary"
                        onClick={onClose}
                    >
                        Go Back
                    </Button>
                </div>
            ) : remoteTrack ? (
                <VideoTrack trackRef={remoteTrack} className="w-full h-full object-cover" />
            ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 animate-pulse">
                    <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mb-4 text-blue-600">
                        <Bot className="h-8 w-8 text-blue-600" />
                    </div>
                    <span className="text-sm font-medium">Connecting to Avatar...</span>
                </div>
            )}

            {/* PIP Self View */}
            {localTrack && (
                <div
                    className={cn(
                        "absolute top-4 right-4 bg-black rounded-xl overflow-hidden border border-white/20 shadow-2xl z-20 transition-all duration-300 group/pip",
                        pipSize === 'sm' ? "w-24 h-32" :
                            pipSize === 'md' ? "w-36 h-48" :
                                "w-52 h-72"
                    )}
                >
                    <VideoTrack trackRef={localTrack} className="w-full h-full object-cover mirror" />

                    {/* PIP Size Controls - Visible on PIP hover */}
                    <div className="absolute bottom-2 left-0 right-0 flex justify-center opacity-0 group-hover/pip:opacity-100 transition-opacity gap-1 px-2">
                        <button
                            onClick={(e) => { e.stopPropagation(); setPipSize('sm'); }}
                            className={cn("p-1 rounded-md bg-black/60 text-white hover:bg-white/20", pipSize === 'sm' && "text-blue-400")}
                            title="Small PIP"
                        >
                            <Square className="w-3 h-3" />
                        </button>
                        <button
                            onClick={(e) => { e.stopPropagation(); setPipSize('md'); }}
                            className={cn("p-1 rounded-md bg-black/60 text-white hover:bg-white/20", pipSize === 'md' && "text-blue-400")}
                            title="Medium PIP"
                        >
                            <Layout className="w-3 h-3" />
                        </button>
                        <button
                            onClick={(e) => { e.stopPropagation(); setPipSize('lg'); }}
                            className={cn("p-1 rounded-md bg-black/60 text-white hover:bg-white/20", pipSize === 'lg' && "text-blue-400")}
                            title="Large PIP"
                        >
                            <Monitor className="w-3 h-3" />
                        </button>
                    </div>
                </div>
            )}

            {/* Live Transcript Overlay */}
            <div className="absolute bottom-4 left-4 right-4 z-30 pointer-events-none">
                <TranscriptOverlay />
            </div>

            {/* Floating Controls */}
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-40 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <CustomControls onClose={onClose} />
            </div>
        </div>
    );
}
