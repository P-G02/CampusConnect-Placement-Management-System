-- Update role check constraint to include ADMINISTRATOR
-- File: migrations/003_update_role_constraint.sql
BEGIN;

-- Drop existing role check constraint
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;

-- Add new constraint allowing ADMINISTRATOR
ALTER TABLE users
    ADD CONSTRAINT users_role_check CHECK (role IN ('STUDENT', 'COMPANY', 'ADMINISTRATOR'));

COMMIT;
