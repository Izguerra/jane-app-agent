'use client';

import dynamic from 'next/dynamic';
import { Footer } from '@/components/footer';

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
