-- 002_demo_accounts.sql
-- Add demo accounts for Student, Company, Administrator.
-- Uses ON CONFLICT (email) DO UPDATE to avoid duplicate inserts.

-- Student demo account (Shah Rukh Khan)
INSERT INTO users (email, password_hash, role, is_active, student_id)
VALUES (
    'srk_0211@gmail.com',
    'scrypt:32768:8:1$CJw9byyeHA4JvLqQ$fdf0bba5c5582c78f67160296add68936e62eeab51765fbc76111fe18a6f822d9e3850b1facc1fb45708f396debd82f8c53afe51e56f639f7acc923d86060b81',
    'STUDENT',
    true,
    'S1001'
)
ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    role = EXCLUDED.role,
    is_active = EXCLUDED.is_active,
    student_id = EXCLUDED.student_id;

-- Company demo account (TCS)
INSERT INTO users (email, password_hash, role, is_active, company_id)
VALUES (
    'tcs@careers.example.com',
    'scrypt:32768:8:1$GuvcNMq10YmT8s2s$338437ebc2b225fd313ee847c23a85f3493d164de4a64be250208e38f43af8392ff795247426dc7d75c4aa7743d36da898bf1e75d2b098d39bbd6029bbbe9367',
    'COMPANY',
    true,
    'C10001'
)
ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    role = EXCLUDED.role,
    is_active = EXCLUDED.is_active,
    company_id = EXCLUDED.company_id;

-- Administrator demo account
INSERT INTO users (email, password_hash, role, is_active)
VALUES (
    'admin@campusconnect.local',
    'scrypt:32768:8:1$5Cs8Jl0t14lQ4u1Z$022cfb491c730707ceecc0e4d4515513c2bab02c5ca3fecf64471e7676f6a441ef8aa65d62bdad337e4fcc0ef54769938613fe84a3953c100d160adf3928fb7d',
    'ADMINISTRATOR',
    true
)
ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    role = EXCLUDED.role,
    is_active = EXCLUDED.is_active;

-- End of migration
