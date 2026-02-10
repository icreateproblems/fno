# Database Guide

This project uses Supabase (PostgreSQL). The schema is defined in `schema/supabase_schema.sql` and summarized here.

## Tables

### stories
- id (uuid, primary key)
- headline (text)
- description (text)
- content_hash (text, unique)
- source (text)
- category (text)
- url (text)
- published_at (timestamp with time zone)
- is_validated (boolean, default false)
- posted (boolean, default false)
- created_at (timestamp with time zone, default now())

### posting_history
- id (uuid, primary key)
- story_id (uuid, references stories.id)
- success (boolean)
- error_message (text)
- created_at (timestamp with time zone, default now())

## Schema Deployment

Run the schema in Supabase SQL editor:

```sql
-- Execute the whole file
-- File: schema/supabase_schema.sql
```

Or from CLI:

```bash
psql "$SUPABASE_URL" < schema/supabase_schema.sql
```

## Constraints & Indices
- `content_hash` UNIQUE on stories (deduplicates identical headlines)
- Foreign key from posting_history.story_id to stories.id

## Data Flow
1. `scripts/fetch_news.py`
   - Fetches RSS
   - Validates stories
   - Batch inserts into `stories` (deduplicated by content_hash)
   - Marks is_validated true (auto-approval)
2. `scripts/post_instagram.py`
   - Reads next validated, unposted story
   - Applies rate limits
   - Posts to Instagram, writes to `posting_history`
   - Marks story as posted on success

## Maintenance
- Old story cleanup handled in `fetch_news.py` via `cleanup_old_stories`
- Content hash prevents duplicates across sources

## Local Testing

```bash
# Check connectivity
python scripts/test_setup.py

# Dry-run fetch (writes to DB)
python scripts/fetch_news.py

# Inspect tables via Supabase dashboard
```

## Supabase Settings
- Project URL and service_role key stored in `.env`
- RLS disabled (service_role bypasses) — keep keys secret

## Backups
- Supabase free tier provides point-in-time recovery within limits; consider periodic exports for safety.
