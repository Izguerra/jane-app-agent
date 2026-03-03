'use client';

import Link from 'next/link';
import { useActionState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Logo } from '@/components/logo';
import { Loader2, Info } from 'lucide-react';
import { signIn, signUp } from './actions';
import { Footer } from '@/components/footer';
import { ActionState } from '@/lib/auth/middleware';

export function Login({ mode = 'signin', isAdmin = false }: { mode?: 'signin' | 'signup', isAdmin?: boolean }) {
  const searchParams = useSearchParams();
  const redirect = searchParams.get('redirect');
  const priceId = searchParams.get('priceId');
  const inviteId = searchParams.get('inviteId');
  const [state, formAction, pending] = useActionState<ActionState, FormData>(
    mode === 'signin' ? signIn : signUp,
    { error: '' }
  );

  return (
    <div className="min-h-[100dvh] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-50">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <Logo className="h-20 w-20 text-orange-600" />
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          {isAdmin
            ? 'Admin Sign In'
            : (mode === 'signin' ? 'Sign in to your account' : 'Create your account')}
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <form className="space-y-6" action={formAction}>
          <input type="hidden" name="redirect" value={redirect || ''} />
          <input type="hidden" name="priceId" value={priceId || ''} />
          <input type="hidden" name="inviteId" value={inviteId || ''} />
          <div>
            {mode === 'signup' && (
              <>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <Label
                      htmlFor="firstName"
                      className="block text-sm font-medium text-gray-700"
                    >
                      First Name
                    </Label>
                    <div className="mt-1">
                      <Input
                        id="firstName"
                        name="firstName"
                        type="text"
                        autoComplete="given-name"
                        defaultValue={state.firstName || ''}
                        required
                        maxLength={50}
                        className="appearance-none rounded-full relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-orange-500 focus:border-orange-500 focus:z-10 sm:text-sm"
                        placeholder="John"
                      />
                    </div>
                  </div>
                  <div>
                    <Label
                      htmlFor="lastName"
                      className="block text-sm font-medium text-gray-700"
                    >
                      Last Name
                    </Label>
                    <div className="mt-1">
                      <Input
                        id="lastName"
                        name="lastName"
                        type="text"
                        autoComplete="family-name"
                        defaultValue={state.lastName || ''}
                        required
                        maxLength={50}
                        className="appearance-none rounded-full relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-orange-500 focus:border-orange-500 focus:z-10 sm:text-sm"
                        placeholder="Doe"
                      />
                    </div>
                  </div>
                </div>

                <div className="mb-4">
                  <Label
                    htmlFor="username"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Username <span className="text-gray-400 font-normal">(Optional)</span>
                  </Label>
                  <div className="mt-1">
                    <Input
                      id="username"
                      name="username"
                      type="text"
                      autoComplete="username"
                      defaultValue={state.username || ''}
                      maxLength={50}
                      className="appearance-none rounded-full relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-orange-500 focus:border-orange-500 focus:z-10 sm:text-sm"
                      placeholder="johndoe123"
                    />
                  </div>
                </div>
              </>
            )}

            <Label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700"
            >
              Email
            </Label>
            <div className="mt-1">
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                defaultValue={state.email}
                required
                maxLength={50}
                className="appearance-none rounded-full relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-orange-500 focus:border-orange-500 focus:z-10 sm:text-sm"
                placeholder="Enter your email"
              />
            </div>
          </div>

          <div>
            <Label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700"
            >
              Password
            </Label>
            <div className="mt-1">
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete={
                  mode === 'signin' ? 'current-password' : 'new-password'
                }
                defaultValue={state.password}
                required
                minLength={8}
                maxLength={100}
                className="appearance-none rounded-full relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-orange-500 focus:border-orange-500 focus:z-10 sm:text-sm"
                placeholder="Enter your password"
              />
            </div>
          </div>

          {mode === 'signin' && (
            <div className="text-right">
              <Link
                href="/forgot-password"
                className="text-sm font-medium text-orange-600 hover:text-orange-500"
              >
                Forgot password?
              </Link>
            </div>
          )}

          {priceId && mode === 'signup' && (
            <div className="rounded-md bg-blue-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <Info className="h-5 w-5 text-blue-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">Phone Number Included</h3>
                  <div className="mt-2 text-sm text-blue-700">
                    <p>You will be assigned a phone number as part of your plan. Please enter your preferred area code (US only).</p>
                  </div>
                </div>
              </div>
              <div className="mt-4">
                <Label htmlFor="preferredAreaCode" className="block text-sm font-medium text-blue-800">
                  Preferred Area Code
                </Label>
                <div className="mt-1">
                  <Input
                    id="preferredAreaCode"
                    name="preferredAreaCode"
                    type="text"
                    maxLength={3}
                    pattern="[0-9]*"
                    className="appearance-none rounded-full block w-full px-3 py-2 border border-blue-300 placeholder-blue-300 text-blue-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="e.g. 415"
                  />
                </div>
              </div>
            </div>
          )}

          {mode === 'signup' && (
            <div className="flex items-start space-x-2">
              <input
                id="terms"
                name="terms"
                type="checkbox"
                required
                className="mt-1 h-4 w-4 text-orange-600 focus:ring-orange-500 border-gray-300 rounded cursor-pointer"
              />
              <label htmlFor="terms" className="text-sm text-gray-700">
                I agree to the{' '}
                <Link href="/terms" className="font-medium text-orange-600 hover:text-orange-500" target="_blank">
                  Terms and Conditions
                </Link>{' '}
                and{' '}
                <Link href="/privacy" className="font-medium text-orange-600 hover:text-orange-500" target="_blank">
                  Privacy Policy
                </Link>
                .
              </label>
            </div>
          )}

          {state?.error && (
            <div className="text-red-500 text-sm">{state.error}</div>
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
                  Loading...
                </>
              ) : mode === 'signin' ? (
                'Sign in'
              ) : (
                'Sign up'
              )}
            </Button>
          </div>

          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-gray-50 px-2 text-gray-500">Or continue with</span>
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            className="w-full rounded-full border-gray-300"
            onClick={async () => {
              const { createClient } = await import('@/lib/supabase/client');
              const supabase = createClient();
              await supabase.auth.signInWithOAuth({
                provider: 'google',
                options: {
                  redirectTo: `${window.location.origin}/auth/callback`,
                },
              });
            }}
          >
            <svg className="mr-2 h-4 w-4" aria-hidden="true" focusable="false" data-prefix="fab" data-icon="google" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 488 512">
              <path fill="currentColor" d="M488 261.8C488 403.3 391.1 504 248 504 110.8 504 0 393.2 0 256S110.8 8 248 8c66.8 0 123 24.5 166.3 64.9l-67.5 64.9C258.5 52.6 94.3 116.6 94.3 256c0 86.5 69.1 156.6 153.7 156.6 98.2 0 135-70.4 140.8-106.9H248v-85.3h236.1c2.3 12.7 3.9 24.9 3.9 41.4z"></path>
            </svg>
            Sign in with Google
          </Button>
        </form>

        {!isAdmin && (
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-gray-50 text-gray-500">
                  {mode === 'signin'
                    ? 'New to our platform?'
                    : 'Already have an account?'}
                </span>
              </div>
            </div>

            <div className="mt-6">
              <Link
                href={
                  mode === 'signin'
                    ? '/#pricing'
                    : `/sign-in?${new URLSearchParams({
                      ...(redirect ? { redirect } : {}),
                      ...(priceId ? { priceId } : {}),
                      ...(inviteId ? { inviteId } : {}),
                    }).toString()}`
                }
                className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-full shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
              >
                {mode === 'signin'
                  ? 'Create an account'
                  : 'Sign in to existing account'}
              </Link>
            </div>
          </div>
        )}

        {/* Admin Sign In - Hidden for separate page */}
        {/* {mode === 'signin' && (
                <div className="mt-4">
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-300" />
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-2 bg-gray-50 text-gray-500">
                        Admin Access
                      </span>
                    </div>
                  </div>
                  <div className="mt-4">
                    <Link
                      href="/admin/settings"
                      className="w-full flex justify-center py-2 px-4 border border-blue-600 rounded-full shadow-sm text-sm font-medium text-blue-600 bg-white hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      🔐 Admin Sign In
                    </Link>
                  </div>
                </div>
              )} */}

      </div>
      <Footer />
    </div >
  );
}
