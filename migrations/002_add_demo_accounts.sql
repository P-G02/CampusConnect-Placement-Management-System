-- Additive migration to insert demo accounts (idempotent)
-- File: migrations/002_add_demo_accounts.sql
BEGIN;

-- Insert demo student user (linked to existing student S1001)
INSERT INTO users (email, password_hash, role, is_active, student_id)
VALUES (
    'srk_0211@gmail.com',
    'scrypt:32768:8:1$FZveT7MnmRYx5bbd$663884ad48dee68724479a51cb1c1687be5989eb3411bd58e21312f15d46a6c91b6933b9fedb715f0a61c6aa5efea05c6fe424ab5c9b10a2e250b3081892c131',
    'STUDENT',
    TRUE,
    'S1001'
) ON CONFLICT (email) DO NOTHING;

-- Insert demo company user (linked to existing company C10001)
INSERT INTO users (email, password_hash, role, is_active, company_id)
VALUES (
    'tcs@careers.example.com',
    'scrypt:32768:8:1$DbgIM4bAqEGaaerS$bd74828886f83e8f1804f048597651015fdd49843a728f86c5a2655b33d78b57c9188a332960e8a68fff350de5e27c1ac5e1ad36f18c6091aaef52ff2029b6bd',
    'COMPANY',
    TRUE,
    'C10001'
) ON CONFLICT (email) DO NOTHING;

-- Insert administrator account (no FK)
INSERT INTO users (email, password_hash, role, is_active)
VALUES (
    'admin@campusconnect.local',
    'scrypt:32768:8:1$fU84KrTUe6XfKWXQ$945cbaac49c12852956bed0f9847365d4604cdd8f9621578df9169623f0264a208a5f534643d55288636ce3a0ddd6e94ec378859b9bdaf7e7eea375872e2f35b',
    'ADMINISTRATOR',
    TRUE
) ON CONFLICT (email) DO NOTHING;

COMMIT;
