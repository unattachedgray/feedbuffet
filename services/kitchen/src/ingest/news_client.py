import os
import json
import time
import requests
from datetime import datetime

# Load environment variables if not already loaded (e.g. by python-dotenv)
# For local run, we might want to load .env explicitly if not running via a runner that does it.
from dotenv import load_dotenv
load_dotenv()

NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
RAW_DUMP_DIR = os.getenv("RAW_DUMP_DIR", "data/raw")

BASE_URL = "https://newsdata.io/api/1/news"

class NewsClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or NEWSDATA_API_KEY
        if not self.api_key:
            raise ValueError("NEWSDATA_API_KEY not found in environment or passed to constructor.")

    def fetch_latest_news(self, query=None, category=None, language="en", page=None, max_pages=3):
        """
        Fetch news articles from NewsData.io.
        
        Args:
        Args:
            query (str): Search query (optional).
            category (str): Category (optional, e.g. 'technology', 'business').
            language (str): Language code. Default "en".
            language (str): Language code. Default "en".
            page (str): Next page token.
            max_pages (int): Maximum number of pages to fetch in this chain.
        
        Returns:
            list[dict]: List of fetched articles (results).
        """
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        all_results = []
        
        current_page = page
        pages_fetched = 0
        
        while pages_fetched < max_pages:
            print(f"Fetching page {pages_fetched + 1} (token: {current_page})...")
            
            params = {
                "apikey": self.api_key,
                "language": language,
            }
            if query:
                params["q"] = query
            if category:
                params["category"] = category
            if current_page:
                params["page"] = current_page
                
            try:
                response = requests.get(BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Save raw dump
                self._save_raw_dump(data, run_id, pages_fetched)
                
                results = data.get("results", [])
                all_results.extend(results)
                
                current_page = data.get("nextPage")
                pages_fetched += 1
                
                if not current_page:
                    break
                    
                # Respect rate limits (1 request per second typically safe, but check headers if needed)
                time.sleep(1)
                
            except Exception as e:
                print(f"Error fetching news: {e}")
                break
                
        return all_results

    def _save_raw_dump(self, data, run_id, page_num):
        """Saves the raw JSON response to a file."""
        date_str = datetime.now().strftime("%Y%m%d")
        dir_path = os.path.join(RAW_DUMP_DIR, date_str)
        os.makedirs(dir_path, exist_ok=True)
        
        filename = f"{run_id}_page{page_num}.json"
        filepath = os.path.join(dir_path, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved raw dump to {filepath}")

if __name__ == "__main__":
    # Test run
    client = NewsClient()
    articles = client.fetch_latest_news(max_pages=1)
    print(f"Fetched {len(articles)} articles.")
