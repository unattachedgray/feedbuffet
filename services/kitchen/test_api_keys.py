"""
Test script to verify API key loading and client initialization
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.ingest.chef import GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY
from src.ingest.chef import gemini_client, openai_client, anthropic_client

print("=" * 60)
print("API KEY LOADING TEST")
print("=" * 60)

print(f"\n✓ GEMINI_API_KEY: {'✓ Loaded' if GEMINI_API_KEY else '✗ Missing'}")
print(f"✓ OPENAI_API_KEY: {'✓ Loaded' if OPENAI_API_KEY else '✗ Missing'}")
print(f"✓ ANTHROPIC_API_KEY: {'✓ Loaded' if ANTHROPIC_API_KEY else '✗ Missing'}")

print(f"\n✓ Gemini Client: {'✓ Initialized' if gemini_client else '✗ Failed'}")
print(f"✓ OpenAI Client: {'✓ Initialized' if openai_client else '✗ Failed'}")
print(f"✓ Anthropic Client: {'✓ Initialized' if anthropic_client else '✗ Failed'}")

print("\n" + "=" * 60)

# Test a simple API call with each client
if openai_client:
    print("\nTesting OpenAI API call...")
    try:
        response = openai_client.chat.completions.create(
            model="gpt-5-nano-2025-08-07",
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=5
        )
        print(f"✓ OpenAI API call successful: {response.choices[0].message.content}")
    except Exception as e:
        print(f"✗ OpenAI API call failed: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
