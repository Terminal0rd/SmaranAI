    async def generate_topic_content(
        self,
        module_id: str,
        topic_index: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Generate detailed teaching content for a SINGLE topic
        More focused and in-depth than teaching all topics at once
        """
        # Get module
        result = await db.execute(
            select(TeacherModule).where(TeacherModule.id == module_id)
        )
        module = result.scalar_one()
        
        if topic_index >= len(module.topics):
            raise ValueError(f"Topic index {topic_index} out of range")
        
        topic = module.topics[topic_index]
        
        # Build focused prompt for single topic
        objectives_str = "\n".join(f"- {obj}" for obj in module.objectives)
        
        prompt = f"""You are teaching the topic: "{topic}" from the module "{module.title}"

Module Objectives:
{objectives_str}

Your job: Explain "{topic}" in depth like a professor would in a lecture.

Structure your explanation as JSON:

{{
  "topic_name": "{topic}",
  "sections": [
    {{
      "type": "definition",
      "title": "What is {topic}?",
      "content": "[3-4 sentences defining the concept clearly]"
    }},
    {{
      "type": "importance",
      "title": "Why {topic} Matters",
      "content": "[2-3 sentences explaining real-world relevance and practical importance]"
    }},
    {{
      "type": "explanation",
      "title": "How {topic} Works",
      "content": "[Detailed explanation with:
- Core concept breakdown
- Step-by-step process
- Technical details
- Key principles]"
    }},
    {{
      "type": "example",
      "title": "Concrete Example",
      "content": "[A worked example with:
**Problem/Scenario**: [describe]

**Solution**:
Step 1: [action] → [explanation]
Step 2: [action] → [explanation]
Step 3: [result]

**Code/Formula** (if applicable):
```
[actual code or formula with comments]
```
]"
    }},
    {{
      "type": "mistakes",
      "title": "Common Mistakes",
      "content": "[List 2-3 common errors:
- **Mistake 1**: [what students do wrong]
  → Why: [reason]
  → Fix: [correct approach]
]"
    }},
    {{
      "type": "practice",
      "title": "Practice Exercise",
      "content": "[One actionable exercise the student can try right now to reinforce this topic]"
    }}
  ]
}}

RULES:
- Be detailed and thorough
- Use clear, simple language
- Include concrete examples with code/formulas
- Point out common errors
- Make it practical and actionable
"""
        
        try:
            response = await llm_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=2000,  # Focused on 1 topic
                bypass_default=True
            )
            
            # Parse JSON
            content = response.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            topic_data = json.loads(content)
            logger.info(f"Successfully generated content for topic {topic_index}: {topic}")
            
        except Exception as e:
            # Fallback for single topic
            logger.warning(f"LLM failed for topic content: {e}. Using fallback.")
            topic_data = {
                "topic_name": topic,
                "sections": [
                    {
                        "type": "definition",
                        "title": f"Understanding {topic}",
                        "content": f"{topic} is a fundamental concept in {module.title}. It represents one of the key building blocks you need to master."
                    },
                    {
                        "type": "explanation",
                        "title": "Key Points",
                        "content": f"When learning {topic}, focus on understanding the core principles and how they apply in practice."
                    },
                    {
                        "type": "practice",
                        "title": "What to Do Next",
                        "content": f"Try to explain {topic} in your own words. Practice with examples to solidify your understanding."
                    }
                ]
            }
        
        return topic_data
    
    async def complete_topic(
        self,
        module_id: str,
        topic_index: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Mark a topic as completed and return next topic index
        """
        # Get lesson state
        result = await db.execute(
            select(TeacherLessonState).where(TeacherLessonState.module_id == module_id)
        )
        lesson_state = result.scalar_one_or_none()
        
        if not lesson_state:
            raise ValueError("Lesson state not found")
        
        # Get module to check total topics
        module_result = await db.execute(
            select(TeacherModule).where(TeacherModule.id == module_id)
        )
        module = module_result.scalar_one()
        total_topics = len(module.topics)
        
        # Update completed topics list
        completed = lesson_state.topics_completed or []
        if topic_index not in completed:
            completed.append(topic_index)
            lesson_state.topics_completed = completed
        
        # Move to next topic
        next_index = topic_index + 1
        all_completed = next_index >= total_topics
        
        if not all_completed:
            lesson_state.current_topic_index = next_index
        else:
            # All topics done, ready for check phase
            lesson_state.current_phase = LessonPhase.CHECK
        
        await db.commit()
        
        return {
            "next_topic_index": next_index if not all_completed else None,
            "all_completed": all_completed,
            "total_topics": total_topics,
            "topics_completed": len(completed)
        }
    
    async def answer_topic_question(
        self,
        module_id: str,
        topic_index: int,
        question: str,
        db: AsyncSession
    ) -> str:
        """
        Answer student's question about a specific topic
        """
        # Get module and topic
        result = await db.execute(
            select(TeacherModule).where(TeacherModule.id == module_id)
        )
        module = result.scalar_one()
        
        if topic_index >= len(module.topics):
            return "Invalid topic index"
        
        topic = module.topics[topic_index]
        
        prompt = f"""You are a patient teacher. A student learning "{topic}" (from {module.title}) asked:

"{question}"

Provide a clear, helpful answer that:
1. Directly addresses their question
2. Uses simple language
3. Includes an example if helpful
4. Encourages further learning

Keep your answer concise (3-5 sentences) but thorough."""
        
        response = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=500
        )
        
        return response
