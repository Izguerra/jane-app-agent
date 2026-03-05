import { Suspense } from 'react';
import { Login } from '../../(login)/login';

export default function AdminSignInPage() {
    return (
        <Suspense>
            {/* Reuse Login component but in Admin Mode */}
            <Login mode="signin" isAdmin={true} />
        </Suspense>
    );
}
