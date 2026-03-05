import './globals.css';
import type { Metadata, Viewport } from 'next';
import { Manrope } from 'next/font/google';
import { getUser, getTeamForUser } from '@/lib/db/queries';
import { SWRConfig } from 'swr';
import { Toaster } from '@/components/ui/sonner';

export const metadata: Metadata = {
  title: 'SupaAgent - AI Customer Support Chatbots',
  description: 'Create intelligent voice and text chatbots for your business. Automate customer support 24/7 with AI-powered agents.'
};

export const viewport: Viewport = {
  maximumScale: 1
};

const manrope = Manrope({ subsets: ['latin'], display: 'swap' });

export default async function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  const [userData, teamData] = await Promise.all([getUser(), getTeamForUser()]);

  // Serialize data to handle Date objects (which cannot be passed to Client Components)
  const user = userData ? JSON.parse(JSON.stringify(userData)) : null;
  const team = teamData ? JSON.parse(JSON.stringify(teamData)) : null;

  return (
    <html
      lang="en"
      className={`bg-white dark:bg-gray-950 text-black dark:text-white ${manrope.className}`}
      suppressHydrationWarning
    >
      <body className="min-h-[100dvh] bg-gray-50" suppressHydrationWarning>
        <SWRConfig
          value={{
            fallback: {
              '/api/user': user,
              '/api/team': team
            }
          }}
        >
          {children}
          <Toaster />
        </SWRConfig>
      </body>
    </html>
  );
}
