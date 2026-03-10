'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Plus, Mail, MessageSquare, Clock, Trash2, Edit2, GripVertical } from 'lucide-react';
import { StepDialog } from './step-dialog';
import { Badge } from '@/components/ui/badge';

interface Step {
    id: string;
    type: 'sms' | 'email' | 'whatsapp' | 'wait';
    order_index: number;
    config: {
        template: string;
        subject?: string;
        timing?: {
            value: number;
            unit: 'minutes' | 'hours' | 'days';
            direction: 'before' | 'after';
            reference: 'appointment_date' | 'trigger_date';
        };
    };
}

interface StepBuilderProps {
    campaignId: string;
    steps: Step[];
    onUpdate: () => void;
}

export function StepBuilder({ campaignId, steps, onUpdate }: StepBuilderProps) {
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [editingStep, setEditingStep] = useState<Step | null>(null);

    const handleSave = async (stepData: any) => {
        try {
            const url = editingStep
                ? `/api/campaigns/${campaignId}/steps/${editingStep.id}`
                : `/api/campaigns/${campaignId}/steps`;

            const method = editingStep ? 'PATCH' : 'POST';

            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(stepData)
            });

            if (!res.ok) throw new Error("Failed to save step");

            onUpdate();
            setIsDialogOpen(false);
            setEditingStep(null);
        } catch (e) {
            console.error(e);
            alert("Failed to save step");
        }
    };

    const handleDelete = async (stepId: string) => {
        if (!confirm("Delete this step?")) return;
        try {
            await fetch(`/api/campaigns/${campaignId}/steps/${stepId}`, { method: 'DELETE' });
            onUpdate();
        } catch (e) {
            console.error(e);
        }
    };

    const openCreate = () => {
        setEditingStep(null);
        setIsDialogOpen(true);
    };

    const openEdit = (step: Step) => {
        setEditingStep(step);
        setIsDialogOpen(true);
    };

    const getIcon = (type: string) => {
        switch (type) {
            case 'email': return <Mail className="h-5 w-5" />;
            case 'whatsapp': return <MessageSquare className="h-5 w-5 text-green-600" />;
            case 'wait': return <Clock className="h-5 w-5" />;
            default: return <MessageSquare className="h-5 w-5" />;
        }
    };

    return (
        <div className="space-y-4">
            <div className="space-y-2">
                {(Array.isArray(steps) ? steps : []).sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0)).map((step, index) => (
                    <Card key={step.id} className="group relative">
                        <CardContent className="flex items-center gap-3 p-2">
                            <div className="cursor-move text-muted-foreground/50 pl-2">
                                <GripVertical className="h-4 w-4" />
                            </div>
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg border bg-muted/50 text-muted-foreground">
                                {getIcon(step.type)}
                            </div>
                            <div className="flex-1 space-y-1">
                                <div className="flex items-center gap-2">
                                    <span className="font-semibold capitalize">{step.type === 'wait' ? 'Wait / Delay' : step.type}</span>
                                    <Badge variant="outline" className="text-xs font-normal">Step {index + 1}</Badge>
                                </div>
                                <div className="text-sm text-muted-foreground line-clamp-1">
                                    {step.type === 'wait' ? (
                                        <span>Wait {step.config?.timing?.value} {step.config?.timing?.unit}</span>
                                    ) : (
                                        step.config?.template || "No content"
                                    )}
                                </div>
                            </div>
                            <div className="flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                                <Button variant="ghost" size="icon" onClick={() => openEdit(step)}>
                                    <Edit2 className="h-4 w-4" />
                                </Button>
                                <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive" onClick={() => handleDelete(step.id)}>
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <Button onClick={openCreate} className="w-full border-dashed" variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Add Step
            </Button>

            <StepDialog
                open={isDialogOpen}
                onOpenChange={setIsDialogOpen}
                step={editingStep}
                onSave={handleSave}
            />
        </div>
    );
}
