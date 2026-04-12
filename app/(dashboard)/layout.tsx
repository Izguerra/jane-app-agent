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







import dynamic from 'next/dynamic';

const VoiceWidget = dynamic(() => import('@/components/voice-widget').then((mod) => mod.VoiceWidget), {
  ssr: false
});

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <section className="flex flex-col min-h-screen">
      <main className="flex-1">{children}</main>
      <Footer />
      <VoiceWidget />
    </section>
  );
}
