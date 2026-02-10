# 🚀 CI/CD Setup Guide - Dual Platform Strategy

This guide will help you set up **both CircleCI and GitHub Actions** for automated Instagram posting.

---

## 📋 Prerequisites

Before starting, gather these values from your `.env` file:

```bash
SUPABASE_URL=https://aafuvuzbbqxlmkbkuypp.supabase.co
SUPABASE_KEY=eyJhbGciOi... (your key)
GROQ_API_KEY=gsk_AnUikO... (your key)
INSTAGRAM_ACCESS_TOKEN=EAAMTr9ZCfa90... (your token)
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841480183610922
INSTAGRAM_APP_ID=2180308679168301
IMGBB_API_KEY=7b0ac486e9... (your key)
```

---

## 🔵 Part 1: GitHub Actions Setup

### Step 1: Enable GitHub Actions

1. Go to your GitHub repository: https://github.com/yaknihaa/my_project
2. Click **Settings** → **Actions** → **General**
3. Under "Actions permissions", select **"Allow all actions and reusable workflows"**
4. Click **Save**

### Step 2: Add Secrets

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"** and add each of these:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `SUPABASE_URL` | `https://aafuvuzbbqxlmkbkuypp.supabase.co` | Database URL |
| `SUPABASE_KEY` | Your Supabase key | Database auth |
| `GROQ_API_KEY` | Your Groq key | AI caption generation |
| `INSTAGRAM_ACCESS_TOKEN` | Your Instagram token | Graph API auth |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | `17841480183610922` | Instagram account |
| `INSTAGRAM_APP_ID` | `2180308679168301` | Facebook app |
| `IMGBB_API_KEY` | Your imgbb key | Image hosting |

### Step 3: Test the Workflow

1. Go to **Actions** tab in GitHub
2. Click on **"News Bot - GitHub Actions"**
3. Click **"Run workflow"** → **"Run workflow"**
4. Wait 3-5 minutes and check the results

✅ **Schedule**: Runs every 90 minutes (16 times/day)

---

## 🟠 Part 2: CircleCI Setup

### Step 1: Connect Repository

1. Go to https://circleci.com/vcs-authorize/
2. Sign in with GitHub
3. Click **"Set Up Project"** for `yaknihaa/my_project`
4. Select **"Use Existing Config"** (we already have `.circleci/config.yml`)
5. Click **"Set Up Project"**

### Step 2: Add Environment Variables

1. In CircleCI, go to **Project Settings** (gear icon)
2. Click **"Environment Variables"** in the left menu
3. Click **"Add Environment Variable"** for each:

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `SUPABASE_URL` | `https://aafuvuzbbqxlmkbkuypp.supabase.co` | Database URL |
| `SUPABASE_KEY` | Your Supabase key | Database auth |
| `GROQ_API_KEY` | Your Groq key | AI caption generation |
| `INSTAGRAM_ACCESS_TOKEN` | Your Instagram token | Graph API auth |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | `17841480183610922` | Instagram account |
| `INSTAGRAM_APP_ID` | `2180308679168301` | Facebook app |
| `IMGBB_API_KEY` | Your imgbb key | Image hosting |

### Step 3: Trigger First Run

1. Go to **Dashboard** → **Your Project**
2. Click **"Trigger Pipeline"**
3. Click **"Trigger Pipeline"** again to confirm
4. Wait 3-5 minutes and check the results

✅ **Schedule**: Runs every 30 minutes (48 times/day)

---

## 📊 Verification Checklist

Use this checklist to verify everything is working:

### GitHub Actions
- [ ] Repository secrets added (7 secrets)
- [ ] Actions enabled in repository settings
- [ ] First manual run completed successfully
- [ ] Scheduled runs appear in Actions tab
- [ ] No errors in workflow logs

### CircleCI
- [ ] Repository connected to CircleCI
- [ ] Environment variables added (7 variables)
- [ ] First pipeline triggered manually
- [ ] Pipeline completed successfully
- [ ] No errors in build logs

### System Health
- [ ] Instagram Graph API token is valid
- [ ] Database connection working
- [ ] News fetching successful
- [ ] Instagram posting successful
- [ ] Both platforms running on schedule

---

## 🎯 Expected Behavior

### Posting Frequency

**Combined Strategy:**
- CircleCI: 48 runs/day (every 30 min)
- GitHub Actions: 16 runs/day (every 90 min)
- **Total**: ~64 attempts/day
- **Actual posts**: ~18-20/day (due to quality filters)

### Current Configuration

**CircleCI Schedule:**
```yaml
cron: "0,30 * * * *"  # :00 and :30 every hour
```

**GitHub Actions Schedule:**
```yaml
cron: '13 0,2,4,6,8,10,12,14,16,18,20,22 * * *'  # :13 every 2 hours
```

---

## 🔍 Monitoring & Troubleshooting

### GitHub Actions Monitoring

**View Logs:**
1. Go to **Actions** tab
2. Click on a workflow run
3. Click on **"fetch-and-post"** job
4. Expand each step to view logs

**Common Issues:**
- ❌ `Secret not found` → Verify secret names match exactly
- ❌ `API rate limit` → Normal, system will retry
- ❌ `No stories to post` → Normal, waiting for quality content

### CircleCI Monitoring

**View Logs:**
1. Go to https://app.circleci.com/pipelines/github/yaknihaa/my_project
2. Click on a pipeline run
3. Click on **"fetch-and-post"** job
4. View step-by-step logs

**Common Issues:**
- ❌ `Environment variable not set` → Add in Project Settings
- ❌ `Build failed` → Check logs for specific error
- ❌ `Rate limit exceeded` → Groq API limit, will auto-retry

### Usage Monitoring

**CircleCI Credits:**
- Dashboard → Insights → Resource Usage
- Monitor monthly minutes used
- Current: ~5,840 min/month (within 6,000 free)

**GitHub Actions Minutes:**
- Settings → Billing → Plans and usage
- Monitor Actions minutes used
- Current: ~1,946 min/month (within 2,000 free)

---

## 💡 Pro Tips

### Optimize Costs
- ✅ Both platforms stay within free tiers
- ✅ Caching enabled for faster builds
- ✅ Small resource class in CircleCI
- ✅ Connection pooling in database

### Improve Posting Success
- Use quality news sources
- Let AI filter low-quality content
- Monitor Groq API rate limits
- Refresh Instagram token monthly

### Failover Strategy
- If CircleCI fails → GitHub Actions continues
- If GitHub Actions fails → CircleCI continues
- Database deduplicates automatically
- No duplicate posts (content hash check)

---

## 📞 Support

**Documentation:**
- [GitHub Actions Docs](https://docs.github.com/actions)
- [CircleCI Docs](https://circleci.com/docs/)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)

**Project Issues:**
- https://github.com/yaknihaa/my_project/issues

**Quick Commands:**
```bash
# Test locally
python verify_instagram_setup.py
python scripts/fetch_news.py
python scripts/post_instagram_graph.py

# Check system health
python verify_production_ready.py
```

---

## ✅ Success Criteria

You're ready for production when:

- [x] All GitHub Actions secrets configured
- [x] All CircleCI environment variables configured
- [x] Both platforms running successfully
- [x] Instagram posts appearing on @fastnewsorg
- [x] No errors in CI/CD logs
- [x] Monitoring dashboards accessible
- [x] System posting 18-20 times/day

---

**🎉 Congratulations! Your automated Instagram news bot is now live!**
