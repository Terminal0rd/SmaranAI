"""
Fix Teacher Tables - Drop and Recreate
"""
import asyncio
import sqlite3

# Path to your database
DB_PATH = "smaranai.db"

def drop_teacher_tables():
    """Drop all teacher tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = [
        'teacher_memory_cards',
        'teacher_check_attempts',
        'teacher_lesson_states',
        'teacher_modules',
        'teacher_roadmaps'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"✅ Dropped {table}")
        except Exception as e:
            print(f"⚠️  Error dropping {table}: {e}")
    
    conn.commit()
    conn.close()
    print("\n✅ All teacher tables dropped")

async def create_teacher_tables():
    """Create teacher tables with correct schema"""
    from app.database import async_engine
    from sqlalchemy import text
    
    async with async_engine.begin() as conn:
        # Create tables one by one with explicit SQL to ensure correct schema
        
        # 1. TeacherRoadmap
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS teacher_roadmaps (
                id VARCHAR NOT NULL PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                subject VARCHAR(255) NOT NULL,
                goal VARCHAR(500),
                total_modules INTEGER NOT NULL DEFAULT 0,
                completed_modules INTEGER NOT NULL DEFAULT 0,
                overall_progress FLOAT NOT NULL DEFAULT 0.0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_teacher_roadmaps_user_id ON teacher_roadmaps(user_id)"))
        print("✅ Created teacher_roadmaps")
        
        # 2. TeacherModule
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS teacher_modules (
                id VARCHAR NOT NULL PRIMARY KEY,
                roadmap_id VARCHAR NOT NULL,
                module_index INTEGER NOT NULL,
                title VARCHAR(500) NOT NULL,
                level VARCHAR(20) NOT NULL DEFAULT 'beginner',
                objectives TEXT NOT NULL,
                topics TEXT NOT NULL,
                prerequisites TEXT,
                estimated_minutes INTEGER NOT NULL DEFAULT 30,
                status VARCHAR(20) NOT NULL DEFAULT 'locked',
                mastery_score FLOAT NOT NULL DEFAULT 0.0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(roadmap_id) REFERENCES teacher_roadmaps(id) ON DELETE CASCADE
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_teacher_modules_roadmap_id ON teacher_modules(roadmap_id)"))
        print("✅ Created teacher_modules")
        
        # 3. TeacherLessonState
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS teacher_lesson_states (
                id VARCHAR NOT NULL PRIMARY KEY,
                module_id VARCHAR NOT NULL UNIQUE,
                current_phase VARCHAR(20) NOT NULL DEFAULT 'teach',
                check_attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 2,
                teach_content TEXT,
                reteach_content TEXT,
                last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(module_id) REFERENCES teacher_modules(id) ON DELETE CASCADE
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_teacher_lesson_states_module_id ON teacher_lesson_states(module_id)"))
        print("✅ Created teacher_lesson_states")
        
        # 4. TeacherCheckAttempt
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS teacher_check_attempts (
                id VARCHAR NOT NULL PRIMARY KEY,
                module_id VARCHAR NOT NULL,
                user_id VARCHAR NOT NULL,
                questions TEXT NOT NULL,
                answers TEXT NOT NULL,
                score FLOAT NOT NULL,
                passed INTEGER NOT NULL DEFAULT 0,
                weak_topics TEXT,
                grading_details TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(module_id) REFERENCES teacher_modules(id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_teacher_check_attempts_module_id ON teacher_check_attempts(module_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_teacher_check_attempts_user_id ON teacher_check_attempts(user_id)"))
        print("✅ Created teacher_check_attempts")
        
        # 5. TeacherMemoryCard
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS teacher_memory_cards (
                id VARCHAR NOT NULL PRIMARY KEY,
                module_id VARCHAR NOT NULL,
                card_type VARCHAR(20) NOT NULL,
                front_text TEXT NOT NULL,
                back_text TEXT NOT NULL,
                display_order INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(module_id) REFERENCES teacher_modules(id) ON DELETE CASCADE
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_teacher_memory_cards_module_id ON teacher_memory_cards(module_id)"))
        print("✅ Created teacher_memory_cards")
    
    print("\n✅ All teacher tables created successfully!")

if __name__ == "__main__":
    print("Step 1: Dropping old tables...")
    drop_teacher_tables()
    
    print("\nStep 2: Creating new tables with correct schema...")
    asyncio.run(create_teacher_tables())
    
    print("\n🎉 Teacher mode database is ready!")
