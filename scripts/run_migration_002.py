#!/usr/bin/env python3
"""Run the 002_demo_accounts.sql migration using psycopg2.
This script reads the SQL file and executes its statements safely.
It is idempotent because the INSERTs use ON CONFLICT to update existing rows.
"""
import os
import psycopg2
import psycopg2.extras

# DB config (must match app.py)
DB_CONFIG = {
    "host": os.getenv('DB_HOST', 'localhost'),
    "port": int(os.getenv('DB_PORT', 5432)),
    "dbname": os.getenv('DB_NAME', 'placement_management'),
    "user": os.getenv('DB_USER', 'postgres'),
    "password": os.getenv('DB_PASS', 'Pass@123'),
}

SQL_PATH = os.path.abspath('migrations/002_demo_accounts.sql')

if not os.path.exists(SQL_PATH):
    raise FileNotFoundError(f"Migration file not found: {SQL_PATH}")

with open(SQL_PATH, 'r', encoding='utf-8') as f:
    sql = f.read()

conn = None
try:
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(sql)
    print('Migration 002_demo_accounts.sql applied successfully.')
except Exception as e:
    print('Error applying migration:', e)
finally:
    if conn:
        conn.close()
