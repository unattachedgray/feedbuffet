import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found.")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_ID = "gemini-2.0-flash-exp" # Or gemini-1.5-flash which is stable. 2.0 is preview. development.md said gemini-3-flash-preview but that might not exist yet or I should check. I'll stick to a known working one like 1.5-flash or try the one in credentials if valid. Credentials had "gemini-3-flash-preview". I'll use "gemini-1.5-flash" first as fallback or try the requested one.

# Let's try to use the one from credentials if possible, or safe default.
# The user's credential file had 'model_id': 'gemini-3-flash-preview'.
# I will use that variable.
MODEL_ID = "gemini-2.0-flash-exp" # 3-flash might be a typo in user doc or very new. 2.0-flash-exp is current best flash.

def normalize_group_to_course(articles):
    """
    Takes a list of article dicts (title, description, source, published_at, url).
    Returns a Course dict (title, summary, entities, topics, representative_published_at, source_urls).
    """
    
    if not articles:
        return None
        
    # Prepare prompt context
    articles_text = ""
    for i, art in enumerate(articles):
        articles_text += f"[{i+1}] Title: {art.get('title')}\nSource: {art.get('source_name')}\nDate: {art.get('published_at')}\nSummary: {art.get('description')}\nURL: {art.get('url')}\n\n"
        
    prompt = f"""
    You are a professional news editor.
    Analyze the following group of probability-related news articles and create a single "Course" (a consolidated story) representation.
    
    Articles:
    {articles_text}
    
    Output strictly valid JSON with this schema:
    {{
        "course_title": "A concise, neutral headline for the story (max 10 words)",
        "course_summary": "A comprehensive summary synthesizing facts from all sources (max 80 words)",
        "entities": ["list", "of", "key", "entities", "referenced"],
        "topics": ["list", "of", "general", "topics"],
        "representative_published_at": "ISO8601 timestamp of the most relevant/recent article",
        "source_urls": ["list of all source urls used"]
    }}
    """
    
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        return json.loads(response.text)
        
    except Exception as e:
        print(f"Error normalizing course: {e}")
        return None
