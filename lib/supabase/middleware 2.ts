import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function updateSession(request: NextRequest) {
    let response = NextResponse.next({
        request: {
            headers: request.headers,
        },
    })

    const supabase = createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                getAll() {
                    return request.cookies.getAll()
                },
                setAll(cookiesToSet) {
                    cookiesToSet.forEach(({ name, value, options }) => {
                        request.cookies.set(name, value)
                    })
                    response = NextResponse.next({
                        request,
                    })
                    cookiesToSet.forEach(({ name, value, options }) =>
                        response.cookies.set(name, value, options)
                    )
                },
            },
        }
    )

    const { data: { session } } = await supabase.auth.getSession()
    const user = session?.user
    const { pathname } = request.nextUrl

    // Debug logging for session state
    if (pathname.startsWith('/api/')) {
        console.log(`[Middleware] ${pathname} - Session exists: ${!!session}, User exists: ${!!user}, Has access_token: ${!!session?.access_token}`)
    }

    const protectedRoutes = ['/dashboard', '/workspaces']
    const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route)) || pathname.includes('/dashboard')

    if (isProtectedRoute && !user) {
        return NextResponse.redirect(new URL('/sign-in', request.url))
    }

    // Inject Authorization header for API routes if session exists
    if (pathname.startsWith('/api/') && session?.access_token) {
        console.log(`[Middleware] Injecting Auth Header for ${pathname}`)
        const requestHeaders = new Headers(request.headers)
        requestHeaders.set('Authorization', `Bearer ${session.access_token}`)

        const apiResponse = NextResponse.next({
            request: {
                headers: requestHeaders,
            },
        })

        // Preserve any cookies set by the Supabase client (e.g., session refresh)
        response.cookies.getAll().forEach((cookie) => {
            apiResponse.cookies.set(cookie)
        })

        return apiResponse
    }

    return response
}
