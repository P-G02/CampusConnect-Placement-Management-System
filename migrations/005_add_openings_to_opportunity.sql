-- 005_add_openings_to_opportunity.sql
-- Add openings column to opportunity table if not exists
-- Safe, additive migration preserving existing data and constraints.

BEGIN;

ALTER TABLE opportunity 
ADD COLUMN IF NOT EXISTS openings INTEGER DEFAULT 5;

-- Add check constraint for positive openings if not already present
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_constraint 
        WHERE conname = 'opportunity_openings_check'
    ) THEN
        ALTER TABLE opportunity 
        ADD CONSTRAINT opportunity_openings_check CHECK (openings > 0);
    END IF;
END $$;

COMMIT;
