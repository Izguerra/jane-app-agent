import { client } from './lib/db/drizzle';

async function testConnection() {
    try {
        console.log('Testing DB connection...');
        const result = await client`SELECT 1`;
        console.log('Connection successful:', result);
        process.exit(0);
    } catch (error) {
        console.error('Connection failed:', error);
        process.exit(1);
    }
}

testConnection();
