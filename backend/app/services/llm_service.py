"""
LLM service for Qwen 2.5 (7B) - Optimized for GTX 1650 (4GB VRAM)
"""
import httpx
from typing import Optional, List, Dict, Any
import logging
import json

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Ollama (Qwen 2.5 7B) - GTX 1650 optimized"""
    
    def __init__(self):
        self.base_url = settings.llm_server_url.rstrip('/')
        self.max_tokens = 350  # Optimized for 4GB VRAM GPU
        self.context_window = 2048  # Limited for GPU memory
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,  # Balanced for quality and consistency
        stop: Optional[List[str]] = None,
        bypass_default: bool = False  # Override cap for teacher mode
    ) -> str:
        """
        Call the LLM using OpenAI-compatible chat completions API
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop: Stop sequences
            
        Returns:
            Generated text
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:  # 2 minutes timeout
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json={
                        "model": "qwen2.5:7b-instruct",
                        "messages": messages,
                        "max_tokens": max_tokens if bypass_default else (max_tokens or self.max_tokens),
                        "temperature": temperature,
                        "stop": stop or [],
                        "stream": False,
                        "num_ctx": self.context_window  # GPU memory optimization
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract message content from OpenAI format
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                return ""
                
        except httpx.TimeoutException:
            logger.error("LLM request timed out")
            raise Exception("LLM request timed out. Please try again.")
        except httpx.HTTPError as e:
            logger.error(f"LLM HTTP error: {e}")
            raise Exception(f"LLM server error: {str(e)}")
        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        stop: Optional[List[str]] = None
    ) -> str:
        """Generate text from a single prompt (wrapper for chat_completion)"""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat_completion(messages, max_tokens, temperature, stop)
    
    async def generate_whiteboard_response(
        self,
        question: str,
        context: str,
        session_summary: str = ""
    ) -> str:
        """
        Generate a whiteboard-style educational response
        **WITH CACHING**: Reuses identical responses for same question+context
        """
        from app.services.response_cache import response_cache
        
        # Check cache first
        cached_response = response_cache.get(question, context)
        if cached_response:
            return cached_response
        
        system_prompt = "You are an AI tutor. Provide clear, concise educational responses with bullet points and examples."

        # Limit context size for GPU memory
        context_limited = (context[:500] + "...") if len(context) > 500 else context
        summary_limited = (session_summary[:200] + "...") if len(session_summary) > 200 else session_summary
        
        user_prompt = f"""CONTEXT: {context_limited if context_limited else "None"}

PREVIOUS: {summary_limited if summary_limited else "Start of session"}

QUESTION: {question}

Provide a clear, educational response."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages)
        
        # Store in cache for future use
        response_cache.set(question, response, context)
        
        return response
    
    async def extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant that extracts key learning concepts. Return ONLY a comma-separated list of concept names, nothing else."},
            {"role": "user", "content": f"Extract the key learning concepts from this educational content:\n\n{text}\n\nCONCEPTS:"}
        ]
        
        response = await self.chat_completion(messages, max_tokens=50, temperature=0.2)
        
        # Parse comma-separated concepts
        concepts = [c.strip() for c in response.split(",") if c.strip()]
        return concepts[:10]  # Limit to 10 concepts
    
    async def generate_quiz_questions(
        self,
        content: str,
        num_questions: int = 5,
        question_types: List[str] = None
    ) -> str:
        """
        Generate quiz questions with STRICT JSON schema validation
        Returns JSON string with validated structure for quiz questions
        """
        types = question_types or ["mcq", "true_false"]
        
        # STRICT system prompt with JSON schema enforcement
        system_prompt = """You are an expert quiz generator for academic learning sessions.

CRITICAL OUTPUT RULES:
1. You MUST respond with ONLY valid JSON - NO markdown code blocks (no ```json```)
2. Use this EXACT schema:
{
  "questions": [
    {
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "correct_index": 0,
      "explanation": "string"
    }
  ]
}

