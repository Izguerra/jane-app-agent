'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { LayoutDashboard, BarChart3, Settings, Building2, Bot } from 'lucide-react';
import { Logo } from '@/components/logo';
import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();
    const pathname = usePathname();
    const [userRole, setUserRole] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const { data: user } = useSWR('/api/user', fetcher);

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const response = await fetch('/api/user');
                if (response.ok) {
                    const data = await response.json();
                    if (data.role === 'supaagent_admin' || data.role === 'owner') {
                        setUserRole(data.role);
                    } else {
                        router.push('/dashboard');
                    }
                } else {
                    router.push('/login');
                }
            } catch (error) {
                console.error('Auth check failed:', error);
                router.push('/login');
            } finally {
                setIsLoading(false);
            }
        };

        checkAuth();
    }, [router]);

    const getPageTitle = () => {
        if (pathname === '/admin/workspaces') return 'Customer Management';
        if (pathname?.startsWith('/admin/workspaces/') && pathname?.includes('/edit')) return 'Edit Customer';
        if (pathname?.startsWith('/admin/workspaces/') && pathname?.includes('/payments')) return 'Payment History';
        if (pathname?.startsWith('/admin/workspaces/')) return 'Customer Profile';
        if (pathname === '/admin/analytics') return 'Analytics Dashboard';
        if (pathname === '/admin/workforce') return 'Workforce Dashboard';
        if (pathname?.startsWith('/admin/workforce/')) return 'Task Details';
        if (pathname === '/admin/settings') return 'Settings';
        return 'Admin Panel';
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-muted-foreground">Loading...</div>
            </div>
        );
    }

    if (!userRole) {
        return null;
    }

    const navigation = [
        { name: 'Analytics', href: '/admin/analytics', icon: BarChart3, current: pathname === '/admin/analytics' },
        { name: 'Customers', href: '/admin/workspaces', icon: LayoutDashboard, current: pathname === '/admin/workspaces' || pathname?.startsWith('/admin/workspaces/') },
        { name: 'Workforce', href: '/admin/workforce', icon: Bot, current: pathname === '/admin/workforce' || pathname?.startsWith('/admin/workforce/') },
        { name: 'Settings', href: '/admin/settings', icon: Settings, current: pathname === '/admin/settings' },
    ];


    // Hide parent header
    return (
        <>
            <style jsx global>{`
                body > section > header {
                    display: none;
                }
            `}</style>
            <div className="flex h-screen bg-gray-50">
                {/* Sidebar */}
                <div className="w-64 bg-white border-r flex flex-col">
                    <div className="px-6 py-4 border-b">
                        <Link href="/admin/analytics">
                            <Logo className="h-14 w-auto" />
                        </Link>
                    </div>

                    <nav className="p-4 space-y-1 flex-1">
                        {navigation.map((item) => {
                            const Icon = item.icon;
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${item.current
                                        ? 'bg-blue-50 text-blue-600'
                                        : 'text-gray-700 hover:bg-gray-100'
                                        }`}
                                >
                                    <Icon className="h-5 w-5" />
                                    {item.name}
                                </Link>
                            );
                        })}
                    </nav>

                    <div className="p-4 border-t bg-white">
                        <div className="text-xs text-muted-foreground mb-3">
                            <p className="font-medium">Admin Panel</p>
                            <p className="mt-1">Role: {userRole}</p>
                        </div>
                        <button
                            onClick={async () => {
                                try {
                                    await fetch('/api/sign-out', { method: 'POST' });
                                    window.location.href = '/';
                                } catch (error) {
                                    console.error('Sign out failed:', error);
                                }
                            }}
                            className="w-full px-3 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
                        >
                            Sign Out
                        </button>
                    </div>
                </div>

                {/* Main Content */}
                <div className="flex-1 flex flex-col overflow-hidden">
                    {/* Header with Title */}
                    <header className="bg-white border-b px-8 py-4 flex items-center justify-between">
                        <h1 className="text-2xl font-bold">{getPageTitle()}</h1>
                        <div className="flex items-center gap-4">
                            {/* User menu or other header actions */}
                        </div>
                    </header>

                    {/* Page Content */}
                    <main className="flex-1 overflow-y-auto bg-gray-50">
                        {children}
                    </main>
                </div>
            </div>
        </>
    );
}
