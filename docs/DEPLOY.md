# 🚀 PRODUCTION DEPLOYMENT GUIDE

## ✅ **CURRENT STATUS: PRODUCTION READY!**

All systems verified and ready to deploy. Run `python verify_production_ready.py` anytime to check status.

---

## 📋 **BASE64 SESSION FOR CIRCLECI**

Copy this exact value to CircleCI:

```
ewogICAgInV1aWRzIjogewogICAgICAgICJwaG9uZV9pZCI6ICJkYmYzYTE4Zi0xYmM5LTQxZjQtYjM1Zi1hM2Y0OWE4N2M1ZDMiLAogICAgICAgICJ1dWlkIjogImFhOWQyNjI5LTU1ODItNDhmNi04ZGVlLWQ1MmU5ODljYzE0MCIsCiAgICAgICAgImNsaWVudF9zZXNzaW9uX2lkIjogIjMxNGMwM2ZjLTA1MTUtNDg0MS05M2I3LWVlMjgzOTcxNmY1YyIsCiAgICAgICAgImFkdmVydGlzaW5nX2lkIjogIjhhYjcwZDE3LTcyODgtNDk4ZS1hZjA2LWRhMGU5ZjFlNDExNSIsCiAgICAgICAgImFuZHJvaWRfZGV2aWNlX2lkIjogImFuZHJvaWQtYWMyZThjNmM1OTVjMTAwMyIsCiAgICAgICAgInJlcXVlc3RfaWQiOiAiNTZkZTRjNjAtYjhlNy00MWEzLWE0MDctZDUzZDc3MDNiMTIwIiwKICAgICAgICAidHJheV9zZXNzaW9uX2lkIjogImY3ZDQ2MDk4LThkOTQtNDczNC05YjNhLTk3MDkwOWZjZTM5NCIKICAgIH0sCiAgICAibWlkIjogImFWdEhLUUFCQUFFZHNfMXVyRlJzWFdYWHZLMXAiLAogICAgImlnX3VfcnVyIjogbnVsbCwKICAgICJpZ193d3dfY2xhaW0iOiBudWxsLAogICAgImF1dGhvcml6YXRpb25fZGF0YSI6IHsKICAgICAgICAiZHNfdXNlcl9pZCI6ICI4MDE2NzM3Njc4NyIsCiAgICAgICAgInNlc3Npb25pZCI6ICI4MDE2NzM3Njc4NyUzQVE1YldKMXF5T1JId0k1JTNBNCUzQUFZaHRaT0NmWFFhbzFvOWJwNEk1aTZ5RFJWRjE4QjFjS21EVXlxNzYzQSIKICAgIH0sCiAgICAiY29va2llcyI6IHt9LAogICAgImxhc3RfbG9naW4iOiAxNzY3NTg5NzAyLjQzNTk2NTMsCiAgICAiZGV2aWNlX3NldHRpbmdzIjogewogICAgICAgICJhcHBfdmVyc2lvbiI6ICIyNjkuMC4wLjE4Ljc1IiwKICAgICAgICAiYW5kcm9pZF92ZXJzaW9uIjogMjYsCiAgICAgICAgImFuZHJvaWRfcmVsZWFzZSI6ICI4LjAuMCIsCiAgICAgICAgImRwaSI6ICI0ODBkcGkiLAogICAgICAgICJyZXNvbHV0aW9uIjogIjEwODB4MTkyMCIsCiAgICAgICAgIm1hbnVmYWN0dXJlciI6ICJPbmVQbHVzIiwKICAgICAgICAiZGV2aWNlIjogImRldml0cm9uIiwKICAgICAgICAibW9kZWwiOiAiNlQgRGV2IiwKICAgICAgICAiY3B1IjogInFjb20iLAogICAgICAgICJ2ZXJzaW9uX2NvZGUiOiAiMzE0NjY1MjU2IgogICAgfSwKICAgICJ1c2VyX2FnZW50IjogIkluc3RhZ3JhbSAyNjkuMC4wLjE4Ljc1IEFuZHJvaWQgKDI2LzguMC4wOyA0ODBkcGk7IDEwODB4MTkyMDsgT25lUGx1czsgNlQgRGV2OyBkZXZpdHJvbjsgcWNvbTsgZW5fVVM7IDMxNDY2NTI1NikiLAogICAgImNvdW50cnkiOiAiVVMiLAogICAgImNvdW50cnlfY29kZSI6IDEsCiAgICAibG9jYWxlIjogImVuX1VTIiwKICAgICJ0aW1lem9uZV9vZmZzZXQiOiAtMTQ0MDAKfQ==
```

---

## 🚀 **DEPLOYMENT STEPS**

### **Step 1: Push Code to GitHub**

```bash
git push origin main
```

### **Step 2: Update CircleCI Environment Variable**

1. **Go to CircleCI Project Settings:**
   https://app.circleci.com/settings/project/github/sakshyambanjade/fastnewsorg/environment-variables

