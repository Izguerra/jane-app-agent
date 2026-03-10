'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Logo } from '@/components/logo';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { resetPasswordAction } from '@/app/(login)/actions';
import { Footer } from '@/components/footer';

export default function ResetPasswordPage() {
    const router = useRouter();
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [pending, setPending] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }

        setPending(true);

        try {
            const formData = new FormData();
            formData.append('password', password);
            formData.append('confirmPassword', confirmPassword);

            const result = await resetPasswordAction(formData);

            if (result.error) {
                setError(result.error);
            } else {
                setSuccess(true);
                // Redirect to sign-in after 3 seconds
                setTimeout(() => {
                    router.push('/sign-in');
                }, 3000);
            }
        } catch (err) {
            setError('An unexpected error occurred. Please try again.');
        } finally {
            setPending(false);
        }
    }

    return (
        <div className="min-h-[100dvh] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-50">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="flex justify-center">
                    <Logo className="h-20 w-20 text-orange-600" />
                </div>
                <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                    Set new password
                </h2>
                <p className="mt-2 text-center text-sm text-gray-600">
                    Enter your new password below
                </p>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                {success ? (
                    <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
                        <div className="text-center">
                            <CheckCircle2 className="mx-auto h-12 w-12 text-green-500" />
                            <h3 className="mt-4 text-lg font-medium text-gray-900">Password updated!</h3>
                            <p className="mt-2 text-sm text-gray-600">
                                Your password has been reset successfully. Redirecting to sign in...
                            </p>
                        </div>
                    </div>
                ) : (
                    <form className="space-y-6" onSubmit={handleSubmit}>
                        <div>
                            <Label
                                htmlFor="password"
                                className="block text-sm font-medium text-gray-700"
                            >
                                New password
                            </Label>
                            <div className="mt-1">
                                <Input
                                    id="password"
                                    name="password"
                                    type="password"
                                    autoComplete="new-password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    minLength={8}
                                    className="appearance-none rounded-full relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-orange-500 focus:border-orange-500 focus:z-10 sm:text-sm"
                                    placeholder="Enter new password"
                                />
                            </div>
                        </div>

                        <div>
                            <Label
                                htmlFor="confirmPassword"
                                className="block text-sm font-medium text-gray-700"
                            >
                                Confirm password
                            </Label>
                            <div className="mt-1">
                                <Input
                                    id="confirmPassword"
                                    name="confirmPassword"
                                    type="password"
                                    autoComplete="new-password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    required
                                    minLength={8}
                                    className="appearance-none rounded-full relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-orange-500 focus:border-orange-500 focus:z-10 sm:text-sm"
                                    placeholder="Confirm new password"
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="text-red-500 text-sm">{error}</div>
                        )}

                        <div>
                            <Button
                                type="submit"
                                className="w-full flex justify-center items-center py-2 px-4 border border-transparent rounded-full shadow-sm text-sm font-medium text-white bg-orange-600 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
                                disabled={pending}
                            >
                                {pending ? (
                                    <>
                                        <Loader2 className="animate-spin mr-2 h-4 w-4" />
                                        Updating...
                                    </>
                                ) : (
                                    'Update password'
                                )}
                            </Button>
                        </div>
                    </form>
                )}
            </div>
            <Footer />
        </div>
    );
}
