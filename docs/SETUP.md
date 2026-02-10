# Detailed Setup Guide

## Table of Contents
1. Prerequisites
2. Local Development Setup
3. Database Configuration
4. Instagram Authentication
5. Testing
6. CI/CD Deployment
7. Common Issues
8. Support

## 1) Prerequisites
- Python 3.10 or 3.11
- Git
- Internet connection
- Accounts: Instagram, Supabase (free), Groq (free). Optional: CircleCI (free), GitHub Actions (free).

## 2) Local Development Setup
```bash
# Clone
git clone https://github.com/sakshyambanjade/fastnewsorg.git
cd fastnewsorg

# Virtual environment
python -m venv venv
# Windows
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Environment file
cp .env.example .env
# Edit .env with your credentials
```

### Fonts (required for image rendering)
```bash
mkdir -p fonts
cd fonts
curl -L -o Inter.zip https://github.com/rsms/inter/releases/download/v3.19/Inter-3.19.zip
unzip Inter.zip
cp "Inter Desktop/Inter-Regular.ttf" .
cp "Inter Desktop/Inter-Bold.ttf" .
cd ..
```

## 3) Database Configuration (Supabase)
1. Create a project at https://supabase.com
2. Settings → API: copy URL and service_role key into `.env`
3. Run the schema: open Supabase SQL editor, paste contents of `schema/supabase_schema.sql`, run
4. Verify tables exist: `stories`, `posting_history`

## 4) Instagram Authentication
```bash
python scripts/ig_login.py
```
- Prompts for username/password
- Creates `ig_session.json`
- Validate session: `python scripts/ig_session_check.py`

## 5) Testing
```bash
# Verify env + connectivity
python scripts/test_setup.py

# Fetch news
python scripts/fetch_news.py

# Generate caption test
python -c "from scripts.groq_caption import generate_caption; print(generate_caption('Breaking: Major earthquake hits Japan'))"

# Post to Instagram (uses next story)
python scripts/post_instagram.py
```

## 6) CI/CD Deployment
- CircleCI (primary): every 30 minutes. See docs/CIRCLECI_SETUP.md
- GitHub Actions (secondary): every 90 minutes. See docs/GITHUB_ACTIONS_SETUP.md
- Required secrets: IG_SESSION_JSON, SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY

## 7) Common Issues
- ModuleNotFoundError: `pip install -r requirements.txt`
- Session invalid: `python scripts/ig_login.py`
- No stories fetched: check network/RSS sources, see logs/fetch_news.log
- Database timeout: verify SUPABASE_URL/KEY in .env
- AI caption fails: check GROQ_API_KEY, rate limits

## 8) Support
- Logs: check `logs/`
- Issues: https://github.com/sakshyambanjade/fastnewsorg/issues
