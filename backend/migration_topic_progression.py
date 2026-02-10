"""
Add topic progression columns to teacher_lesson_states

Enables topic-by-topic teaching instead of all-at-once dump.
"""

import sqlite3

conn = sqlite3.connect('e:/Github Projects/SmaranAI/backend/smaranai.db')
cursor = conn.cursor()

try:
    # Add current_topic_index column
    cursor.execute("""
        ALTER TABLE teacher_lesson_states 
        ADD COLUMN current_topic_index INTEGER DEFAULT 0
    """)
    print("[OK] Added current_topic_index column")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("[SKIP] current_topic_index already exists")
    else:
        raise

try:
    # Add topics_completed column
    cursor.execute("""
        ALTER TABLE teacher_lesson_states 
        ADD COLUMN topics_completed TEXT
    """)
    print("[OK] Added topics_completed column")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("[SKIP] topics_completed already exists")
    else:
        raise

conn.commit()
conn.close()
print("\n[SUCCESS] Migration completed")
