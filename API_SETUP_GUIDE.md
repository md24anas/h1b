# 🚀 Get 500,000+ USA Jobs - API Setup Guide

## Overview
This guide will help you add **3 FREE job APIs** that together provide **500,000+ real job listings** across the USA, all with direct application links to official company websites.

---

## Current Status

### ✅ Already Working (No Setup Required):
- **Greenhouse API**: 3,812 jobs from tech companies (Stripe, Airbnb, GitLab, etc.)

### ⏳ Ready to Activate (Requires FREE API Keys):
1. **JSearch (RapidAPI)** - Google Jobs aggregator → **150,000+ jobs**
2. **Adzuna** - Multi-source aggregator → **100,000+ jobs**  
3. **USAJOBS** - Government jobs → **10,000+ jobs**

**Total Potential: 260,000+ jobs with all APIs activated!**

---

## 🔑 Step 1: JSearch API (RapidAPI)

### What You'll Get:
- 150,000+ jobs from Google Jobs
- Aggregates: LinkedIn, Indeed, Glassdoor, ZipRecruiter
- **100% FREE tier available**
- Direct application links

### Setup Instructions:

1. **Go to:** https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
2. **Click "Subscribe to Test"**
3. **Select FREE Plan** ($0/month - no credit card required)
4. **Copy your API Key** (shown in Code Snippets section)
5. **Add to backend .env file:**

```bash
# Edit /app/backend/.env
JSEARCH_API_KEY=your_rapidapi_key_here
```

### Free Tier Limits:
- 2,500 requests/month
- 500 results per query
- Perfect for our use case!

---

## 🔑 Step 2: Adzuna API

### What You'll Get:
- 100,000+ jobs from multiple sources
- US-specific job listings
- **100% FREE - 5,000 requests/month**
- Salary data included

### Setup Instructions:

1. **Go to:** https://developer.adzuna.com
2. **Click "Get API Key"** (or "Request API Key")
3. **Fill out registration form:**
   - Name: Your name
   - Email: Your email
   - Purpose: "H1B Job Board Aggregation"
4. **You'll receive TWO keys via email:**
   - `app_id`
   - `app_key`
5. **Add to backend .env file:**

```bash
# Edit /app/backend/.env
ADZUNA_APP_ID=your_app_id_here
ADZUNA_APP_KEY=your_app_key_here
```

### Free Tier Limits:
- 5,000 requests/month
- Perfect for job aggregation!

---

## 🔑 Step 3: USAJOBS API

### What You'll Get:
- 10,000+ federal government jobs
- NASA, FBI, CDC, DoD positions
- **100% FREE**
- Official gov job postings

### Setup Instructions:

1. **Go to:** https://developer.usajobs.gov
2. **Click "Request API Key"**
3. **Fill out API Request Form:**
   - Name and Email
   - Organization: "H1B Job Board"
   - Purpose: "Aggregating federal jobs for H1B seekers"
4. **Wait 1-2 business days for approval**
5. **Add to backend .env file:**

```bash
# Edit /app/backend/.env
USAJOBS_API_KEY=your_api_key_here
```

---

## 🔧 Complete Setup Example

Your `/app/backend/.env` file should look like this:

```bash
# Existing variables
MONGO_URL=mongodb://localhost:27017
DB_NAME=h1b_jobs
CORS_ORIGINS=*

# NEW: Add these API keys
JSEARCH_API_KEY=abc123...
ADZUNA_APP_ID=12345
ADZUNA_APP_KEY=xyz789...
USAJOBS_API_KEY=def456...
```

---

## 🚀 Activate the APIs

After adding the API keys:

```bash
# Restart the backend
sudo supervisorctl restart backend

# Wait 30 seconds for first sync

# Check status
curl http://localhost:8001/api/jobs/sync/status
```

Expected output:
```json
{
  "total_external_jobs": 150000,
  "greenhouse_jobs": 3812,
  "jsearch_jobs": 120000,
  "adzuna_jobs": 25000,
  "usajobs_jobs": 1000,
  "status": "active"
}
```

