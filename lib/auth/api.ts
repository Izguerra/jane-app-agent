/**
 * Utility to get the session token for backend API calls
 */

import { cookies } from 'next/headers';

export async function getAuthToken(): Promise<string | null> {
    const sessionCookie = (await cookies()).get('session');
    return sessionCookie?.value || null;
}

/**
 * Fetch wrapper that automatically includes auth token
 */
export async function authenticatedFetch(
    url: string,
    options: RequestInit = {}
): Promise<Response> {
    const token = await getAuthToken();

    const headers = new Headers(options.headers);
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    return fetch(url, {
        ...options,
        headers,
    });
}
