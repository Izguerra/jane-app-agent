"use client";

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { ChevronRight } from "lucide-react";
import { ReactNode } from "react";

export interface Column<T> {
    header: ReactNode;
    accessorKey?: keyof T;
    cell?: (item: T) => ReactNode;
    className?: string;
}

interface DataTableProps<T> {
    data: T[];
    columns: Column<T>[];
    onRowClick?: (item: T) => void;
    isLoading?: boolean;
    emptyMessage?: string;
}

export function DataTable<T extends { id?: string | number }>({
    data,
    columns,
    onRowClick,
    isLoading,
    emptyMessage = "No records found.",
}: DataTableProps<T>) {
    if (isLoading) {
        return (
            <div className="w-full border rounded-md p-8 flex justify-center text-muted-foreground">
                Loading...
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="w-full border rounded-md p-8 flex justify-center text-muted-foreground">
                {emptyMessage}
            </div>
        );
    }

    return (
        <div className="border rounded-md">
            <Table>
                <TableHeader>
                    <TableRow>
                        {columns.map((col, idx) => (
                            <TableHead key={idx} className={col.className}>
                                {col.header}
                            </TableHead>
                        ))}
                        {onRowClick && <TableHead className="w-[50px]"></TableHead>}
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data.map((item, rowIdx) => (
                        <TableRow
                            key={item.id || rowIdx}
                            className={onRowClick ? "cursor-pointer hover:bg-muted/50" : ""}
                            onClick={() => onRowClick && onRowClick(item)}
                        >
                            {columns.map((col, colIdx) => (
                                <TableCell key={colIdx} className={col.className}>
                                    {col.cell
                                        ? col.cell(item)
                                        : col.accessorKey
                                            ? (item[col.accessorKey] as ReactNode)
                                            : null}
                                </TableCell>
                            ))}
                            {onRowClick && (
                                <TableCell>
                                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                                </TableCell>
                            )}
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}