2. **Find `IG_SESSION_JSON` variable:**
   - If it exists: Click "Edit"
   - If not: Click "Add Environment Variable"

3. **Paste the base64 session:**
   - Variable name: `IG_SESSION_JSON`
   - Value: (paste the base64 string above)
   - **IMPORTANT:** Paste the ENTIRE string (no spaces, no line breaks)

4. **Click "Save"**

### **Step 3: Verify Other Environment Variables**

Make sure these are also set in CircleCI:
- ✅ `SUPABASE_URL`
- ✅ `SUPABASE_KEY`
- ✅ `GROQ_API_KEY`
- ✅ `TELEGRAM_BOT_TOKEN` (optional, for alerts)
- ✅ `TELEGRAM_CHAT_ID` (optional, for alerts)

### **Step 4: Trigger Pipeline**

**Option A - Automatic (Recommended):**
- Wait for next scheduled run (every 30 minutes: :00 and :30)
- Next run: Check CircleCI dashboard for timing

**Option B - Manual Trigger:**
```bash
# Make a trivial change to trigger pipeline
git commit --allow-empty -m "Trigger pipeline"
git push origin main
```

**Option C - CircleCI Dashboard:**
- Go to: https://app.circleci.com/pipelines/github/sakshyambanjade/fastnewsorg
- Click "Trigger Pipeline" (if available)

### **Step 5: Monitor First Run**

Watch the pipeline logs for:
```
✅ Instagram session ready!
✅ Instagram login successful
✅ Posted to Instagram: [post_id]
```

---

## 🔍 **WHAT WILL HAPPEN**

### **Automated Behavior:**

1. **Every 30 minutes** (at :00 and :30 of each hour)
2. **Random 60% skip chance** (anti-detection)
3. **Nepal timezone aware** (posts 7 AM - 10 PM Nepal time)
4. **Quality filtering** (only 80+ score stories)
5. **Max 20 posts per day**
6. **Human-like delays** (3-8 minutes between actions)
7. **Varied captions** (5 different styles)

### **Expected Daily Output:**

- **48 pipeline runs** (every 30 min)
- **~29 posting attempts** (60% skip)
- **15-18 actual posts** (after quality filter + daily limit)

---

## 📊 **MONITORING**

### **Check Pipeline Status:**
https://app.circleci.com/pipelines/github/sakshyambanjade/fastnewsorg

### **View Recent Logs:**
Click on latest workflow → `fetch-and-post` job → Check logs

### **Verify Posts:**
https://www.instagram.com/fastnewsorg/

### **Check Database:**
Log into Supabase to see:
- `stories` table (fetched stories)
- `posting_history` table (posted stories)

---

## 🛠️ **MAINTENANCE**

### **Session Renewal (Every 30 Days):**

```bash
# Regenerate session
python fix_instagram_session.py

# Copy the new base64 output
# Update CircleCI IG_SESSION_JSON variable
```

Set calendar reminder for **February 4, 2026**.

### **Verify System Health:**

```bash
python verify_production_ready.py
```

### **Check Logs:**

```bash
# Local logs (if running locally)
tail -f logs/news_bot.log

# CircleCI logs
# View in dashboard
```

---

## ⚠️ **TROUBLESHOOTING**

### **If Posts Don't Appear:**

1. **Check CircleCI logs** for errors
2. **Verify session** is valid (not expired)
3. **Check random skip** - might have skipped legitimately
4. **Verify Nepal time** - might be sleeping hours (1-6 AM)
5. **Check daily limit** - might have hit 20 posts

### **If Session Errors:**

```bash
# Regenerate session
python fix_instagram_session.py

# Update CircleCI variable with new base64
```

### **If No Stories Found:**

- RSS feeds might be down
- Quality filter too strict (80+ score)
- No breaking news at the moment

### **Emergency Stop:**

- Pause CircleCI workflow in dashboard
- Or delete/disable scheduled workflow

---

## ✅ **PRODUCTION CHECKLIST**

- [x] All environment variables set
- [x] Instagram session fresh (0 days old)
- [x] Database connection working
- [x] Groq API working
- [x] CircleCI config validated
- [x] Code pushed to main
- [ ] **→ Update IG_SESSION_JSON in CircleCI** ← DO THIS NOW
- [ ] Trigger first pipeline run
- [ ] Verify first successful post
- [ ] Set session renewal reminder (Feb 4, 2026)

---

## 🎉 **SUCCESS METRICS**

After deployment, you should see:

- ✅ **15-18 posts per day**
- ✅ **Posts during Nepal daytime hours**
- ✅ **Varied caption styles**
- ✅ **High-quality news stories only**
- ✅ **No Instagram bot detection**
- ✅ **Consistent schedule**

---

## 📞 **SUPPORT**

If issues persist:
1. Check CircleCI logs first
2. Run `verify_production_ready.py`
3. Check Instagram account for warnings
4. Review Supabase logs

---

**Deployed:** January 5, 2026  
**Session Valid Until:** February 4, 2026  
**Next Action:** Update CircleCI IG_SESSION_JSON variable
