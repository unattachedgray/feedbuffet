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
- **Project Init**: Created `apps/web` (Next.js), `services/kitchen` (Python).
- **News Client**: Implemented `news_client.py` (NewsData.io).
- **Database**: Models defined in `src/db/models.py`.
- **Grouping**: Jaccard similarity in `src/ingest/grouping.py`.
- **AI**: Gemini normalizer in `src/ingest/normalizer.py`.
- **Pipeline**: `run_kitchen.py` orchestration.
- **Fixes**: Resolved import paths, centralized `Base`, and added robust DB URL parsing.
- **Success**: Connected to Supabase via IPv4 Pooler. Pipeline successfully ingested 10 articles and performed initial grouping.
