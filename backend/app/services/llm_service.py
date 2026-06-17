"""
LLM service - Supports Groq (cloud) and Ollama (local)
Switchable via LLM_PROVIDER env var: "groq" or "ollama"
"""
import httpx
from typing import Optional, List, Dict, Any
import logging
import json

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class LLMService:
    """
    LLM service with dual backend support:
    - Groq: Fast cloud API (llama-3.3-70b-versatile)
    - Ollama: Local LLM (qwen2.5:7b-instruct)
    
    Switch via LLM_PROVIDER env var. RAG/embeddings stay local regardless.
    """
    
    def __init__(self):
        self.provider = settings.llm_provider.lower()  # "groq" or "ollama"
        
        if self.provider == "groq":
            self.base_url = "https://api.groq.com/openai"
            self.api_key = settings.groq_api_key
            self.model_name = settings.groq_model
            self.default_max_tokens = 2048
            self.context_window = 32768
            logger.info(f"LLM Provider: Groq ({self.model_name})")
        else:
            self.base_url = settings.llm_server_url.rstrip('/')
            self.api_key = None
            self.model_name = settings.ollama_model
            self.default_max_tokens = 500
            self.context_window = 2048
            logger.info(f"LLM Provider: Ollama ({self.model_name})")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        timeout: int = 60,
        bypass_default: bool = False
    ) -> str:
        """
        Get chat completion from LLM (Groq or Ollama)
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            timeout: Request timeout in seconds
        
        Returns:
            Response text from LLM
        """
        try:
            # Build headers
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # Groq is fast - shorter timeouts. Ollama needs longer.
            if self.provider == "groq":
                timeout_config = httpx.Timeout(
                    timeout=min(float(timeout), 120.0),  # Groq rarely needs >60s
                    connect=30.0,
                    read=min(float(timeout), 120.0),
                    write=30.0
                )
            else:
                timeout_config = httpx.Timeout(
                    timeout=float(timeout),
                    connect=60.0,
                    read=float(timeout),
                    write=60.0
                )
            
            # API endpoint
            api_url = f"{self.base_url}/v1/chat/completions"
            
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.post(
                    api_url,
                    headers=headers,
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": False
                    }
                )
                
                if response.status_code != 200:
                    error_text = response.text[:500]
                    logger.error(f"LLM ({self.provider}) returned status {response.status_code}: {error_text}")
                    raise Exception(f"LLM request failed with status {response.status_code}: {error_text}")
                
                result = response.json()
                return result["choices"][0]["message"]["content"]
                
        except httpx.ReadTimeout:
            logger.error(f"LLM ({self.provider}) request timed out after {timeout}s")
            raise Exception("LLM request timed out. Please try again.")
        except Exception as e:
            logger.error(f"LLM ({self.provider}) request failed: {e}")
            raise Exception(f"LLM server error: {str(e)}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        stop: Optional[List[str]] = None
    ) -> str:
        """Generate text from a single prompt (wrapper for chat_completion)"""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat_completion(messages, max_tokens or self.default_max_tokens, temperature)
    
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

        # Groq can handle more context, Ollama needs limits
        if self.provider == "groq":
            context_limited = (context[:2000] + "...") if len(context) > 2000 else context
            summary_limited = (session_summary[:500] + "...") if len(session_summary) > 500 else session_summary
            response_tokens = 2000
        else:
            context_limited = (context[:500] + "...") if len(context) > 500 else context
            summary_limited = (session_summary[:200] + "...") if len(session_summary) > 200 else session_summary
            response_tokens = 1000
        
        user_prompt = f"""CONTEXT: {context_limited if context_limited else "None"}

PREVIOUS: {summary_limited if summary_limited else "Start of session"}

QUESTION: {question}

Provide a clear, educational response."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(messages, max_tokens=response_tokens)
        
        # Store in cache for future use
        response_cache.set(question, response, context)
        
        return response
    
    async def extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant that extracts key learning concepts. Return ONLY a comma-separated list of concept names, nothing else."},
            {"role": "user", "content": f"Extract the key learning concepts from this educational content:\n\n{text}\n\nCONCEPTS:"}
        ]
        
        response = await self.chat_completion(messages, max_tokens=100, temperature=0.2)
        
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
- "options": Array of EXACTLY 4 strings, each 15-60 chars (keep SHORT)
- "correct_index": Integer 0-3 (position of correct answer in options array)
- "explanation": 1 sentence max

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
  * Same style and length as correct answer (15-60 chars)
  
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
        
        # Groq can handle more content for better questions
        content_limit = 4000 if self.provider == "groq" else 2000
        
        # Enhanced user prompt
        user_prompt = f"""Generate {num_questions} quiz questions from this content.

---CONTENT---
{content[:content_limit]}
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
        
        # Groq: more tokens, shorter timeout. Ollama: fewer tokens, longer timeout.
        if self.provider == "groq":
            return await self.chat_completion(messages, max_tokens=2000, temperature=0.3, timeout=60)
        else:
            return await self.chat_completion(messages, max_tokens=1200, temperature=0.3, timeout=300)
    
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
        
        response = await self.chat_completion(messages, max_tokens=100, temperature=0.3)
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
        
        return await self.chat_completion(chat_messages, max_tokens=200, temperature=0.2)
    
    async def health_check(self) -> bool:
        """Check if LLM server is healthy"""
        try:
            if self.provider == "groq":
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{self.base_url}/v1/models",
                        headers=headers
                    )
                    return response.status_code == 200
            else:
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
