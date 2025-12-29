import feedparser
import time
import requests
import json
import os
from datetime import datetime

class GoogleNewsClient:
    def __init__(self):
        self.base_url = "https://news.google.com/rss/search"
    
    def fetch_latest_news(self, query=None, category=None, language="en", page=None, max_pages=1, hl="en-US", gl="US", ceid="US:en"):
        """
        Fetch news from Google News RSS.
        Note: 'page' and 'max_pages' are ignored as RSS is usually single-page.
        'category' is treated as a query if 'query' is not provided.
        """
        # Topic Mapping
        TOPIC_MAP = {
            'business': 'BUSINESS',
            'technology': 'TECHNOLOGY',
            'entertainment': 'ENTERTAINMENT',
            'sports': 'SPORTS',
            'science': 'SCIENCE',
            'health': 'HEALTH',
            'world': 'WORLD',
            'nation': 'NATION'
        }
        
        url = self.base_url
        params = {
            "hl": hl,
            "gl": gl,
            "ceid": ceid
        }
        
        
        url = self.base_url
        params = {
            "hl": hl,
            "gl": gl,
            "ceid": ceid
        }
        
        # Determine Endpoint
        if category and category.lower() in TOPIC_MAP:
             # Use Topic Endpoint
             topic_id = TOPIC_MAP[category.lower()]
             url = f"https://news.google.com/rss/headlines/section/topic/{topic_id}"
             print(f"Fetching Google News Topic: {topic_id}")
             
        elif not category or category.lower() == 'top' or category.lower() == 'headlines':
             # Use Top Stories (Headlines) Endpoint
             # Base URL is search, we want headlines
             url = "https://news.google.com/rss"
             print(f"Fetching Google News Top Stories")
             
        else:
            # Use Search Endpoint for custom queries/categories
            q = query
            if not q and category:
                q = category 
            
            if not q:
                url = "https://news.google.com/rss" # Fallback to headlines if query is empty partial
                print(f"Fetching Top Stories (Empty Query)")
            else:
                url = "https://news.google.com/rss/search"
                params["q"] = q
                print(f"Fetching Google News RSS Search: {q}")
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            articles = []
            for entry in feed.entries:
                # Normalize to our internal dict format
                # We need: title, link, description, pubDate, source_id, language
                
                # Google News RSS source title is often "Publication Name"
                source = entry.source.title if 'source' in entry else "Google News"
                
                # Description often contains HTML, simplistic cleanup or keep as is?
                # Keeping as is, frontend can handle or we strip later. 
                # Actually, Google News RSS description is often just a link list or a snippet.
                
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "description": entry.summary if 'summary' in entry else "",
                    "pubDate": entry.published if 'published' in entry else datetime.now().isoformat(),
                    "source_id": source,
                    "language": "en", # RSS default context
                    "category": category or "general" 
                })
            
            return articles
            
        except Exception as e:
            print(f"Error fetching Google News: {e}")
            return []

if __name__ == "__main__":
    client = GoogleNewsClient()
    news = client.fetch_latest_news(query="SpaceX")
    print(f"Fetched {len(news)} articles.")
    if news:
        print(news[0])
