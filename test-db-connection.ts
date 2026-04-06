import { db } from './lib/db/drizzle';
import { agents } from './lib/db/schema';
import { eq } from 'drizzle-orm';

async function testConnection() {
  console.log('Testing Drizzle connection...');
  try {
    const allAgents = await db.select().from(agents).limit(1);
    console.log('Connection successful. Found agents:', allAgents.length);
  } catch (error) {
    console.error('Connection failed:', error);
    process.exit(1);
  }
}

testConnection();
