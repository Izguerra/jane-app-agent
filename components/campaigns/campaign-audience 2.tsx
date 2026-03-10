'use client';

import useSWR from 'swr';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Loader2, AlertCircle } from 'lucide-react';
import { formatDateTime } from '@/lib/utils/date';

interface Enrollment {
    id: string;
    status: string;
    current_step_order: number;
    next_run_at?: string;
    created_at: string;
    error_message?: string;
    customer: {
        id: string;
        first_name?: string;
        last_name?: string;
        email?: string;
        phone?: string;
    };
}

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export function CampaignAudience({ campaignId }: { campaignId: string }) {
    const { data: enrollments, isLoading } = useSWR<Enrollment[]>(campaignId ? `/api/campaigns/${campaignId}/enrollments` : null, fetcher);

    if (isLoading) {
        return (
            <Card>
                <CardContent className="p-8 flex justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </CardContent>
            </Card>
        );
    }

    const safeEnrollments = Array.isArray(enrollments) ? enrollments : [];

    return (
        <Card>
            <CardHeader>
                <CardTitle>Audience & Enrollments</CardTitle>
                <CardDescription>{safeEnrollments.length} customers enrolled in this campaign.</CardDescription>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Customer</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Progress</TableHead>
                            <TableHead className="text-right">Enrolled At</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {safeEnrollments.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                                    No enrollments yet.
                                </TableCell>
                            </TableRow>
                        ) : (
                            safeEnrollments.map((enrollment) => (
                                <TableRow key={enrollment.id}>
                                    <TableCell>
                                        <div className="flex items-center gap-3">
                                            <Avatar className="h-8 w-8">
                                                <AvatarFallback className="text-xs">
                                                    {(enrollment.customer.first_name?.[0] || '') + (enrollment.customer.last_name?.[0] || '')}
                                                </AvatarFallback>
                                            </Avatar>
                                            <div>
                                                <div className="font-medium text-sm">
                                                    {enrollment.customer.first_name} {enrollment.customer.last_name}
                                                </div>
                                                <div className="text-xs text-muted-foreground">
                                                    {enrollment.customer.email || enrollment.customer.phone}
                                                </div>
                                            </div>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <Badge
                                            variant={enrollment.status === 'active' ? 'default' : enrollment.status === 'completed' ? 'secondary' : 'destructive'}
                                            className="capitalize"
                                        >
                                            {enrollment.status}
                                        </Badge>
                                        {(enrollment.status === 'failed' || enrollment.status === 'paused') && enrollment.error_message && (
                                            <div className="flex flex-col gap-1 text-xs text-destructive mt-1">
                                                <div className="flex items-center gap-1 font-medium">
                                                    <AlertCircle className="h-3 w-3" />
                                                    <span>Error</span>
                                                </div>
                                                <span className="whitespace-normal break-words max-w-[300px] bg-red-50 p-1 rounded border border-red-100">
                                                    {enrollment.error_message}
                                                </span>
                                            </div>
                                        )}
                                    </TableCell>
                                    <TableCell>
                                        <div className="text-sm">
                                            <span className="font-medium">Step {enrollment.current_step_order}</span>
                                            {enrollment.next_run_at && enrollment.status === 'active' && (
                                                <div className="text-xs text-muted-foreground">
                                                    Next: {formatDateTime(enrollment.next_run_at)}
                                                </div>
                                            )}
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-right text-sm text-muted-foreground">
                                        {formatDateTime(enrollment.created_at)}
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
}
