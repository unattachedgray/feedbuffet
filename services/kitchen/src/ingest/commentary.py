import os
import json
import time
from typing import List, Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load .env from kitchen directory explicitly
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
print(f"Loading .env from: {env_path}")
print(f".env exists: {os.path.exists(env_path)}")
load_dotenv(env_path)

# Load API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

print(f"GEMINI_API_KEY loaded: {bool(GEMINI_API_KEY)}")
print(f"OPENAI_API_KEY loaded: {bool(OPENAI_API_KEY)}")
print(f"ANTHROPIC_API_KEY loaded: {bool(ANTHROPIC_API_KEY)}")

# Initialize clients AFTER loading env vars
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

openai_client = None
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    print(f"OpenAI client initialized: {openai_client is not None}")
except ImportError:
    print("OpenAI package not installed")

anthropic_client = None
try:
    from anthropic import Anthropic
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
    print(f"Anthropic client initialized: {anthropic_client is not None}")
except ImportError:
    print("Anthropic package not installed")


def generate_commentary(courses_data: List[Dict[str, Any]], target_language: str = "English", model: str = "gemini") -> str:
    """
    Generate AI commentary on today's news stories.
    
    Args:
        courses_data: List of course dictionaries with titles and summaries
        target_language: Language for the commentary
        model: AI model to use (gemini, gpt5nano, claude)
    
    Returns:
        Commentary text string
    """
    if not courses_data:
        return f"No news stories available for commentary today."
    
    # Create a summary of today's news
    news_summary = "\n\n".join([
        f"• {course.get('title', 'Untitled')}: {course.get('summary', 'No summary')[:150]}..."
        for course in courses_data[:10]  # Limit to top 10 stories
    ])
    
    prompt = f"""You are an insightful news analyst. Provide a brief, engaging commentary on today's top news stories in {target_language}.

Today's Top Stories:
{news_summary}

Provide a 2-3 paragraph analysis highlighting:
1. Key themes and trends across these stories
2. Notable implications or connections between events
3. Your perspective on what matters most

Keep it conversational and opinionated. Write in {target_language}."""

    try:
        if model == "gemini":
            if not gemini_client:
                return "Gemini API not configured."
            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            return response.text
            
        elif model == "gpt5nano":
            if not openai_client:
                return "OpenAI API not configured."
            response = openai_client.chat.completions.create(
                model="gpt-5-nano-2025-08-07",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            return response.choices[0].message.content
            
        elif model == "claude":
            if not anthropic_client:
                return "Anthropic API not configured."
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
            
    except Exception as e:
        print(f"Commentary generation error ({model}): {e}")
        return f"Unable to generate commentary at this time."
    
    return "Model not supported for commentary."
