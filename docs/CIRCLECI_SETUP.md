# CircleCI Setup Guide

## Overview
CircleCI (free 6,000 min/month) runs the bot every 30 minutes.

## Steps
1) Log in at https://circleci.com/vcs-authorize/ and connect the GitHub repo.
2) Select **Use Existing Config** (config is in `.circleci/config.yml`).
3) Encode Instagram session locally:
```bash
python encode_session.py
```
Copy the generated base64 string.
4) Add environment variables in CircleCI Project Settings → Environment Variables:
- IG_SESSION_JSON = <base64 ig_session.json>
- SUPABASE_URL = https://<project>.supabase.co
- SUPABASE_KEY = <service_role key>
- GROQ_API_KEY = <your groq key>
5) Trigger a pipeline manually to verify.

## Schedule
Configured in `.circleci/config.yml`:
- Cron: `18,48 * * * *` (twice per hour)
- ~5,760 min/month (within free tier)

## Troubleshooting
- **IG_SESSION_JSON empty/0 bytes**: regenerate with `python encode_session.py`, ensure no line breaks.
- **DB connection failed**: check SUPABASE_URL/KEY, test with `curl "$SUPABASE_URL/rest/v1/stories?limit=1" -H "apikey: $SUPABASE_KEY"`.
- **No stories to post**: normal when no new validated stories.
- **Rate limit exceeded**: wait 60 minutes (3 posts/hour cap).

## Tips
- Caching is enabled for pip.
- Resource class is `small` to save minutes.
- Adjust frequency by editing cron in `.circleci/config.yml`.

## Support
- CircleCI docs: https://circleci.com/docs/
- Project issues: https://github.com/sakshyambanjade/fastnewsorg/issues
