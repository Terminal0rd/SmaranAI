"""
Database cleanup script for Teacher Mode removal
Run this to drop all teacher-related tables
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('smaranai.db')
cursor = conn.cursor()

print("[CLEANUP] Dropping Teacher Mode tables...")

# Tables to drop (in order to avoid foreign key constraints)
tables_to_drop = [
    "teacher_memory_cards",
    "teacher_check_attempts",
    "conversation_turns",
    "concept_mastery",
    "teacher_lesson_states",
    "teacher_modules",
    "teacher_roadmaps"
]

for table in tables_to_drop:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"✓ Dropped table: {table}")
    except Exception as e:
        print(f"⚠ Warning: Could not drop {table}: {e}")

conn.commit()
conn.close()

print("\n[SUCCESS] Teacher Mode database cleanup complete!")
print("All teacher tables have been removed.")
