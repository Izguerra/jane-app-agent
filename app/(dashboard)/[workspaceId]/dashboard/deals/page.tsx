'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Plus, Search, DollarSign, TrendingUp, Calendar } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useParams } from 'next/navigation';

const fetcher = (url: string) => fetch(url, { credentials: 'include' }).then((res) => res.json());

export default function DealsPage() {
    const params = useParams();
    const workspaceId = params?.workspaceId as string;
    const [page, setPage] = useState(1);
    const [stageFilter, setStageFilter] = useState('');

    const { data, error, isLoading } = useSWR(
        `/api/deals?page=${page}&limit=20${stageFilter ? `&stage=${stageFilter}` : ''}`,
        fetcher
    );

    const getStageBadge = (stage: string) => {
        const variants: Record<string, { variant: any; label: string; color: string }> = {
            'lead': { variant: 'secondary', label: 'Lead', color: 'bg-gray-100' },
            'qualified': { variant: 'default', label: 'Qualified', color: 'bg-blue-100' },
            'proposal': { variant: 'default', label: 'Proposal', color: 'bg-purple-100' },
            'negotiation': { variant: 'default', label: 'Negotiation', color: 'bg-blue-100' },
            'closed_won': { variant: 'default', label: 'Won', color: 'bg-green-100' },
            'closed_lost': { variant: 'destructive', label: 'Lost', color: 'bg-red-100' }
        };

        const config = variants[stage] || { variant: 'default', label: stage, color: 'bg-gray-100' };
        return <Badge variant={config.variant} className="text-xs">{config.label}</Badge>;
    };

    const formatCurrency = (cents: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(cents / 100);
    };

    const formatDate = (dateString: string) => {
        if (!dateString) return 'Not set';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Deals</h2>
                    <p className="text-muted-foreground">Track sales opportunities and pipeline</p>
                </div>
                <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    New Deal
                </Button>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-4">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        type="search"
                        placeholder="Search deals..."
                        className="pl-9"
                    />
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant={stageFilter === '' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setStageFilter('')}
                    >
                        All
                    </Button>
                    <Button
                        variant={stageFilter === 'lead' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setStageFilter('lead')}
                    >
                        Leads
                    </Button>
                    <Button
                        variant={stageFilter === 'qualified' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setStageFilter('qualified')}
                    >
                        Qualified
                    </Button>
                    <Button
                        variant={stageFilter === 'proposal' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setStageFilter('proposal')}
                    >
                        Proposal
                    </Button>
                </div>
            </div>

            {/* Deals Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {isLoading ? (
                    <div className="col-span-full p-8 text-center text-muted-foreground">
                        Loading...
                    </div>
                ) : data?.items?.length === 0 ? (
                    <div className="col-span-full p-8 text-center text-muted-foreground">
                        No deals found.
                    </div>
                ) : (
                    data?.items?.map((deal: any) => (
                        <Card key={deal.id} className="hover:shadow-md transition-shadow">
                            <CardHeader className="pb-3">
                                <div className="flex items-start justify-between">
                                    <CardTitle className="text-lg">{deal.title}</CardTitle>
                                    {getStageBadge(deal.stage)}
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                {deal.value && (
                                    <div className="flex items-center gap-2">
                                        <DollarSign className="h-4 w-4 text-muted-foreground" />
                                        <span className="text-lg font-semibold">{formatCurrency(deal.value)}</span>
                                    </div>
                                )}
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <TrendingUp className="h-4 w-4" />
                                    <span>{deal.probability}% probability</span>
                                </div>
                                <Progress value={deal.probability} className="h-2" />
                                {deal.expected_close_date && (
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                        <Calendar className="h-4 w-4" />
                                        <span>Expected: {formatDate(deal.expected_close_date)}</span>
                                    </div>
                                )}
                                {deal.description && (
                                    <p className="text-sm text-muted-foreground line-clamp-2 mt-2">
                                        {deal.description}
                                    </p>
                                )}
                            </CardContent>
                        </Card>
                    ))
                )}
            </div>

            {/* Pagination */}
            {data?.items?.length > 0 && (
                <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                        Showing {((page - 1) * 20) + 1} to {Math.min(page * 20, data?.total || 0)} of {data?.total || 0} results
                    </p>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage((p) => Math.max(1, p - 1))}
                            disabled={page === 1 || isLoading}
                        >
                            Previous
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage((p) => p + 1)}
                            disabled={!data || !data.items || data.items.length < 20 || isLoading}
                        >
                            Next
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
