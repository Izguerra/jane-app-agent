
import dotenv from 'dotenv';
import { eq, sql } from 'drizzle-orm';

dotenv.config({ path: '/Users/randyesguerra/Documents/Documents-Randy/Projects/JaneAppAgent/.env' });

async function checkUser() {
    // Dynamic import to ensure env is loaded first
    const { db } = await import('./lib/db/drizzle');
    const { users, teamMembers } = await import('./lib/db/schema');

    const email = 'resguerra75@gmail.com';
    console.log(`Checking user: ${email}`);

    // Debug: Check if POSTGRES_URL is loaded
    console.log('POSTGRES_URL loaded:', process.env.POSTGRES_URL ? 'YES' : 'NO');

    const user = await db.query.users.findFirst({
        where: sql`lower(${users.email}) = ${email.toLowerCase()}`,
        with: {
            teamMembers: true
        }
    });

    if (!user) {
        console.log('User NOT FOUND in local DB.');
    } else {
        console.log('User FOUND in local DB:');
        console.log(JSON.stringify(user, null, 2));
        console.log(`Match Supabase ID check: ${user.id}`);
    }
    process.exit(0);
}

checkUser().catch(console.error);
