"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Hammer, Database, TextCursorInput, Eye, Zap, Info } from "lucide-react";
import { AgentFormData } from "../../_components/types";

interface Step5Props {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
}

interface Capability {
    id: string;
    name: string;
    description: string;
    icon: React.ReactNode;
    color: string;
}

const BROWSER_CAPABILITIES: Capability[] = [
    {
        id: "extraction",
        name: "Structured Data Extraction",
        description: "Extracting tables, prices, and JSON data from complex web pages.",
        icon: <Database className="h-5 w-5 text-white" />,
        color: "bg-blue-600"
    },
    {
        id: "form-filling",
        name: "Intelligent Form Interaction",
        description: "Handling logins, checkouts, and multi-step registrations using your profile context.",
        icon: <TextCursorInput className="h-5 w-5 text-white" />,
        color: "bg-purple-600"
    },
    {
        id: "visual-reasoning",
        name: "Visual Verification",
        description: "Analyze screenshots to handle visual-only elements (e.g., pop-ups, maps).",
        icon: <Eye className="h-5 w-5 text-white" />,
        color: "bg-emerald-600"
    },
    {
        id: "autonomous-navigation",
        name: "Multi-Domain Navigation",
        description: "Ability to jump between different websites to complete a single complex task.",
        icon: <Zap className="h-5 w-5 text-white" />,
        color: "bg-blue-600"
    }
];

export function Step5BrowserCapabilities({ formData, setFormData }: Step5Props) {
    const handleToggle = (id: string) => {
        setFormData(prev => {
            const current = new Set(prev.allowedWorkerTypes || []);
            // For now, we store these in allowedWorkerTypes with a prefix or just as slugs
            // In the backend, 'openclaw' is the worker type, but we can treat these as 'skills'
            const slug = `openclaw:${id}`;
            if (current.has(slug)) {
                current.delete(slug);
            } else {
                current.add(slug);
            }
            return {
                ...prev,
                allowedWorkerTypes: Array.from(current)
            };
        });
    };

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Hammer className="h-5 w-5 text-indigo-600" />
                        Browser Skills & Automation
                    </CardTitle>
                    <CardDescription>
                        Enable specific browsing capabilities. The agent will use these tools to fulfill your requests.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {BROWSER_CAPABILITIES.map((cap) => {
                            const isSelected = formData.allowedWorkerTypes?.includes(`openclaw:${cap.id}`);
                            return (
                                <div
                                    key={cap.id}
                                    onClick={() => handleToggle(cap.id)}
                                    className={`
                                        relative p-5 rounded-2xl border transition-all cursor-pointer flex flex-col gap-3
                                        hover:shadow-lg
                                        ${isSelected
                                            ? 'border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500'
                                            : 'border-slate-100 bg-white shadow-sm hover:border-slate-300'
                                        }
                                    `}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2.5 rounded-xl shrink-0 ${cap.color}`}>
                                            {cap.icon}
                                        </div>
                                        <div>
                                            <h4 className="font-bold text-slate-900 leading-tight">{cap.name}</h4>
                                            {isSelected && (
                                                <Badge variant="secondary" className="mt-1 text-[10px] bg-indigo-200 text-indigo-700 border-0">
                                                    Enabled
                                                </Badge>
                                            )}
                                        </div>
                                    </div>
                                    <p className="text-sm text-slate-500 leading-relaxed">
                                        {cap.description}
                                    </p>
                                </div>
                            );
                        })}
                    </div>
                </CardContent>
            </Card>

            <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 flex gap-3">
                <Info className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
                <div className="space-y-1">
                    <p className="text-sm font-semibold text-blue-900">Personalized Automation</p>
                    <p className="text-sm text-blue-700 leading-relaxed">
                        When 'Form Interaction' is enabled, the agent will securely use the personal details provided in the previous step to assist with bookings and purchases.
                    </p>
                </div>
            </div>
        </div>
    );
}
