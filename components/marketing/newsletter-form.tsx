'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { subscribeToNewsletter } from '@/app/actions/newsletter';
import { Send, CheckCircle2, AlertCircle } from 'lucide-react';

export function NewsletterForm() {
    const [status, setStatus] = useState<{ type: 'success' | 'error' | null; message: string }>({
        type: null,
        message: '',
    });
    const [isSubmitting, setIsSubmitting] = useState(false);

    async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setIsSubmitting(true);
        setStatus({ type: null, message: '' });

        const formData = new FormData(e.currentTarget);
        const result = await subscribeToNewsletter(formData);

        setStatus({
            type: result.success ? 'success' : 'error',
            message: result.message,
        });
        setIsSubmitting(false);

        if (result.success) {
            (e.target as HTMLFormElement).reset();
        }
    }

    return (
        <div className="w-full max-w-md mx-auto">
            <h3 className="text-gray-900 text-lg font-semibold mb-4 text-center">Stay updated with SupaAgent</h3>

            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
                <div className="flex gap-2">
                    <Input
                        type="email"
                        name="email"
                        placeholder="Enter your email"
                        required
                        disabled={isSubmitting}
                        className="bg-white"
                    />
                    <Button
                        type="submit"
                        disabled={isSubmitting}
                        className="bg-blue-600 hover:bg-blue-700 text-white shrink-0"
                    >
                        {isSubmitting ? (
                            <span className="animate-spin">⏳</span>
                        ) : (
                            <Send className="h-4 w-4" />
                        )}
                        <span className="sr-only">Subscribe</span>
                    </Button>
                </div>

                {status.type && (
                    <div className={`flex items-center gap-2 text-sm ${status.type === 'success' ? 'text-green-600' : 'text-red-600'
                        }`}>
                        {status.type === 'success' ? (
                            <CheckCircle2 className="h-4 w-4" />
                        ) : (
                            <AlertCircle className="h-4 w-4" />
                        )}
                        {status.message}
                    </div>
                )}
            </form>
        </div>
    );
}
