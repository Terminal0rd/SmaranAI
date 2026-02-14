"""
Streaming LLM service for real-time token generation
"""
import httpx
import json
import logging
from typing import AsyncIterator

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def stream_chat_completion(
    messages: list[dict[str, str]],
    model: str = "qwen2.5:7b-instruct",
    max_tokens: int = 350,
    temperature: float = 0.3,
    num_ctx: int = 2048
) -> AsyncIterator[str]:
    """
    Stream chat completion tokens in real-time
    
    Yields:
        str: Individual tokens as they're generated
    """
    base_url = settings.llm_server_url.rstrip('/')
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{base_url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True,  # Enable streaming
                    "num_ctx": num_ctx
                },
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    # Skip empty lines
                    if not line.strip():
                        continue
                    
                    # Skip "data: " prefix
                    if line.startswith("data: "):
                        line = line[6:]
                    
                    # Skip [DONE] marker
                    if line.strip() == "[DONE]":
                        break
                    
                    try:
                        # Parse JSON chunk
                        chunk = json.loads(line)
                        
                        # Extract content from delta
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            
                            if content:
                                yield content
                                
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse streaming chunk: {line}")
                        continue
                        
    except httpx.HTTPError as e:
        logger.error(f"Streaming HTTP error: {e}")
        raise Exception(f"Streaming failed: {str(e)}")
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        raise Exception(f"Streaming failed: {str(e)}")
