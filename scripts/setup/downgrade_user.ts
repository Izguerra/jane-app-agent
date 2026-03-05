
import { db } from '@/lib/db/drizzle';
import { users } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';

const emailToPromote = process.argv[2];

if (!emailToPromote) {
    console.error('Please provide an email address as an argument.');
    process.exit(1);
}

async function main() {
    console.log(`Downgrading ${emailToPromote} to owner...`);

    const user = await db.select().from(users).where(eq(users.email, emailToPromote)).limit(1);

    if (user.length === 0) {
        console.error('User not found.');
        process.exit(1);
    }

    await db.update(users).set({ role: 'owner' }).where(eq(users.id, user[0].id));

    console.log(`Successfully downgraded ${user[0].name} (${user[0].email}) to owner.`);
    process.exit(0);
}

main().catch((err) => {
    console.error(err);
    process.exit(1);
});
