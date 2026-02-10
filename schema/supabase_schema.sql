CREATE TABLE IF NOT EXISTS stories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  headline TEXT NOT NULL,
  description TEXT,
  content_hash VARCHAR(64) UNIQUE NOT NULL,
  source VARCHAR(100) NOT NULL,
  category VARCHAR(50) DEFAULT 'general',
  url TEXT,
  image_url TEXT,
  published_at TIMESTAMP,
  fetched_at TIMESTAMP DEFAULT NOW(),
  is_validated BOOLEAN DEFAULT FALSE,
  published BOOLEAN DEFAULT FALSE,
  platform VARCHAR(50) DEFAULT 'instagram',
  post_id TEXT,
  rejected BOOLEAN DEFAULT FALSE,
  posted_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stories_hash ON stories(content_hash);
CREATE INDEX IF NOT EXISTS idx_stories_validated ON stories(is_validated);
CREATE INDEX IF NOT EXISTS idx_stories_published ON stories(published);
CREATE INDEX IF NOT EXISTS idx_stories_published_at ON stories(published_at DESC);

ALTER TABLE stories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public can read validated stories"
ON stories FOR SELECT
USING (is_validated = true);

CREATE POLICY "Service role full access"
ON stories
USING (auth.jwt() ->> 'role' = 'service_role')
WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

CREATE TABLE IF NOT EXISTS posting_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  story_id UUID REFERENCES stories(id) ON DELETE CASCADE,
  platform VARCHAR(50) DEFAULT 'instagram',
  posted_at TIMESTAMP DEFAULT NOW(),
  success BOOLEAN NOT NULL,
  post_id TEXT,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_posting_history_time ON posting_history(posted_at DESC);

ALTER TABLE posting_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access on posting_history"
ON posting_history
USING (auth.jwt() ->> 'role' = 'service_role')
WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
  DELETE FROM stories WHERE fetched_at < NOW() - INTERVAL '7 days';
  DELETE FROM posting_history WHERE created_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;
