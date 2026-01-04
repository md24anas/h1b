# 🇺🇸 USAJOBS API Integration Setup

## Overview
USAJOBS is the official US government jobs portal. This integration allows you to fetch **REAL government job listings** that are updated daily.

## Current Status
⚠️ **USAJOBS API Key Required** - The integration code is ready, but you need to register for a free API key.

## How to Get USAJOBS API Key

### Step 1: Register for API Access
1. Go to https://developer.usajobs.gov
2. Click on **"Request API Key"**
3. Fill out the API Request Form with:
   - Your name and email
   - Organization/Purpose: "H1B Job Board Application"
   - Description: "Aggregating federal government job postings for H1B seekers"

### Step 2: Receive Your API Key
- You'll receive an API key via email within 1-2 business days
- The API is **100% FREE** to use

### Step 3: Add API Key to Environment
Once you receive your API key:

```bash
# Add to /app/backend/.env file
USAJOBS_API_KEY=your_api_key_here
```

### Step 4: Restart Backend
```bash
sudo supervisorctl restart backend
```

## What You'll Get

### Job Sources After Adding USAJOBS:
1. **Greenhouse** (Currently Active) - 3,800+ jobs from tech companies
2. **USAJOBS** (After Setup) - 10,000+ government jobs
3. **Arbeitnow** (Currently Active) - Remote/European jobs

### USAJOBS Features:
- ✅ Official US government job postings
- ✅ Federal agency positions
- ✅ Clear salary ranges
- ✅ Direct application links
- ✅ Updated daily
- ✅ Jobs across all 50 states

### Example Jobs You'll See:
- Software Developer - NASA
- Data Scientist - CDC
- Cybersecurity Analyst - DHS
- IT Specialist - Department of Defense
- Research Scientist - NIH

## API Limits
- **Free Tier**: 10,000 results per query
- **Rate Limit**: Reasonable use (we fetch once per minute)
- **No Cost**: Completely free API

## Troubleshooting

### If USAJOBS jobs aren't appearing:
1. Check if API key is in `.env` file
2. Verify backend has restarted: `sudo supervisorctl status backend`
3. Check logs: `tail -f /var/log/supervisor/backend.err.log | grep USAJOBS`
4. Verify API key is valid at https://developer.usajobs.gov

### Check Integration Status:
```bash
curl http://localhost:8001/api/jobs/sync/status
```

Should show:
```json
{
  "usajobs_jobs": 100,  // This number should be > 0 if working
  "greenhouse_jobs": 3812,
  "status": "active"
}
```

## Documentation
- Official API Docs: https://developer.usajobs.gov/api-reference/
- Support Email: access@usajobs.gov

## Note
Government jobs typically don't sponsor H1B visas, but they're included because:
1. Some federal contractor positions DO sponsor
2. Provides full spectrum of available US opportunities
3. Useful for US citizens/permanent residents also using the platform

---

**Once you have your API key, just add it to the `.env` file and restart - the integration will automatically start pulling government jobs!**
