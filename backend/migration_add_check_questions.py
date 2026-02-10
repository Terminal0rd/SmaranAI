"""
Add check_questions column to teacher_lesson_states

This migration adds the check_questions JSON column to cache generated questions
and prevent the regeneration bug that causes grading mismatches.

Run this AFTER restarting the backend.
"""

import sqlite3

# Connect to database
conn = sqlite3.connect('e:/Github Projects/SmaranAI/backend/smaranai.db')
cursor = conn.cursor()

try:
    # Add check_questions column
    cursor.execute("""
        ALTER TABLE teacher_lesson_states 
        ADD COLUMN check_questions TEXT
    """)
    
    conn.commit()
    print("[OK] Migration successful: Added check_questions column")
    
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("[SKIP] Column already exists, skipping migration")
    else:
        print(f"[ERROR] {e}")
        raise
finally:
    conn.close()
