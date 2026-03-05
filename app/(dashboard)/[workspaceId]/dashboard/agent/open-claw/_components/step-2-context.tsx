"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { CardDescription } from "@/components/ui/card";
import { AgentFormData } from "../../_components/types";
import { User, Building2, Heart } from "lucide-react";

interface Step2Props {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
}

export function Step2Context({ formData, setFormData }: Step2Props) {
    const handleChange = (field: keyof AgentFormData, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    return (
        <div className="space-y-8">
            {/* User Profile */}
            <div className="space-y-4">
                <div className="flex items-center gap-2 mb-2">
                    <User className="h-5 w-5 text-blue-600" />
                    <h3 className="font-semibold text-lg">Personal Profile</h3>
                </div>
                <CardDescription>
                    Provide your contact details so the agent can fill out forms and book appointments on your behalf.
                </CardDescription>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Label htmlFor="user_email">Your Email</Label>
                        <Input
                            id="user_email"
                            value={formData.user_email || ""}
                            onChange={(e) => handleChange("user_email", e.target.value)}
                            placeholder="you@example.com"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="user_phone">Your Phone</Label>
                        <Input
                            id="user_phone"
                            value={formData.user_phone || ""}
                            onChange={(e) => handleChange("user_phone", e.target.value)}
                            placeholder="+1 (555) 000-0000"
                        />
                    </div>
                </div>
            </div>

            {/* Business/Identity Context */}
            <div className="space-y-4 pt-6 border-t font-sans">
                <div className="flex items-center gap-2 mb-2">
                    <Building2 className="h-5 w-5 text-indigo-600" />
                    <h3 className="font-semibold text-lg">Business & Identity Context</h3>
                </div>
                <CardDescription>
                    If this agent acts on behalf of your business, provide that context here.
                </CardDescription>

                <div className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="businessName">Business Name</Label>
                        <Input
                            id="businessName"
                            value={formData.businessName}
                            onChange={(e) => handleChange("businessName", e.target.value)}
                            placeholder="e.g. Acme Corp"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="businessDescription">Bio / Business Description</Label>
                        <Textarea
                            id="businessDescription"
                            value={formData.businessDescription}
                            onChange={(e) => handleChange("businessDescription", e.target.value)}
                            placeholder="e.g. A boutique marketing agency specializing in local SEO..."
                            rows={3}
                        />
                    </div>
                </div>
            </div>

            {/* Personal Preferences */}
            <div className="space-y-4 pt-6 border-t">
                <div className="flex items-center gap-2 mb-2">
                    <Heart className="h-5 w-5 text-pink-600" />
                    <h3 className="font-semibold text-lg">Personal Preferences</h3>
                </div>
                <CardDescription>
                    List any habits, preferences, or strict rules for the agent (e.g., flight preferences, seating, dietary restrictions).
                </CardDescription>

                <div className="space-y-2">
                    <Label htmlFor="personalPreferences">Specific Rules & Preferences</Label>
                    <Textarea
                        id="personalPreferences"
                        value={formData.personalPreferences || ""}
                        onChange={(e) => handleChange("personalPreferences", e.target.value)}
                        placeholder="e.g. Always prefer aisle seats. I have a platinum status with Marriott. Never book flights before 10 AM..."
                        rows={4}
                    />
                </div>
            </div>
        </div>
    );
}
