-- Migration: Create knowledge base sources table
-- Description: Table for tracking workspace-specific knowledge base data sources

-- Knowledge Base Sources Table
CREATE TABLE IF NOT EXISTS knowledge_base_sources (
    id VARCHAR(20) PRIMARY KEY,
    workspace_id VARCHAR(20) NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL, -- 'website_crawler', 'file_upload', 'salesforce', 'zendesk', 'slack', 'google_drive', 'notion'
    name VARCHAR(255) NOT NULL,
    config JSONB NOT NULL, -- Source-specific configuration (URL, file path, API credentials, etc.)
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'syncing', 'active', 'error', 'paused'
    last_synced_at TIMESTAMP,
    document_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add source tracking to documents table
ALTER TABLE documents ADD COLUMN IF NOT EXISTS source_id VARCHAR(20) REFERENCES knowledge_base_sources(id) ON DELETE SET NULL;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) DEFAULT 'active';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_kb_sources_workspace ON knowledge_base_sources(workspace_id);
CREATE INDEX IF NOT EXISTS idx_kb_sources_type ON knowledge_base_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_kb_sources_status ON knowledge_base_sources(status);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source_id);
CREATE INDEX IF NOT EXISTS idx_documents_sync_status ON documents(sync_status);
