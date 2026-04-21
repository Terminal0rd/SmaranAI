"""
Migration script: Improve generic session titles
Replaces generic 'Subject Session' titles with first user message content
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.session import Session, Message


async def improve_session_titles():
    """Update sessions with generic titles to use first user message"""
    async with AsyncSessionLocal() as db:
        # Find sessions with generic 'X Session' titles
        result = await db.execute(select(Session))
        all_sessions = result.scalars().all()
        
        generic_sessions = [s for s in all_sessions if s.title and s.title.endswith(' Session')]
        
        if not generic_sessions:
            print("No generic session titles found. All good!")
            return
        
        print(f"Found {len(generic_sessions)} sessions with generic titles. Improving...")
        
        fixed = 0
        for session in generic_sessions:
            # Get first user message
            msg_result = await db.execute(
                select(Message)
                .where(
                    Message.session_id == session.id,
                    Message.role == "user"
                )
                .order_by(Message.created_at)
                .limit(1)
            )
            first_message = msg_result.scalar_one_or_none()
            
            if first_message:
                title = first_message.content[:60].strip()
                if len(first_message.content) > 60:
                    title += '...'
                old_title = session.title
                session.title = title
                fixed += 1
                print(f"  OK '{old_title}' -> '{title}'")
            else:
                print(f"  -- '{session.title}' (no messages, keeping as-is)")
        
        await db.commit()
        print(f"\nDone! Improved {fixed} session titles.")


if __name__ == "__main__":
    asyncio.run(improve_session_titles())
