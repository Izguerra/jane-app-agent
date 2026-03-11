-- Rename table
ALTER TABLE agent_settings RENAME TO agents;

-- Add new columns to agents table
ALTER TABLE agents ADD COLUMN name VARCHAR(100) NOT NULL DEFAULT 'My Agent';
ALTER TABLE agents ADD COLUMN is_orchestrator BOOLEAN DEFAULT FALSE;
ALTER TABLE agents ADD COLUMN description TEXT;

-- Add agent_id to integrations table
ALTER TABLE integrations ADD COLUMN agent_id VARCHAR(20) REFERENCES agents(id);

-- Add agent_id to communications table
ALTER TABLE communications ADD COLUMN agent_id VARCHAR(20) REFERENCES agents(id);
