'use client';

import { useState, useEffect } from 'react';
import useSWR, { mutate } from 'swr';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Settings, Shield, Key, Puzzle, Check, X, Copy, Trash2 } from 'lucide-react';
import Link from 'next/link';

const fetcher = (url: string) => fetch(url, { credentials: 'include' }).then((res) => res.json());

type Tab = 'general' | 'security' | 'api-keys' | 'integrations';

interface GeneralSettings {
    company_name: string;
    support_email: string;
    default_language: string;
    timezone: string;
}

interface SecurityOverview {
    two_factor_enabled: boolean;
    password_last_changed: string | null;
    active_sessions_count: number;
}

interface ActiveSession {
    id: string;
    device_name: string;
    location: string;
    ip_address: string;
    last_active_at: string;
    created_at: string;
}

interface APIKey {
    id: string;
    name: string;
    key_prefix: string;
    last_used_at: string | null;
    created_at: string;
}

interface PlatformIntegration {
    id: string;
    provider: string;
    display_name: string;
    description: string;
    is_enabled: boolean;
    customer_count: number;
    health_status: string;
    last_checked: string | null;
}

export default function AdminSettingsPage() {
    const [activeTab, setActiveTab] = useState<Tab>('general');
    const [formData, setFormData] = useState<GeneralSettings>({
        company_name: '',
        support_email: '',
        default_language: 'en-US',
        timezone: 'America/New_York',
    });
    const [isSaving, setIsSaving] = useState(false);
    const [newApiKeyName, setNewApiKeyName] = useState('');
    const [generatedKey, setGeneratedKey] = useState<string | null>(null);
    const [testResult, setTestResult] = useState<{ provider: string; status: string; message: string } | null>(null);

    const { data: generalSettings, error: generalError } = useSWR<GeneralSettings>(
        '/api/admin/settings/general',
        fetcher
    );
    const { data: securityOverview } = useSWR<SecurityOverview>('/api/admin/settings/security', fetcher);
    const { data: activeSessions } = useSWR<ActiveSession[]>('/api/admin/settings/security/sessions', fetcher);
    const { data: apiKeys } = useSWR<APIKey[]>('/api/admin/settings/api-keys', fetcher);
    const { data: integrations } = useSWR<PlatformIntegration[]>('/api/admin/settings/integrations', fetcher);


    // Update form when data loads
    useEffect(() => {
        if (generalSettings) {
            setFormData(generalSettings);
        }
    }, [generalSettings]);

    const handleSaveGeneral = async () => {
        setIsSaving(true);
        try {
            const response = await fetch('/api/admin/settings/general', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(formData),
            });

            if (response.ok) {
                mutate('/api/admin/settings/general');
                alert('Settings saved successfully!');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            alert('Failed to save settings');
        } finally {
            setIsSaving(false);
        }
    };

    const handleGenerateAPIKey = async () => {
        if (!newApiKeyName.trim()) {
            alert('Please enter a name for the API key');
            return;
        }

        try {
            const response = await fetch('/api/admin/settings/api-keys', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ name: newApiKeyName }),
            });

            if (response.ok) {
                const data = await response.json();
                setGeneratedKey(data.key);
                setNewApiKeyName('');
                mutate('/api/admin/settings/api-keys');
            }
        } catch (error) {
            console.error('Error generating API key:', error);
            alert('Failed to generate API key');
        }
    };

    const handleDeleteAPIKey = async (keyId: string) => {
        if (!confirm('Are you sure you want to delete this API key?')) return;

        try {
            const response = await fetch(`/api/admin/settings/api-keys/${keyId}`, {
                method: 'DELETE',
                credentials: 'include',
            });

            if (response.ok) {
                mutate('/api/admin/settings/api-keys');
            }
        } catch (error) {
            console.error('Error deleting API key:', error);
            alert('Failed to delete API key');
        }
    };

    const handleToggleIntegration = async (provider: string, isEnabled: boolean) => {
        try {
            const response = await fetch(`/api/admin/settings/integrations/${provider}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ is_enabled: isEnabled }),
            });

            if (response.ok) {
                mutate('/api/admin/settings/integrations');
            }
        } catch (error) {
            console.error('Error toggling integration:', error);
            alert('Failed to toggle integration');
        }
    };

    const handleRevokeSession = async (sessionId: string) => {
        if (!confirm('Are you sure you want to revoke this session?')) return;

        try {
            const response = await fetch(`/api/admin/settings/security/sessions/${sessionId}`, {
                method: 'DELETE',
                credentials: 'include',
            });

            if (response.ok) {
                mutate('/api/admin/settings/security/sessions');
            }
        } catch (error) {
            console.error('Error revoking session:', error);
            alert('Failed to revoke session');
        }
    };

    const handleTestConnection = async (provider: string) => {
        try {
            const response = await fetch(`/api/admin/settings/integrations/${provider}/test`, {
                method: 'POST',
                credentials: 'include',
            });

            if (response.ok) {
                const result = await response.json();
                // Show result in dialog instead of alert
                setTestResult({
                    provider: provider.toUpperCase(),
                    status: result.status,
                    message: result.message
                });
                // Refresh integrations to update health status
                mutate('/api/admin/settings/integrations');
            } else {
                setTestResult({
                    provider: provider.toUpperCase(),
                    status: 'error',
                    message: 'Failed to test connection'
                });
            }
        } catch (error) {
            console.error('Error testing connection:', error);
            setTestResult({
                provider: provider.toUpperCase(),
                status: 'error',
                message: 'Failed to test connection'
            });
        }
    };

    const tabs = [
        { id: 'general' as Tab, label: 'General', icon: Settings },
        { id: 'security' as Tab, label: 'Security', icon: Shield },
        { id: 'api-keys' as Tab, label: 'API Keys', icon: Key },
        { id: 'integrations' as Tab, label: 'Integrations', icon: Puzzle },
    ];

    return (
        <div className="p-8 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Platform Settings</h1>
                    <p className="text-muted-foreground mt-1">Manage your account, security, and integration preferences.</p>
                </div>
                <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-lg border">
                    <div className="h-10 w-10 bg-green-700 rounded flex items-center justify-center">
                        <span className="text-white font-semibold">SA</span>
                    </div>
                    <div>
                        <p className="font-semibold">SupaAgent Inc.</p>
                        <p className="text-sm text-muted-foreground">Admin Account</p>
                    </div>
                    <Button variant="outline" size="sm">Edit Profile</Button>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="border-b">
                <div className="flex gap-6">
                    {tabs.map((tab) => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${activeTab === tab.id
                                    ? 'border-blue-600 text-blue-600'
                                    : 'border-transparent text-muted-foreground hover:text-foreground'
                                    }`}
                            >
                                <Icon className="h-4 w-4" />
                                <span className="font-medium">{tab.label}</span>
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Tab Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">
                    {/* General Tab */}
                    {activeTab === 'general' && (
                        <Card>
                            <CardHeader>
                                <CardTitle>General Information</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <Label htmlFor="company_name">Company Name</Label>
                                        <Input
                                            id="company_name"
                                            value={formData.company_name || ''}
                                            onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <Label htmlFor="support_email">Support Email</Label>
                                        <Input
                                            id="support_email"
                                            type="email"
                                            value={formData.support_email || ''}
                                            onChange={(e) => setFormData({ ...formData, support_email: e.target.value })}
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <Label htmlFor="language">Default Language</Label>
                                        <select
                                            id="language"
                                            className="w-full px-3 py-2 border rounded-md"
                                            value={formData.default_language}
                                            onChange={(e) => setFormData({ ...formData, default_language: e.target.value })}
                                        >
                                            <option value="en-US">English (US)</option>
                                            <option value="es">Spanish</option>
                                            <option value="fr">French</option>
                                        </select>
                                    </div>
                                    <div>
                                        <Label htmlFor="timezone">Timezone</Label>
                                        <select
                                            id="timezone"
                                            className="w-full px-3 py-2 border rounded-md"
                                            value={formData.timezone}
                                            onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                                        >
                                            <option value="America/New_York">Eastern Time (ET)</option>
                                            <option value="America/Chicago">Central Time (CT)</option>
                                            <option value="America/Denver">Mountain Time (MT)</option>
                                            <option value="America/Los_Angeles">Pacific Time (PT)</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="flex justify-end">
                                    <Button onClick={handleSaveGeneral} disabled={isSaving}>
                                        {isSaving ? 'Saving...' : 'Save Changes'}
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Security Tab */}
                    {activeTab === 'security' && (
                        <>
                            <Card>
                                <CardHeader>
                                    <CardTitle>Password</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <p className="text-sm text-muted-foreground">
                                        Last changed: {securityOverview?.password_last_changed || '3 months ago'}
                                    </p>
                                    <Button>Update Password</Button>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader>
                                    <CardTitle>Active Sessions</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-3">
                                        {activeSessions?.map((session) => (
                                            <div key={session.id} className="flex items-center justify-between p-3 border rounded-lg">
                                                <div>
                                                    <p className="font-medium">{session.device_name}</p>
                                                    <p className="text-sm text-muted-foreground">
                                                        {session.location} • Active {new Date(session.last_active_at).toLocaleString()}
                                                    </p>
                                                </div>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => handleRevokeSession(session.id)}
                                                >
                                                    <X className="h-4 w-4 text-red-600" />
                                                </Button>
                                            </div>
                                        ))}
                                        {(!activeSessions || activeSessions.length === 0) && (
                                            <p className="text-sm text-muted-foreground text-center py-4">No active sessions</p>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        </>
                    )}

                    {/* API Keys Tab */}
                    {activeTab === 'api-keys' && (
                        <Card>
                            <CardHeader>
                                <CardTitle>API Keys</CardTitle>
                                <p className="text-sm text-muted-foreground">Manage API keys for accessing the SupaAgent platform.</p>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {/* Generate New Key */}
                                <div className="flex gap-2">
                                    <Input
                                        placeholder="API Key Name (e.g., Production Server)"
                                        value={newApiKeyName}
                                        onChange={(e) => setNewApiKeyName(e.target.value)}
                                    />
                                    <Button onClick={handleGenerateAPIKey}>Generate New Key</Button>
                                </div>

                                {/* Show generated key */}
                                {generatedKey && (
                                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                                        <p className="text-sm font-medium text-green-900 mb-2">API Key Generated!</p>
                                        <div className="flex items-center gap-2">
                                            <code className="flex-1 p-2 bg-white border rounded text-sm">{generatedKey}</code>
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => {
                                                    navigator.clipboard.writeText(generatedKey);
                                                    alert('Copied to clipboard!');
                                                }}
                                            >
                                                <Copy className="h-4 w-4" />
                                            </Button>
                                        </div>
                                        <p className="text-xs text-green-700 mt-2">
                                            ⚠️ Save this key now. You won't be able to see it again!
                                        </p>
                                    </div>
                                )}

                                {/* API Keys Table */}
                                <div className="border rounded-lg overflow-hidden">
                                    <table className="w-full">
                                        <thead className="bg-gray-50 border-b">
                                            <tr>
                                                <th className="text-left p-3 text-xs font-medium text-muted-foreground uppercase">Name</th>
                                                <th className="text-left p-3 text-xs font-medium text-muted-foreground uppercase">Token</th>
                                                <th className="text-left p-3 text-xs font-medium text-muted-foreground uppercase">Last Used</th>
                                                <th className="text-left p-3 text-xs font-medium text-muted-foreground uppercase">Action</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {apiKeys?.map((key) => (
                                                <tr key={key.id} className="border-b last:border-0">
                                                    <td className="p-3">{key.name}</td>
                                                    <td className="p-3">
                                                        <code className="text-sm text-muted-foreground">{key.key_prefix}</code>
                                                    </td>
                                                    <td className="p-3 text-sm text-muted-foreground">
                                                        {key.last_used_at ? new Date(key.last_used_at).toLocaleDateString() : 'Just now'}
                                                    </td>
                                                    <td className="p-3">
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            onClick={() => handleDeleteAPIKey(key.id)}
                                                        >
                                                            <Trash2 className="h-4 w-4 text-red-600" />
                                                        </Button>
                                                    </td>
                                                </tr>
                                            ))}
                                            {(!apiKeys || apiKeys.length === 0) && (
                                                <tr>
                                                    <td colSpan={4} className="p-8 text-center text-muted-foreground">
                                                        No API keys yet. Generate one above to get started.
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Integrations Tab */}
                    {activeTab === 'integrations' && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Integrations</CardTitle>
                                <p className="text-sm text-muted-foreground">Manage platform-wide integration availability.</p>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                {Array.isArray(integrations) && integrations.length > 0 ? (
                                    integrations.map((integration) => (
                                        <div key={integration.id} className="p-4 border rounded-lg space-y-3">
                                            <div className="flex items-start justify-between">
                                                <div className="flex items-start gap-3 flex-1">
                                                    <div className="h-10 w-10 bg-blue-100 rounded flex items-center justify-center flex-shrink-0">
                                                        <span className="text-lg">
                                                            {integration.provider === 'slack' ? '💬' :
                                                                integration.provider === 'stripe' ? '💳' :
                                                                    integration.provider === 'hubspot' ? '🔶' : '📧'}
                                                        </span>
                                                    </div>
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2">
                                                            <p className="font-medium">{integration.display_name}</p>
                                                            {integration.health_status === 'operational' && (
                                                                <Badge className="bg-green-100 text-green-700 text-xs">
                                                                    ✓ Operational
                                                                </Badge>
                                                            )}
                                                            {integration.health_status === 'degraded' && (
                                                                <Badge className="bg-yellow-100 text-yellow-700 text-xs">
                                                                    ⚠ Degraded
                                                                </Badge>
                                                            )}
                                                            {integration.health_status === 'down' && (
                                                                <Badge className="bg-red-100 text-red-700 text-xs">
                                                                    ✕ Down
                                                                </Badge>
                                                            )}
                                                        </div>
                                                        <p className="text-sm text-muted-foreground mt-1">
                                                            {integration.description}
                                                        </p>
                                                        <p className="text-xs text-muted-foreground mt-2">
                                                            {integration.customer_count} {integration.customer_count === 1 ? 'customer' : 'customers'} connected
                                                        </p>
                                                    </div>
                                                </div>
                                                <Switch
                                                    checked={integration.is_enabled}
                                                    onCheckedChange={(checked) => handleToggleIntegration(integration.provider, checked)}
                                                />
                                            </div>
                                            <div className="flex justify-end">
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => handleTestConnection(integration.provider)}
                                                >
                                                    Test Connection
                                                </Button>
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div className="text-center p-4 text-muted-foreground">
                                        No integrations available.
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    )}
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    {activeTab === 'security' && (
                        <Card className="border-green-200 bg-green-50">
                            <CardContent className="p-4">
                                <div className="flex items-start gap-3">
                                    <div className="h-10 w-10 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                                        <Check className="h-5 w-5 text-green-600" />
                                    </div>
                                    <div>
                                        <p className="font-medium text-green-900">Two-Factor Auth</p>
                                        <p className="text-sm text-green-700 mt-1">
                                            {securityOverview?.two_factor_enabled ? 'Enabled' : 'Disabled'}
                                        </p>
                                        <Button size="sm" variant="outline" className="mt-2">
                                            Configure
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    <Card>
                        <CardHeader>
                            <CardTitle className="text-sm">Quick Notifications</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            <div className="flex items-center justify-between">
                                <span className="text-sm">Email Alerts</span>
                                <Switch defaultChecked />
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm">Marketing Updates</span>
                                <Switch />
                            </div>
                            <Link href="#" className="text-sm text-blue-600 hover:underline block mt-2">
                                Manage all notifications
                            </Link>
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Test Connection Result Dialog */}
            <Dialog open={testResult !== null} onOpenChange={() => setTestResult(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>{testResult?.provider} Connection Test</DialogTitle>
                        <DialogDescription>
                            Test connection result for {testResult?.provider}
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        <div className="flex items-center gap-2">
                            <span className="font-semibold">Status:</span>
                            <Badge variant={testResult?.status === 'operational' ? 'default' : 'destructive'}>
                                {testResult?.status}
                            </Badge>
                        </div>
                        <div>
                            <span className="font-semibold">Message:</span>
                            <p className="mt-1 text-sm text-muted-foreground">{testResult?.message}</p>
                        </div>
                        <Button onClick={() => setTestResult(null)} className="w-full">
                            Close
                        </Button>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
}