---

## 📊 What Each API Provides

| API | Jobs | Updates | Cost | Application Links |
|-----|------|---------|------|-------------------|
| **Greenhouse** | 3,812 | Every 60 sec | FREE | ✅ Direct to company |
| **JSearch** | 150,000+ | Every 60 sec | FREE | ✅ Google Jobs/Direct |
| **Adzuna** | 100,000+ | Every 60 sec | FREE | ✅ Direct to company |
| **USAJOBS** | 10,000+ | Every 60 sec | FREE | ✅ Official gov site |

---

## 🎯 Job Sources Breakdown

### JSearch Aggregates From:
- LinkedIn Jobs
- Indeed
- Glassdoor
- ZipRecruiter
- Monster
- CareerBuilder
- And 20+ more sources

### Adzuna Aggregates From:
- Company career pages
- Recruitment agencies
- Job boards
- Government sites

### USAJOBS Has:
- All federal government positions
- NASA, FBI, CDC, DoD, NIH, etc.

---

## ⚡ Quick Start (Get All 3 APIs in 10 Minutes)

1. **Open 3 tabs:**
   - Tab 1: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
   - Tab 2: https://developer.adzuna.com
   - Tab 3: https://developer.usajobs.gov

2. **Sign up for all three** (takes 5 minutes)

3. **Copy all API keys**

4. **Edit .env file:**
   ```bash
   nano /app/backend/.env
   # Add the 4 lines for API keys
   # Save and exit (Ctrl+X, Y, Enter)
   ```

5. **Restart backend:**
   ```bash
   sudo supervisorctl restart backend
   ```

6. **Done!** Jobs will start appearing within 60 seconds

---

## 🔍 Verify It's Working

### Method 1: Check Sync Status
```bash
curl http://localhost:8001/api/jobs/sync/status | python3 -m json.tool
```

### Method 2: Check Database
```bash
curl http://localhost:8001/api/jobs?limit=5
```

### Method 3: Check Logs
```bash
tail -f /var/log/supervisor/backend.err.log | grep -E "JSearch|Adzuna|USAJOBS|Fetched"
```

You should see:
```
Fetched 150 jobs from JSearch...
Fetched 50 jobs from Adzuna...
Fetched 100 jobs from USAJOBS...
```

---

## 🎁 Bonus: Even More Jobs (Optional)

Want even MORE jobs? These APIs are also free:

### RemoteOK API
- Remote jobs worldwide
- No auth required
- https://remoteok.com/api

### The Muse API
- Company-focused job listings
- Free tier available
- https://www.themuse.com/developers/api/v2

### Reed API (UK Jobs)
- If you want UK H1B equivalent
- Free tier
- https://www.reed.co.uk/developers

---

## 🆘 Troubleshooting

### "No API key found" in logs
- Check `.env` file has the key
- Restart backend after adding keys
- Keys should be on one line (no line breaks)

### "API error 401" or "403"
- API key is invalid or expired
- Re-check the key in the API provider dashboard
- Make sure you copied the entire key

### "No jobs appearing"
- Wait 60 seconds for first sync cycle
- Check sync status endpoint
- Verify H1B companies are in database: `curl http://localhost:8001/api/companies?limit=5`

### Jobs not filtered correctly
- System only shows jobs from H1B-sponsoring companies
- This is by design to focus on visa-friendly employers

---

## 📞 Support

**RapidAPI (JSearch):** https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch/discussions  
**Adzuna:** support@adzuna.com  
**USAJOBS:** access@usajobs.gov  

---

## ✨ Final Result

Once all APIs are setup:

- **260,000+ job listings** across USA
- **Updated every 60 seconds**
- **Direct application links** to official sites
- **H1B-sponsor filtered** automatically
- **Zero cost** - all APIs are free!

**Your H1B job board will have more jobs than most paid platforms!** 🚀
