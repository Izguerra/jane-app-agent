import { db } from './lib/db/drizzle';
import { sql } from 'drizzle-orm';

async function listTables() {
  console.log('Listing Tables...');
  try {
    const result = await db.execute(sql`SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'`);
    console.log('Tables in public schema:');
    // Result is an array of objects
    (result as any).forEach((row: any) => console.log(`- ${row.table_name}`));
  } catch (error) {
    console.error('Failed to list tables:', error);
    process.exit(1);
  }
}

listTables();
