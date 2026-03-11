'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Logo } from '@/components/logo';
import { Loader2, ArrowLeft, KeyRound, Mail } from 'lucide-react';
import { sendPasswordResetEmail, verifyResetCode } from '@/app/(login)/actions';
import { Footer } from '@/components/footer';

export default function ForgotPasswordPage() {
    const router = useRouter();
    const [step, setStep] = useState<'email' | 'code'>('email');
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [devOtp, setDevOtp] = useState<string | null>(null);

    async function handleEmailSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsLoading(true);
        setError(null);
        setDevOtp(null);

        try {
            const formData = new FormData(event.currentTarget);
            const result = await sendPasswordResetEmail(formData);

            if (result.error) {
                setError(result.error);
            } else {
                setStep('code');
                if (result.devOtp) {
                    setDevOtp(result.devOtp);
                    setOtp(result.devOtp); // Auto-fill for convenience
                }
            }
        } catch (err) {
            setError('An unexpected error occurred. Please try again.');
        } finally {
            setIsLoading(false);
        }
    }

    async function handleCodeSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('email', email);
            formData.append('code', otp);

            const result = await verifyResetCode(formData);

            if (result.error) {
                setError(result.error);
            } else {
                router.push('/reset-password');
            }
        } catch (err) {
            setError('Verification failed. Please try again.');
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div className="min-h-[100dvh] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-50">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="flex justify-center">
                    <Logo className="h-20 w-20 text-blue-600" />
                </div>
                <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                    {step === 'email' ? 'Reset your password' : 'Enter Verification Code'}
                </h2>
                <p className="mt-2 text-center text-sm text-gray-600">
                    {step === 'email'
                        ? "Enter your email and we'll send you a recovery code"
                        : `We sent a code to ${email}`}
                </p>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
                    {devOtp && step === 'code' && (
                        <div className="mb-6 rounded-md bg-yellow-50 p-4 border border-yellow-200">
                            <p className="text-sm text-yellow-800 font-bold mb-1">Dev Mode Code:</p>
                            <p className="text-2xl font-mono text-yellow-900 tracking-widest">{devOtp}</p>
                            <p className="text-xs text-yellow-600 mt-2">Code auto-filled below</p>
                        </div>
                    )}

                    {step === 'email' ? (
                        <form className="space-y-6" onSubmit={handleEmailSubmit}>
                            <div>
                                <Label htmlFor="email" className="block text-sm font-medium text-gray-700">
                                    Email address
                                </Label>
                                <div className="mt-1 relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Mail className="h-5 w-5 text-gray-400" />
                                    </div>
                                    <Input
                                        id="email"
                                        name="email"
                                        type="email"
                                        autoComplete="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                        className="pl-10 appearance-none rounded-full block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                        placeholder="Enter your email"
                                    />
                                </div>
                            </div>

                            {error && <div className="text-red-500 text-sm">{error}</div>}

                            <Button
                                type="submit"
                                className="w-full flex justify-center items-center py-2 px-4 border border-transparent rounded-full shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="animate-spin mr-2 h-4 w-4" />
                                        Sending...
                                    </>
                                ) : (
                                    'Send Recovery Code'
                                )}
                            </Button>
                        </form>
                    ) : (
                        <form className="space-y-6" onSubmit={handleCodeSubmit}>
                            <div>
                                <Label htmlFor="code" className="block text-sm font-medium text-gray-700">
                                    Verification Code
                                </Label>
                                <div className="mt-1 relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <KeyRound className="h-5 w-5 text-gray-400" />
                                    </div>
                                    <Input
                                        id="code"
                                        name="code"
                                        type="text"
                                        value={otp}
                                        onChange={(e) => setOtp(e.target.value)}
                                        required
                                        className="pl-10 appearance-none rounded-full block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm tracking-widest text-lg"
                                        placeholder="123456"
                                    />
                                </div>
                            </div>

                            {error && <div className="text-red-500 text-sm">{error}</div>}

                            <Button
                                type="submit"
                                className="w-full flex justify-center items-center py-2 px-4 border border-transparent rounded-full shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="animate-spin mr-2 h-4 w-4" />
                                        Verifying...
                                    </>
                                ) : (
                                    'Verify Code'
                                )}
                            </Button>

                            <div className="text-center mt-4">
                                <button
                                    type="button"
                                    onClick={() => setStep('email')}
                                    className="text-sm font-medium text-blue-600 hover:text-blue-500"
                                >
                                    Use a different email
                                </button>
                            </div>
                        </form>
                    )}

                    <div className="mt-6">
                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-gray-300" />
                            </div>
                            <div className="relative flex justify-center text-sm">
                                <span className="px-2 bg-white text-gray-500">
                                    Or
                                </span>
                            </div>
                        </div>

                        <div className="mt-6 text-center">
                            <Link
                                href="/sign-in"
                                className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-500"
                            >
                                <ArrowLeft className="mr-2 h-4 w-4" />
                                Back to sign in
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
            <Footer />
        </div>
    );
}
