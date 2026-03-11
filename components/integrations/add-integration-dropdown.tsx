'use client';

import { useState } from 'react';
import { ChevronDown, Check, Lock, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuGroup,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface IntegrationDetail {
    provider: string;
    display_name: string;
    category: string;
    available: boolean;
    connected: boolean;
    disabled: boolean;
    requires_upgrade: boolean;
    usage?: string;
}

interface AddIntegrationDropdownProps {
    integrations: IntegrationDetail[];
    onSelect: (provider: string) => void;
    disabled?: boolean;
}

const CATEGORY_LABELS: Record<string, string> = {
    calendar: '📅 Calendar',
    messaging: '💬 Messaging',
    ecommerce: '🛒 E-commerce',
    crm: '📊 CRM',
    booking: '📋 Booking',
    widget: '🌐 Website',
    voice: '📞 Voice',
};

export function AddIntegrationDropdown({
    integrations,
    onSelect,
    disabled = false
}: AddIntegrationDropdownProps) {
    // Group integrations by category
    const categories = integrations.reduce((acc, integration) => {
        const cat = integration.category;
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(integration);
        return acc;
    }, {} as Record<string, IntegrationDetail[]>);

    // Filter to only show not-yet-connected integrations
    const availableCategories = Object.entries(categories).filter(
        ([, items]) => items.some(i => !i.connected)
    );

    if (availableCategories.length === 0) {
        return (
            <Button disabled className="opacity-50">
                <Plus className="h-4 w-4 mr-2" />
                No More Integrations Available
            </Button>
        );
    }

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button disabled={disabled}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Integration
                    <ChevronDown className="h-4 w-4 ml-2" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-64" align="end">
                {availableCategories.map(([category, items], idx) => (
                    <div key={category}>
                        {idx > 0 && <DropdownMenuSeparator />}
                        <DropdownMenuLabel className="text-xs text-gray-500">
                            {CATEGORY_LABELS[category] || category}
                        </DropdownMenuLabel>
                        <DropdownMenuGroup>
                            {items.filter(i => !i.connected).map((integration) => (
                                <DropdownMenuItem
                                    key={integration.provider}
                                    disabled={integration.disabled || integration.requires_upgrade}
                                    onClick={() => onSelect(integration.provider)}
                                    className="flex items-center justify-between cursor-pointer"
                                >
                                    <span>{integration.display_name}</span>
                                    {integration.usage && (
                                        <span className="text-xs text-muted-foreground ml-2">
                                            {integration.usage}
                                        </span>
                                    )}
                                    {integration.requires_upgrade && (
                                        <span className="flex items-center text-xs text-blue-600 ml-2">
                                            <Lock className="h-3 w-3 mr-1" />
                                            Upgrade
                                        </span>
                                    )}
                                    {integration.disabled && !integration.requires_upgrade && (
                                        <span className="text-xs text-gray-400">
                                            Limit reached
                                        </span>
                                    )}
                                </DropdownMenuItem>
                            ))}
                        </DropdownMenuGroup>
                    </div>
                ))}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
