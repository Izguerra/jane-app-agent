import { v4 as uuidv4 } from 'uuid';

/**
 * Generate a cryptographically secure UUID v4
 * 
 * This function replaces the old generateId() which used custom prefixes.
 * UUIDs are the standard for secure, unique identifiers.
 * 
 * Format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx (36 characters including hyphens)
 * Example: 550e8400-e29b-41d4-a716-446655440000
 * 
 * @returns A UUID v4 string
 */
export function generateId(): string {
    return uuidv4();
}

/**
 * Validate if a string is a valid UUID v4
 * 
 * @param id - The string to validate
 * @returns True if valid UUID v4, false otherwise
 */
export function isValidUUID(id: string): boolean {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return uuidRegex.test(id);
}
