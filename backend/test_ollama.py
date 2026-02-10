"""
Quick test script to verify Ollama integration
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_service import llm_service


async def test_ollama():
    print("=" * 60)
    print("Testing Ollama Integration")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n1. Testing health check...")
    try:
        is_healthy = await llm_service.health_check()
        if is_healthy:
            print("✓ Ollama is running and accessible")
        else:
            print("✗ Ollama health check failed")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False
    
    # Test 2: Simple Chat Completion
    print("\n2. Testing chat completion...")
    try:
        response = await llm_service.chat_completion(
            messages=[{"role": "user", "content": "What is 2+2? Answer in one sentence."}],
            max_tokens=50,
            temperature=0.1
        )
        print(f"✓ Response received: {response[:100]}...")
    except Exception as e:
        print(f"✗ Chat completion error: {e}")
        return False
    
    # Test 3: Generate method
    print("\n3. Testing generate method...")
    try:
        response = await llm_service.generate(
            "Define the term 'algorithm' in one sentence.",
            max_tokens=50
        )
        print(f"✓ Response received: {response[:100]}...")
    except Exception as e:
        print(f"✗ Generate error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All tests passed! Ollama integration is working.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_ollama())
    sys.exit(0 if success else 1)
