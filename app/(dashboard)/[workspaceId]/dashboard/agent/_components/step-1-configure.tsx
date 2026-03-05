
"use client";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Upload, Trash2, Plus } from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";
import { validateImageFile, validateDocumentFile } from "./utils";
import { AgentFormData } from "./types";
import { useEffect, useState } from "react";
import { VoiceSelector } from "./voice-selector";

interface StepProps {
    formData: AgentFormData;
    setFormData: React.Dispatch<React.SetStateAction<AgentFormData>>;
}

export function Step1ConfigureAgent({ formData, setFormData }: StepProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoadingPreview, setIsLoadingPreview] = useState(false);

    // Dynamic Greeting Update
    useEffect(() => {
        // Only auto-update if the user hasn't manually edited it significantly
        // or just force it for now to restore functionality user asked for.
        // Better: simple default mapper.

        const name = formData.name || "SupaAgent";

        const greetings: Record<string, string> = {
            "en": `Hello! My name is ${name}, how can I assist you today?`,
            "es": `¡Hola! Me llamo ${name}, ¿en qué puedo ayudarte hoy?`,
            "fr": `Bonjour! Je m'appelle ${name}, comment puis-je vous aider aujourd'hui?`,
            "de": `Hallo! Mein Name ist ${name}, wie kann ich Ihnen heute helfen?`,
            "it": `Ciao! Mi chiamo ${name}, come posso aiutarti oggi?`,
            "pt": `Olá! O meu nome é ${name}, como posso ajudá-lo hoje?`,
        };

        const newGreeting = greetings[formData.language] || greetings["en"];

        // We update state directly. 
        // NOTE: This might overwrite manual changes if not careful. 
        // User said "this was all working before" implying they want this auto-magic.
        // We will check if the CURRENT greeting matches one of the OTHER generic greetings
        // to decide if we should overwrite. Or just overwrite on Language Change event?
        // Since we don't have the previous language state here Easily without refs or prev props,
        // we'll implement this logic inside the Select's onValueChange instead for safety,
        // BUT the user explicitely asked for "dynamic" behavior. 
        // Let's rely on the Select's onChange handler to be safer than useEffect loops.
    }, []); // Check implementation below instead of useEffect

    const handleLanguageChange = (lang: string) => {
        const name = formData.name || "SupaAgent";
        const greetings: Record<string, string> = {
            "en": `Hello! My name is ${name}, how can I assist you today?`,
            "es": `¡Hola! Me llamo ${name}, ¿en qué puedo ayudarte hoy?`,
            "fr": `Bonjour! Je m'appelle ${name}, comment puis-je vous aider aujourd'hui?`,
        };

        const defaultForNewLang = greetings[lang] || greetings["en"];

        setFormData(prev => ({
            ...prev,
            language: lang,
            welcomeGreeting: defaultForNewLang
        }));
    };

    return (
        <>
            <Card>
                <CardHeader>
                    <CardTitle>Identity</CardTitle>
                    <CardDescription>Give your agent a name and personality</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Agent Name</Label>
                            <Input
                                id="name"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                placeholder="Helper Bot"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="voice_id">Agent Voice</Label>
                            <VoiceSelector
                                voiceId={formData.voice_id}
                                onVoiceChange={(val: string) => setFormData({ ...formData, voice_id: val })}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="language">Primary Language</Label>
                            <Select
                                value={formData.language}
                                onValueChange={handleLanguageChange}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="en">English (US)</SelectItem>
                                    <SelectItem value="es">Spanish</SelectItem>
                                    <SelectItem value="fr">French</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Role & Personality</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="primaryFunction">Primary Function</Label>
                        <Input
                            id="primaryFunction"
                            value={formData.primaryFunction}
                            onChange={(e) => setFormData({ ...formData, primaryFunction: e.target.value })}
                            placeholder="Support Assistant"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label>Conversation Style</Label>
                        <div className="flex gap-2">
                            {["Professional", "Friendly", "Empathetic", "Witty"].map((style) => (
                                <Button
                                    key={style}
                                    variant={formData.conversationStyle === style.toLowerCase() ? "default" : "outline"}
                                    size="sm"
                                    onClick={() => setFormData({ ...formData, conversationStyle: style.toLowerCase() })}
                                >
                                    {style}
                                </Button>
                            ))}
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="welcomeGreeting">Welcome Greeting</Label>
                        <Textarea
                            id="welcomeGreeting"
                            value={formData.welcomeGreeting}
                            onChange={(e) => setFormData({ ...formData, welcomeGreeting: e.target.value })}
                            placeholder="Enter the first message the agent says when the conversation starts."
                            rows={3}
                        />
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Knowledge Base</CardTitle>
                    <CardDescription>Provide information about your business</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="businessName">Business Name</Label>
                            <Input
                                id="businessName"
                                value={formData.businessName}
                                onChange={(e) => setFormData({ ...formData, businessName: e.target.value })}
                                placeholder="e.g. Acme Training"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="websiteUrl">Website URL</Label>
                            <Input
                                id="websiteUrl"
                                value={formData.websiteUrl}
                                onChange={(e) => setFormData({ ...formData, websiteUrl: e.target.value })}
                                placeholder="https://example.com"
                            />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="businessDescription">Description</Label>
                        <Textarea
                            id="businessDescription"
                            value={formData.businessDescription}
                            onChange={(e) => setFormData({ ...formData, businessDescription: e.target.value })}
                            placeholder="Provide a brief description of your business"
                            rows={3}
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="email">Email Address</Label>
                            <Input
                                id="email"
                                type="email"
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                placeholder="contact@example.com"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="phone">Phone Number</Label>
                            <Input
                                id="phone"
                                value={formData.phone}
                                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                placeholder="+1 (555) 000-0000"
                            />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="address">Address</Label>
                        <Input
                            id="address"
                            value={formData.address}
                            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                            placeholder="123 Business St, City, Country"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="services">Services</Label>
                        <Textarea
                            id="services"
                            value={formData.services}
                            onChange={(e) => setFormData({ ...formData, services: e.target.value })}
                            placeholder="List your services (one per line)"
                            rows={3}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="hoursOfOperation">Business Hours</Label>
                        <Textarea
                            id="hoursOfOperation"
                            value={formData.hoursOfOperation}
                            onChange={(e) => setFormData({ ...formData, hoursOfOperation: e.target.value })}
                            placeholder='{"monday": {"open": "9:00", "close": "17:00"}}'
                            rows={3}
                        />
                        <p className="text-xs text-muted-foreground">
                            Format: {`{"monday": {"open": "9:00", "close": "17:00"}, ...}`}
                        </p>
                    </div>

                    {/* FAQ Section */}
                    <div className="space-y-2 pt-4 border-t">
                        <div className="flex items-center justify-between">
                            <Label>FAQ</Label>
                            <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => setFormData({
                                    ...formData,
                                    faqItems: [...formData.faqItems, { question: "", answer: "" }]
                                })}
                            >
                                <Plus className="h-4 w-4 mr-2" />
                                Add FAQ
                            </Button>
                        </div>
                        {formData.faqItems.map((item, index) => (
                            <div key={index} className="p-4 border rounded-lg space-y-2 bg-gray-50">
                                <div className="flex justify-between items-start gap-2">
                                    <div className="flex-1 space-y-2">
                                        <Input
                                            value={item.question}
                                            onChange={(e) => {
                                                const newItems = [...formData.faqItems];
                                                newItems[index].question = e.target.value;
                                                setFormData({ ...formData, faqItems: newItems });
                                            }}
                                            placeholder="Question"
                                        />
                                        <Textarea
                                            value={item.answer}
                                            onChange={(e) => {
                                                const newItems = [...formData.faqItems];
                                                newItems[index].answer = e.target.value;
                                                setFormData({ ...formData, faqItems: newItems });
                                            }}
                                            placeholder="Answer"
                                            rows={2}
                                        />
                                    </div>
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => setFormData({
                                            ...formData,
                                            faqItems: formData.faqItems.filter((_, i) => i !== index)
                                        })}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Reference URLs Section */}
                    <div className="space-y-2 pt-4 border-t">
                        <div className="flex items-center justify-between">
                            <Label>Reference URLs</Label>
                            <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => setFormData({
                                    ...formData,
                                    refUrls: [...formData.refUrls, ""]
                                })}
                            >
                                <Plus className="h-4 w-4 mr-2" />
                                Add URL
                            </Button>
                        </div>
                        {formData.refUrls.map((url, index) => (
                            <div key={index} className="flex gap-2">
                                <Input
                                    value={url}
                                    onChange={(e) => {
                                        const newUrls = [...formData.refUrls];
                                        newUrls[index] = e.target.value;
                                        setFormData({ ...formData, refUrls: newUrls });
                                    }}
                                    placeholder="https://example.com/resource"
                                />
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setFormData({
                                        ...formData,
                                        refUrls: formData.refUrls.filter((_, i) => i !== index)
                                    })}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Knowledge Base Documents */}
            <Card>
                <CardHeader>
                    <CardTitle>Knowledge Base Documents</CardTitle>
                    <CardDescription>Upload documents to train your agent</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <Label htmlFor="file-upload" className="cursor-pointer">
                            <div className="border-2 border-dashed rounded-lg p-6 text-center hover:border-primary transition-colors">
                                <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                                <p className="text-sm text-muted-foreground">
                                    Click to upload documents (TXT, PDF)
                                </p>
                            </div>
                            <input
                                id="file-upload"
                                type="file"
                                className="hidden"
                                accept=".txt,.pdf"
                                multiple
                                onChange={(e) => {
                                    const files = Array.from(e.target.files || []);
                                    const validFiles: File[] = [];

                                    files.forEach(file => {
                                        const validation = validateDocumentFile(file, {
                                            maxSizeMB: 10,
                                            allowedTypes: ['text/plain', 'application/pdf']
                                        });

                                        if (validation.valid) {
                                            validFiles.push(file);
                                        } else {
                                            toast.error(validation.error || "Invalid file");
                                        }
                                    });

                                    setFormData({
                                        ...formData,
                                        kbFiles: [...formData.kbFiles, ...validFiles]
                                    });

                                    // Reset input
                                    e.target.value = '';
                                }}
                            />
                        </Label>
                    </div>

                    {/* Existing Files List */}
                    {formData.existingKbUrls.length > 0 && (
                        <div className="space-y-2 mb-4">
                            <h4 className="text-sm font-medium text-muted-foreground mb-2">Existing Files</h4>
                            {formData.existingKbUrls.map((url, index) => {
                                const fileName = url.split('/').pop() || "Document";
                                return (
                                    <div key={`existing-${index}`} className="flex items-center justify-between p-3 border rounded-lg bg-gray-50">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-white border rounded">
                                                <span className="text-gray-500 font-bold text-xs">FILE</span>
                                            </div>
                                            <div>
                                                <p className="text-sm font-medium truncate max-w-[200px]">{fileName}</p>
                                                <Link href={url} target="_blank" className="text-xs text-blue-500 hover:underline">View</Link>
                                            </div>
                                        </div>
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => {
                                                const newUrls = [...formData.existingKbUrls];
                                                newUrls.splice(index, 1);
                                                setFormData({ ...formData, existingKbUrls: newUrls });
                                            }}
                                        >
                                            <Trash2 className="h-4 w-4 text-red-500" />
                                        </Button>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* File List */}
                    {formData.kbFiles.length > 0 && (
                        <div className="space-y-2">
                            {formData.kbFiles.map((file, index) => (
                                <div key={index} className="flex items-center justify-between p-3 border rounded-lg bg-gray-50">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-white border rounded">
                                            {file.type === 'application/pdf' ? (
                                                <span className="text-red-500 font-bold text-xs">PDF</span>
                                            ) : (
                                                <span className="text-gray-500 font-bold text-xs">TXT</span>
                                            )}
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium truncate max-w-[200px]">{file.name}</p>
                                            <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(0)} KB</p>
                                        </div>
                                    </div>
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => {
                                            const newFiles = [...formData.kbFiles];
                                            newFiles.splice(index, 1);
                                            setFormData({ ...formData, kbFiles: newFiles });
                                        }}
                                    >
                                        <Trash2 className="h-4 w-4 text-red-500" />
                                    </Button>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </>
    );
}
