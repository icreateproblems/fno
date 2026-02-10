# Multi-CircleCI Account Strategy

## Goal
Use multiple CircleCI accounts to get more free compute minutes while posting to the same Instagram account.

## Benefits
- **Account 1**: 6,000 min/month
- **Account 2**: 6,000 min/month  
- **Account 3**: 6,000 min/month
- **Total**: 18,000 min/month (3x more capacity!)

## Setup Instructions

### 1. Current Account (Account 1)
- **Repo**: sakshyambanjade/fastnewsorg
- **Schedule**: Every 20 minutes at :00, :20, :40
- **Keeps current setup**

### 2. Account 2 Setup

**Step 1: Create new GitHub account**
- Email: your_email+circleci2@gmail.com
- Username: sakshyambanjade2 (or similar)

**Step 2: Fork/Create duplicate repo**
```bash
# Option A: Fork the repo to new account
# Go to https://github.com/sakshyambanjade/fastnewsorg
# Click "Fork" and select your new account

# Option B: Push to new repo
git remote add account2 https://github.com/sakshyambanjade2/fastnewsorg.git
git push account2 main
```

**Step 3: Update .circleci/config.yml schedule**
Change line 79 from:
```yaml
cron: "0,20,40 * * * *"   # :00, :20, :40
```
To:
```yaml
cron: "10,30,50 * * * *"   # :10, :30, :50
```

**Step 4: Connect to CircleCI**
- Sign up for CircleCI with NEW GitHub account
- Connect the forked repository
- Add same 4 environment variables:
  - SUPABASE_URL
  - SUPABASE_KEY
  - GROQ_API_KEY
  - IG_SESSION_JSON (same as Account 1!)

### 3. Account 3 Setup (Optional)

**Schedule options:**
- `"5,25,45 * * * *"` - Every 20 min at :05, :25, :45
- `"15,35,55 * * * *"` - Every 20 min at :15, :35, :55

## Posting Schedule

With 2 accounts:
```
Account 1: 12:00, 12:20, 12:40, 1:00, 1:20, 1:40...
Account 2: 12:10, 12:30, 12:50, 1:10, 1:30, 1:50...
Result: Post every 10 minutes!
```

With 3 accounts:
```
Account 1: :00, :20, :40
Account 2: :10, :30, :50
Account 3: :05, :25, :45 or :15, :35, :55
Result: Post every 5-10 minutes!
```

## Rate Limit Management

Instagram allows **3 posts/hour, 60/day** per account. With staggered schedules:
- 2 CircleCI accounts = Up to 6 attempts/hour (but still limited to 3 successful posts/hour by Instagram)
- The database `posted` flag prevents duplicate posts
- If one CircleCI run fails, another picks it up

## Important Notes

1. **Same credentials everywhere**: All CircleCI accounts use the same:
   - Supabase database (shared story queue)
   - Groq API key
   - Instagram session (same IG account)

2. **Database handles deduplication**: The `posted` flag ensures no story is posted twice

3. **Cost**: All accounts use free tiers (no cost)

4. **Maintenance**: Update all repos when you make code changes

## Quick Start

**For Account 2:**
```bash
# 1. Create config for alternate schedule
cp .circleci/config.yml .circleci/config-account2.yml

# 2. Edit the cron schedule
# Change: cron: "0,20,40 * * * *"
# To: cron: "10,30,50 * * * *"

# 3. Fork repo to new GitHub account
# 4. Push config-account2.yml as config.yml to forked repo
# 5. Set up CircleCI with same environment variables
```
