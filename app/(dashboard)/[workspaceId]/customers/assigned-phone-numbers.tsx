'use client';

import useSWR from 'swr';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Phone } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

const fetcher = (url: string) => fetch(url, { credentials: 'include' }).then((res) => res.json());

interface AssignedPhoneNumbersProps {
    customerId: string;
}

export function AssignedPhoneNumbers({ customerId }: AssignedPhoneNumbersProps) {
    // In a real implementation, this would fetch phone numbers assigned to this customer
    // For now, we'll show a placeholder
    const { data, isLoading } = useSWR('/api/phone-numbers', fetcher);

    // Mock assigned numbers for this customer
    const assignedNumbers = [
        { id: '1', number: '+1 (555) 123-4567', type: 'Primary', status: 'active' },
        { id: '2', number: '+1 (555) 987-6543', type: 'Support', status: 'active' },
    ];

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Assigned Phone Numbers</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-3">
                        {[...Array(2)].map((_, i) => (
                            <Skeleton key={i} className="h-16 w-full" />
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Assigned Phone Numbers</CardTitle>
            </CardHeader>
            <CardContent>
                {assignedNumbers.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-4">
                        No phone numbers assigned
                    </p>
                ) : (
                    <div className="space-y-3">
                        {assignedNumbers.map((phoneNumber) => (
                            <div
                                key={phoneNumber.id}
                                className="flex items-center justify-between p-3 bg-muted rounded-lg"
                            >
                                <div className="flex items-center space-x-3">
                                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                                        <Phone className="h-5 w-5 text-primary" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium">{phoneNumber.number}</p>
                                        <p className="text-xs text-muted-foreground">{phoneNumber.type}</p>
                                    </div>
                                </div>
                                <Badge variant={phoneNumber.status === 'active' ? 'default' : 'secondary'}>
                                    {phoneNumber.status}
                                </Badge>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
