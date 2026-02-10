"""
Clear Old Teacher Data and Add New Tables

Run this to reset Teacher Mode for the new conversational system
"""

import sqlite3

conn = sqlite3.connect('e:/Github Projects/SmaranAI/backend/smaranai.db')
cursor = conn.cursor()

print("[RESET] Clearing old Teacher Mode data...")

# Delete all existing data (CASCADE will handle related tables)
try:
    cursor.execute("DELETE FROM teacher_memory_cards")
    cursor.execute("DELETE FROM teacher_check_attempts")
    cursor.execute("DELETE FROM teacher_lesson_states")
    cursor.execute("DELETE FROM teacher_modules")
    cursor.execute("DELETE FROM teacher_roadmaps")
    print("[OK] Cleared old data")
except Exception as e:
    print(f"[INFO] Some tables may not exist yet: {e}")

# Create new tables
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_turns (
            id TEXT PRIMARY KEY,
            module_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            turn_index INTEGER NOT NULL,
            speaker TEXT NOT NULL,
            message TEXT NOT NULL,
            concept_tag TEXT,
            pdf_references TEXT,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (module_id) REFERENCES teacher_modules(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("[OK] Created conversation_turns table")
except Exception as e:
    print(f"[SKIP] conversation_turns: {e}")

try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS concept_mastery (
            id TEXT PRIMARY KEY,
            module_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            concept TEXT NOT NULL,
            mastery_score REAL NOT NULL DEFAULT 0.0,
            attempts INTEGER NOT NULL DEFAULT 0,
            last_assessed TIMESTAMP NOT NULL,
            FOREIGN KEY (module_id) REFERENCES teacher_modules(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(module_id, user_id, concept)
        )
    """)
    print("[OK] Created concept_mastery table")
except Exception as e:
    print(f"[SKIP] concept_mastery: {e}")

conn.commit()
conn.close()

print("\n[SUCCESS] Migration complete! Teacher Mode has been reset.")
print("[READY] New conversational system ready to use.")
