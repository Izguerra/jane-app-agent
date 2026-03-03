'use client';

import Link from 'next/link';
import { Logo } from '@/components/logo';
import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Footer } from '@/components/footer';

export default function AuthCodeErrorPage() {
    return (
        <div className="min-h-[100dvh] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-50">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="flex justify-center">
                    <Logo className="h-20 w-20 text-orange-600" />
                </div>

                <div className="mt-8 bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
                    <div className="text-center">
                        <AlertCircle className="mx-auto h-12 w-12 text-red-500" />
                        <h2 className="mt-4 text-2xl font-bold text-gray-900">
                            Authentication Error
                        </h2>
                        <p className="mt-2 text-sm text-gray-600">
                            The authentication link has expired or is invalid.
                            This can happen if the link was already used or has timed out.
                        </p>

                        <div className="mt-6 space-y-3">
                            <Link href="/forgot-password">
                                <Button className="w-full bg-orange-600 hover:bg-orange-700 rounded-full">
                                    Request new reset link
                                </Button>
                            </Link>
                            <Link href="/sign-in">
                                <Button variant="outline" className="w-full rounded-full mt-2">
                                    Back to sign in
                                </Button>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
            <Footer />
        </div>
    );
}
