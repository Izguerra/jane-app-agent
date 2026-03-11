'use client';

import { useActionState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';
import { updateAccount } from '@/app/(login)/actions';
import { User } from '@/lib/db/schema';
import useSWR from 'swr';
import { Suspense, useEffect } from 'react';
import { ActivityLogSection } from './activity-log-section';
import { SubscriptionCard } from './subscription-card';
import { BillingHistory } from './billing-history';
import { useSearchParams } from 'next/navigation';
import { toast } from 'sonner';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

type ActionState = {
  firstName?: string;
  lastName?: string;
  username?: string;
  error?: string;
  success?: string;
};

type AccountFormProps = {
  state: ActionState;
  firstNameValue?: string;
  lastNameValue?: string;
  usernameValue?: string;
  emailValue?: string;
};

function AccountForm({
  state,
  firstNameValue = '',
  lastNameValue = '',
  usernameValue = '',
  emailValue = ''
}: AccountFormProps) {
  return (
    <>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="firstName" className="mb-2">
            First Name
          </Label>
          <Input
            id="firstName"
            name="firstName"
            placeholder="First Name"
            defaultValue={state.firstName || firstNameValue}
            required
            maxLength={50}
          />
        </div>
        <div>
          <Label htmlFor="lastName" className="mb-2">
            Last Name
          </Label>
          <Input
            id="lastName"
            name="lastName"
            placeholder="Last Name"
            defaultValue={state.lastName || lastNameValue}
            required
            maxLength={50}
          />
        </div>
      </div>
      <div>
        <Label htmlFor="username" className="mb-2">
          Username
        </Label>
        <Input
          id="username"
          name="username"
          placeholder="username"
          defaultValue={state.username || usernameValue}
          required
          maxLength={50}
        />
      </div>
      <div>
        <Label htmlFor="email" className="mb-2">
          Email
        </Label>
        <Input
          id="email"
          name="email"
          type="email"
          placeholder="Enter your email"
          defaultValue={emailValue}
          required
        />
      </div>
    </>
  );
}

function AccountFormWithData({ state }: { state: ActionState }) {
  const { data: user } = useSWR<User>('/api/user', fetcher);
  return (
    <AccountForm
      state={state}
      firstNameValue={user?.firstName ?? ''}
      lastNameValue={user?.lastName ?? ''}
      usernameValue={user?.username ?? ''}
      emailValue={user?.email ?? ''}
    />
  );
}

export default function ProfilePage() {
  const [state, formAction, isPending] = useActionState<ActionState, FormData>(
    updateAccount,
    {}
  );

  // Handle redirect from Stripe
  const searchParams = useSearchParams();
  useEffect(() => {
    if (searchParams.get('checkout') === 'success') {
      toast.success("Subscription updated successfully!");
    } else if (searchParams.get('checkout') === 'cancel') {
      toast.info("Checkout cancelled.");
    }
  }, [searchParams]);

  return (
    <section className="flex-1 p-4 lg:p-8">
      <h1 className="text-lg lg:text-2xl font-medium text-gray-900 mb-6">
        Profile
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Account Information</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" action={formAction}>
            <div className="space-y-4">
              <Suspense fallback={<AccountForm state={state} />}>
                <AccountFormWithData state={state} />
              </Suspense>
            </div>
            {state.error && (
              <p className="text-red-500 text-sm">{state.error}</p>
            )}
            {state.success && (
              <p className="text-green-500 text-sm">{state.success}</p>
            )}
            <Button
              type="submit"
              className="bg-orange-500 hover:bg-orange-600 text-white"
              disabled={isPending}
            >
              {isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save Changes'
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="mt-8 space-y-8">
        <SubscriptionCard />
        <BillingHistory />
        <ActivityLogSection />
      </div>
    </section>
  );
}
