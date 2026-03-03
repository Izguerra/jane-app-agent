'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Download, ExternalLink, FileText } from "lucide-react";
import useSWR from 'swr';
import { Skeleton } from "@/components/ui/skeleton";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export function BillingHistory() {
    const { data: invoices, isLoading } = useSWR('/api/billing/invoices', fetcher);

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Billing History</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        <Skeleton className="h-10 w-full" />
                        <Skeleton className="h-10 w-full" />
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Don't render if there's an error or no data
    if (!invoices || !Array.isArray(invoices) || invoices.length === 0) {
        return null;
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Billing History</CardTitle>
                <CardDescription>Recent invoices and payments</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="rounded-md border">
                    <table className="w-full text-sm">
                        <thead className="bg-muted/50 text-muted-foreground">
                            <tr>
                                <th className="px-4 py-3 text-left font-medium">Date</th>
                                <th className="px-4 py-3 text-left font-medium">Amount</th>
                                <th className="px-4 py-3 text-left font-medium">Status</th>
                                <th className="px-4 py-3 text-right font-medium">Invoice</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y">
                            {invoices.map((invoice: any) => (
                                <tr key={invoice.id} className="hover:bg-muted/50 transition-colors">
                                    <td className="px-4 py-3">
                                        {new Date(invoice.date * 1000).toLocaleDateString()}
                                    </td>
                                    <td className="px-4 py-3 font-medium">
                                        {new Intl.NumberFormat('en-US', { style: 'currency', currency: invoice.currency }).format(invoice.amount)}
                                    </td>
                                    <td className="px-4 py-3">
                                        <Badge variant={invoice.status === 'paid' ? 'outline' : 'secondary'} className={invoice.status === 'paid' ? 'text-green-600 border-green-200 bg-green-50' : ''}>
                                            {invoice.status}
                                        </Badge>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        {invoice.pdf_url && (
                                            <Button variant="ghost" size="sm" asChild>
                                                <a href={invoice.pdf_url} target="_blank" rel="noopener noreferrer">
                                                    <Download className="h-4 w-4 mr-1" />
                                                    PDF
                                                </a>
                                            </Button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </CardContent>
        </Card>
    );
}
