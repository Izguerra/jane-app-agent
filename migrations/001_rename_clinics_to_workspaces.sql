-- SupaAgent Database Migration: clinics → workspaces
-- This migration renames the clinics table to workspaces to better reflect the SaaS nature

BEGIN;

-- Step 1: Rename the main table
ALTER TABLE clinics RENAME TO workspaces;

-- Step 2: Rename foreign key columns in related tables
ALTER TABLE agent_settings RENAME COLUMN clinic_id TO workspace_id;
ALTER TABLE communications RENAME COLUMN clinic_id TO workspace_id;
ALTER TABLE integrations RENAME COLUMN clinic_id TO workspace_id;

-- Step 3: Add new usage tracking columns to workspaces
ALTER TABLE workspaces 
  ADD COLUMN IF NOT EXISTS conversations_this_month INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS voice_minutes_this_month INTEGER DEFAULT 0;

-- Step 4: Rename indexes (if they exist)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'clinics_pkey') THEN
    ALTER INDEX clinics_pkey RENAME TO workspaces_pkey;
  END IF;
  
  IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'clinics_team_id_idx') THEN
    ALTER INDEX clinics_team_id_idx RENAME TO workspaces_team_id_idx;
  END IF;
END $$;

-- Step 5: Update sequence name
ALTER SEQUENCE IF EXISTS clinics_id_seq RENAME TO workspaces_id_seq;

-- Step 6: Verify the migration
DO $$
BEGIN
  -- Check that workspaces table exists
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workspaces') THEN
    RAISE EXCEPTION 'Migration failed: workspaces table does not exist';
  END IF;
  
  -- Check that clinics table no longer exists
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'clinics') THEN
    RAISE EXCEPTION 'Migration failed: clinics table still exists';
  END IF;
  
  -- Check that new columns exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'workspaces' AND column_name = 'conversations_this_month'
  ) THEN
    RAISE EXCEPTION 'Migration failed: conversations_this_month column missing';
  END IF;
  
  RAISE NOTICE 'Migration completed successfully!';
END $$;

COMMIT;

-- Rollback script (run this if you need to undo the migration)
-- BEGIN;
-- ALTER TABLE workspaces RENAME TO clinics;
-- ALTER TABLE agent_settings RENAME COLUMN workspace_id TO clinic_id;
-- ALTER TABLE communications RENAME COLUMN workspace_id TO clinic_id;
-- ALTER TABLE integrations RENAME COLUMN workspace_id TO clinic_id;
-- ALTER TABLE workspaces DROP COLUMN IF EXISTS conversations_this_month;
-- ALTER TABLE workspaces DROP COLUMN IF EXISTS voice_minutes_this_month;
-- ALTER INDEX workspaces_pkey RENAME TO clinics_pkey;
-- ALTER SEQUENCE workspaces_id_seq RENAME TO clinics_id_seq;
-- COMMIT;
