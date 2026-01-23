"""
LLM service for Phi-3 integration via OpenAI-compatible API
"""
import httpx
from typing import Optional, List, Dict, Any
import logging
import json

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with local Phi-3 LLM server via OpenAI-compatible API"""
    
    def __init__(self):
        self.base_url = settings.llm_server_url.rstrip('/')
        self.max_tokens = settings.llm_max_tokens
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        stop: Optional[List[str]] = None
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
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minutes timeout
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json={
                        "model": "phi-3",
                        "messages": messages,
                        "max_tokens": max_tokens or self.max_tokens,
                        "temperature": temperature,
                        "stop": stop or [],
                        "stream": False
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
        """
        system_prompt = """You are an expert AI tutor helping a student learn. Create clear, educational responses in a "whiteboard" style.

FORMAT YOUR RESPONSE AS STRUCTURED NOTES:
- Use clear headings with ## for main topics
- Use bullet points for key concepts
- Include examples where helpful
- Add formulas in LaTeX format ($...$) if mathematical
- Keep explanations clear and progressive
- Be thorough but concise"""

        user_prompt = f"""CONTEXT FROM KNOWLEDGE BASE:
{context if context else "No additional context available."}

PREVIOUS CONVERSATION SUMMARY:
{session_summary if session_summary else "This is the start of the session."}

STUDENT'S QUESTION:
{question}

Please provide a clear, educational whiteboard-style response."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self.chat_completion(messages)
    
    async def extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant that extracts key learning concepts. Return ONLY a comma-separated list of concept names, nothing else."},
            {"role": "user", "content": f"Extract the key learning concepts from this educational content:\n\n{text}\n\nCONCEPTS:"}
        ]
        
        response = await self.chat_completion(messages, max_tokens=200, temperature=0.3)
        
        # Parse comma-separated concepts
        concepts = [c.strip() for c in response.split(",") if c.strip()]
        return concepts[:10]  # Limit to 10 concepts
    
    async def generate_quiz_questions(
        self,
        content: str,
        num_questions: int = 5,
        question_types: List[str] = None
    ) -> str:
        """Generate quiz questions from content"""
        types = question_types or ["mcq", "true_false"]  # Remove short_answer to simplify
        
        # Simplified system prompt
        system_prompt = "You are a quiz generator. Generate questions in JSON format ONLY. No explanations."
        
        # Much simpler user prompt
        user_prompt = f"""Create {num_questions} quiz questions from this content.

CONTENT:
{content[:1000]}

OUTPUT (JSON array only, no markdown):
[
  {{"type": "mcq", "question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "A"}},
  {{"type": "true_false", "question": "...", "answer": "True"}}
]"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self.chat_completion(messages, max_tokens=800, temperature=0.3)  # Reduced from 1500
    
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
        
        response = await self.chat_completion(messages, max_tokens=200, temperature=0.5)
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
        
        return await self.chat_completion(chat_messages, max_tokens=200, temperature=0.3)
    
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
