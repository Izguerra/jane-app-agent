import { db } from '@/lib/db/drizzle';
import { sql } from 'drizzle-orm';

export const dynamic = 'force-dynamic';

export default async function TestDBPage() {
    try {
        const result = await db.execute(sql`SELECT 1`);
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold text-green-600">Database Connection Successful</h1>
                <pre className="mt-4 p-4 bg-gray-100 rounded">
                    {JSON.stringify(result, null, 2)}
                </pre>
            </div>
        );
    } catch (error: any) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold text-red-600">Database Connection Failed</h1>
                <pre className="mt-4 p-4 bg-red-50 text-red-900 rounded whitespace-pre-wrap">
                    {error.message}
                    {'\n\n'}
                    {JSON.stringify(error, null, 2)}
                </pre>
            </div>
        );
    }
}
