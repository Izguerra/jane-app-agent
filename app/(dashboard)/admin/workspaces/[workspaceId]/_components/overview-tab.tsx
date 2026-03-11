'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Link } from 'lucide-react';
import { Mail, PhoneCall, Building2, User, Users, CreditCard, Calendar, MessageSquare, Clock, DollarSign } from 'lucide-react';

interface OverviewTabProps {
    workspace: any;
    getPlanBadge: (plan: string, status: string) => React.ReactNode;
    getIntegrationName: (provider: string) => string;
    getIntegrationCategory: (provider: string) => string;
    getAvatarColor: (name: string) => string;
    getInitials: (name: string) => string;
}

export function OverviewTab({
    workspace,
    getPlanBadge,
    getIntegrationName,
    getIntegrationCategory,
    getAvatarColor,
    getInitials
}: OverviewTabProps) {
    if (!workspace) return null;



    return (
        <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Total Conversations</p>
                                <p className="text-3xl font-bold mt-2">
                                    {workspace.stats.total_conversations.toLocaleString()}
                                    {workspace.limits?.conv_limit && <span className="text-sm text-muted-foreground font-normal ml-1">/ {workspace.limits.conv_limit.toLocaleString()}</span>}
                                </p>
                            </div>
                            <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                                <MessageSquare className="h-6 w-6 text-blue-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Voice Usage (Min)</p>
                                <p className="text-3xl font-bold mt-2">
                                    {workspace.stats.voice_usage_minutes}m
                                    {workspace.limits?.voice_minutes && <span className="text-sm text-muted-foreground font-normal ml-1">/ {workspace.limits.voice_minutes.toLocaleString()}</span>}
                                </p>
                            </div>
                            <div className="h-12 w-12 rounded-full bg-purple-100 flex items-center justify-center">
                                <Clock className="h-6 w-6 text-purple-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Lifetime Value</p>
                                <p className="text-3xl font-bold mt-2">${workspace.stats.lifetime_value.toFixed(2)}</p>
                            </div>
                            <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
                                <DollarSign className="h-6 w-6 text-green-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column - Account Info & Agent Config */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Account Information */}
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <CardTitle>Account Information</CardTitle>
                            <Button variant="link" className="text-orange-600" asChild>
                                {/* We can't use Link component here directly if we don't import it from next/link, passing via props or just importing */}
                                <a href={`/admin/workspaces/${workspace.id}/edit`}>Edit Details</a>
                            </Button>
                        </CardHeader>
                        <CardContent className="grid grid-cols-2 gap-4">
                            <div className="min-w-0">
                                <label className="text-sm text-muted-foreground">First Name</label>
                                <div className="flex items-center gap-2 mt-2">
                                    <User className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                    <span className="font-medium truncate">{workspace.owner_first_name || '-'}</span>
                                </div>
                            </div>
                            <div className="min-w-0">
                                <label className="text-sm text-muted-foreground">Last Name</label>
                                <div className="flex items-center gap-2 mt-2">
                                    <User className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                    <span className="font-medium truncate">{workspace.owner_last_name || '-'}</span>
                                </div>
                            </div>
                            <div className="min-w-0">
                                <label className="text-sm text-muted-foreground">Email Address</label>
                                <div className="flex items-center gap-2 mt-2">
                                    <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                    <span className="font-medium truncate">{workspace.owner_email}</span>
                                </div>
                            </div>
                            <div className="min-w-0">
                                <label className="text-sm text-muted-foreground">Company</label>
                                <div className="flex items-center gap-2 mt-2">
                                    <Building2 className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                    <span className="font-medium truncate">{workspace.name}</span>
                                </div>
                            </div>
                            <div className="min-w-0">
                                <label className="text-sm text-muted-foreground">Role</label>
                                <div className="flex items-center gap-2 mt-2">
                                    <Users className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                    <span className="font-medium">Owner</span>
                                </div>
                            </div>
                            <div className="min-w-0">
                                <label className="text-sm text-muted-foreground">Subscription Plan</label>
                                <div className="flex items-center gap-2 mt-2">
                                    <CreditCard className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                    {getPlanBadge(workspace.plan, workspace.status)}
                                </div>
                            </div>
                            <div className="min-w-0 col-span-2">
                                <label className="text-sm text-muted-foreground">Registered Date</label>
                                <div className="flex items-center gap-2 mt-2">
                                    <Calendar className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                    <span className="font-medium">
                                        {new Date(workspace.created_at).toLocaleDateString('en-US', {
                                            year: 'numeric',
                                            month: 'long',
                                            day: 'numeric'
                                        })}
                                    </span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Agent Configuration */}
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <CardTitle>Agent Configuration</CardTitle>
                            {workspace.limits?.agents && <span className="text-sm text-muted-foreground">{workspace.agents.length} / {workspace.limits.agents} Agents</span>}
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {workspace.agents.length > 0 ? (
                                workspace.agents.map((agent: any) => (
                                    <div key={agent.id}>
                                        {agent.phone_numbers.map((phone: any, idx: number) => (
                                            <div key={idx} className="flex items-center justify-between p-4 border rounded-lg mb-2">
                                                <div className="flex items-center gap-3">
                                                    <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                                                        <PhoneCall className="h-5 w-5 text-green-600" />
                                                    </div>
                                                    <div>
                                                        <div className="font-medium">{phone.number}</div>
                                                        <div className="text-sm text-muted-foreground">Active Voice Number • {phone.provider}</div>
                                                    </div>
                                                </div>
                                                <div className="flex gap-2">
                                                    <Badge variant="secondary" className="bg-blue-50 text-blue-700">Voice Enabled</Badge>
                                                    <Badge variant="secondary">GPT-4</Badge>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ))
                            ) : (
                                <div className="text-sm text-muted-foreground text-center py-4">
                                    No agents configured
                                </div>
                            )}

                            <div className="border-t pt-4">
                                <h4 className="font-medium mb-3">INTEGRATIONS</h4>
                                <div className="space-y-2">
                                    {workspace.integrations.length > 0 ? (
                                        workspace.integrations.map((integration: any) => (
                                            <div key={integration.id} className="flex items-center justify-between p-3 border rounded-lg">
                                                <div className="flex items-center gap-3">
                                                    <div className="h-8 w-8 rounded bg-gray-100 flex items-center justify-center text-xs font-medium">
                                                        {integration.provider.substring(0, 2).toUpperCase()}
                                                    </div>
                                                    <div>
                                                        <div className="text-sm font-medium">{getIntegrationName(integration.provider)}</div>
                                                        <div className="text-xs text-muted-foreground">{getIntegrationCategory(integration.provider)}</div>
                                                    </div>
                                                </div>
                                                {integration.is_active ? (
                                                    <Badge className="bg-green-100 text-green-700">Connected</Badge>
                                                ) : (
                                                    <Badge variant="outline" className="text-gray-500">Inactive</Badge>
                                                )}
                                            </div>
                                        ))
                                    ) : (
                                        <div className="text-sm text-muted-foreground text-center py-4">
                                            No integrations configured
                                        </div>
                                    )}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Right Column - Subscription & Billing */}
                <div className="space-y-6">
                    {/* Subscription */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Subscription</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                                <div className="flex items-center gap-2 mb-2">
                                    <CreditCard className="h-5 w-5 text-orange-600" />
                                    <span className="font-medium">{workspace.plan}</span>
                                </div>
                                <div className="text-sm text-muted-foreground">
                                    {workspace.plan_amount ? `$${workspace.plan_amount} / month` : '$49.00 / month'}
                                </div>
                                <div className="text-sm text-muted-foreground mt-1">
                                    Next billing: Jan 12, 2026
                                </div>
                            </div>
                            <Button className="w-full" variant="outline">
                                Manage Subscription
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Billing History */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Billing History</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                <div className="grid grid-cols-[1fr_auto_auto] gap-4 text-xs font-medium text-muted-foreground pb-2 border-b">
                                    <div>DATE</div>
                                    <div className="text-right">AMOUNT</div>
                                    <div className="text-right">STATUS</div>
                                </div>
                                {workspace.billing_history && workspace.billing_history.length > 0 ? (
                                    workspace.billing_history.map((bill: any, index: number) => (
                                        <div key={index} className="grid grid-cols-[1fr_auto_auto] gap-4 text-sm items-center">
                                            <div className="truncate">{bill.date}</div>
                                            <div className="text-right whitespace-nowrap">${bill.amount.toFixed(2)}</div>
                                            <div className="text-right">
                                                {bill.status === 'Paid' ? (
                                                    <Badge className="bg-green-100 text-green-700 text-xs">Paid</Badge>
                                                ) : (
                                                    <Badge variant="secondary" className="text-xs">{bill.status}</Badge>
                                                )}
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div className="text-sm text-muted-foreground text-center py-4">No billing history found</div>
                                )}
                            </div>
                            <Button variant="link" className="w-full mt-4 text-orange-600" asChild>
                                <a href={`/admin/workspaces/${workspace.id}/payments`}>
                                    View Billing →
                                </a>
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Team Members */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Team Members</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center gap-3 min-w-0">
                                <Avatar className={`h-10 w-10 flex-shrink-0 ${getAvatarColor(workspace.owner_name)}`}>
                                    <AvatarFallback className="text-white">
                                        {getInitials(workspace.owner_name)}
                                    </AvatarFallback>
                                </Avatar>
                                <div className="min-w-0 flex-1">
                                    <div className="font-medium text-sm truncate">{workspace.owner_name}</div>
                                    <div className="text-xs text-muted-foreground truncate">{workspace.owner_email}</div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
