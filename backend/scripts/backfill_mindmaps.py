"""
Script to extract concepts from existing sessions and populate mind maps
Run this once to backfill concepts from old chat sessions
"""
import asyncio
import sys
import re
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import get_db
from app.models.session import Message
from app.services.mindmap_service import mindmap_service
from sqlalchemy import select


async def extract_concepts_from_text(text: str, question: str = "") -> list:
    """Extract concepts using regex fallback"""
    # Combine question and response
    full_text = question + " " + text[:1000]
    
    # Extract multi-word capitalized phrases
    multi_word = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', full_text)
    
    # Extract single capitalized words
    single_word = re.findall(r'\b[A-Z][a-z]{3,}\b', full_text)
    
    # Common words to exclude
    exclude = {'The', 'This', 'That', 'These', 'Those', 'What', 'When', 'Where', 'Why', 'How',
              'Which', 'Who', 'Explain', 'Define', 'Describe', 'Tell', 'Give', 'Show', 'True', 'False'}
    
    # Combine and filter
    all_concepts = multi_word + [w for w in single_word if w not in exclude]
    
    # Get unique concepts
    return list(dict.fromkeys(all_concepts))[:8]


async def backfill_mindmaps():
    """Backfill concepts from existing sessions"""
    print("🧠 Starting Mind Map backfill...")
    
    async for db in get_db():
        try:
            # Get all messages
            result = await db.execute(
                select(Message).where(Message.role == "assistant")
            )
            messages = result.scalars().all()
            
            print(f"📝 Found {len(messages)} assistant messages")
            
            # Group by session
            from collections import defaultdict
            session_messages = defaultdict(list)
            
            for msg in messages:
                session_messages[msg.session_id].append(msg)
            
            print(f"💬 Processing {len(session_messages)} sessions...")
            
            # Process each session
            total_concepts = 0
            for session_id, msgs in session_messages.items():
                # Get session details
                from app.models.session import Session
                session_result = await db.execute(
                    select(Session).where(Session.id == session_id)
                )
                session = session_result.scalar_one_or_none()
                
                if not session:
                    continue
                
                # Extract concepts from all messages in session
                all_concepts = []
                for msg in msgs:
                    concepts = await extract_concepts_from_text(msg.content)
                    all_concepts.extend(concepts)
                
                # Get unique concepts
                unique_concepts = list(dict.fromkeys(all_concepts))[:10]
                
                if unique_concepts:
                    print(f"  ✓ Session '{session.title}': {len(unique_concepts)} concepts")
                    
                    # Add to mindmap
                    await mindmap_service.add_concepts(
                        db,
                        session.user_id,
                        session.subject_id,
                        unique_concepts
                    )
                    total_concepts += len(unique_concepts)
            
            print(f"\n✅ Backfill complete! Added {total_concepts} concepts to mind maps")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break


if __name__ == "__main__":
    asyncio.run(backfill_mindmaps())
