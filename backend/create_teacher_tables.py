"""
Direct SQL Migration for Teacher Mode Tables
Run this with: python create_teacher_tables.py
"""
import asyncio
from sqlalchemy import text
from app.database import async_engine, Base
from app.models.teacher import (
    TeacherRoadmap, TeacherModule, TeacherLessonState,
    TeacherCheckAttempt, TeacherMemoryCard
)

async def create_tables():
    """Create all teacher mode tables"""
    async with async_engine.begin() as conn:
        # Create tables using SQLAlchemy
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Teacher mode tables created successfully!")
    print("\nCreated tables:")
    print("- teacher_roadmaps")
    print("- teacher_modules")
    print("- teacher_lesson_states")
    print("- teacher_check_attempts")
    print("- teacher_memory_cards")

if __name__ == "__main__":
    print("Creating Teacher Mode tables...")
    asyncio.run(create_tables())
