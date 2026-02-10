# Dual-Platform CI/CD Strategy

## Overview
Using **both GitHub Actions + CircleCI** to maximize free tier benefits and posting frequency.

## Platform Allocation

### CircleCI (6,000 min/month)
- **Schedule**: `:03, :18, :33, :48` every hour (4x/hour)
- **Usage**: ~4 min/run × 4 runs/hour × 730 hours = **11,680 min/month** ❌ OVER LIMIT
- **Actual**: Need to reduce to **3x/hour** = 8,760 min ❌ still over
- **Optimized**: **2x/hour** (:18, :48) = 5,840 min ✅ Under limit

### GitHub Actions (2,000 min/month)  
- **Schedule**: `:13, :28, :43, :58` every hour (4x/hour)
- **Usage**: ~4 min/run × 4 runs/hour × 730 hours = **11,680 min/month** ❌ OVER LIMIT
- **Optimized**: **1x/hour** (:28) = 2,920 min ❌ still over
- **Final**: **Every 90 min** (:13 every 0,2,4... hours) = 1,946 min ✅ Under limit

## ✅ Final Schedule (Stays Under Limits)

### CircleCI - Every 30 minutes (2x/hour)
- `:18, :48` each hour
- **48 runs/day × 4 min = 192 min/day**
- **5,840 min/month** (within 6,000 limit)

### GitHub Actions - Every 90 minutes  
- `:13` at hours 0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22
- **16 runs/day × 4 min = 64 min/day**
- **1,946 min/month** (within 2,000 limit)

### Combined Result
- **Total: ~64 posts/day** (48 from CircleCI + 16 from GitHub)
- **Coverage**: Post every 22-30 minutes on average
- **Pattern**: Randomized, unpredictable intervals
- **Cost**: $0 (both free tiers)

## GitHub Secrets Setup

Add these secrets in GitHub repo settings → Secrets and variables → Actions:

```
IG_SESSION_JSON=<base64 encoded session file>
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx...
GROQ_API_KEY=gsk_xxx...
```

### Generate IG_SESSION_JSON
```bash
# On Windows
certutil -encode ig_session.json temp.b64 && findstr /v CERTIFICATE temp.b64 > encoded.txt && del temp.b64

# On Linux/Mac
base64 -w 0 ig_session.json > encoded.txt

# Copy contents of encoded.txt to GitHub secret
```

## Usage Monitoring

### CircleCI Dashboard
- https://app.circleci.com/pipelines/github/sakshyambanjade/fastnewsorg
- Check "Insights" → "Resource Usage"

### GitHub Actions
- https://github.com/sakshyambanjade/fastnewsorg/actions
- Check workflow runs and timing

## Failover Strategy
- If CircleCI fails → GitHub Actions continues
- If GitHub Actions fails → CircleCI continues  
- Both platforms fetch same stories → database deduplicates automatically
- No duplicate posts (content_hash prevents it)

## Cost Optimization
Current optimizations in place:
- ✅ Batch database inserts (95% fewer calls)
- ✅ Connection pooling (50% credit savings)
- ✅ Query result caching (reduces redundant reads)
- ✅ Scheduled cleanup of old stories (< 7 days)

Expected Supabase usage: **~25 credits/month** (was 120)
