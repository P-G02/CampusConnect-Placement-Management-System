#!/usr/bin/env python3
import os, sys
import psycopg2

# DB config (must match app.py)
DB_CONFIG = {
    "host": os.getenv('DB_HOST', 'localhost'),
    "port": int(os.getenv('DB_PORT', 5432)),
    "dbname": os.getenv('DB_NAME', 'placement_management'),
    "user": os.getenv('DB_USER', 'postgres'),
    "password": os.getenv('DB_PASS', 'Pass@123'),
}

SQL_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'migrations', '002_add_demo_accounts.sql'))

if not os.path.exists(SQL_FILE):
    print('SQL file not found:', SQL_FILE)
    sys.exit(1)

with open(SQL_FILE, 'r', encoding='utf-8') as f:
    sql_content = f.read()

conn = None
try:
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(sql_content)
    print('Migration executed successfully.')
except Exception as e:
    print('Error executing migration:', e)
finally:
    if conn:
        conn.close()
