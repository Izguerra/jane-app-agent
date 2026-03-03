'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { RichTextEditor } from '@/components/ui/rich-text-editor';
import { Mail, MessageSquare, Clock } from 'lucide-react';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';

interface StepDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    step?: any;
    onSave: (data: any) => void;
}

export function StepDialog({ open, onOpenChange, step, onSave }: StepDialogProps) {
    const [type, setType] = useState('sms');
    const [subject, setSubject] = useState('');
    const [content, setContent] = useState('');
    const [htmlContent, setHtmlContent] = useState('');

    // Timing State
    const [timingValue, setTimingValue] = useState('2');
    const [timingUnit, setTimingUnit] = useState('minutes');
    const [timingDirection, setTimingDirection] = useState('before');
    const [timingReference, setTimingReference] = useState('appointment_date');

    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (step) {
            setType(step.type);
            setSubject(step.config?.subject || '');
            setContent(step.config?.template || '');
            setHtmlContent(step.config?.html_template || step.config?.template || '');
            if (step.config?.timing) {
                setTimingValue(step.config.timing.value.toString());
                setTimingUnit(step.config.timing.unit);
                setTimingDirection(step.config.timing.direction);
                setTimingReference(step.config.timing.reference);
            }
        } else {
            resetForm();
        }
    }, [step, open]);

    const resetForm = () => {
        setType('sms');
        setSubject('');
        setContent('');
        setHtmlContent('');
        setTimingValue('15');
        setTimingUnit('minutes');
        setTimingDirection('before');
        setTimingReference('appointment_date');
    };

    const handleImageUpload = async (file: File): Promise<string> => {
        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch('/api/uploads', {
            method: 'POST',
            body: formData,
        });

        if (!res.ok) {
            throw new Error('Upload failed');
        }

        const data = await res.json();
        return data.url;
    };

    const handleSave = () => {
        setIsSaving(true);
        const isEmail = type === 'email';

        const config: any = {
            // For email, store both plain text version (for preview) and HTML
            template: isEmail ? stripHtml(htmlContent) : content,
            html_template: isEmail ? htmlContent : undefined,
            subject: isEmail ? subject : undefined,
            timing: {
                value: parseInt(timingValue),
                unit: timingUnit,
                direction: timingDirection,
                reference: timingReference
            }
        };

        const payload = {
            type,
            order_index: step?.order_index || 0,
            config
        };

        onSave(payload);
        setTimeout(() => setIsSaving(false), 500);
    };

    // Simple HTML stripper for preview text
    const stripHtml = (html: string): string => {
        const tmp = document.createElement('div');
        tmp.innerHTML = html;
        return tmp.textContent || tmp.innerText || '';
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>{step ? 'Edit Step Settings' : 'Add Step'}</DialogTitle>
                    <DialogDescription>Configure the message and timing for this step.</DialogDescription>
                </DialogHeader>

                <div className="py-6 space-y-8">
                    {/* Channel Selector */}
                    <ToggleGroup type="single" value={type} onValueChange={(val) => val && setType(val)} className="justify-start gap-4">
                        <ToggleGroupItem value="sms" className="flex-col h-24 w-24 gap-2 border-2 data-[state=on]:border-primary data-[state=on]:bg-primary/5">
                            <MessageSquare className="h-6 w-6" />
                            <span className="text-xs font-medium">SMS</span>
                        </ToggleGroupItem>
                        <ToggleGroupItem value="whatsapp" className="flex-col h-24 w-24 gap-2 border-2 data-[state=on]:border-primary data-[state=on]:bg-primary/5">
                            <MessageSquare className="h-6 w-6 text-green-600" />
                            <span className="text-xs font-medium">WhatsApp</span>
                        </ToggleGroupItem>
                        <ToggleGroupItem value="email" className="flex-col h-24 w-24 gap-2 border-2 data-[state=on]:border-primary data-[state=on]:bg-primary/5">
                            <Mail className="h-6 w-6" />
                            <span className="text-xs font-medium">Email</span>
                        </ToggleGroupItem>
                        <ToggleGroupItem value="wait" className="flex-col h-24 w-24 gap-2 border-2 data-[state=on]:border-primary data-[state=on]:bg-primary/5">
                            <Clock className="h-6 w-6" />
                            <span className="text-xs font-medium">Wait / Delay</span>
                        </ToggleGroupItem>
                    </ToggleGroup>

                    {/* Timing */}
                    <div className="space-y-4">
                        <Label className="text-xs uppercase text-muted-foreground font-semibold tracking-wider">Timing & Scheduling</Label>
                        <div className="flex items-center gap-2">
                            <div className="flex items-center gap-2 bg-muted/50 p-1 rounded-md border">
                                <span className="pl-3 text-sm font-medium">Run</span>
                                <Input
                                    type="number"
                                    className="w-16 h-8 text-center bg-background"
                                    value={timingValue}
                                    onChange={(e) => setTimingValue(e.target.value)}
                                />
                            </div>

                            <Select value={timingUnit} onValueChange={setTimingUnit}>
                                <SelectTrigger className="w-[110px]">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="minutes">Minutes</SelectItem>
                                    <SelectItem value="hours">Hours</SelectItem>
                                    <SelectItem value="days">Days</SelectItem>
                                </SelectContent>
                            </Select>

                            <Select value={timingDirection} onValueChange={setTimingDirection}>
                                <SelectTrigger className="w-[100px]">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="before">Before</SelectItem>
                                    <SelectItem value="after">After</SelectItem>
                                </SelectContent>
                            </Select>

                            <Select value={timingReference} onValueChange={(val: any) => setTimingReference(val)}>
                                <SelectTrigger className="flex-1 min-w-[180px]">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="appointment_date">Appointment Date</SelectItem>
                                    <SelectItem value="trigger_date">Trigger Date</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    {/* Message Content */}
                    {type !== 'wait' && (
                        <div className="space-y-4">
                            <Label className="text-xs uppercase text-muted-foreground font-semibold tracking-wider">Message Content</Label>

                            {type === 'email' && (
                                <div className="space-y-2">
                                    <Label>Subject Line</Label>
                                    <Input
                                        placeholder="e.g. Reminder: Your Appointment"
                                        value={subject}
                                        onChange={(e) => setSubject(e.target.value)}
                                    />
                                </div>
                            )}

                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <Label>Body</Label>
                                </div>

                                {type === 'email' ? (
                                    // Rich text editor for email
                                    <RichTextEditor
                                        content={htmlContent}
                                        onChange={setHtmlContent}
                                        placeholder="Write your email content here..."
                                        onImageUpload={handleImageUpload}
                                    />
                                ) : (
                                    // Plain text for SMS/WhatsApp
                                    <>
                                        <div className="text-xs text-muted-foreground bg-muted/50 p-3 rounded-md border mb-2">
                                            <span className="font-medium block mb-1">Available Variables:</span>
                                            <div className="flex flex-wrap gap-2">
                                                <code className="bg-background px-1.5 py-0.5 rounded text-[11px]">{'{{first_name}}'}</code>
                                                <code className="bg-background px-1.5 py-0.5 rounded text-[11px]">{'{{last_name}}'}</code>
                                                <code className="bg-background px-1.5 py-0.5 rounded text-[11px]">{'{{appointment_date}}'}</code>
                                                <code className="bg-background px-1.5 py-0.5 rounded text-[11px]">{'{{appointment_id}}'}</code>
                                            </div>
                                        </div>
                                        <Textarea
                                            className="min-h-[150px] resize-y"
                                            placeholder="Type your message here..."
                                            value={content}
                                            onChange={(e) => setContent(e.target.value)}
                                        />
                                    </>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
                    <Button onClick={handleSave} disabled={isSaving}>
                        {isSaving ? 'Saving...' : 'Save Step'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
