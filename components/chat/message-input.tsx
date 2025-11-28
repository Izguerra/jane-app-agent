import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send } from "lucide-react";

interface MessageInputProps {
    onSendMessage: (message: string) => void;
    isLoading: boolean;
}

export function MessageInput({ onSendMessage, isLoading }: MessageInputProps) {
    const [inputValue, setInputValue] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputValue.trim() || isLoading) return;
        onSendMessage(inputValue.trim());
        setInputValue("");
    };

    return (
        <div className="p-4 bg-card">
            <form onSubmit={handleSubmit} className="flex gap-3 items-center">
                <div className="flex-1 relative">
                    <Input
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Type a message..."
                        disabled={isLoading}
                        className="w-full  rounded-full h-12 px-6 focus-visible:ring-0 focus-visible:ring-offset-0 placeholder:text-gray-400"
                    />
                </div>
                <Button
                    type="submit"
                    size="icon"
                    disabled={isLoading}
                    className="h-12 w-12 rounded-full  shrink-0"
                >
                    <Send className="h-5 w-5" />
                </Button>
            </form>
        </div>
    );
}
