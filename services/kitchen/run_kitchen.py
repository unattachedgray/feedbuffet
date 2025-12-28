import time
import sys
import os

# Ensure we can import src
sys.path.append(os.getcwd())

# Import DB engine first to ensure it loads
from src.db.engine import get_db, engine, Base
from src.db.models import Article, Course, CourseArticle

from src.ingest.news_client import NewsClient
from src.ingest.grouping import simple_group_articles
from src.ingest.normalizer import normalize_group_to_course

def main():
    print("Starting Kitchen Service...")
    
    # 1. Init DB (Idempotent usually, or use Alembic later)
    print("Initializing Database...")
    Base.metadata.create_all(bind=engine)
    
    # 2. Fetch News
    print("Fetching News...")
    client = NewsClient()
    # Ingest small amount for dev
    articles_data = client.fetch_latest_news(query="technology", max_pages=1)
    print(f"Fetched {len(articles_data)} raw articles.")
    
    # 3. Save Articles to DB (and return objects for grouping)
    db = next(get_db())
    saved_articles = []
    
    try:
        for ad in articles_data:
            # Check dupes
            url = ad.get('link') or ad.get('url') # NewsData uses 'link' or 'url' depending on version? Check raw dump. 
            # NewsData API 'results' usually have 'link'.
            if not url:
                continue
                
            existing = db.query(Article).filter(Article.url == url).first()
            if not existing:
                new_art = Article(
                    url=url,
                    source_name=ad.get('source_id'), # or source_name
                    title=ad.get('title'),
                    description=ad.get('description'),
                    published_at=ad.get('pubDate'), # need parsing? NewsData returns string. SQLA might complain.
                    language=ad.get('language')
                )
                db.add(new_art)
                db.flush() # to get ID
                saved_articles.append(new_art)
            else:
                saved_articles.append(existing)
        
        db.commit()
        print(f"Saved/Found {len(saved_articles)} articles in DB.")
        
        # 4. Group
        print("Grouping articles...")
        groups = simple_group_articles(saved_articles)
        print(f"Found {len(groups)} groups.")
        
        # 5. Normalize (AI)
        for i, group in enumerate(groups):
            if len(group) < 2: # Skip singletons for MVP cost saving? Or process all.
                print(f"Skipping group {i} (size {len(group)})")
                continue
                
            print(f"Normalizing group {i} (size {len(group)})...")
            course_data = normalize_group_to_course([
                {
                    'title': a.title,
                    'description': a.description,
                    'source_name': a.source_name,
                    'published_at': str(a.published_at),
                    'url': a.url
                } for a in group
            ])
            
            if course_data:
                # Save Course
                # Generate key?
                c_key = f"course_{int(time.time())}_{i}"
                
                new_course = Course(
                    course_key=c_key,
                    title=course_data.get('course_title'),
                    summary=course_data.get('course_summary'),
                    entities_json=course_data.get('entities'),
                    topics_json=course_data.get('topics'),
                    source_urls=course_data.get('source_urls'),
                    # published_at ?
                )
                db.add(new_course)
                db.flush()
                
                # Link articles
                for art in group:
                    # Check if already linked?
                    link = CourseArticle(course_id=new_course.id, article_id=art.id)
                    db.add(link)
                
                db.commit()
                print(f"Created Course: {new_course.title}")
                
    except Exception as e:
        print(f"Error in main loop: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
