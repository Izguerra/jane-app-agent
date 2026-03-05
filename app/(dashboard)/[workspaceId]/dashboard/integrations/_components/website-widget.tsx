"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { ChevronDown, ChevronUp } from "lucide-react";
import { toast } from "sonner";

interface WebsiteWidgetProps {
    workspaceId: string;
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function WebsiteWidget({ workspaceId, expanded, onToggleExpand }: WebsiteWidgetProps) {
    const isExpanded = expanded === 'website';

    return (
        <Card>
            <CardHeader className="cursor-pointer" onClick={() => onToggleExpand('website')}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <CardTitle>Website Widget</CardTitle>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                    <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onToggleExpand('website'); }}>
                        {isExpanded ? 'Hide' : 'Show'}
                    </Button>
                </div>
                <CardDescription>Embed the chat widget on your website (Shopify, WordPress, etc.)</CardDescription>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-4">
                    <div className="p-4 bg-muted rounded-lg space-y-2">
                        <Label>Embed Code</Label>
                        <p className="text-sm text-muted-foreground">Copy and paste this code into your website's HTML (e.g., inside a custom HTML block or theme file).</p>
                        <div className="relative">
                            <pre className="p-4 bg-zinc-950 text-zinc-50 rounded-lg overflow-x-auto text-sm">
                                {`<iframe
  src="${typeof window !== 'undefined' ? window.location.origin : 'https://app.supaagent.com'}/embed/chat/${workspaceId || 'YOUR_WORKSPACE_ID'}"
  width="100%"
  height="600px"
  style="border: none; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);"
></iframe>`}
                            </pre>
                            <Button
                                size="sm"
                                variant="secondary"
                                className="absolute top-2 right-2"
                                onClick={() => {
                                    const code = `<iframe
  src="${window.location.origin}/embed/chat/${workspaceId || 'YOUR_WORKSPACE_ID'}"
  width="100%"
  height="600px"
  style="border: none; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);"
></iframe>`;
                                    navigator.clipboard.writeText(code);
                                    toast.success("Code copied to clipboard");
                                }}
                            >
                                Copy
                            </Button>
                        </div>
                    </div>
                </CardContent>
            )}
        </Card>
    );
}
