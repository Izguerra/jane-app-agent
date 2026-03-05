-- Fix missing column rename in communication_logs table
-- The initial migration missed renaming clinic_id to workspace_id in this table

BEGIN;

-- Check if the old column exists
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'communication_logs' AND column_name = 'clinic_id'
  ) THEN
    -- Rename the column
    ALTER TABLE communication_logs RENAME COLUMN clinic_id TO workspace_id;
    RAISE NOTICE 'Renamed communication_logs.clinic_id to workspace_id';
  ELSE
    RAISE NOTICE 'Column communication_logs.clinic_id does not exist, skipping rename';
  END IF;
END $$;

COMMIT;
