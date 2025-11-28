import { User, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface ChatMessageProps {
    role: "user" | "assistant";
    content: string;
}

export function ChatMessage({ role, content }: ChatMessageProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                "flex w-full mb-4",
                role === "user" ? "justify-end" : "justify-start"
            )}
        >
            <div
                className={cn(
                    "flex items-end max-w-[85%] gap-3",
                    role === "user" ? "flex-row-reverse" : "flex-row"
                )}
            >
                <div
                    className={cn(
                        "h-10 w-10 rounded-full flex items-center justify-center shrink-0 shadow-modern-md-sm",
                        role === "user"
                            ? "bg-blue-500 text-white"
                            : "bg-card text-primary"
                    )}
                >
                    {role === "user" ? (
                        <User className="h-5 w-5" />
                    ) : (
                        <Bot className="h-5 w-5" />
                    )}
                </div>
                <div
                    className={cn(
                        "p-4 rounded-2xl text-sm leading-relaxed shadow-sm",
                        role === "user"
                            ? "bg-blue-500 text-white rounded-br-none shadow-modern-md-sm"
                            : "bg-card text-primary rounded-bl-none shadow-modern-md-sm"
                    )}
                >
                    {content}
                </div>
            </div>
        </motion.div>
    );
}
