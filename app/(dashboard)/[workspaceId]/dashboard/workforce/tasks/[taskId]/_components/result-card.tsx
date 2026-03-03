"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, XCircle, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ResultTable } from "./result-table";

interface ResultCardProps {
    data: any;
    status: string;
}

export function ResultCard({ data, status }: ResultCardProps) {
    const [showDebug, setShowDebug] = useState(false);

    // If data is null/undefined
    if (!data) return null;

    // Determine if successful
    const isSuccess = status === "completed" && data?.status !== "error";

    // Check if it's an array (use ResultTable)
    const isArray = Array.isArray(data) || Object.values(data).some(v => Array.isArray(v));

    if (isArray && !showDebug) {
        return (
            <div className="space-y-4">
                <ResultTable data={data} />
                <div className="flex justify-end">
                    <Button variant="ghost" size="sm" onClick={() => setShowDebug(!showDebug)} className="text-muted-foreground">
                        {showDebug ? "Hide Debug Info" : "Show Debug Info"}
                    </Button>
                </div>
                {showDebug && <DebugView data={data} />}
            </div>
        );
    }

    return (
        <Card className={isSuccess ? "border-green-200 bg-green-50/10" : "border-red-200 bg-red-50/10"}>
            <CardHeader className="flex flex-row items-center justify-between">
                <div className="flex items-center gap-2">
                    {isSuccess ? (
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                    ) : (
                        <XCircle className="h-5 w-5 text-red-600" />
                    )}
                    <CardTitle className="text-lg">
                        {isSuccess ? "Task Completed Successfully" : "Task Failed"}
                    </CardTitle>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setShowDebug(!showDebug)}>
                    {showDebug ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    <span className="ml-1">{showDebug ? "Hide Debug" : "Show Debug"}</span>
                </Button>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Main Content */}
                <div className="grid grid-cols-1 gap-4">
                    {typeof data === 'object' ? (
                        Object.entries(data).map(([key, value]) => {
                            // Skip complex objects or long arrays in summary view
                            if (typeof value === 'object' && value !== null) return null;
                            if (key === 'status') return null; // Already shown in header

                            return (
                                <div key={key} className="flex flex-col space-y-1">
                                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                        {key.replace(/_/g, " ")}
                                    </span>
                                    <span className="text-sm font-medium break-words">
                                        {String(value)}
                                    </span>
                                </div>
                            );
                        })
                    ) : (
                        <div className="text-sm">{String(data)}</div>
                    )}
                </div>

                {/* Debug View */}
                {showDebug && <DebugView data={data} />}
            </CardContent>
        </Card>
    );
}

function DebugView({ data }: { data: any }) {
    return (
        <div className="mt-4 pt-4 border-t">
            <h4 className="text-sm font-medium text-muted-foreground mb-2">Raw Output</h4>
            <pre className="bg-muted p-4 rounded-lg text-xs overflow-auto max-h-96 font-mono">
                {JSON.stringify(data, null, 2)}
            </pre>
        </div>
    );
}
