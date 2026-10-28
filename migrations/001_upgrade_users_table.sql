-- =============================================================
-- CampusConnect: Additive users table migration (v2)
-- Safe to re-run. Uses one transaction block.
-- Does NOT drop, truncate, or recreate existing tables.
-- =============================================================

BEGIN;

-- ── Step 1: Remove old demo accounts (lowercase roles, no FK links)
-- These will be re-seeded properly by seed_demo_accounts.py
DELETE FROM users
WHERE email IN (
    'student@campusconnect.demo',
    'company@campusconnect.demo',
    'demo.student@campusconnect.local',
    'demo.company@campusconnect.local'
);

-- ── Step 2: Drop old role check constraint (lowercase format)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'users'
          AND constraint_name = 'users_role_check'
          AND table_schema = 'public'
    ) THEN
        ALTER TABLE users DROP CONSTRAINT users_role_check;
    END IF;
END $$;

-- ── Step 3: Drop other old constraints if they exist
DO $$
DECLARE c TEXT;
BEGIN
    FOR c IN SELECT constraint_name FROM information_schema.table_constraints
             WHERE table_name = 'users' AND table_schema = 'public'
               AND constraint_name IN (
                   'users_not_both_student_company',
                   'users_student_has_student_id',
                   'users_company_has_company_id'
               )
    LOOP
        EXECUTE 'ALTER TABLE users DROP CONSTRAINT ' || quote_ident(c);
    END LOOP;
END $$;

-- ── Step 4: Uppercase any leftover roles
UPDATE users SET role = UPPER(role) WHERE role IN ('student', 'company');

-- ── Step 5: Add student_id FK column if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'student_id' AND table_schema = 'public'
    ) THEN
        ALTER TABLE users
            ADD COLUMN student_id VARCHAR(6) REFERENCES student(student_id) ON DELETE SET NULL;
    END IF;
END $$;

-- ── Step 6: Add company_id FK column if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'company_id' AND table_schema = 'public'
    ) THEN
        ALTER TABLE users
            ADD COLUMN company_id VARCHAR(6) REFERENCES company(company_id) ON DELETE SET NULL;
    END IF;
END $$;

-- ── Step 7: Add is_active column if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'is_active' AND table_schema = 'public'
    ) THEN
        ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
    END IF;
END $$;

-- ── Step 8: Add updated_at column if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'updated_at' AND table_schema = 'public'
    ) THEN
        ALTER TABLE users ADD COLUMN updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- ── Step 9: Add new constraints (UPPERCASE roles, mutual-exclusivity)
ALTER TABLE users
    ADD CONSTRAINT users_role_check
        CHECK (role IN ('STUDENT', 'COMPANY'));

ALTER TABLE users
    ADD CONSTRAINT users_not_both_student_company
        CHECK (NOT (student_id IS NOT NULL AND company_id IS NOT NULL));

ALTER TABLE users
    ADD CONSTRAINT users_student_has_student_id
        CHECK (role != 'STUDENT' OR student_id IS NOT NULL);

ALTER TABLE users
    ADD CONSTRAINT users_company_has_company_id
        CHECK (role != 'COMPANY' OR company_id IS NOT NULL);

-- ── Step 10: Indexes
CREATE INDEX IF NOT EXISTS idx_users_role       ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_student_id ON users(student_id);
CREATE INDEX IF NOT EXISTS idx_users_company_id ON users(company_id);

COMMIT;
