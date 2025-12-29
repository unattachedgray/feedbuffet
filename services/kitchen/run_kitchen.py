import time
import sys
import os
import json
import uuid
from datetime import datetime

# Fix Windows terminal encoding for Unicode characters
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Ensure we can import src
sys.path.append(os.getcwd())

# Import DB engine first to ensure it loads
from src.db.engine import get_db, engine, Base
from src.db.models import Article, Course, CourseArticle

from src.ingest.google_news_client import GoogleNewsClient
from src.ingest.grouping import simple_group_articles
from src.ingest.normalizer import normalize_group_to_course

def parse_date(date_str):
    if not date_str: return None
    try:
        # Try simplistic parsing for YYYY-MM-DD HH:MM:SS
        # Google News RSS uses RFC 822 usually (e.g. 'Sun, 28 Dec 2025 15:30:00 GMT')
        # dparser or similar is best, but for now try fromisoformat or a util
        # Let's try standard dateutil if available or rudimentary parser?
        # For simplicity, let's try a common format or just return string if SQLAlchemy handles it? 
        # SQLAlchemy DateTime needs python datetime.
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except:
        try:
             return datetime.fromisoformat(date_str)
        except:
             return None

import argparse

from src.utils.status_reporter import update_kitchen_status

def main():
    # Load model config from web app
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'apps', 'web', 'lib', 'model_config.json')
    with open(config_path, 'r') as f:
        model_config = json.load(f)
    
    model_choices = [m['id'] for m in model_config['models']]
    default_model = model_config['defaultModel']
    
    parser = argparse.ArgumentParser(description='FeedBuffet Kitchen Service')
    parser.add_argument('--category', type=str, help='Specific category to fetch')
    parser.add_argument('--categories', type=str, help='Comma-separated list of categories')
    parser.add_argument('--query', type=str, help='Specific keyword query')
    parser.add_argument('--hl', type=str, default='en-US', help='Language (e.g. en-US)')
    parser.add_argument('--gl', type=str, default='US', help='Location (e.g. US)')
    parser.add_argument('--ceid', type=str, default='US:en', help='Country:Language (e.g. US:en)')
    parser.add_argument('--model', type=str, default=default_model, choices=model_choices, help='AI model to use')
    args = parser.parse_args()

    # 1. Init DB
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    update_kitchen_status(db, "Warming up the kitchen...", 5)
    
    # 2. Fetch News (Google News RSS)
    # client = NewsClient() 
    client = GoogleNewsClient()
    all_articles_data = []
    
    if args.category:
        CATEGORIES = [args.category]
    elif args.categories:
        CATEGORIES = [c.strip() for c in args.categories.split(',') if c.strip()]
    elif args.query:
        CATEGORIES = [] # Use query instead
        update_kitchen_status(db, f"Hunting for '{args.query}'...", 10)
        data = client.fetch_latest_news(query=args.query, max_pages=1, hl=args.hl, gl=args.gl, ceid=args.ceid)
        all_articles_data.extend(data)
    else:
        # Broadening
        CATEGORIES = ["top", "business", "technology", "science", "entertainment", "health", "sports", "world"]

    for i, cat in enumerate(CATEGORIES):
        print(f"Fetching category: {cat}...")
        update_kitchen_status(db, f"Sourcing ingredients: {cat}...", 10 + (i * 5))
        try:
            cat_data = client.fetch_latest_news(category=cat, max_pages=1, hl=args.hl, gl=args.gl, ceid=args.ceid)
            all_articles_data.extend(cat_data)
            time.sleep(1) 
        except Exception as e:
            print(f"Failed to fetch {cat}: {e}")

    update_kitchen_status(db, f"Chopping {len(all_articles_data)} raw items...", 40)
    print(f"Fetched {len(all_articles_data)} raw articles.")
    
    # 3. Chef's Special: Batch Cooking with Deduplication
    
    # Fetch "Menu" (Existing Courses from last 24h to avoid dupes)
    # We simply fetch all recent titles
    db = next(get_db())
    recent_courses = db.query(Course.title).order_by(Course.published_at.desc()).limit(100).all()
    existing_titles = [r[0] for r in recent_courses]
    
    print(f"Chef: Checking against {len(existing_titles)} items on the menu.")
    update_kitchen_status(db, "Chef is designing the menu...", 50)

    # Convert raw data to standardized dicts for the Chef
    cleaned_ingredients = []
    for ad in all_articles_data:
        if not isinstance(ad, dict): continue
        if not ad.get('title'): continue
        
        cleaned_ingredients.append({
            'title': ad.get('title'),
            'source_name': ad.get('source_id', 'Google News'),
            'published_at': str(parse_date(ad.get('pubDate'))),
            'link': ad.get('link') or ad.get('url'),
            'description': ad.get('description', '')
        })

    # Call the Chef
    # Dynamic Chunking
    from src.ingest.chef import cook_batch, create_dynamic_batches
    
    # 25,000 chars is roughly 6-8k tokens. 
    # Gemini 1.5/Flight is 1M+, but let's be safe for output generation limits.
    # We want to send as much as possible to get better clustering context.
    # Language Mapping for Chef Prompt
    HL_TO_LANG = {
        'en-US': 'English', 'en-GB': 'English', 'en-IN': 'English',
        'ko': 'Korean', 'ja': 'Japanese', 'zh-CN': 'Simplified Chinese', 'zh-TW': 'Traditional Chinese',
        'fr': 'French', 'de': 'German', 'es': 'Spanish', 'it': 'Italian', 'pt-BR': 'Portuguese',
        'ru': 'Russian', 'ar': 'Arabic', 'hi': 'Hindi', 'id': 'Indonesian'
    }
    target_lang_name = HL_TO_LANG.get(args.hl, "English")

    # Model-specific batch sizes from config
    MODEL_BATCH_SIZES = {m['id']: m['maxChars'] for m in model_config['models']}
    
    batch_size = MODEL_BATCH_SIZES.get(args.model, 3600000)
    batches = create_dynamic_batches(cleaned_ingredients, max_chars=batch_size)
    
    new_courses_data = []
    total_chunks = len(batches)
    
    # Language Mapping for Chef Prompt
    HL_TO_LANG = {
        'en-US': 'English', 'en-GB': 'English', 'en-IN': 'English',
        'ko': 'Korean', 'ja': 'Japanese', 'zh-CN': 'Simplified Chinese', 'zh-TW': 'Traditional Chinese',
        'fr': 'French', 'de': 'German', 'es': 'Spanish', 'it': 'Italian', 'pt-BR': 'Portuguese',
        'ru': 'Russian', 'ar': 'Arabic', 'hi': 'Hindi', 'id': 'Indonesian'
    }
    target_lang_name = HL_TO_LANG.get(args.hl, "English")

    for i, chunk in enumerate(batches):
        base_progress = 60 + int((i/total_chunks)*30)
        
        def batch_status_updater(msg):
            update_kitchen_status(db, f"Batch {i+1}/{total_chunks}: {msg}", base_progress)

        update_kitchen_status(db, f"Chef preparing Batch {i + 1}/{total_chunks} " + f"({len(chunk)} items)...", base_progress)
        
        print(f"Cooking dynamic batch {i+1} with {len(chunk)} items for {target_lang_name} using {args.model}...")
        
        # Pass the human-readable language name and model choice
        cooked = cook_batch(chunk, existing_titles, target_language=target_lang_name, status_callback=batch_status_updater, model=args.model)
        new_courses_data.extend(cooked)
        
        # Rate limit safety
        if i < total_chunks - 1:
            time.sleep(2)

    update_kitchen_status(db, f"Plating {len(new_courses_data)} new courses...", 90)

    # 4. Serve (Save to DB)
    for course_data in new_courses_data:
        try:
            # Robust Parsing for Sources
            # AI might return strings or objects. Standardize to objects.
            raw_sources = course_data.get('sources') or course_data.get('source_urls') or []
            clean_sources = []
            
            for s in raw_sources:
                if isinstance(s, str):
                    clean_sources.append({
                        'url': s, 
                        'title': 'Source Link', 
                        'source': new_url_domain(s)
                    })
                elif isinstance(s, dict):
                     # Ensure keys exist, check alternates
                     url_val = s.get('url') or s.get('link') or s.get('href') or '#'
                     clean_sources.append({
                         'url': url_val,
                         'title': s.get('title', 'Related Article'),
                         'source': s.get('source', new_url_domain(url_val))
                     })
            
            # Generate ID
            c_key = f"course_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            
            # Normalize Category
            cat_raw = course_data.get('category', 'course').lower().strip()
            # Remove strict allowed_cats filtering to support dynamic categories

            new_course = Course(
                course_key=c_key,
                title=course_data.get('title'),
                summary=course_data.get('summary'),
                entities_json=course_data.get('entities', []),
                topics_json=course_data.get('topics', []),
                source_urls=clean_sources, # Save the cleaned list of objects
                published_at=parse_date(course_data.get('representative_published_at')) or datetime.now(),
                category=cat_raw,
                language=args.hl # Capture the language setting
            )
            db.add(new_course)
            
            # Note: We aren't saving individual Articles anymore in this flow?
            # The spec implies "Course" is the primary unit. 
            # If we want to keep Articles table populated, we'd need to extract them from the 'raw_items' 
            # based on the group attribution returned by the AI.
            # BUT, the AI prompt didn't ask to map exact "raw indices" to the course.
            # Simplified Spec: Just save the Course. The source_urls are stored in the JSONB.
            # This is cleaner.
            
        except Exception as e:
            print(f"Failed to plate course: {e}")

    print(f"Service Complete. Added {len(new_courses_data)} courses.")
    print(f"DEBUG: new_courses_data length = {len(new_courses_data)}")
    print(f"DEBUG: new_courses_data is truthy? {bool(new_courses_data)}")
    
    # Generate AI commentary on today's news (before closing DB)
    if new_courses_data:
        try:
            print(f"DEBUG: Attempting to generate commentary with {len(new_courses_data)} courses...")
            from src.ingest.chef import generate_commentary
            print(f"Generating AI commentary using {args.model}...")
            commentary = generate_commentary(new_courses_data, target_lang_name, args.model)
            
            # Safe print for Unicode content
            try:
                print(f"Commentary generated: {commentary[:100]}...")
            except UnicodeEncodeError:
                print(f"Commentary generated: [Contains non-ASCII characters, length={len(commentary)}]")
            
            # Save commentary to services/kitchen directory
            commentary_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'latest_commentary.txt')
            print(f"Saving commentary to: {commentary_path}")
            with open(commentary_path, 'w', encoding='utf-8') as f:
                f.write(commentary)
            print(f"Commentary saved successfully!")
        except Exception as e:
            print(f"Failed to generate commentary: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No courses to generate commentary from.")

    db.commit()
    update_kitchen_status(db, "Service Complete!", 100, is_active=False)
    db.close()

def new_url_domain(url):
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace('www.', '')
    except:
        return 'News'

if __name__ == "__main__":
    main()
