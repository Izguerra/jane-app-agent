
import { createAdminClient } from './lib/supabase/admin';
import * as dotenv from 'dotenv';
dotenv.config({ path: '.env' });

async function checkUser() {
    const email = 'resguerra75@gmail.com';
    const supabase = createAdminClient();

    // List users to find by email (admin.getUserByEmail doesn't exist directly in some versions, simpler to list or get via generic)
    // Actually lists are paginated.
    // Try explicit ID if we can guess it? No.
    // Use listUsers with filter?

    const { data, error } = await supabase.auth.admin.listUsers();

    if (error) {
        console.error('Error listing users:', error);
        return;
    }

    const user = data.users.find(u => u.email === email);

    if (!user) {
        console.log('User not found.');
    } else {
        console.log('User Found:', {
            id: user.id,
            email: user.email,
            providers: user.app_metadata.providers,
            identities: user.identities,
            confirmed_at: user.confirmed_at,
            last_sign_in: user.last_sign_in_at
        });
    }
}

checkUser();
