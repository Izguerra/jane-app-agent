import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';

const getBackendUrl = () => {
    let url = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';
    if (url.includes('localhost')) {
        url = url.replace('localhost', '127.0.0.1');
    }
    return url;
};

const BACKEND_URL = getBackendUrl();

export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const error = searchParams.get('error');

        // If user denied access
        if (error) {
            console.error('OAuth error:', error);
            return NextResponse.redirect(new URL('/dashboard/integrations?error=access_denied', request.url));
        }

        if (!code || !state) {
            console.error('Missing code or state in OAuth callback');
            return NextResponse.redirect(new URL('/dashboard/integrations?error=invalid_callback', request.url));
        }

        // Forward the OAuth callback to the backend
        const backendCallbackUrl = `${BACKEND_URL}/api/auth/google/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`;

        console.log('Forwarding OAuth callback to backend:', backendCallbackUrl);

        const response = await fetch(backendCallbackUrl, {
            method: 'GET',
            headers: {
                'Cookie': request.headers.get('cookie') || '',
            },
            redirect: 'manual', // Don't follow redirects automatically
        });

        // Get any Set-Cookie headers from the backend response
        const setCookieHeaders = response.headers.getSetCookie();

        // Create redirect response
        const redirectUrl = new URL('/dashboard/integrations?success=true', request.url);
        const redirectResponse = NextResponse.redirect(redirectUrl);

        // Forward any cookies from the backend
        if (setCookieHeaders && setCookieHeaders.length > 0) {
            setCookieHeaders.forEach(cookie => {
                redirectResponse.headers.append('Set-Cookie', cookie);
            });
        }

        return redirectResponse;

    } catch (error: any) {
        console.error('Error in Google OAuth callback:', error);
        return NextResponse.redirect(
            new URL('/dashboard/integrations?error=callback_failed', request.url)
        );
    }
}
