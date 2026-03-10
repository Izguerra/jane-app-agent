import { db } from '../drizzle';
import { sql } from 'drizzle-orm';
import { v4 as uuidv4 } from 'uuid';

/**
 * Migration Script: Convert all IDs from varchar(20) to UUID v4 (varchar(36))
 * 
 * This script migrates all existing numeric/short IDs to cryptographically secure UUIDs.
 * 
 * CRITICAL: This is a destructive migration that will:
 * 1. Change all ID formats across all tables
 * 2. Invalidate existing user sessions
 * 3. Require users to re-login
 * 
 * BACKUP YOUR DATABASE BEFORE RUNNING THIS SCRIPT!
 */

interface IdMapping {
    oldId: string;
    newId: string;
}

const tables = [
    { name: 'users', idColumn: 'id', fkReferences: [] },
    { name: 'teams', idColumn: 'id', fkReferences: [] },
    { name: 'team_members', idColumn: 'id', fkReferences: ['user_id', 'team_id'] },
    { name: 'activity_logs', idColumn: 'id', fkReferences: ['team_id', 'user_id'] },
    { name: 'invitations', idColumn: 'id', fkReferences: ['team_id', 'invited_by'] },
    { name: 'workspaces', idColumn: 'id', fkReferences: ['team_id'] },
    { name: 'integrations', idColumn: 'id', fkReferences: ['workspace_id', 'agent_id'] },
    { name: 'agents', idColumn: 'id', fkReferences: ['workspace_id'] },
    { name: 'communications', idColumn: 'id', fkReferences: ['workspace_id', 'integration_id', 'agent_id'] },
    { name: 'documents', idColumn: 'id', fkReferences: ['workspace_id'] },
    { name: 'customers', idColumn: 'id', fkReferences: ['workspace_id'] },
    { name: 'phone_numbers', idColumn: 'id', fkReferences: ['workspace_id', 'agent_id'] },
    { name: 'conversation_messages', idColumn: 'id', fkReferences: ['workspace_id', 'communication_id'] },
    { name: 'whatsapp_templates', idColumn: 'id', fkReferences: ['workspace_id'] },
    { name: 'contact_submissions', idColumn: 'id', fkReferences: [] },
];

