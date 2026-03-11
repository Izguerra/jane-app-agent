-- Migration: Add phone_numbers table for Twilio provisioning
-- Created: 2025-12-06

CREATE TABLE IF NOT EXISTS phone_numbers (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    friendly_name VARCHAR(255),
    country_code VARCHAR(2),
    
    -- Capabilities
    voice_enabled BOOLEAN DEFAULT FALSE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    whatsapp_enabled BOOLEAN DEFAULT FALSE,
    
    -- Configuration
    voice_url TEXT,
    whatsapp_webhook_url TEXT,
    
    -- Twilio details
    twilio_sid VARCHAR(255) UNIQUE,
    
    -- Billing
    monthly_cost DECIMAL(10,2),
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_phone_numbers_workspace ON phone_numbers(workspace_id);
CREATE INDEX IF NOT EXISTS idx_phone_numbers_phone ON phone_numbers(phone_number);
CREATE INDEX IF NOT EXISTS idx_phone_numbers_twilio_sid ON phone_numbers(twilio_sid);

-- Add WhatsApp template table
CREATE TABLE IF NOT EXISTS whatsapp_templates (
    id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    category VARCHAR(50),  -- MARKETING, UTILITY, AUTHENTICATION
    status VARCHAR(50),    -- PENDING, APPROVED, REJECTED
    template_id VARCHAR(255),  -- Meta template ID
    components JSONB,      -- Template structure
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(workspace_id, name, language)
);

CREATE INDEX IF NOT EXISTS idx_whatsapp_templates_workspace ON whatsapp_templates(workspace_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_templates_status ON whatsapp_templates(status);

COMMENT ON TABLE phone_numbers IS 'Stores Twilio phone numbers provisioned for workspaces';
COMMENT ON TABLE whatsapp_templates IS 'Stores WhatsApp message templates for Meta WhatsApp API';