FIELD REQUIREMENTS:
- "question": Non-empty string, 10+ chars, references specific content
- "options": Array of EXACTLY 4 strings, each 30-100 chars
- "correct_index": Integer 0-3 (position of correct answer in options array)
- "explanation": Brief explanation of correct answer

CONTENT RULES:
1. Generate questions ONLY from provided content
2. NO generic/template questions
3. Reference specific facts, concepts, definitions

OPTION FORMATTING RULES (CRITICAL):
- Write options as PLAIN TEXT ONLY
- NO markdown: no **, no ##, no *italic*, no `code`, no ---
- NO list prefixes: don't write "A)", "1)", "•", "-"
- Just write the option text directly
- Example: "The process of organizing data to reduce redundancy"

MCQ DISTRACTOR RULES:
- Each MCQ needs 3 realistic, plausible distractors
- Distractors should be:
  * Common misconceptions about the topic
  * Similar but incorrect concepts from content
  * Edge cases or partial truths
  * Same style and length as correct answer (30-100 chars)
  
FORBIDDEN DISTRACTOR TYPES:
- "This was not discussed"
- "The opposite is true"
- "None of the above"
- "All of the above"
- Any meta-answer about the question
- Any placeholder like "...", "option X"

EXAMPLE VALID OUTPUT:
{
  "questions": [
    {
      "question": "What is database normalization?",
      "options": [
        "The process of organizing data to reduce redundancy",
        "The process of backing up database files regularly",
        "The technique for indexing database tables",
        "A method for encrypting sensitive data"
      ],
      "correct_index": 0,
      "explanation": "Normalization organizes data to minimize redundancy and dependency"
    }
  ]
}

JSON VALIDATION CHECKLIST:
- Valid JSON syntax (no trailing commas, proper quotes)
- "questions" array with at least 1 item
- Each question has all required fields
- Options array has exactly 4 items
- correct_index is 0, 1, 2, or 3
- No markdown formatting in any text field"""
        
        # Enhanced user prompt
        user_prompt = f"""Generate {num_questions} quiz questions from this content.

---CONTENT---
{content[:2000]}
---END---

Generate {num_questions} questions as valid JSON (schema from system prompt).
Remember:
- correct_index is 0-3 (array position, not letter)
- Options are plain text (no markdown, no prefixes)
- Distractors are realistic misconceptions
- Output ONLY the JSON object, nothing else"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self.chat_completion(messages, max_tokens=300, temperature=0.3)
    
    async def generate_youtube_keywords(
        self,
        topic: str,
        subject: str
    ) -> List[str]:
        """Generate YouTube search keywords for a topic"""
        messages = [
            {"role": "system", "content": "Generate YouTube search queries. Return ONLY the queries, one per line."},
            {"role": "user", "content": f"Generate 5 YouTube search queries to find educational videos about:\nSubject: {subject}\nTopic: {topic}"}
        ]
        
        response = await self.chat_completion(messages, max_tokens=50, temperature=0.3)
        queries = [q.strip() for q in response.strip().split("\n") if q.strip()]
        return queries[:5]
    
    async def summarize_session(self, messages: List[Dict[str, str]]) -> str:
        """Summarize a conversation session"""
        conversation = "\n".join([
            f"{m['role'].upper()}: {m['content'][:500]}"
            for m in messages[-10:]
        ])
        
        chat_messages = [
            {"role": "system", "content": "Summarize this learning session in 2-3 sentences, highlighting key topics discussed."},
            {"role": "user", "content": f"CONVERSATION:\n{conversation}"}
        ]
        
        return await self.chat_completion(chat_messages, max_tokens=100, temperature=0.2)
    
    async def health_check(self) -> bool:
        """Check if LLM server is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try the models endpoint first (OpenAI-compatible)
                response = await client.get(f"{self.base_url}/v1/models")
                if response.status_code == 200:
                    return True
                # Fallback to health endpoint
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


# Global instance
llm_service = LLMService()
