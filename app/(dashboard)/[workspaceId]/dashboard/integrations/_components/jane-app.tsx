"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { ChevronDown, ChevronUp } from "lucide-react";
import { toggleIntegration } from "./utils";

interface JaneAppIntegrationProps {
    integrations: any[];
    expanded: string | null;
    onToggleExpand: (provider: string) => void;
}

export function JaneAppIntegration({ integrations, expanded, onToggleExpand }: JaneAppIntegrationProps) {
    const isExpanded = expanded === 'jane';
    const isActive = integrations?.some((i: any) => i.provider === 'jane' && i.is_active) ?? false;

    return (
        <Card>
            <CardHeader className="cursor-pointer" onClick={() => onToggleExpand('jane')}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <CardTitle>Jane App</CardTitle>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                    <Switch
                        checked={isActive}
                        onCheckedChange={(c) => toggleIntegration('jane', c)}
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
                <CardDescription>Connect your Jane App clinic management system</CardDescription>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-4">
                    <div className="p-4 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg text-sm border border-yellow-200 dark:border-yellow-800">
                        <p className="font-semibold text-yellow-700 dark:text-yellow-500">⚠️ Integration Not Yet Implemented</p>
                        <p className="mt-2 text-xs text-yellow-600 dark:text-yellow-400">Jane App integration is planned for a future release. For now, please use Google Calendar or Microsoft Exchange for appointment management.</p>
                    </div>
                </CardContent>
            )}
        </Card>
    );
}
