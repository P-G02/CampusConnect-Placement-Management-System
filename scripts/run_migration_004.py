import sys
sys.path.insert(0, '.')
import psycopg2
from app import DB_CONFIG

def run():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        # Check if PK already exists
        cur.execute("SELECT 1 FROM pg_constraint WHERE conname = 'student_skill_pkey'")
        if cur.fetchone():
            print("student_skill_pkey already exists.")
            return

        with open('migrations/004_dedup_and_pk_student_skill.sql', 'r', encoding='utf-8') as f:
            sql = f.read()

        cur.execute(sql)
        conn.commit()
        print("Migration 004 applied successfully.")
    except Exception as e:
        conn.rollback()
        print("Migration 004 failed:", e)
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    run()
