import { useRef, useEffect } from "react";
import { ChatMessage } from "./chat-message";
import { Loader2 } from "lucide-react";

interface Message {
    role: "user" | "assistant";
    content: string;
}

interface MessageListProps {
    messages: Message[];
    isLoading: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    return (
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
                <div className="text-center text-muted-foreground mt-10">
                    <p>Hi! I'm Jane.</p>
                    <p>How can I help you today?</p>
                </div>
            )}
            {messages.map((msg, index) => (
                <ChatMessage key={index} role={msg.role} content={msg.content} />
            ))}
            {isLoading && (
                <div className="flex justify-start">
                    <div className="flex items-center gap-2 bg-muted p-3 rounded-lg">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm">Thinking...</span>
                    </div>
                </div>
            )}
            <div ref={messagesEndRef} />
        </div>
    );
}
