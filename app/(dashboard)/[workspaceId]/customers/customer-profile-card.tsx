'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Mail, Phone, MapPin, Calendar, Edit, Trash2 } from 'lucide-react';

interface Customer {
    id: string;
    first_name: string;
    last_name: string;
    email: string;
    phone: string;
    status: string;
    plan?: string;
    avatar_url?: string;
    created_at: string;
    company_name?: string;
    // CRM Fields
    customer_type?: string;
    lifecycle_stage?: string;
    crm_status?: string;
}

interface CustomerProfileCardProps {
    customer: Customer;
    onEdit?: () => void;
    onDelete?: () => void;
}

export function CustomerProfileCard({ customer, onEdit, onDelete }: CustomerProfileCardProps) {
    console.log('CustomerProfileCard received customer:', customer);

    const getStatusVariant = (status: string) => {
        switch (status) {
            case 'active':
                return 'default';
            case 'trialing':
                return 'secondary';
            case 'past_due':
                return 'destructive';
            case 'churned':
                return 'outline';
            default:
                return 'default';
        }
    };

    const initials = `${customer?.first_name?.[0] || '?'}${customer?.last_name?.[0] || '?'}`;
    const fullName = customer?.first_name && customer?.last_name
        ? `${customer.first_name} ${customer.last_name}`
        : 'Unknown Customer';

    const joinedYear = customer?.created_at
        ? new Date(customer.created_at).getFullYear()
        : new Date().getFullYear();

    return (
        <Card className="overflow-hidden">
            <CardContent className="p-6">
                {/* Avatar with Online Status */}
                <div className="flex flex-col items-center text-center space-y-3">
                    <div className="relative">
                        <Avatar className="h-24 w-24">
                            <AvatarImage src={customer?.avatar_url} />
                            <AvatarFallback className="text-2xl bg-primary/10">
                                {initials}
                            </AvatarFallback>
                        </Avatar>
                        {/* Online Status Indicator */}
                        <div className="absolute bottom-1 right-1 h-4 w-4 bg-green-500 border-2 border-white rounded-full" />
                    </div>

                    {/* Name and Customer Since */}
                    <div className="space-y-1">
                        <h3 className="font-semibold text-xl">
                            {fullName}
                        </h3>
                        <p className="text-sm text-muted-foreground">
                            Customer since {joinedYear}
                        </p>
                    </div>
                </div>

                {/* Contact Information */}
                <div className="mt-6 space-y-3">
                    {/* Phone */}
                    <div className="flex items-start space-x-3">
                        <div className="mt-0.5 p-2 bg-muted rounded">
                            <Phone className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-xs text-muted-foreground uppercase tracking-wider">Phone</p>
                            <p className="text-sm font-medium truncate">
                                {customer?.phone || 'Not provided'}
                            </p>
                        </div>
                    </div>

                    {/* Email */}
                    <div className="flex items-start space-x-3">
                        <div className="mt-0.5 p-2 bg-muted rounded">
                            <Mail className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-xs text-muted-foreground uppercase tracking-wider">Email</p>
                            <p className="text-sm font-medium truncate">
                                {customer?.email || 'Not provided'}
                            </p>
                        </div>
                    </div>

                    {/* Location */}
                    {customer?.company_name && (
                        <div className="flex items-start space-x-3">
                            <div className="mt-0.5 p-2 bg-muted rounded">
                                <MapPin className="h-4 w-4 text-muted-foreground" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-xs text-muted-foreground uppercase tracking-wider">Company</p>
                                <p className="text-sm font-medium truncate">
                                    {customer.company_name}
                                </p>
                            </div>
                        </div>
                    )}
                </div>

                {/* CRM Details */}
                <div className="pt-3 border-t">
                    <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider">CRM Details</p>

                    {/* Customer Type */}
                    <div className="flex justify-between items-center text-sm py-1">
                        <span className="text-muted-foreground">Type:</span>
                        <Badge variant="outline" className="capitalize">
                            {customer?.customer_type || '—'}
                        </Badge>
                    </div>

                    {/* Lifecycle Stage */}
                    <div className="flex justify-between items-center text-sm py-1">
                        <span className="text-muted-foreground">Stage:</span>
                        <Badge variant="secondary" className="capitalize">
                            {customer?.lifecycle_stage || '—'}
                        </Badge>
                    </div>

                    {/* CRM Status */}
                    <div className="flex justify-between items-center text-sm py-1">
                        <span className="text-muted-foreground">Status:</span>
                        <span className="font-medium capitalize">
                            {customer?.crm_status || '—'}
                        </span>
                    </div>
                </div>

                {/* View CRM Profile Button */}
                <div className="mt-6">
                    <Button
                        variant="link"
                        className="w-full text-primary p-0 h-auto font-normal"
                        onClick={onEdit}
                    >
                        View CRM Profile
                    </Button>
                </div>

                {/* Action Buttons */}
                <div className="mt-4 pt-4 border-t flex gap-2">
                    <Button variant="outline" size="sm" className="flex-1" onClick={onEdit}>
                        <Edit className="h-4 w-4 mr-1" />
                        Edit
                    </Button>
                    <Button variant="outline" size="sm" className="flex-1" onClick={onDelete}>
                        <Trash2 className="h-4 w-4 mr-1" />
                        Delete
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
