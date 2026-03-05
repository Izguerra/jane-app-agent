-- Migration: 005_outbound_calling.sql
-- Description: Add appointments, deals, and enhanced communications tracking for outbound calling

-- ============================================================================
-- APPOINTMENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS appointments (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    appointment_date TIMESTAMP NOT NULL,
    duration_minutes INTEGER DEFAULT 60,
    status TEXT NOT NULL DEFAULT 'scheduled',  -- 'scheduled', 'confirmed', 'completed', 'cancelled', 'no_show', 'pending_reschedule'
    location TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_appointments_workspace ON appointments(workspace_id);
CREATE INDEX IF NOT EXISTS idx_appointments_customer ON appointments(customer_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);

-- ============================================================================
-- DEALS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS deals (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    customer_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    value DECIMAL(10, 2),
    stage TEXT NOT NULL DEFAULT 'lead',  -- 'lead', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost'
    probability INTEGER DEFAULT 50,  -- 0-100
    expected_close_date DATE,
    source TEXT,  -- 'website', 'referral', 'cold_call', etc.
    assigned_to TEXT,  -- User ID
    notes TEXT,
    last_contact_date TIMESTAMP,
    next_follow_up_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_deals_workspace ON deals(workspace_id);
CREATE INDEX IF NOT EXISTS idx_deals_customer ON deals(customer_id);
CREATE INDEX IF NOT EXISTS idx_deals_stage ON deals(stage);
CREATE INDEX IF NOT EXISTS idx_deals_follow_up ON deals(next_follow_up_date);

-- ============================================================================
-- APPOINTMENT REMINDERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS appointment_reminders (
    id TEXT PRIMARY KEY,
    appointment_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    reminder_type TEXT NOT NULL,  -- '24h_before', '1h_before', 'custom'
    scheduled_time TIMESTAMP NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'sent', 'failed', 'cancelled'
    communication_id TEXT,  -- Link to communication record
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
    FOREIGN KEY (communication_id) REFERENCES communications(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_reminders_scheduled ON appointment_reminders(scheduled_time, status);
CREATE INDEX IF NOT EXISTS idx_reminders_appointment ON appointment_reminders(appointment_id);
CREATE INDEX IF NOT EXISTS idx_reminders_workspace ON appointment_reminders(workspace_id);

-- ============================================================================
-- ENHANCE COMMUNICATIONS TABLE
-- ============================================================================

-- Add outbound call tracking fields
ALTER TABLE communications ADD COLUMN IF NOT EXISTS call_intent TEXT;
ALTER TABLE communications ADD COLUMN IF NOT EXISTS call_outcome TEXT;
ALTER TABLE communications ADD COLUMN IF NOT EXISTS call_context JSONB;
ALTER TABLE communications ADD COLUMN IF NOT EXISTS customer_id TEXT;
ALTER TABLE communications ADD COLUMN IF NOT EXISTS twilio_call_sid TEXT;
ALTER TABLE communications ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;
ALTER TABLE communications ADD COLUMN IF NOT EXISTS parent_communication_id TEXT;
ALTER TABLE communications ADD COLUMN IF NOT EXISTS campaign_id TEXT;
ALTER TABLE communications ADD COLUMN IF NOT EXISTS campaign_name TEXT;

-- Add foreign key constraints (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'communications_customer_id_fkey'
    ) THEN
        ALTER TABLE communications ADD CONSTRAINT communications_customer_id_fkey 
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'communications_parent_communication_id_fkey'
    ) THEN
        ALTER TABLE communications ADD CONSTRAINT communications_parent_communication_id_fkey 
        FOREIGN KEY (parent_communication_id) REFERENCES communications(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add indexes for new fields
CREATE INDEX IF NOT EXISTS idx_communications_customer ON communications(customer_id);
CREATE INDEX IF NOT EXISTS idx_communications_intent ON communications(call_intent);
CREATE INDEX IF NOT EXISTS idx_communications_outcome ON communications(call_outcome);
CREATE INDEX IF NOT EXISTS idx_communications_twilio_sid ON communications(twilio_call_sid);
CREATE INDEX IF NOT EXISTS idx_communications_campaign ON communications(campaign_id);

-- ============================================================================
-- ENHANCE CUSTOMERS TABLE
-- ============================================================================

-- Add lead tracking fields
ALTER TABLE customers ADD COLUMN IF NOT EXISTS last_contact_date TIMESTAMP;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS next_follow_up_date TIMESTAMP;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS lead_source TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS tags TEXT[];

CREATE INDEX IF NOT EXISTS idx_customers_follow_up ON customers(next_follow_up_date);
CREATE INDEX IF NOT EXISTS idx_customers_lead_source ON customers(lead_source);

-- ============================================================================
-- ENHANCE TEAMS TABLE
-- ============================================================================

-- Add reminder settings
ALTER TABLE teams ADD COLUMN IF NOT EXISTS reminder_settings JSONB DEFAULT '{
    "enabled": true,
    "reminder_times": ["24h_before", "1h_before"],
    "max_retry_attempts": 2,
    "retry_interval_minutes": 30
}'::jsonb;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE appointments IS 'Customer appointments for scheduling and reminders';
COMMENT ON TABLE deals IS 'Sales opportunities and pipeline management';
COMMENT ON TABLE appointment_reminders IS 'Scheduled reminders for appointments';
COMMENT ON COLUMN communications.call_intent IS 'Purpose of the call: appointment_reminder, deal_follow_up, lead_qualification, customer_service';
COMMENT ON COLUMN communications.call_outcome IS 'Result of the call: confirmed, rescheduled, cancelled, no_answer, voicemail, qualified, not_interested';
COMMENT ON COLUMN communications.call_context IS 'JSON context data: appointment_id, deal_id, customer details, etc.';
COMMENT ON COLUMN communications.campaign_id IS 'Link to campaign for tracking campaign performance';
COMMENT ON COLUMN communications.campaign_name IS 'Campaign name for quick reference without join';
