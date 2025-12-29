# FeedBuffet Backend Specification (`backend_spec.md`)

## 1. System Overview

This repository contains two primary components:

1. **The Busser (API):** Serves news to the frontend and orchestrates the AI Analyst.
2. **The Kitchen (Worker):** A scheduled job that fetches raw RSS data, sends the **entire batch** to Gemini for clustering, and updates the database.

**Tech Stack:** Python 3.10+, FastAPI, Supabase, Google Gemini 3 Flash.

---

## 2. Component A: The Kitchen (Ingestion Worker)

*File: `src/kitchen/chef.py*`

**The "Batch Cooking" Mechanism:**
Instead of processing items one-by-one, we ingest the entire feed state at once to allow the AI to determine the true story count.

### The Workflow (Function: `run_cooking_cycle`)

1. **Fetch Ingredients:**
* Pull the specific Google News RSS feed (e.g., top 50-100 items).
* *Optimization:* Extract `title`, `link`, `snippet`, `source`, `published_date`, and `image_url`.


2. **Fetch "Menu" (Context Check):**
* Query Supabase for the **titles of active courses** published in the last 24 hours.
* *Goal:* Prevent re-cooking stories we already have.


3. **The Cook (Gemini 3 Flash Call):**
* **Input:**
* `raw_feed`: The list of 50+ new items.
* `existing_stories`: The list of titles currently on the "Menu".


* **Prompt Logic:**
> "Here is a list of raw news items and a list of stories we already have.
> 1. Group the raw items into unique stories.
> 2. **IGNORE** any groups that match the 'existing_stories' list (we don't want duplicates).
> 3. For the remaining new groups, synthesize a 'Course' object (Title, Summary, List of Source Links, Image URL).
> 4. Return a JSON list of NEW Courses only."
> 
> 




4. **Serve (DB Upsert):**
* Insert the returned JSON objects into the Supabase `courses` table.



---

## 3. Component B: The Busser (API & Analyst)

*File: `src/busser/routes.py*`

### Endpoint 1: Chat with Analyst (`POST /api/chat`)

**The Router/Server Logic:**

* **Input:** User message + History.
* **Process:**
1. **Load Context:** Fetch full text of active Courses from Supabase.
2. **Init Gemini:**
* **Model:** `gemini-3-flash-preview`
* **Tools:** `[GoogleSearchRetrieval]` (Native Grounding)
* **Lens (System Prompt):** "You are the FeedBuffet Analyst. Use the provided Context first. If the user asks for breaking news or topics NOT in the context, you MUST trigger the Google Search tool."


3. **Execute:** Pass to Gemini. The model decides whether to talk (Context) or fetch (Tool).


* **Output:** Final answer.

### Endpoint 2: Get Menu (`GET /api/news`)

* **Process:** Return the current `courses` from Supabase (created by the Kitchen).

---

## 4. Database Schema (Supabase)

**Table: `courses**`

* `id` (uuid, primary key)
* `title` (text)
* `summary` (text)
* `entities` (jsonb) -> `['Nvidia', 'Jensen Huang']`
* `sources` (jsonb) -> `[{'url': '...', 'name': 'CNBC'}]`
* `main_image_url` (text)
* `published_at` (timestamp)
* `embedding` (vector) -> *Optional for future semantic search*

---

## 5. Development Roadmap for Agent

1. **Setup:** Create `src/kitchen`, `src/busser`, `src/core`. Connect `database.py` to Supabase.
2. **The Kitchen (First):**
* Install `feedparser`.
* Implement `fetch_rss()`.
* Implement `cook_with_gemini()` using the **Batch + De-dupe** prompt logic.
* *Test:* Run the script manually and check Supabase for clean, non-duplicate rows.


3. **The Busser (Second):**
* Setup FastAPI.
* Create `/api/chat` with Gemini + Tools.
* *Test:* Connect a simple frontend or `curl` to chat with the news.