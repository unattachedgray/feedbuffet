# FeedBuffet — Development Plan (Gemini 3 Flash + Free-Tier Friendly)

## Project Goal
Build a backend-first system that:
1) ingests news from NewsData.io
2) groups related articles into **Courses** (one story across sources)
3) curates Courses into **Plates** (rule-driven curation)
4) lets a **Critic** (AI chat) analyze a Plate using a **Sauce** (lens)

This is designed to run on free tiers now and scale to production later with minimal re-architecture.

---

## Locked Vocabulary
- **Plate**: curated, shareable news collection (public/unlisted/private)
- **Course**: grouped story (multi-source)
- **Sauce**: lens / interpretation spec (structured)
- **Critic**: conversational AI scoped to a Plate + Sauce

---

## Hosting & Services (Free Tier Now → Pro Later)

### Frontend + API hosting
- **Vercel** (Next.js app + API routes)
  - Hobby plan is free (good for personal/hobby use). :contentReference[oaicite:0]{index=0}

### Database + Auth + Storage (optional)
- **Supabase**
  - Postgres DB + Auth + Storage + Edge Functions
  - Free tier includes 500MB DB + 1GB file storage; free projects may pause after inactivity. :contentReference[oaicite:1]{index=1}

### News ingestion
- **NewsData.io**
  - Free tier: 200 credits/day; 10 articles per credit; 12-hour delay on articles. :contentReference[oaicite:2]{index=2}

### Optional (recommended) free-tier add-ons
- **Upstash Redis** (rate limiting + small caches)
  - Free tier: 256MB and 500K commands/month. :contentReference[oaicite:3]{index=3}
- (Later) background jobs / cron:
  - Vercel Cron OR Supabase scheduled jobs (pick one when needed)

---

## Tech Stack
- **Backend language:** Python 3.10+ (local dev + job runner)
- **Web/API:** Next.js on Vercel (API routes)
- **AI:** Google Gemini 3 Flash (`gemini-3-flash-preview`)
- **DB:** Supabase Postgres (dev/prod). SQLite allowed for local-only dev.
- **ORM:** SQLAlchemy + Alembic migrations (recommended)
- **HTTP:** `requests` for NewsData.io

---

## Repo Layout (suggested)
- `/apps/web` (Next.js on Vercel)
  - `/app` UI pages (later)
  - `/app/api/*` API routes (Plate, Course, Critic endpoints)
- `/services/kitchen` (Python ingestion + grouping)
  - `src/ingest/*`
  - `src/ai/*`
  - `src/db/*`
  - `run_kitchen.py`
- `/shared`
  - schemas (JSON schemas), prompt templates, constants

---

## Environment Variables
- `NEWSDATA_API_KEY`
- `GEMINI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` (server-side only)
- `RAW_DUMP_DIR=data/raw`
- (Optional) `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`

Never commit secrets.

---

# Phase 1 — The Kitchen (Ingestion & Course Creation)
Goal: Turn raw articles into normalized **Articles**, then grouped **Courses**.

## Step 1.1 News Client
**File:** `services/kitchen/src/ingest/news_client.py`
- `fetch_latest_news(query="technology", page=None, max_pages=3) -> list[dict]`
- Use `requests`
- Handle pagination
- Save raw JSON responses to:
  - `data/raw/YYYYMMDD/<run_id>_pageN.json`

Notes:
- NewsData free tier has limits and 12-hour delay. :contentReference[oaicite:4]{index=4}

## Step 1.2 Database Schema (Supabase-ready)
Implement these tables (either SQL migrations or SQLAlchemy models).

### `articles`
- `id` UUID PK
- `url` TEXT UNIQUE
- `source_name` TEXT
- `title` TEXT
- `description` TEXT
- `published_at` TIMESTAMP
- `language` TEXT NULL
- `ingested_at` TIMESTAMP default now()

### `courses`
- `id` UUID PK
- `course_key` TEXT UNIQUE  (stable key to prevent duplicates)
- `title` TEXT
- `summary` TEXT
- `entities_json` JSONB
- `topics_json` JSONB NULL
- `source_urls` JSONB  (urls merged into this course)
- `published_at` TIMESTAMP
- `created_at` TIMESTAMP default now()

### `course_articles`
- `course_id` FK
- `article_id` FK
- unique(course_id, article_id)

### `plates`
- `id` UUID PK
- `name` TEXT UNIQUE
- `visibility` TEXT (public/unlisted/private)
- `rules_json` JSONB
- `created_at` TIMESTAMP

### `sauces`
- `id` UUID PK
- `plate_id` FK
- `name` TEXT
- `definition_json` JSONB (structured sauce spec)
- `is_default` BOOL
- `created_at` TIMESTAMP

### `plate_cache`
- `plate_id` FK UNIQUE
- `cache_provider` TEXT ("gemini")
- `cache_name` TEXT
- `updated_at` TIMESTAMP
- `expires_at` TIMESTAMP NULL

