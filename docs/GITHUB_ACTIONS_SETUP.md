# GitHub Actions Setup Guide

## Overview
GitHub Actions (free 2,000 min/month) runs the bot every 90 minutes as a backup to CircleCI.

## Steps
1) Ensure workflow exists: `.github/workflows/news-bot.yml` (already present).
2) Encode Instagram session locally:
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("ig_session.json"))
```
Copy the output.
3) Add repository secrets (Settings → Secrets → Actions):
- IG_SESSION_JSON = <base64 ig_session.json>
- SUPABASE_URL = https://<project>.supabase.co
- SUPABASE_KEY = <service_role key>
- GROQ_API_KEY = <your groq key>
4) Enable Actions (Settings → Actions → General → Allow all actions).
5) Manually run once: Actions tab → News Bot → Run workflow.

## Schedule
Cron in `.github/workflows/news-bot.yml`:
- `13 0,2,4,6,8,10,12,14,16,18,20,22 * * *` (every 90 minutes)
- ~1,440 min/month (within 2,000 free minutes)

## Troubleshooting
- **Secrets not found**: verify names match exactly.
- **Session file 0 bytes**: regenerate base64; ensure no line breaks.
- **pip install failed**: rerun with `pip install --no-cache-dir -r requirements.txt`.
- **Instagram login failed**: re-run `scripts/ig_login.py`, re-encode, update secret.

## Monitoring
- Actions tab → workflow runs → view logs.
- Failed runs upload logs as artifacts.

## Usage Tuning
- Reduce frequency: change cron to `13 */3 * * *` (every 3 hours).
- Speed up builds: dependency cache is enabled via `actions/setup-python`.

## Support
- GitHub Actions docs: https://docs.github.com/actions
- Project issues: https://github.com/sakshyambanjade/fastnewsorg/issues
