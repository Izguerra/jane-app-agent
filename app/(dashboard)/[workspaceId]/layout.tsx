'use client';

import { use, useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, usePathname } from 'next/navigation';
import useSWR from 'swr';
import { Button } from '@/components/ui/button';
import { Users, Settings, Shield, Activity, Menu, Building2, Plug, Bot, BarChart3, MessageSquare, Database, LogOut, Calendar, Briefcase, Target, Box } from 'lucide-react';

import { Logo } from '@/components/logo';
import { useRouter } from 'next/navigation';

interface LayoutProps {
    children: React.ReactNode;
    params: Promise<{ workspaceId: string }>;
}

export default function DashboardLayout({ children, params: paramsPromise }: LayoutProps) {
    const pathname = usePathname();
    const params = use(paramsPromise);
    const router = useRouter();
    const workspaceId = params.workspaceId;
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    const { data: user } = useSWR<any>('/api/user', async (url: string) => {
        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to fetch');
        return res.json();
    });

    // Central Workspace Redirection: If URL workspace is stale/invalid, redirect to user's real primary workspace
    useEffect(() => {
        if (mounted && user?.workspaceId && workspaceId && workspaceId !== user.workspaceId) {
            // Only redirect if it's not a team/org ID format (which we support via backend aliasing)
            const isAlias = workspaceId.startsWith('tm_') || workspaceId.startsWith('org_');
            if (!isAlias) {
                console.log(`LAYOUT REDIRECT: URL workspace ${workspaceId} != user workspace ${user.workspaceId}. Redirecting...`);
                const newPath = pathname.replace(workspaceId, user.workspaceId);
                router.replace(newPath);
            }
        }
    }, [mounted, user, workspaceId, router, pathname]);

    const baseHref = workspaceId ? `/${workspaceId}/dashboard` : '/dashboard';

    type NavItem = {
        href: string;
        icon: any;
        label: string;
    };

    // All navigation items - no role restrictions for team members
    // (all team members should see all pages)
    // All navigation items - only generate if workspaceId is present
    const navItems: NavItem[] = workspaceId && workspaceId !== 'undefined' ? [
        { href: `${baseHref}/analytics`, icon: BarChart3, label: 'Analytics' },
        { href: `/${workspaceId}/customers`, icon: Users, label: 'Customers' },
        { href: `${baseHref}/history`, icon: MessageSquare, label: 'Communications' },
        { href: `${baseHref}/campaigns`, icon: Target, label: 'Campaigns' },
        { href: `${baseHref}/appointments`, icon: Calendar, label: 'Appointments' },
        { href: `${baseHref}/deals`, icon: Briefcase, label: 'Deals' },
        { href: `${baseHref}/workforce`, icon: Bot, label: 'Workforce' },
        { href: `${baseHref}/agent`, icon: Bot, label: 'Agents' },
        { href: `/${workspaceId}/settings/workers`, icon: Box, label: 'AI Workers' },
        { href: `${baseHref}/integrations`, icon: Plug, label: 'Integrations' },
        { href: `${baseHref}/account`, icon: Settings, label: 'Account' },
        { href: `${baseHref}/team`, icon: Users, label: 'Team' },
        { href: `${baseHref}/security`, icon: Shield, label: 'Security' }
    ] : [];

    const getPageTitle = () => {
        if (pathname === '/dashboard/analytics' || pathname?.endsWith('/dashboard/analytics')) return 'Dashboard';
        if (pathname?.includes('/customers')) return 'Customer Management';
        if (pathname?.endsWith('/history')) return 'Communications History';
        if (pathname?.endsWith('/campaigns')) return 'Campaigns';
        if (pathname?.endsWith('/appointments')) return 'Appointments';
        if (pathname?.endsWith('/deals')) return 'Deals';
        if (pathname?.endsWith('/workforce')) return 'Workforce';
        if (pathname?.includes('/workforce/tasks/')) return 'Task Details';
        if (pathname?.endsWith('/agent')) return 'Agents';
        if (pathname?.includes('/agent/')) return 'Edit Agent';
        if (pathname?.endsWith('/integrations')) return 'Integrations';
        if (pathname?.endsWith('/account')) return 'Account Settings';
        if (pathname?.endsWith('/team')) return 'Team Members';
        if (pathname?.endsWith('/security')) return 'Security';
        if (pathname?.includes('/settings/workers')) return 'Worker Instances';
        return 'Dashboard';
    };


    return (
        <>
            <style jsx global>{`
          body > section > header {
              display: none;
          }
      `}</style>
            <div className="flex flex-col min-h-screen bg-gray-50">
                {/* Mobile header */}
                <div className="lg:hidden flex items-center justify-between bg-white border-b border-gray-200 p-4">
                    <div className="flex items-center">
                        <Logo className="h-8 w-auto mr-4" />
                        <span className="font-medium">{getPageTitle()}</span>
                    </div>
                    <Button
                        className="-mr-3"
                        variant="ghost"
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    >
                        <Menu className="h-6 w-6" />
                        <span className="sr-only">Toggle sidebar</span>
                    </Button>
                </div>

                <div className="flex flex-1 overflow-hidden h-full">
                    {/* Sidebar */}
                    <aside
                        className={`w-64 bg-white border-r border-gray-200 lg:block flex flex-col ${isSidebarOpen ? 'block' : 'hidden'
                            } lg:relative absolute inset-y-0 left-0 z-40 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
                            }`}
                    >
                        <div className="px-6 py-4 border-b hidden lg:block">
                            <Link href={workspaceId && workspaceId !== 'undefined' ? baseHref : '/'}>
                                <Logo className="h-14 w-auto" />
                            </Link>
                        </div>

                        <nav className="flex-1 overflow-y-auto p-4">
                            {navItems.map((item) => (
                                <Link key={item.href} href={item.href} passHref>
                                    <Button
                                        variant={pathname === item.href ? 'secondary' : 'ghost'}
                                        className={`shadow-none my-1 w-full justify-start ${pathname === item.href ? 'bg-gray-100' : ''
                                            }`}
                                        onClick={() => setIsSidebarOpen(false)}
                                    >
                                        <item.icon className="h-4 w-4 mr-2" />
                                        {item.label}
                                    </Button>
                                </Link>
                            ))}
                        </nav>

                        <div className="p-4 border-t bg-white">
                            <Button
                                variant="ghost"
                                className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50"
                                onClick={async () => {
                                    await fetch('/api/sign-out', { method: 'POST' });
                                    window.location.href = '/';
                                }}
                            >
                                <LogOut className="h-4 w-4 mr-2" />
                                Sign Out
                            </Button>
                        </div>
                    </aside>

                    {/* Main content area wrapper */}
                    <div className="flex-1 flex flex-col overflow-hidden">
                        {/* New Desktop Header */}
                        <header className="h-[89px] bg-white border-b px-8 py-4 hidden lg:flex items-center justify-between">
                            <h1 className="text-2xl font-bold text-gray-900">{getPageTitle()}</h1>
                        </header>

                        {/* Main content */}
                        <main className="flex-1 overflow-y-auto p-4 lg:p-8 bg-gray-50">
                            {children}
                        </main>
                    </div>
                </div>
            </div>
        </>
    );
}
