"use client";

import { useEffect, useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, User, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import dynamic from 'next/dynamic';
const Markdown = dynamic(() => import('markdown-to-jsx'), { ssr: false });

type Message = {
    role: 'user' | 'ai';
    content: string;
};

interface ChatSessionProps {
    workspaceId?: number; // If provided, uses public API. If not, uses authenticated API.
    className?: string;
    embedded?: boolean;
    agentId?: string; // Add agentId to props
}

export function ChatSession({ workspaceId, className, embedded, agentId }: ChatSessionProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [initializing, setInitializing] = useState(true);
    const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Endpoints based on mode
    const settingsUrl = agentId
        ? `/api/agents/${agentId}/settings?translate=true`
        : workspaceId
            ? `/api/public/agent-settings/${workspaceId}?translate=true`
            : "/api/public/active-agent-settings?translate=true";

    const chatUrl = workspaceId
        ? `/api/public/chat/${workspaceId}`
        : "/api/chat";

    // Fetch language setting and set initial greeting
    useEffect(() => {
        const fetchLanguageAndSetGreeting = async () => {
            try {
                const response = await fetch(settingsUrl);
                if (!response.ok) throw new Error("Failed to fetch settings");

                const settings = await response.json();
                const language = settings.language || 'en';

                const greetings: Record<string, string> = {
                    en: "Hi there! I'm SupaAgent. How can I help you today?",
                    es: "¡Hola! Soy SupaAgent. ¿Cómo puedo ayudarte hoy?",
                    fr: "Bonjour! Je suis SupaAgent. Comment puis-je vous aider aujourd'hui?",
                    de: "Hallo! Ich bin SupaAgent. Wie kann ich Ihnen heute helfen?",
                    it: "Ciao! Sono SupaAgent. Come posso aiutarti oggi?",
                    pt: "Olá! Eu sou a SupaAgent. Como posso ajudar hoje?",
                    zh: "你好！我是SupaAgent。今天有什么可以帮你的吗？",
                    ja: "こんにちは！SupaAgentです。今日はどのようなご用件でしょうか？",
                    ko: "안녕하세요! SupaAgent입니다. 오늘 어떻게 도와드릴까요?",
                    uk: "Привіт! Я SupaAgent. Як я можу вам допомогти сьогодні?"
                };

                // Use custom welcome message if set, otherwise use localized default
                const greeting = settings.welcome_message || greetings[language] || greetings.en;
                setMessages([{ role: 'ai', content: greeting }]);

                if (settings.avatar_url) {
                    setAvatarUrl(settings.avatar_url);
                }
            } catch (error) {
                console.error("Failed to fetch language setting:", error);
                setMessages([{ role: 'ai', content: "Hi there! I'm SupaAgent. How can I help you today?" }]);
            } finally {
                setInitializing(false);
            }
        };

        fetchLanguageAndSetGreeting();
    }, [settingsUrl]);

    const scrollToBottom = () => {
        if (scrollRef.current) {
            const { scrollHeight, clientHeight } = scrollRef.current;
            scrollRef.current.scrollTo({
                top: scrollHeight - clientHeight,
                behavior: 'smooth'
            });
        }
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const [sessionId, setSessionId] = useState("");


    // Initialize session ID
    useEffect(() => {
        // If embedded (public widget), try to persist session
        // If preview (dashboard), generate fresh every time
        let sid = "";
        if (embedded) {
            sid = localStorage.getItem("supa_agent_session_id") || "";
        }

        // Migration: Ensure prefix for consistency
        if (sid && !sid.startsWith("ann_")) {
            sid = `ann_${sid}`;
            if (embedded) localStorage.setItem("supa_agent_session_id", sid);
        }

        if (!sid) {
            sid = `ann_${crypto.randomUUID()}`;
            if (embedded) {
                localStorage.setItem("supa_agent_session_id", sid);
            }
        }
        setSessionId(sid);
    }, [embedded]);

    const sendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userMsg = input.trim();
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setInput("");
        setIsLoading(true);

        try {
            const body: any = {
                message: userMsg,
                history: messages,
                session_id: sessionId
            };
            if (agentId) {
                body.agent_id = agentId;
            }

            const response = await fetch(chatUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || "Failed to send message");
            }
            if (!response.body) throw new Error("No response body");

            setIsLoading(false); // Hide typing indicator once we get the stream
            setMessages(prev => [...prev, { role: 'ai', content: "" }]);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                setMessages(prev => {
                    const newMessages = [...prev];
                    newMessages[newMessages.length - 1] = {
                        ...newMessages[newMessages.length - 1],
                        content: newMessages[newMessages.length - 1].content + chunk
                    };
                    return newMessages;
                });
            }
        } catch (error: any) {
            toast.error(error.message || "Failed to send message");
            console.error(error);
            setIsLoading(false);
        }
    };

    return (
        <div className={cn("flex flex-col h-full bg-background min-h-0", className)}>
            <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0" ref={scrollRef}>
                {messages.map((msg, i) => (
                    <div
                        key={i}
                        className={cn(
                            "flex w-full gap-2",
                            msg.role === 'user' ? "justify-end" : "justify-start"
                        )}
                    >
                        {msg.role === 'ai' && (
                            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 overflow-hidden">
                                {avatarUrl ? (
                                    <img src={avatarUrl} alt="AI" className="w-full h-full object-cover" />
                                ) : (
                                    <Bot className="h-5 w-5 text-primary" />
                                )}
                            </div>
                        )}
                        <div
                            className={cn(
                                "max-w-[80%] px-4 py-2 rounded-2xl text-sm",
                                msg.role === 'user'
                                    ? "bg-blue-600 text-white rounded-tr-none"
                                    : "bg-white dark:bg-zinc-800 border shadow-sm rounded-tl-none"
                            )}
                        >
                            <MessageContent content={msg.content} />
                        </div>
                        {msg.role === 'user' && (
                            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                                <User className="h-5 w-5 text-white" />
                            </div>
                        )}
                    </div>
                ))}
                {isLoading && (
                    <div className="flex justify-start gap-2">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 overflow-hidden">
                            {avatarUrl ? (
                                <img src={avatarUrl} alt="AI" className="w-full h-full object-cover" />
                            ) : (
                                <Bot className="h-5 w-5 text-primary" />
                            )}
                        </div>
                        <div className="bg-white dark:bg-zinc-800 px-4 py-2 rounded-2xl rounded-tl-none border shadow-sm">
                            <div className="flex gap-1">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                            </div>
                        </div>
                    </div>
                )}
                {/* Scroll anchor removed */}
            </div>
            <div className="p-4 bg-background border-t shrink-0">
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        sendMessage();
                    }}
                    className="flex gap-2"
                >
                    <Input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type a message..."
                        className="rounded-full"
                    />
                    <Button
                        type="submit"
                        size="icon"
                        className="rounded-full shrink-0"
                        disabled={!input.trim() || isLoading}
                    >
                        <Send className="h-4 w-4" />
                    </Button>
                </form>
            </div>
        </div>
    );
}

function MessageContent({ content }: { content: string }) {
    return (
        <div className="prose prose-sm dark:prose-invert max-w-none break-words prose-p:leading-relaxed prose-pre:p-0">
            <Markdown
                options={{
                    overrides: {
                        a: {
                            component: ({ children, ...props }: React.HTMLProps<HTMLAnchorElement>) => (
                                <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline font-medium break-all">
                                    {children}
                                </a>
                            )
                        }
                    }
                }}
            >
                {content}
            </Markdown>
        </div>
    );
}
