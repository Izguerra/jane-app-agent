
import { db } from './lib/db/drizzle';
import { users } from './lib/db/schema';

async function testConnection() {
    try {
        console.log('Testing DB connection...');
        const result = await db.select().from(users).limit(1);
        console.log('DB Connection successful:', result);
    } catch (error) {
        console.error('DB Connection failed:', error);
    }
}

testConnection();
