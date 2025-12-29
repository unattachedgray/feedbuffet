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

# Strict user requirement: gemini-3-flash-preview
MODEL_ID = "gemini-3-flash-preview"

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

def normalize_article_groups(groups_of_articles):
    """
    Takes a list of groups (each group is a list of articles).
    Returns a list of Course dicts in the same order.
    """
    if not groups_of_articles: return []

    batch_context = ""
    for g_idx, articles in enumerate(groups_of_articles):
        batch_context += f"--- GROUP {g_idx} START ---\n"
        for i, art in enumerate(articles):
             batch_context += f"[{i+1}] Title: {art.get('title')}\nSource: {art.get('source_name')}\nDate: {art.get('published_at')}\nSummary: {art.get('description')}\nURL: {art.get('url')}\n\n"
        batch_context += f"--- GROUP {g_idx} END ---\n\n"

    prompt = f"""
    You are a professional news editor.
    You will be given multiple separate groups of news articles.
    For EACH group, analyze the articles and create a single "Course" (consolidated story) representation.
    
    Input Data:
    {batch_context}
    
    Output strictly valid JSON as a LIST of objects, where the order matches the input groups:
    [
        {{
            "course_title": "Headline (max 10 words)",
            "course_summary": "Summary (max 80 words)",
            "entities": ["entity1", "entity2"],
            "topics": ["topic1", "topic2"],
            "representative_published_at": "ISO8601 timestamp",
            "source_urls": ["url1", "url2"]
        }},
        ...
    ]
    """

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        data = json.loads(response.text)
        if isinstance(data, list):
            return data
        else:
            # Fallback if model returns single object instead of list
            return [data] if data else []
            
    except Exception as e:
        print(f"Error normalizing batch: {e}")
        return [None] * len(groups_of_articles)