### (Recommended for Critic)
`critic_sessions`, `critic_messages` for chat history.

## Step 1.3 Grouping (Pre-AI)
**File:** `services/kitchen/src/ingest/grouping.py`
Goal: Reduce LLM cost and keep grouping stable.

MVP algorithm:
- bucket by 6–12 hour time window
- compute token set from normalized titles
- group by Jaccard similarity threshold (e.g. >= 0.35)
- cap group size to 5–12 articles

Output: list of groups of article IDs.

## Step 1.4 AI Normalizer → Course
**File:** `services/kitchen/src/ingest/normalizer.py`
Input: one group of 5–12 articles (title + description + source + published_at + url)
Output: STRICT JSON:
```json
{
  "course_title": "...",
  "course_summary": "...",
  "entities": ["..."],
  "topics": ["..."],
  "representative_published_at": "ISO8601",
  "source_urls": ["..."]
}
```

# Phase 1 Development Logs

## Initial Implementation (Completed)
- **Project Init**: Created `apps/web` (Next.js), `services/kitchen` (Python).
- **News Client**: Implemented `GoogleNewsClient` (Google News RSS) replacing NewsData.io for better free-tier access.
- **Database**: Models defined in `src/db/models.py` with Supabase integration.
- **AI Chef**: Implemented batch processing with `chef.py` using Gemini 3 Flash for semantic grouping and deduplication.
- **Pipeline**: `run_kitchen.py` orchestration with real-time status reporting.
- **Fixes**: Resolved import paths, centralized `Base`, and added robust DB URL parsing.
- **Success**: Connected to Supabase via IPv4 Pooler. Pipeline successfully ingested and processed news.

## Session 2025-12-28 (Major UX & Performance Enhancements)

### Core Features Implemented
1. **Multi-Tab Feed Management ("Plates")**
   - Implemented `PlateManagerWrapper` and `PlateTabs` components
   - Tabs positioned in navbar with auto-numbering (1, 2, 3...)
   - Double-click to rename tabs
   - Click "+" to add new tabs
   - Delete tabs with confirmation (hover to reveal "x" button)
   - Persistent state via localStorage

2. **Language & Regional Settings**
   - Added `SettingsMenu` with language (hl), region (gl), and category selection
   - Integrated with Google News RSS API for localized content
   - Added `language` column to `courses` table for future filtering
   - AI generates titles/summaries in user's selected language

3. **Real-Time Status Updates**
   - Implemented `KitchenStatus` table for live progress tracking
   - `RefreshButton` polls `/api/status` and displays granular updates
   - Status shows: category fetching, batch processing, AI consultation
   - Added grace period to prevent race conditions on startup

4. **Performance Optimizations**
   - Increased batch size to 200k characters (minimizes API calls)
   - Added status callbacks within `cook_batch` for granular updates
   - Service Role Key for status API to bypass RLS
   - Fixed refresh button to work on first click

### Bug Fixes
- Fixed `user_interactions` table null constraint error (explicit UUID generation)
- Fixed course title links to navigate to actual article URLs
- Fixed "Top News" category fetching for non-English locales
- Fixed purge functionality with correct deletion order and RLS bypass
- Fixed refresh button "undefined" display and race conditions
- Fixed CourseFeed data structure to match Supabase column names

### Database Migrations
- `migrate_v3.py`: Added `KitchenStatus` table
- `migrate_v4.py`: Added `language` column to `courses` table

### API Enhancements
- `/api/ingest`: Now accepts `categories` array for multi-category fetching
- `/api/status`: Uses Service Role Key for reliable status reads
- `/api/track`: Tracks user interactions with encryption
- `/api/purge`: Robust cache clearing with proper FK constraint handling

## Next Steps

### Immediate Priorities
1. **Performance Monitoring**: Monitor Gemini API rate limits and optimize batch processing
2. **Error Handling**: Add retry logic and better error messages for failed ingestion
3. **Plate-Specific Feeds**: Implement per-plate content filtering and caching
4. **URL Structure**: Implement shareable feed URLs (e.g., `/feed/[unique-id]`)

### Feature Roadmap
1. **Sauces (Lenses)**: Implement AI analysis perspectives
2. **Critic Chat**: Scoped conversational AI for each plate
3. **User Authentication**: Replace localStorage with proper auth (Google OAuth)
4. **Personalization**: Use interaction data for content recommendations
5. **Advanced Plate Management**: Reordering, archiving, sharing settings
6. **Category Management**: Allow users to define custom categories
7. **Multi-language Support**: Full i18n for UI (currently content-only)

### Technical Debt
- Remove duplicate `published_at` and `language` column definitions in `models.py`
- Implement proper error boundaries in React components
- Add comprehensive logging for kitchen service
- Set up automated testing for critical paths
- Implement proper session management for Critic chat

