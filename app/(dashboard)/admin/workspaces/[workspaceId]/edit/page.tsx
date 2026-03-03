'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import useSWR, { mutate } from 'swr';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { ArrowLeft, Save } from 'lucide-react';
import Link from 'next/link';
import { toast } from 'sonner';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface WorkspaceDetails {
    id: string;
    name: string;
    owner_email: string;
    owner_name: string;
    owner_first_name: string;
    owner_last_name: string;
    phone: string | null;
    address: string | null;
    website: string | null;
}

export default function EditWorkspacePage() {
    const params = useParams();
    const router = useRouter();
    const workspaceId = params?.workspaceId as string;

    const { data: workspace, error, isLoading } = useSWR<WorkspaceDetails>(
        workspaceId ? `/api/workspaces/${workspaceId}` : null,
        fetcher
    );

    const [formData, setFormData] = useState({
        workspace_name: '',
        owner_first_name: '',
        owner_last_name: '',
        owner_email: '',
        phone: '',
        address: '',
        website: '',
    });

    const [isSaving, setIsSaving] = useState(false);

    // Initialize form data when workspace loads
    useEffect(() => {
        if (workspace) {
            setFormData({
                workspace_name: workspace.name || '',
                owner_first_name: workspace.owner_first_name || '',
                owner_last_name: workspace.owner_last_name || '',
                owner_email: workspace.owner_email || '',
                phone: workspace.phone || '',
                address: workspace.address || '',
                website: workspace.website || '',
            });
        }
    }, [workspace]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSaving(true);

        try {
            const response = await fetch(`/api/workspaces/${workspaceId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });

            if (response.ok) {
                toast.success('Workspace details updated successfully');
                mutate(`/api/workspaces/${workspaceId}`);
                mutate('/api/workspaces');
                router.push(`/admin/workspaces/${workspaceId}`);
            } else {
                const error = await response.json();
                toast.error(error.detail || 'Failed to update workspace');
            }
        } catch (error) {
            toast.error('An error occurred while saving');
        } finally {
            setIsSaving(false);
        }
    };

    if (isLoading) {
        return (
            <div className="p-8">
                <div className="text-muted-foreground">Loading...</div>
            </div>
        );
    }

    if (error || !workspace) {
        return (
            <div className="p-8">
                <div className="text-destructive">Failed to load workspace details</div>
            </div>
        );
    }

    return (
        <div className="p-8 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex flex-row items-center gap-2 flex-nowrap">
                    <Button variant="ghost" size="sm" asChild>
                        <Link href={`/admin/workspaces/${workspaceId}`} className="flex items-center gap-2">
                            <ArrowLeft className="h-4 w-4" />
                            <span>Back to Details</span>
                        </Link>
                    </Button>
                </div>
            </div>

            {/* Title */}
            <div>
                <h1 className="text-3xl font-bold">Edit Workspace Details</h1>
                <p className="text-muted-foreground mt-1">Update workspace and owner information</p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Workspace Information */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Workspace Information</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <Label htmlFor="workspace_name">Workspace Name (Company)</Label>
                                <Input
                                    id="workspace_name"
                                    name="workspace_name"
                                    value={formData.workspace_name}
                                    onChange={handleChange}
                                    placeholder="Enter workspace name"
                                    required
                                />
                            </div>

                            <div>
                                <Label htmlFor="phone">Phone Number</Label>
                                <Input
                                    id="phone"
                                    name="phone"
                                    type="tel"
                                    value={formData.phone}
                                    onChange={handleChange}
                                    placeholder="+1 (555) 123-4567"
                                />
                            </div>

                            <div>
                                <Label htmlFor="website">Website</Label>
                                <Input
                                    id="website"
                                    name="website"
                                    type="url"
                                    value={formData.website}
                                    onChange={handleChange}
                                    placeholder="https://example.com"
                                />
                            </div>

                            <div>
                                <Label htmlFor="address">Address</Label>
                                <Textarea
                                    id="address"
                                    name="address"
                                    value={formData.address}
                                    onChange={handleChange}
                                    placeholder="Enter business address"
                                    rows={3}
                                />
                            </div>
                        </CardContent>
                    </Card>

                    {/* Owner Information */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Owner Information</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <Label htmlFor="owner_first_name">First Name</Label>
                                <Input
                                    id="owner_first_name"
                                    name="owner_first_name"
                                    value={formData.owner_first_name}
                                    onChange={handleChange}
                                    placeholder="John"
                                    required
                                />
                            </div>

                            <div>
                                <Label htmlFor="owner_last_name">Last Name</Label>
                                <Input
                                    id="owner_last_name"
                                    name="owner_last_name"
                                    value={formData.owner_last_name}
                                    onChange={handleChange}
                                    placeholder="Doe"
                                    required
                                />
                            </div>

                            <div>
                                <Label htmlFor="owner_email">Email Address</Label>
                                <Input
                                    id="owner_email"
                                    name="owner_email"
                                    type="email"
                                    value={formData.owner_email}
                                    onChange={handleChange}
                                    placeholder="john@example.com"
                                    required
                                />
                            </div>

                            <div className="pt-4">
                                <p className="text-sm text-muted-foreground">
                                    Changing the email address will update the owner's login credentials.
                                </p>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-end gap-4 mt-6">
                    <Button
                        type="button"
                        variant="outline"
                        onClick={() => router.push(`/admin/workspaces/${workspaceId}`)}
                    >
                        Cancel
                    </Button>
                    <Button type="submit" disabled={isSaving}>
                        <Save className="h-4 w-4 mr-2" />
                        {isSaving ? 'Saving...' : 'Save Changes'}
                    </Button>
                </div>
            </form>
        </div>
    );
}
