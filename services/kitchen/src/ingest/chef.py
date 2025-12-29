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

def create_dynamic_batches(items: List[Dict[str, Any]], max_chars: int = 25000) -> List[List[Dict[str, Any]]]:
    """
    Chunks items dynamically based on the length of their string representation.
    Safely fills the context window without overstuffing.
    """
    batches = []
    current_batch = []
    current_chars = 0
    
    for item in items:
        # Estimate size: Title + Description + Metadata
        item_str = str(item)
        item_len = len(item_str)
        
        # If adding this item exceeds max, push current batch
        if current_batch and (current_chars + item_len > max_chars):
             batches.append(current_batch)
             current_batch = []
             current_chars = 0
        
        current_batch.append(item)
        current_chars += item_len
        
    if current_batch:
        batches.append(current_batch)
        
    return batches

def cook_batch(raw_items: List[Dict[str, Any]], existing_titles: List[str] = [], target_language: str = "English", status_callback=None, model: str = "gemini") -> List[Dict[str, Any]]:
    """
    Takes a large batch of raw news items and a list of existing story titles.
    Uses AI (Gemini, GPT-4o, or Claude) to:
    1. Cluster raw items into stories.
    2. Filter out stories that semantically match 'existing_titles'.
    3. Synthesize new Courses.
    """
    if not raw_items: return []

    # Prepare Context
    raw_text = ""
    for i, item in enumerate(raw_items):
        raw_text += f"ID: {i}\nTitle: {item.get('title')}\nSource: {item.get('source_name', 'Unknown')}\nDate: {item.get('published_at')}\nLink: {item.get('link') or item.get('url')}\nSnippet: {item.get('description')}\n\n"

    existing_text = "\n".join([f"- {t}" for t in existing_titles]) if existing_titles else "(None)"

    prompt = f"""
    You are the Executive Chef of a news intelligence service.
    
    GOAL:
    Organize the provided "Raw Ingredients" (news items) into "Courses" (consolidated news stories).
    You must also check the "Menu" (existing stories) and IGNORE any new items that cover the same story, to prevent duplicates.
    
    **CRITICAL**: Output the 'title' and 'summary' fields in the target language: {target_language}.
    However, keep 'category', 'entities', and 'topics' in English for internal tagging consistency.

    INPUTS:
    
    --- EXISTING MENU (Do NOT create courses for these topics) ---
    {existing_text}
    
    --- RAW INGREDIENTS (Cluster these) ---
    {raw_text}
    
    INSTRUCTIONS:
    1. Group the Raw Ingredients by specific semantic topic. **Prefer creating MORE small groups rather than merging loosely related stories.**
    2. If a group matches a topic already on the Existing Menu, DISCARD it completely.
    3. For each NEW group, synthesize a "Course" object.
    4. **CRITICAL**: For 'category', choose the most fitting single-word category (e.g., 'politics', 'ai', 'crypto', 'finance'). Output must be lowercase.
    5. **CRITICAL**: For 'sources', return a list of objects exactly like {{"title": "...", "url": "...", "source": "..."}}. You MUST extract the URL from the raw ingredients provided. Do not hallucinate links.
    
    OUTPUT SCHEMA (JSON List):
    [
        {{
            "title": "Concise, neutral headline (max 10 words)",
            "summary": "Deep synthesis of the story (max 80 words)",
            "category": "business",  
            "entities": ["entity1", "entity2"],
            "topics": ["topic1", "topic2"],
            "sources": [
                {{"title": "Headline of article 1", "url": "https://actual.link/...", "source": "Source Name"}},
                {{"title": "Headline of article 2", "url": "https://actual.link/...", "source": "Source Name"}}
            ],
            "representative_published_at": "ISO8601 timestamp"
        }}
    ]
    """

    try:
        print(f"Chef is cooking batch with {model}...")
        if status_callback: status_callback(f"Consulting AI Chef ({model})...")
        
        if model == "gemini":
            if not gemini_client:
                raise ValueError("Gemini API key not configured")
            response = gemini_client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            response_text = response.text
            
        elif model == "gpt5nano":
            if not openai_client:
                raise ValueError("OpenAI API key not configured")
            response = openai_client.chat.completions.create(
                model="gpt-5-nano-2025-08-07",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            response_text = response.choices[0].message.content
            
        elif model == "claude":
            if not anthropic_client:
                raise ValueError("Anthropic API key not configured")
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.content[0].text
        else:
            raise ValueError(f"Unknown model: {model}")
        
        if status_callback: status_callback("Plating AI results...")
        
        # Robust JSON parsing with fallback
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as je:
            print(f"JSON Parse Error: {je}")
            # Safe print for Unicode content
            try:
                preview = response_text[:500]
                print(f"Response preview: {preview}...")
            except UnicodeEncodeError:
                print(f"Response preview: [Contains non-ASCII characters, length={len(response_text)}]")
            # Try to extract JSON array from markdown code blocks
            if "```json" in response_text:
                try:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_str = response_text[json_start:json_end].strip()
                    data = json.loads(json_str)
                except:
                    return []
            else:
                return []
        
        if isinstance(data, list):
            return data
        return [data] if data else []

    except Exception as e:
        print(f"Chef Burned the Meal ({model}): {e}")
        import traceback
        traceback.print_exc()
        return []

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
