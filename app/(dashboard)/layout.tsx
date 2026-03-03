'use client';

import Link from 'next/link';
import { use, useState, Suspense, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Footer } from '@/components/footer';
import { Home, LogOut, Users } from 'lucide-react';
import { Logo } from '@/components/logo';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { signOut } from '@/app/(login)/actions';
import { useRouter, usePathname } from 'next/navigation';
import { User } from '@/lib/db/schema';
import useSWR, { mutate } from 'swr';

const fetcher = async (url: string) => {
  const res = await fetch(url);
  if (res.status === 401) {
    return null;
  }
  if (!res.ok) {
    throw new Error('Failed to fetch');
  }
  return res.json();
};

function UserMenu() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { data: user, error } = useSWR<User & { workspaceId?: string }>('/api/user', fetcher);
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  async function handleSignOut() {
    await signOut();
    mutate('/api/user');
    window.location.href = '/';
  }

  if (!mounted || !user) {
    return (
      <>
        <div className="hidden md:flex items-center space-x-6 mr-4">
          <Link href="#features" className="text-sm font-medium text-gray-700 hover:text-gray-900">Features</Link>
          <Link href="#how-it-works" className="text-sm font-medium text-gray-700 hover:text-gray-900">How It Works</Link>
          <Link href="#pricing" className="text-sm font-medium text-gray-700 hover:text-gray-900">Pricing</Link>
          <Link href="#faq" className="text-sm font-medium text-gray-700 hover:text-gray-900">FAQ</Link>
          <Link href="#contact" className="text-sm font-medium text-gray-700 hover:text-gray-900">Contact</Link>
        </div>
        <Link
          href="/admin/sign-in"
          className="text-sm font-medium text-gray-700 hover:text-gray-900"
        >
          Admin Sign In
        </Link>
        <Link
          href="/sign-in"
          className="text-sm font-medium text-gray-700 hover:text-gray-900"
        >
          Customer Sign In
        </Link>
        <Button asChild className="rounded-full">
          <Link href="#pricing">Sign Up</Link>
        </Button>
      </>
    );
  }

  return (
    <DropdownMenu open={isMenuOpen} onOpenChange={setIsMenuOpen}>
      <DropdownMenuTrigger suppressHydrationWarning>
        <Avatar className="cursor-pointer size-9">
          <AvatarImage alt={user.name || ''} />
          <AvatarFallback>
            {user.email
              .split(' ')
              .map((n) => n[0])
              .join('')}
          </AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="flex flex-col gap-1">
        {user.workspaceId && (
          <DropdownMenuItem className="cursor-pointer">
            <Link
              href={
                user.role === 'owner' || user.role === 'supaagent_admin'
                  ? '/admin/analytics'
                  : `/${user.workspaceId}/dashboard/analytics`
              }
              className="flex w-full items-center"
            >
              <Home className="mr-2 h-4 w-4" />
              <span>Dashboard</span>
            </Link>
          </DropdownMenuItem>
        )}
        <DropdownMenuItem className="cursor-pointer" onSelect={(e) => {
          e.preventDefault();
          handleSignOut();
        }}>
          <LogOut className="mr-2 h-4 w-4" />
          <span>Sign out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function Header() {
  const { data: user } = useSWR<User & { workspaceId?: string }>('/api/user', fetcher);
  const [mounted, setMounted] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    setMounted(true);
  }, []);

  const dashboardLink = mounted && (user?.role === 'owner' || user?.role === 'supaagent_admin')
    ? '/admin/analytics'
    : user?.workspaceId
      ? `/${user.workspaceId}/dashboard/analytics`
      : '/dashboard/analytics';

  return (
    <header className="border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Link
            href={dashboardLink}
            className="flex items-center"
          >
            <Logo className="h-14 w-auto" />
          </Link>
          {mounted && pathname !== '/' && (
            <h1 className="text-xl font-semibold text-gray-900 border-l pl-4 border-gray-200">
              {pathname === '/dashboard/analytics' || pathname?.endsWith('/dashboard/analytics') ? 'Dashboard' :
                pathname?.endsWith('/history') ? 'Communications History' :
                  pathname?.endsWith('/agent') ? 'Agents' :
                    pathname?.includes('/agent/') ? 'Edit Agent' :
                      pathname?.endsWith('/integrations') ? 'Integrations' :
                        pathname?.endsWith('/account') ? 'Account Settings' :
                          pathname?.endsWith('/team') ? 'Team Members' :
                            pathname?.endsWith('/security') ? 'Security' :
                              'Dashboard'}
            </h1>
          )}
        </div>
        <div className="flex items-center space-x-4">
          <Suspense fallback={<div className="h-9" />}>
            <UserMenu />
          </Suspense>
        </div>
      </div>
    </header>
  );
}

import dynamic from 'next/dynamic';

const VoiceWidget = dynamic(() => import('@/components/voice-widget').then((mod) => mod.VoiceWidget), {
  ssr: false
});

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <section className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-1">{children}</main>
      <Footer />
      <VoiceWidget />
    </section>
  );
}
