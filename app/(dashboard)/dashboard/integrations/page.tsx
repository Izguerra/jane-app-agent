'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import useSWR from 'swr';
import { Loader2 } from 'lucide-react';



export default function IntegrationsRedirectPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { data: user, error } = useSWR('/api/user');

    useEffect(() => {
        if (user && user.workspaceId) {
            // Construct query string to preserve success params
            const params = new URLSearchParams(searchParams);
            // Redirect to correct URL with workspace ID
            router.replace(`/${user.workspaceId}/dashboard/integrations?${params.toString()}`);
        } else if (error) {
            router.push('/sign-in');
        }
    }, [user, error, router, searchParams]);

    return (
        <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-muted-foreground">Redirecting to your workspace...</p>
        </div>
    );
}
