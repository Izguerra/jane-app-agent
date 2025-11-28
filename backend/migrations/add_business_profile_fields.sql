-- Add new columns to clinics table
ALTER TABLE clinics ADD COLUMN IF NOT EXISTS address VARCHAR(255);
ALTER TABLE clinics ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE clinics ADD COLUMN IF NOT EXISTS website VARCHAR(255);
ALTER TABLE clinics ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE clinics ADD COLUMN IF NOT EXISTS business_hours TEXT;
ALTER TABLE clinics ADD COLUMN IF NOT EXISTS services TEXT;
ALTER TABLE clinics ADD COLUMN IF NOT EXISTS faq TEXT;
ALTER TABLE clinics ADD COLUMN IF NOT EXISTS reference_urls TEXT;

-- Create knowledge_documents table
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id SERIAL PRIMARY KEY,
    clinic_id INTEGER NOT NULL REFERENCES clinics(id),
    filename VARCHAR(255) NOT NULL,
    content TEXT,
    file_type VARCHAR(50),
    file_path VARCHAR(500),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
