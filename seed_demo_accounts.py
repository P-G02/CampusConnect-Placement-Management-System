#!/usr/bin/env python3
"""
CampusConnect - Demo Account Seeder
====================================
Creates the two local demo accounts:
  - demo.student@campusconnect.local  (STUDENT, linked to S1001)
  - demo.company@campusconnect.local  (COMPANY, linked to C10001)

Safe to re-run: will NOT overwrite existing accounts or create duplicates.
Passwords are hashed with Werkzeug's PBKDF2-SHA256.

SECURITY NOTE: Change demo credentials before any public deployment.
"""

import sys
import psycopg2
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "placement_management",
    "user": "postgres",
    "password": "Pass@123",
}

DEMO_ACCOUNTS = [
    {
        "email": "demo.student@campusconnect.local",
        "password": "StudentDemo@123",
        "role": "STUDENT",
        "student_id": "S1001",
        "company_id": None,
    },
    {
        "email": "demo.company@campusconnect.local",
        "password": "CompanyDemo@123",
        "role": "COMPANY",
        "student_id": None,
        "company_id": "C10001",
    },
]


def seed():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cur = conn.cursor()

        for account in DEMO_ACCOUNTS:
            email = account["email"].lower().strip()

            # ── Verify linked profile exists ──────────────────────────────
            if account["role"] == "STUDENT":
                cur.execute(
                    "SELECT student_id FROM student WHERE student_id = %s",
                    (account["student_id"],),
                )
                if not cur.fetchone():
                    print(
                        f"[ERROR] Student {account['student_id']} not found. "
                        "Run 002_seed_placement_data.sql first."
                    )
                    conn.rollback()
                    sys.exit(1)
            elif account["role"] == "COMPANY":
                cur.execute(
                    "SELECT company_id FROM company WHERE company_id = %s",
                    (account["company_id"],),
                )
                if not cur.fetchone():
                    print(
                        f"[ERROR] Company {account['company_id']} not found. "
                        "Run 002_seed_placement_data.sql first."
                    )
                    conn.rollback()
                    sys.exit(1)

            # ── Skip if account already exists ────────────────────────────
            cur.execute("SELECT user_id, email FROM users WHERE email = %s", (email,))
            existing = cur.fetchone()
            if existing:
                print(
                    f"[SKIP]  Account already exists: {email} (user_id={existing[0]})"
                )
                continue

            # ── Hash password and insert ──────────────────────────────────
            pwd_hash = generate_password_hash(account["password"])
            cur.execute(
                """
                INSERT INTO users
                    (email, password_hash, role, student_id, company_id, is_active)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                RETURNING user_id
                """,
                (
                    email,
                    pwd_hash,
                    account["role"],
                    account["student_id"],
                    account["company_id"],
                ),
            )
            new_id = cur.fetchone()[0]
            print(f"[OK]    Created {account['role']} account: {email} (user_id={new_id})")

        conn.commit()
        print("\n[DONE] Seed complete. Demo accounts are ready.\n")
        print("  Student : demo.student@campusconnect.local / StudentDemo@123")
        print("  Company : demo.company@campusconnect.local / CompanyDemo@123")
        print("\n  ⚠  Change these credentials before any public deployment!\n")

    except psycopg2.Error as e:
        print(f"[DB ERROR] {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    seed()
