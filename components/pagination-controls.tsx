'use client';

import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
    hasNext?: boolean;
    hasPrev?: boolean;
}

export function PaginationControls({
    currentPage,
    totalPages,
    onPageChange,
    hasNext,
    hasPrev
}: PaginationProps) {
    const canGoPrev = hasPrev !== undefined ? hasPrev : currentPage > 1;
    const canGoNext = hasNext !== undefined ? hasNext : currentPage < totalPages;

    return (
        <div className="flex items-center justify-center gap-2 mt-4">
            <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(currentPage - 1)}
                disabled={!canGoPrev}
                className="gap-1"
            >
                <ChevronLeft className="h-4 w-4" />
                Previous
            </Button>

            <div className="flex items-center gap-1 text-sm text-gray-600">
                Page <span className="font-medium">{currentPage}</span> of <span className="font-medium">{totalPages}</span>
            </div>

            <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(currentPage + 1)}
                disabled={!canGoNext}
                className="gap-1"
            >
                Next
                <ChevronRight className="h-4 w-4" />
            </Button>
        </div>
    );
}