async function migrateToUUID() {
    console.log('🚀 Starting UUID migration...\n');

    // Step 1: Alter column types to support UUID (varchar(36))
    console.log('Step 1: Altering column types to varchar(36)...');
    for (const table of tables) {
        console.log(`  - Altering ${table.name}.${table.idColumn}`);
        await db.execute(sql.raw(`
      ALTER TABLE ${table.name} 
      ALTER COLUMN ${table.idColumn} TYPE VARCHAR(36)
    `));

        // Alter foreign key columns
        for (const fkColumn of table.fkReferences) {
            console.log(`  - Altering ${table.name}.${fkColumn}`);
            await db.execute(sql.raw(`
        ALTER TABLE ${table.name} 
        ALTER COLUMN ${fkColumn} TYPE VARCHAR(36)
      `));
        }
    }
    console.log('✅ Column types altered\n');

    // Step 2: Create ID mappings for each table
    console.log('Step 2: Generating UUID mappings...');
    const allMappings: Record<string, IdMapping[]> = {};

    for (const table of tables) {
        const rows: any[] = await db.execute(sql.raw(`
      SELECT ${table.idColumn} as old_id FROM ${table.name}
    `)) as any;

        const mappings: IdMapping[] = rows.map((row: any) => ({
            oldId: row.old_id,
            newId: uuidv4(),
        }));

        allMappings[table.name] = mappings;
        console.log(`  - Generated ${mappings.length} UUID(s) for ${table.name}`);
    }
    console.log('✅ UUID mappings generated\n');

    // Step 3: Update primary keys
    console.log('Step 3: Updating primary keys...');
    for (const table of tables) {
        const mappings = allMappings[table.name];

        for (const mapping of mappings) {
            await db.execute(sql.raw(`
        UPDATE ${table.name}
        SET ${table.idColumn} = '${mapping.newId}'
        WHERE ${table.idColumn} = '${mapping.oldId}'
      `));
        }

        console.log(`  - Updated ${mappings.length} primary key(s) in ${table.name}`);
    }
    console.log('✅ Primary keys updated\n');

    // Step 4: Update foreign keys
    console.log('Step 4: Updating foreign keys...');

    // Users FK refs
    const userMappings = allMappings['users'];
    for (const mapping of userMappings) {
        await db.execute(sql.raw(`UPDATE team_members SET user_id = '${mapping.newId}' WHERE user_id = '${mapping.oldId}'`));
        await db.execute(sql.raw(`UPDATE activity_logs SET user_id = '${mapping.newId}' WHERE user_id = '${mapping.oldId}'`));
        await db.execute(sql.raw(`UPDATE invitations SET invited_by = '${mapping.newId}' WHERE invited_by = '${mapping.oldId}'`));
    }
    console.log('  - Updated user FK references');

    // Teams FK refs
    const teamMappings = allMappings['teams'];
    for (const mapping of teamMappings) {
        await db.execute(sql.raw(`UPDATE team_members SET team_id = '${mapping.newId}' WHERE team_id = '${mapping.oldId}'`));
        await db.execute(sql.raw(`UPDATE activity_logs SET team_id = '${mapping.newId}' WHERE team_id = '${mapping.oldId}'`));
        await db.execute(sql.raw(`UPDATE invitations SET team_id = '${mapping.newId}' WHERE team_id = '${mapping.oldId}'`));
        await db.execute(sql.raw(`UPDATE workspaces SET team_id = '${mapping.newId}' WHERE team_id = '${mapping.oldId}'`));
    }
    console.log('  - Updated team FK references');

    // Workspaces FK refs
    const workspaceMappings = allMappings['workspaces'];
    for (const mapping of workspaceMappings) {
        await db.execute(sql.raw(`UPDATE integrations SET workspace_id = '${mapping.newId}' WHERE workspace_id = '${mapping.oldId}'`));
        await db.execute(sql.raw(`UPDATE agents SET workspace_id = '${mapping.newId}' WHERE workspace_id = '${mapping.oldId}'`));
        await db.execute(sql.raw(`UPDATE communications SET workspace_id = '${mapping.newId}' WHERE workspace_id = '${mapping.oldId}'`));
        await db.execute(sql.raw(`UPDATE documents SET workspace_id = '${mapping.newId}' WHERE workspace_id = '${mapping.oldId}'`));
        await db.execute(sql.raw(`UPDATE customers SET workspace_id = '${mapping.newId}' WHERE workspace_id = '${mapping.oldId}'`));
        await db.execute(sql.raw(`UPDATE phone_numbers SET workspace_id = '${mapping.newId}' WHERE workspace_id = '${mapping.oldId}'`));
        await db.execute(sql.raw(`UPDATE conversation_messages SET workspace_id = '${mapping.newId}' WHERE workspace_id = '${mapping.oldId}'`));
        await db.execute(sql.raw(`UPDATE whatsapp_templates SET workspace_id = '${mapping.newId}' WHERE workspace_id = '${mapping.oldId}'`));
    }
    console.log('  - Updated workspace FK references');

    // Agents FK refs
    const agentMappings = allMappings['agents'];
    for (const mapping of agentMappings) {
        await db.execute(sql.raw(`UPDATE integrations SET agent_id = '${mapping.newId}' WHERE agent_id = '${mapping.oldId}'`));
        await db.execute(sql.raw(`UPDATE communications SET agent_id = '${mapping.newId}' WHERE agent_id = '${mapping.oldId}'`));
        await db.execute(sql.raw(`UPDATE phone_numbers SET agent_id = '${mapping.newId}' WHERE agent_id = '${mapping.oldId}'`));
    }
    console.log('  - Updated agent FK references');

    // Integrations FK refs
    const integrationMappings = allMappings['integrations'];
    for (const mapping of integrationMappings) {
        await db.execute(sql.raw(`UPDATE communications SET integration_id = '${mapping.newId}' WHERE integration_id = '${mapping.oldId}'`));
    }
    console.log('  - Updated integration FK references');

    // Communications FK refs
    const communicationMappings = allMappings['communications'];
    for (const mapping of communicationMappings) {
        await db.execute(sql.raw(`UPDATE conversation_messages SET communication_id = '${mapping.newId}' WHERE communication_id = '${mapping.oldId}'`));
    }
    console.log('  - Updated communication FK references');

    console.log('\n✅ All foreign keys updated\n');

    // Step 5: Verification
    console.log('Step 5: Verifying data integrity...');
    for (const table of tables) {
        const count: any = await db.execute(sql.raw(`SELECT COUNT(*) as count FROM ${table.name}`));
        console.log(`  - ${table.name}: ${count[0].count} rows`);
    }

    console.log('\n🎉 UUID migration completed successfully!');
    console.log('\n⚠️  IMPORTANT: Users must re-login as session cookies reference old IDs');
}

// Run migration
migrateToUUID()
    .then(() => {
        console.log('\nMigration finished. Exiting...');
        process.exit(0);
    })
    .catch((error) => {
        console.error('\n❌ Migration failed:', error);
        console.error('\n⚠️  CRITICAL: Restore from backup immediately!');
        process.exit(1);
    });
