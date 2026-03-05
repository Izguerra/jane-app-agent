import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

/**
 * Formats a date string or Date object to a localized string.
 * Handles the missing 'Z' issue for UTC stamps from backend.
 * Uses browser's default locale and timezone.
 */
export function formatDateTime(date: string | Date | null | undefined): string {
    if (!date) return 'N/A';

    let d: Date;
    if (typeof date === 'string') {
        // Check if it looks like the naive UTC string from backend
        const isNaive = !date.endsWith('Z') && !date.includes('+') && date.includes('T');
        d = new Date(isNaive ? date + 'Z' : date);
    } else {
        d = date;
    }

    // Check for invalid date
    if (isNaN(d.getTime())) return 'Invalid Date';

    return new Intl.DateTimeFormat(undefined, {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: undefined // Use locale default for 12/24h
    }).format(d);
}

export function formatTimeOnly(date: string | Date | null | undefined): string {
    if (!date) return '';

    let d: Date;
    if (typeof date === 'string') {
        const isNaive = !date.endsWith('Z') && !date.includes('+') && date.includes('T');
        d = new Date(isNaive ? date + 'Z' : date);
    } else {
        d = date;
    }

    if (isNaN(d.getTime())) return '';

    return new Intl.DateTimeFormat(undefined, {
        hour: 'numeric',
        minute: '2-digit',
        hour12: undefined
    }).format(d);
}

export function formatDateOnly(date: string | Date | null | undefined): string {
    if (!date) return '';

    let d: Date;
    if (typeof date === 'string') {
        const isNaive = !date.endsWith('Z') && !date.includes('+') && date.includes('T');
        d = new Date(isNaive ? date + 'Z' : date);
    } else {
        d = date;
    }

    if (isNaN(d.getTime())) return '';

    return new Intl.DateTimeFormat(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    }).format(d);
}
