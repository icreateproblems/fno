# Telegram Alert Setup Guide

## Quick Setup (5 minutes)

### Step 1: Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow prompts:
   - Enter bot name (e.g., "News Bot Monitor")
   - Enter bot username (e.g., "mynewsbot_alert_bot")
4. **Copy the bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Get Your Chat ID

**Method 1 (Easiest):**
1. Search for **@userinfobot** on Telegram
2. Send `/start`
3. Bot will reply with your chat ID (looks like: `123456789`)

**Method 2 (Alternative):**
1. Send any message to your bot
2. Open: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for `"chat":{"id":123456789}` in the response
4. Copy the number

### Step 3: Add to .env

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### Step 4: Test Alert

```bash
python -c "from app.alerts import alert_info; alert_info('🎉 News Bot is online!', {'Status': 'Ready'})"
```

You should receive a Telegram message!

---

## What You'll Receive

### 📨 Every Post (INFO)
```
ℹ️ INFO ALERT

✅ Post successful!

Headline: Breaking: Major tech company announces...

Details:
• Quality Score: 85/100
• Safety Score: 95/100
• Status: Posted to Instagram

🕐 2026-01-03 12:00:00 UTC
```

### ⏭️ Every Skip (INFO)
```
ℹ️ INFO ALERT

⏭️ Post skipped

Headline: Clickbait headline you won't believe...

Reason: Low quality score - Clickbait detected

Details:
• Quality Score: 35/100
• Action: Skipped

🕐 2026-01-03 12:05:00 UTC
```

### ⚠️ Content Safety Violations (WARNING)
```
⚠️ WARNING ALERT

Content safety violation blocked!

Headline: Controversial hateful content...

Violations:
• Hate speech pattern detected
• Misinformation indicators
• Unreliable source

Details:
• Violations: 3
• Action: Content blocked

🕐 2026-01-03 12:10:00 UTC
```

### ❌ API Failures (ERROR)
```
❌ ERROR ALERT

GROQ API failure!

Connection timeout after 3 retries

Details:
• API: GROQ
• Time: 12:15:00 UTC

🕐 2026-01-03 12:15:00 UTC
```

### 🚨 System Critical (CRITICAL)
```
🚨 CRITICAL ALERT

⚠️ No posts in 3 hours!
The bot may have stopped working.

Details:
• Last Post: 3h ago
• Action: Check logs and CI/CD

🕐 2026-01-03 12:20:00 UTC
```

### 📊 Daily Summary (INFO)
```
ℹ️ INFO ALERT

📊 Daily Summary

✅ Posts: 48
⏭️ Skipped: 12
❌ Errors: 2

Details:
• Success Rate: 80.0%
• Total Processed: 60

🕐 2026-01-03 23:59:59 UTC
```

---

## Alert Severity Levels

| Severity | Emoji | When | Action Needed |
|----------|-------|------|---------------|
| **INFO** | ℹ️ | Normal operations | None - just FYI |
| **WARNING** | ⚠️ | Minor issues, auto-recovered | Monitor trend |
| **ERROR** | ❌ | Failed operations | Check if persistent |
| **CRITICAL** | 🚨 | System down or major issue | Immediate action |

---

## Customizing Alerts

### Reduce Alert Frequency

If too many messages, edit `app/alerts.py`:

```python
# Only alert on skips with score < 30 (very low quality)
def alert_post_skipped(self, headline: str, score: int, reason: str):
    if score < 30:  # Add this condition
        message = f"⏭️ Post skipped\n\n*Headline:* {headline[:100]}..."
        # ... rest of code
```

### Disable Success Alerts

Comment out in `scripts/post_instagram.py`:

```python
# alert_manager.alert_post_success(story["headline"], score, safety_score)
```

### Add Custom Alerts

In your scripts:

```python
from app.alerts import alert_manager

# Custom info
alert_manager.send_alert("Custom message", "INFO", {"Key": "Value"})

# Quick helpers
from app.alerts import alert_info, alert_warning, alert_error, alert_critical

alert_info("Process started")
alert_warning("Low performance detected")
alert_error("Failed to connect")
alert_critical("System offline")
```

---

## Alert Schedule

**Real-time:**
- Every post (success/skip)
- Content safety violations
- API failures
- Error rate spikes

**Periodic:**
- Daily summary (11:59 PM UTC)
- Health check results (if monitoring enabled)
- Storage warnings (when >400MB)

**On-demand:**
- Manual health checks
- Test suite runs
- System monitoring

---

## Troubleshooting

### Not Receiving Alerts

**Check 1: Bot token valid?**
```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```
Should return bot info

**Check 2: Chat ID correct?**
```bash
# Send test message
python -c "from app.alerts import alert_manager; alert_manager.send_telegram_alert('Test', 'INFO')"
```

**Check 3: Environment loaded?**
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('TELEGRAM_BOT_TOKEN'))"
```

### Too Many Messages

1. **Disable success alerts** - Only get notified of issues
2. **Increase skip threshold** - Only alert on very low scores
3. **Batch alerts** - Collect and send summary every hour
4. **Filter by severity** - Only CRITICAL and ERROR

### Bot Not Responding

1. Make sure you sent `/start` to your bot first
2. Check bot is not blocked
3. Verify chat ID is correct (not group ID)
4. For group alerts, add bot to group and use group ID

---

## Privacy & Security

✅ **Safe:**
- Bot token = Your bot, your control
- Chat ID = Private conversation
- Messages sent directly to you only
- No data stored by Telegram bot

⚠️ **Keep Secret:**
- Never commit `.env` to git (already in `.gitignore`)
- Don't share bot token publicly
- Revoke token if compromised: @BotFather → `/mybots` → Select bot → Bot Settings → Revoke token

---

## Advanced: Group Alerts

To send alerts to a Telegram group:

1. Create a group
2. Add your bot to the group
3. Make bot admin (optional)
4. Get group ID:
   - Send message in group
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Look for `"chat":{"id":-123456789}` (negative number)
5. Use group ID as `TELEGRAM_CHAT_ID`

---

## Success!

Once configured, you'll receive:
- ✅ Every successful post with scores
- ⏭️ Every skipped post with reason
- ⚠️ All warnings and errors
- 🚨 Critical system alerts
- 📊 Daily summary

**No need to check logs manually - Telegram keeps you informed! 🎉**
