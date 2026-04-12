'use client';

import { useState } from 'react';
import useSWR, { mutate } from 'swr';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog';
import { Globe, FileText, Loader2, Plus, Trash2, RefreshCw, Pause, Play } from 'lucide-react';



interface KnowledgeBaseSource {
    id: string;
    workspace_id: string;
    source_type: string;
    name: string;
    config: Record<string, any>;
    status: string;
    last_synced_at: string | null;
    document_count: number;
    error_message: string | null;
    created_at: string;
    updated_at: string;
}

import { useParams } from 'next/navigation';

export default function KnowledgeBasePage() {
    const params = useParams();
    const workspaceId = params.workspaceId as string;

    const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
    const [selectedSourceType, setSelectedSourceType] = useState<string | null>(null);
    const [websiteUrl, setWebsiteUrl] = useState('');
    const [sourceName, setSourceName] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const { data: sources, error } = useSWR<KnowledgeBaseSource[]>(
        `/api/workspaces/${workspaceId}/knowledge-base/sources`
    );

    const handleAddSource = async () => {
        if (!selectedSourceType || !sourceName) return;

        setIsSubmitting(true);
        try {
            const config = selectedSourceType === 'website_crawler'
                ? { url: websiteUrl }
                : { file_path: '' }; // File upload will be handled separately

            const response = await fetch(`/api/workspaces/${workspaceId}/knowledge-base/sources`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer DEVELOPER_BYPASS'
                },
                body: JSON.stringify({
                    source_type: selectedSourceType,
                    name: sourceName,
                    config,
                }),
            });

            if (response.ok) {
                mutate(`/api/workspaces/${workspaceId}/knowledge-base/sources`);
                setIsAddDialogOpen(false);
                setSelectedSourceType(null);
                setWebsiteUrl('');
                setSourceName('');
            }
        } catch (error) {
            console.error('Error adding source:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleSync = async (sourceId: string) => {
        try {
            await fetch(`/api/workspaces/${workspaceId}/knowledge-base/sources/${sourceId}/sync`, {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer DEVELOPER_BYPASS'
                }
            });
            mutate(`/api/workspaces/${workspaceId}/knowledge-base/sources`);
        } catch (error) {
            console.error('Error syncing source:', error);
        }
    };

    const handlePause = async (sourceId: string) => {
        try {
            await fetch(`/api/workspaces/${workspaceId}/knowledge-base/sources/${sourceId}/pause`, {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer DEVELOPER_BYPASS'
                }
            });
            mutate(`/api/workspaces/${workspaceId}/knowledge-base/sources`);
        } catch (error) {
            console.error('Error pausing source:', error);
        }
    };

    const handleResume = async (sourceId: string) => {
        try {
            await fetch(`/api/workspaces/${workspaceId}/knowledge-base/sources/${sourceId}/resume`, {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer DEVELOPER_BYPASS'
                }
            });
            mutate(`/api/workspaces/${workspaceId}/knowledge-base/sources`);
        } catch (error) {
            console.error('Error resuming source:', error);
        }
    };

    const handleDelete = async (sourceId: string) => {
        if (!confirm('Are you sure you want to delete this source?')) return;

        try {
            await fetch(`/api/workspaces/${workspaceId}/knowledge-base/sources/${sourceId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': 'Bearer DEVELOPER_BYPASS'
                }
            });
            mutate(`/api/workspaces/${workspaceId}/knowledge-base/sources`);
        } catch (error) {
            console.error('Error deleting source:', error);
        }
    };

    const getStatusBadge = (status: string) => {
        const variants: Record<string, { variant: any; label: string }> = {
            pending: { variant: 'secondary', label: 'Pending' },
            syncing: { variant: 'default', label: 'Syncing...' },
            active: { variant: 'default', label: 'Active' },
            error: { variant: 'destructive', label: 'Error' },
            paused: { variant: 'secondary', label: 'Paused' },
        };
        const config = variants[status] || variants.pending;
        return <Badge variant={config.variant}>{config.label}</Badge>;
    };

    return (
        <div className="p-6 space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Knowledge Base Sources</h1>
                    <p className="text-muted-foreground mt-1">
                        Connect your data sources to train the AI agent. The agent will automatically index content from connected sources to answer user queries.
                    </p>
                </div>
                <Button onClick={() => setIsAddDialogOpen(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Source
                </Button>
            </div>

            {/* Add Source Dialog */}
            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Add Knowledge Base Source</DialogTitle>
                        <DialogDescription>
                            Connect a data source to train your AI agent
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        {!selectedSourceType ? (
                            <div className="grid grid-cols-2 gap-4">
                                <Card
                                    className="cursor-pointer hover:border-primary transition-colors"
                                    onClick={() => setSelectedSourceType('website_crawler')}
                                >
                                    <CardHeader>
                                        <Globe className="w-8 h-8 mb-2 text-primary" />
                                        <CardTitle className="text-lg">Website Crawler</CardTitle>
                                        <CardDescription>
                                            Enter a URL to automatically crawl and index pages
                                        </CardDescription>
                                    </CardHeader>
                                </Card>
                                <Card
                                    className="cursor-pointer hover:border-primary transition-colors"
                                    onClick={() => setSelectedSourceType('file_upload')}
                                >
                                    <CardHeader>
                                        <FileText className="w-8 h-8 mb-2 text-primary" />
                                        <CardTitle className="text-lg">Upload Files</CardTitle>
                                        <CardDescription>
                                            PDF, TXT, CSV, or MD files manually
                                        </CardDescription>
                                    </CardHeader>
                                </Card>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                <div>
                                    <Label htmlFor="sourceName">Source Name</Label>
                                    <Input
                                        id="sourceName"
                                        placeholder="e.g., Company Website"
                                        value={sourceName}
                                        onChange={(e) => setSourceName(e.target.value)}
                                    />
                                </div>
                                {selectedSourceType === 'website_crawler' && (
                                    <div>
                                        <Label htmlFor="websiteUrl">Website URL</Label>
                                        <Input
                                            id="websiteUrl"
                                            type="url"
                                            placeholder="https://example.com"
                                            value={websiteUrl}
                                            onChange={(e) => setWebsiteUrl(e.target.value)}
                                        />
                                    </div>
                                )}
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        onClick={() => {
                                            setSelectedSourceType(null);
                                            setWebsiteUrl('');
                                            setSourceName('');
                                        }}
                                    >
                                        Back
                                    </Button>
                                    <Button
                                        onClick={handleAddSource}
                                        disabled={isSubmitting || !sourceName || (selectedSourceType === 'website_crawler' && !websiteUrl)}
                                    >
                                        {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                                        Add Source
                                    </Button>
                                </div>
                            </div>
                        )}
                    </div>
                </DialogContent>
            </Dialog>

            {/* Active Sources */}
            <div>
                <h2 className="text-xl font-semibold mb-4">Active Connections</h2>
                {!sources ? (
                    <div className="flex justify-center py-12">
                        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                    </div>
                ) : sources.length === 0 ? (
                    <Card>
                        <CardContent className="py-12 text-center text-muted-foreground">
                            No sources connected yet. Add a source to get started.
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid gap-4">
                        {sources.map((source) => (
                            <Card key={source.id}>
                                <CardHeader>
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-start gap-3">
                                            {source.source_type === 'website_crawler' ? (
                                                <Globe className="w-5 h-5 mt-1 text-primary" />
                                            ) : (
                                                <FileText className="w-5 h-5 mt-1 text-primary" />
                                            )}
                                            <div>
                                                <CardTitle>{source.name}</CardTitle>
                                                <CardDescription className="mt-1">
                                                    {source.source_type === 'website_crawler' && source.config.url}
                                                    {source.source_type === 'file_upload' && 'File upload'}
                                                </CardDescription>
                                                <div className="flex items-center gap-2 mt-2">
                                                    {getStatusBadge(source.status)}
                                                    <span className="text-sm text-muted-foreground">
                                                        {source.document_count} documents
                                                    </span>
                                                    {source.last_synced_at && (
                                                        <span className="text-sm text-muted-foreground">
                                                            • Last synced {new Date(source.last_synced_at).toLocaleString()}
                                                        </span>
                                                    )}
                                                </div>
                                                {source.error_message && (
                                                    <p className="text-sm text-destructive mt-2">{source.error_message}</p>
                                                )}
                                            </div>
                                        </div>
                                        <div className="flex gap-2">
                                            {source.status === 'paused' ? (
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => handleResume(source.id)}
                                                >
                                                    <Play className="w-4 h-4" />
                                                </Button>
                                            ) : (
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => handlePause(source.id)}
                                                    disabled={source.status === 'syncing'}
                                                >
                                                    <Pause className="w-4 h-4" />
                                                </Button>
                                            )}
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleSync(source.id)}
                                                disabled={source.status === 'syncing'}
                                            >
                                                <RefreshCw className={`w-4 h-4 ${source.status === 'syncing' ? 'animate-spin' : ''}`} />
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleDelete(source.id)}
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </CardHeader>
                            </Card>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
