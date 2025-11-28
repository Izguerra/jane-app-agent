"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState, useEffect } from "react";
import useSWR, { mutate } from "swr";
import { toast } from "sonner";
import { Plus, Trash2, Upload } from "lucide-react";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function BusinessProfilePage() {
    const { data: business, error } = useSWR("/api/clinics/me", fetcher);
    const { data: documents } = useSWR("/api/clinics/documents", fetcher, {
        shouldRetryOnError: false,
        onError: (err) => console.log("Documents fetch failed (optional):", err)
    });
    const [isLoading, setIsLoading] = useState(false);
    const [faqItems, setFaqItems] = useState<Array<{ question: string, answer: string }>>([]);
    const [refUrls, setRefUrls] = useState<string[]>([]);

    useEffect(() => {
        if (business) {
            try {
                setFaqItems(JSON.parse(business.faq || "[]"));
                setRefUrls(JSON.parse(business.reference_urls || "[]"));
            } catch (e) {
                setFaqItems([]);
                setRefUrls([]);
            }
        }
    }, [business]);

    async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsLoading(true);

        const formData = new FormData(event.currentTarget);
        const data = {
            name: formData.get("name"),
            address: formData.get("address"),
            phone: formData.get("phone"),
            website: formData.get("website"),
            description: formData.get("description"),
            services: formData.get("services"),
            business_hours: formData.get("business_hours"),
            faq: JSON.stringify(faqItems),
            reference_urls: JSON.stringify(refUrls),
        };

        try {
            const response = await fetch("/api/clinics/me", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                throw new Error("Failed to update business profile");
            }

            await mutate("/api/clinics/me");
            toast.success("Business profile updated successfully");
        } catch (error) {
            toast.error("Failed to update business profile");
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    }

    async function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
        const file = event.target.files?.[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("/api/clinics/documents", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) throw new Error("Upload failed");

            await mutate("/api/clinics/documents");
            toast.success("Document uploaded successfully");
        } catch (error) {
            toast.error("Failed to upload document");
        }
    }

    async function deleteDocument(id: number) {
        try {
            await fetch(`/api/clinics/documents/${id}`, { method: "DELETE" });
            await mutate("/api/clinics/documents");
            toast.success("Document deleted");
        } catch (error) {
            toast.error("Failed to delete document");
        }
    }

    if (error) return <div>Failed to load business data</div>;
    if (!business) return <div>Loading...</div>;

    return (
        <div className="max-w-4xl mx-auto py-8 space-y-6">
            <h1 className="text-2xl font-bold mb-6">Business Profile</h1>

            <Card className="card-modern">
                <CardHeader>
                    <CardTitle>General Information</CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={onSubmit} className="space-y-6">
                        <div className="space-y-2">
                            <Label htmlFor="name">Business Name</Label>
                            <Input
                                id="name"
                                name="name"
                                defaultValue={business.name}
                                placeholder="Acme Dental"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="description">Description</Label>
                            <Textarea
                                id="description"
                                name="description"
                                defaultValue={business.description}
                                placeholder="Tell customers about your business..."
                                rows={3}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="address">Address</Label>
                            <Input
                                id="address"
                                name="address"
                                defaultValue={business.address}
                                placeholder="123 Main St, City, State 12345"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="phone">Phone</Label>
                                <Input
                                    id="phone"
                                    name="phone"
                                    defaultValue={business.phone}
                                    placeholder="(555) 123-4567"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="website">Website</Label>
                                <Input
                                    id="website"
                                    name="website"
                                    defaultValue={business.website}
                                    placeholder="https://example.com"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="services">Services</Label>
                            <Textarea
                                id="services"
                                name="services"
                                defaultValue={business.services}
                                placeholder="List your services (one per line)"
                                rows={3}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="business_hours">Business Hours (JSON)</Label>
                            <Textarea
                                id="business_hours"
                                name="business_hours"
                                defaultValue={business.business_hours}
                                placeholder='{"monday": {"open": "9:00", "close": "17:00"}}'
                                rows={3}
                            />
                            <p className="text-xs text-muted-foreground">
                                Format: {`{"monday": {"open": "9:00", "close": "17:00"}, ...}`}
                            </p>
                        </div>

                        <div className="pt-4">
                            <Button
                                type="submit"
                                className="w-full sm:w-auto"
                                disabled={isLoading}
                            >
                                {isLoading ? "Saving..." : "Save Changes"}
                            </Button>
                        </div>
                    </form>
                </CardContent>
            </Card>

            {/* FAQ Section */}
            <Card className="card-modern">
                <CardHeader>
                    <CardTitle>FAQ</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {faqItems.map((item, index) => (
                        <div key={index} className="p-4 border rounded-lg space-y-2">
                            <div className="flex justify-between items-start">
                                <div className="flex-1 space-y-2">
                                    <Input
                                        value={item.question}
                                        onChange={(e) => {
                                            const newItems = [...faqItems];
                                            newItems[index].question = e.target.value;
                                            setFaqItems(newItems);
                                        }}
                                        placeholder="Question"
                                    />
                                    <Textarea
                                        value={item.answer}
                                        onChange={(e) => {
                                            const newItems = [...faqItems];
                                            newItems[index].answer = e.target.value;
                                            setFaqItems(newItems);
                                        }}
                                        placeholder="Answer"
                                        rows={2}
                                    />
                                </div>
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setFaqItems(faqItems.filter((_, i) => i !== index))}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                    ))}
                    <Button
                        type="button"
                        variant="outline"
                        onClick={() => setFaqItems([...faqItems, { question: "", answer: "" }])}
                    >
                        <Plus className="h-4 w-4 mr-2" />
                        Add FAQ
                    </Button>
                </CardContent>
            </Card>

            {/* Reference URLs */}
            <Card className="card-modern">
                <CardHeader>
                    <CardTitle>Reference URLs</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {refUrls.map((url, index) => (
                        <div key={index} className="flex gap-2">
                            <Input
                                value={url}
                                onChange={(e) => {
                                    const newUrls = [...refUrls];
                                    newUrls[index] = e.target.value;
                                    setRefUrls(newUrls);
                                }}
                                placeholder="https://example.com/resource"
                            />
                            <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() => setRefUrls(refUrls.filter((_, i) => i !== index))}
                            >
                                <Trash2 className="h-4 w-4" />
                            </Button>
                        </div>
                    ))}
                    <Button
                        type="button"
                        variant="outline"
                        onClick={() => setRefUrls([...refUrls, ""])}
                    >
                        <Plus className="h-4 w-4 mr-2" />
                        Add URL
                    </Button>
                </CardContent>
            </Card>

            {/* Knowledge Documents */}
            <Card className="card-modern">
                <CardHeader>
                    <CardTitle>Knowledge Base Documents</CardTitle>
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
                                onChange={handleFileUpload}
                            />
                        </Label>
                    </div>

                    {documents && documents.length > 0 && (
                        <div className="space-y-2">
                            {documents.map((doc: any) => (
                                <div key={doc.id} className="flex items-center justify-between p-3 border rounded-lg">
                                    <div>
                                        <p className="font-medium">{doc.filename}</p>
                                        <p className="text-xs text-muted-foreground">
                                            {new Date(doc.uploaded_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => deleteDocument(doc.id)}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
