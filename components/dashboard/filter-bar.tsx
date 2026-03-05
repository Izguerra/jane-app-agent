"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Search, SlidersHorizontal } from "lucide-react";
import { ReactNode } from "react";

export interface FilterOption {
    label: string;
    value: string;
}

export interface FilterConfig {
    key: string;
    label: string;
    options: FilterOption[];
}

interface FilterBarProps {
    onSearchChange?: (value: string) => void;
    searchValue?: string;
    searchPlaceholder?: string;
    filters?: FilterConfig[];
    onFilterChange?: (key: string, value: string) => void;
    activeFilters?: Record<string, string>;
    children?: ReactNode; // For extra buttons or custom filters
    className?: string;
}

export function FilterBar({
    onSearchChange,
    searchValue,
    searchPlaceholder = "Search...",
    filters = [],
    onFilterChange,
    activeFilters = {},
    children,
    className,
}: FilterBarProps) {
    return (
        <div className={`flex flex-col sm:flex-row gap-4 items-center justify-between py-4 ${className}`}>
            <div className="flex flex-1 items-center space-x-2 w-full">
                {onSearchChange && (
                    <div className="relative flex-1 max-w-sm">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            type="search"
                            placeholder={searchPlaceholder}
                            className="pl-8"
                            value={searchValue}
                            onChange={(e) => onSearchChange(e.target.value)}
                        />
                    </div>
                )}
                {filters.map((filter) => (
                    <Select
                        key={filter.key}
                        value={activeFilters[filter.key]}
                        onValueChange={(val) => onFilterChange && onFilterChange(filter.key, val)}
                    >
                        <SelectTrigger className="w-[180px]" suppressHydrationWarning>
                            <div className="flex items-center gap-2">
                                <span className="text-muted-foreground hidden sm:inline-block">{filter.label}:</span>
                                <SelectValue placeholder={filter.label} />
                            </div>
                        </SelectTrigger>
                        <SelectContent suppressHydrationWarning>
                            <SelectItem value="all">All</SelectItem>
                            {filter.options.map((option) => (
                                <SelectItem key={option.value} value={option.value}>
                                    {option.label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                ))}
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                {children}
                <Button variant="outline" size="icon">
                    <SlidersHorizontal className="h-4 w-4" />
                </Button>
            </div>
        </div>
    );
}
