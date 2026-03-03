"use client";

import { Building2, User, Sparkles, Shield, Globe, Zap } from "lucide-react";
import { AgentFormData } from "./types";

interface StepTypeSelectionProps {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
    onSelect: () => void;
}

export function StepTypeSelection({ formData, setFormData, onSelect }: StepTypeSelectionProps) {
    const handleSelect = (type: "business" | "personal") => {
        setFormData(prev => ({
            ...prev,
            agentType: type,
            // Pre-configure personal agents with all capabilities
            ...(type === "personal" ? {
                conversationStyle: "casual",
                allowedWorkerTypes: [
                    "web-research", "job-search", "email-worker",
                    "flight-tracker", "map-worker", "weather-worker",
                    "openclaw"
                ],
            } : {}),
        }));
        // Auto-advance after selection
        setTimeout(() => onSelect(), 150);
    };

    return (
        <div className="space-y-8">
            <div className="text-center space-y-2">
                <h2 className="text-3xl font-bold text-gray-900">What kind of agent do you want to build?</h2>
                <p className="text-gray-500 text-lg">Choose the type that best fits your use case. You can always adjust settings later.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto mt-8">
                {/* Business Agent Card */}
                <button
                    onClick={() => handleSelect("business")}
                    className={`group relative p-8 rounded-2xl border-2 text-left transition-all duration-200 hover:shadow-xl hover:scale-[1.02] ${formData.agentType === "business"
                            ? "border-blue-500 bg-blue-50/50 shadow-lg ring-2 ring-blue-200"
                            : "border-gray-200 bg-white hover:border-blue-300"
                        }`}
                >
                    <div className="absolute top-4 right-4">
                        {formData.agentType === "business" && (
                            <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center">
                                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                        )}
                    </div>

                    <div className="w-14 h-14 rounded-xl bg-blue-100 flex items-center justify-center mb-4 group-hover:bg-blue-200 transition-colors">
                        <Building2 className="w-7 h-7 text-blue-600" />
                    </div>

                    <h3 className="text-xl font-bold text-gray-900 mb-2">Business Agent</h3>
                    <p className="text-gray-500 mb-6">Represents your company. Answers customer questions, books appointments, and manages orders with strict guardrails.</p>

                    <div className="space-y-3">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Shield className="w-4 h-4 text-blue-500 flex-shrink-0" />
                            <span>Strict scope control &amp; guardrails</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Building2 className="w-4 h-4 text-blue-500 flex-shrink-0" />
                            <span>Business identity &amp; branding</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Zap className="w-4 h-4 text-blue-500 flex-shrink-0" />
                            <span>Selective tool permissions</span>
                        </div>
                    </div>

                    <div className="mt-6 pt-4 border-t border-gray-100">
                        <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Best for</span>
                        <p className="text-sm text-gray-600 mt-1">Customer support, sales, appointment booking, e-commerce</p>
                    </div>
                </button>

                {/* Personal Agent Card */}
                <button
                    onClick={() => handleSelect("personal")}
                    className={`group relative p-8 rounded-2xl border-2 text-left transition-all duration-200 hover:shadow-xl hover:scale-[1.02] ${formData.agentType === "personal"
                            ? "border-purple-500 bg-purple-50/50 shadow-lg ring-2 ring-purple-200"
                            : "border-gray-200 bg-white hover:border-purple-300"
                        }`}
                >
                    <div className="absolute top-4 right-4">
                        {formData.agentType === "personal" && (
                            <div className="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center">
                                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                        )}
                    </div>

                    <div className="w-14 h-14 rounded-xl bg-purple-100 flex items-center justify-center mb-4 group-hover:bg-purple-200 transition-colors">
                        <User className="w-7 h-7 text-purple-600" />
                    </div>

                    <h3 className="text-xl font-bold text-gray-900 mb-2">Personal Agent</h3>
                    <p className="text-gray-500 mb-6">Your own AI assistant. Knows your preferences, browses the web, and manages your daily life with full capabilities.</p>

                    <div className="space-y-3">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Globe className="w-4 h-4 text-purple-500 flex-shrink-0" />
                            <span>Web browsing &amp; open-ended conversations</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Sparkles className="w-4 h-4 text-purple-500 flex-shrink-0" />
                            <span>Personalized to your preferences</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Zap className="w-4 h-4 text-purple-500 flex-shrink-0" />
                            <span>All tools &amp; skills enabled by default</span>
                        </div>
                    </div>

                    <div className="mt-6 pt-4 border-t border-gray-100">
                        <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Best for</span>
                        <p className="text-sm text-gray-600 mt-1">Personal assistant, research, travel planning, life management</p>
                    </div>
                </button>
            </div>
        </div>
    );
}
