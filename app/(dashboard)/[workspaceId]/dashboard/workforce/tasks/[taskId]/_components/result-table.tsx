import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ExternalLink } from "lucide-react";

interface ResultTableProps {
    data: any;
}

export function ResultTable({ data }: ResultTableProps) {
    if (!data || typeof data !== 'object') return null;

    // 1. Identify if there is a primary list of items
    // Strategies:
    // a) Root is an array
    // b) Root has a property that is an array (e.g. "jobs_found", "results", "items")

    let items: any[] = [];
    let title = "Results";

    if (Array.isArray(data)) {
        items = data;
    } else {
        // Look for the first array property
        const arrayKey = Object.keys(data).find(key => Array.isArray(data[key]) && data[key].length > 0);
        if (arrayKey) {
            items = data[arrayKey];
            title = arrayKey.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
        }
    }

    // If no list found, fall back to JSON view in parent (or handle here, but parent does it)
    if (items.length === 0) return null;

    // 2. Determine columns dynamically from the first item
    const firstItem = items[0];
    if (typeof firstItem !== 'object' || firstItem === null) return null;

    const headers = Object.keys(firstItem).filter(k =>
        k !== 'content' && k !== 'url'
    );

    // Explicitly add snippet/content at the end if exists, but handling it specially? 
    // For now let's stick to key fields.
    // Actually, for Job Search, we want: title, source, relevance_score. URL should be a link on Title.

    return (
        <Card>
            <CardHeader>
                <CardTitle className="text-lg">{title}</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="rounded-md border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                {headers.map((header) => (
                                    <TableHead key={header} className="capitalize whitespace-nowrap">
                                        {header.replace(/_/g, " ")}
                                    </TableHead>
                                ))}
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {items.map((item, i) => (
                                <TableRow key={i}>
                                    {headers.map((header) => {
                                        const value = item[header];
                                        return (
                                            <TableCell key={`${i}-${header}`}>
                                                {renderCell(header, value, item)}
                                            </TableCell>
                                        );
                                    })}
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            </CardContent>
        </Card>
    );
}

function renderCell(key: string, value: any, item: any) {
    // Special handling for Title to include URL
    if (key === 'title' && item.url) {
        return (
            <a href={item.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 hover:underline text-blue-600 font-medium whitespace-normal min-w-[200px]">
                {value}
                <ExternalLink className="h-3 w-3 shrink-0" />
            </a>
        );
    }

    // Snippet truncation
    if (key === 'snippet' && typeof value === 'string') {
        return (
            <div className="text-muted-foreground text-xs max-w-[400px] line-clamp-3" title={value}>
                {value}
            </div>
        );
    }

    if (typeof value === 'boolean') return value ? "Yes" : "No";
    if (typeof value === 'object') return JSON.stringify(value);
    return <span className="whitespace-nowrap">{value}</span>;
}
