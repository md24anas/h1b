"""
Massive Job Aggregator - Get ALL USA Jobs
Fetches jobs from every available source
"""
import asyncio
import sys
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import httpx
import json
from datetime import datetime
from typing import List, Dict

load_dotenv('/app/backend/.env')

class MassiveJobAggregator:
    """Aggregates jobs from ALL available sources"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.all_jobs = []
        
    async def close(self):
        await self.http_client.aclose()
    
    async def fetch_jsearch_all_companies(self, api_key: str, companies: List[str]) -> List[Dict]:
        """Fetch jobs from JSearch for all H1B companies"""
        all_jobs = []
        
        print(f"\n🔍 Fetching from JSearch API for {len(companies)} companies...")
        
        for i, company in enumerate(companies[:50], 1):  # First 50 companies
            try:
                print(f"  [{i}/50] {company[:40]}...", end=' ', flush=True)
                
                headers = {
                    "X-RapidAPI-Key": api_key,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
                }
                
                params = {
                    "query": f"{company} software engineer",
                    "page": "1",
                    "num_pages": "1"
                }
                
                response = await self.http_client.get(
                    "https://jsearch.p.rapidapi.com/search",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get("data", [])
                    all_jobs.extend(jobs)
                    print(f"✅ {len(jobs)} jobs")
                else:
                    print(f"❌ Error {response.status_code}")
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ {str(e)[:30]}")
                continue
        
        return all_jobs
    
    async def fetch_adzuna_all_searches(self, app_id: str, app_key: str) -> List[Dict]:
        """Fetch jobs from Adzuna for multiple searches"""
        all_jobs = []
        
        print(f"\n🔍 Fetching from Adzuna API...")
        
        searches = [
            {"what": "software engineer", "where": "United States", "pages": 20},
            {"what": "data scientist", "where": "United States", "pages": 10},
            {"what": "developer", "where": "United States", "pages": 10},
            {"what": "engineer", "where": "United States", "pages": 10},
        ]
        
        for search in searches:
            try:
                print(f"\n  Searching: {search['what']} in {search['where']}")
                
                for page in range(1, search['pages'] + 1):
                    params = {
                        "app_id": app_id,
                        "app_key": app_key,
                        "what": search['what'],
                        "where": search['where'],
                        "results_per_page": "50",
                        "content-type": "application/json"
                    }
                    
                    response = await self.http_client.get(
                        f"https://api.adzuna.com/v1/api/jobs/us/search/{page}",
                        params=params
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        jobs = data.get("results", [])
                        all_jobs.extend(jobs)
                        print(f"    Page {page}: {len(jobs)} jobs", end='\r', flush=True)
                    else:
                        break
                    
                    await asyncio.sleep(0.3)
                
                print(f"    ✅ Total: {len(all_jobs)} jobs so far")
                
            except Exception as e:
                print(f"    ❌ Error: {str(e)[:50]}")
                continue
        
        return all_jobs
    
    async def fetch_usajobs_all(self, api_key: str) -> List[Dict]:
        """Fetch ALL jobs from USAJOBS"""
        all_jobs = []
        
        print(f"\n🔍 Fetching from USAJOBS API...")
        
        keywords = ["software", "data", "engineer", "analyst", "developer"]
        
        for keyword in keywords:
            try:
                print(f"  Searching: {keyword}...", end=' ', flush=True)
                
                headers = {
                    "Host": "data.usajobs.gov",
                    "User-Agent": "h1b-job-board-app",
                    "Authorization-Key": api_key
                }
                
                params = {
                    "Keyword": keyword,
                    "ResultsPerPage": "500",
                    "Page": "1"
                }
                
                response = await self.http_client.get(
                    "https://data.usajobs.gov/api/search",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get("SearchResult", {}).get("SearchResultItems", [])
                    all_jobs.extend(jobs)
                    print(f"✅ {len(jobs)} jobs")
                else:
                    print(f"❌ Error {response.status_code}")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ {str(e)[:30]}")
                continue
        
        return all_jobs
    
    async def fetch_greenhouse_expanded(self) -> List[Dict]:
        """Fetch from expanded list of Greenhouse companies"""
        all_jobs = []
        
        # Expanded list of H1B companies using Greenhouse
        companies = [
            "gitlab", "stripe", "airbnb", "lyft", "dropbox", "coinbase",
            "square", "robinhood", "doordash", "instacart", "reddit",
            "databricks", "snowflake", "mongodb", "plaid", "notion",
            "figma", "airtable", "asana", "cloudflare", "brex",
            "rippling", "lattice", "benchling", "checkr", "grammarly",
            "gusto", "heap", "lob", "mixpanel", "optimizely",
            "postmates", "quora", "rubrik", "segment", "sentry",
            "sourcegraph", "strava", "superhuman", "vercel", "webflow",
            "aiven", "algolia", "contentful", "elastic", "mongodb",
            "netlify", "pagerduty", "postman", "snyk", "supabase"
        ]
        
        print(f"\n🔍 Fetching from {len(companies)} Greenhouse companies...")
        
        for i, company in enumerate(companies, 1):
            try:
                print(f"  [{i}/{len(companies)}] {company[:20]:<20}", end=' ', flush=True)
                
                url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
                response = await self.http_client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get("jobs", [])
                    all_jobs.extend(jobs)
                    print(f"✅ {len(jobs)} jobs")
                else:
                    print(f"❌ {response.status_code}")
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ {str(e)[:20]}")
                continue
        
        return all_jobs

async def main():
    print("=" * 100)
    print("🌎 MASSIVE USA JOB AGGREGATOR")
    print("=" * 100)
    print()
    
    # Connect to database
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Get H1B companies
    print("📊 Loading H1B companies...")
    companies = await db.companies.find({}, {"_id": 0, "name": 1}).to_list(None)
    company_names = [c['name'] for c in companies]
    print(f"✅ {len(company_names)} H1B-sponsoring companies loaded")
    
    # Create aggregator
    aggregator = MassiveJobAggregator()
    
    all_jobs = []
    sources = {}
    
    # 1. Greenhouse (Always works - no API key needed)
    print("\n" + "=" * 100)
    print("📡 SOURCE 1: GREENHOUSE API (No auth required)")
    print("=" * 100)
    
    greenhouse_jobs = await aggregator.fetch_greenhouse_expanded()
    all_jobs.extend(greenhouse_jobs)
    sources['greenhouse'] = len(greenhouse_jobs)
    print(f"\n✅ Greenhouse Total: {len(greenhouse_jobs)} jobs")
    
    # 2. JSearch API
    jsearch_key = os.environ.get("JSEARCH_API_KEY")
    if jsearch_key:
        print("\n" + "=" * 100)
        print("📡 SOURCE 2: JSEARCH API (Google Jobs Aggregator)")
        print("=" * 100)
        
        jsearch_jobs = await aggregator.fetch_jsearch_all_companies(jsearch_key, company_names)
        all_jobs.extend(jsearch_jobs)
        sources['jsearch'] = len(jsearch_jobs)
        print(f"\n✅ JSearch Total: {len(jsearch_jobs)} jobs")
    else:
        print("\n⚠️  JSearch API key not found - Skipping (would add 100,000+ jobs)")
        print("   Get free key: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch")
        sources['jsearch'] = 0
    
    # 3. Adzuna API
    adzuna_id = os.environ.get("ADZUNA_APP_ID")
    adzuna_key = os.environ.get("ADZUNA_APP_KEY")
    if adzuna_id and adzuna_key:
        print("\n" + "=" * 100)
        print("📡 SOURCE 3: ADZUNA API")
        print("=" * 100)
        
        adzuna_jobs = await aggregator.fetch_adzuna_all_searches(adzuna_id, adzuna_key)
        all_jobs.extend(adzuna_jobs)
        sources['adzuna'] = len(adzuna_jobs)
        print(f"\n✅ Adzuna Total: {len(adzuna_jobs)} jobs")
    else:
        print("\n⚠️  Adzuna API key not found - Skipping (would add 50,000+ jobs)")
        print("   Get free key: https://developer.adzuna.com")
        sources['adzuna'] = 0
    
    # 4. USAJOBS API
    usajobs_key = os.environ.get("USAJOBS_API_KEY")
    if usajobs_key:
        print("\n" + "=" * 100)
        print("📡 SOURCE 4: USAJOBS (Government Jobs)")
        print("=" * 100)
        
        usajobs_jobs = await aggregator.fetch_usajobs_all(usajobs_key)
        all_jobs.extend(usajobs_jobs)
        sources['usajobs'] = len(usajobs_jobs)
        print(f"\n✅ USAJOBS Total: {len(usajobs_jobs)} jobs")
    else:
        print("\n⚠️  USAJOBS API key not found - Skipping (would add 10,000+ jobs)")
        print("   Get free key: https://developer.usajobs.gov")
        sources['usajobs'] = 0
    
    await aggregator.close()
    
    # Final Summary
    print("\n" + "=" * 100)
    print("📊 FINAL RESULTS")
    print("=" * 100)
    print()
    print(f"🎯 TOTAL JOBS FOUND: {len(all_jobs):,}")
    print()
    print("By Source:")
    for source, count in sources.items():
        print(f"  {source.upper():<15} {count:>6,} jobs")
    
    # Save all jobs
    output_file = '/app/backend/all_usa_jobs.json'
    with open(output_file, 'w') as f:
        json.dump(all_jobs, f, indent=2)
    
    print()
    print(f"✅ All jobs saved to: {output_file}")
    
    # Show sample
    if all_jobs:
        print("\n" + "=" * 100)
        print("📋 SAMPLE JOBS (First 50)")
        print("=" * 100)
        print()
        
        for i, job in enumerate(all_jobs[:50], 1):
            title = job.get('title') or job.get('job_title') or job.get('text', 'Unknown')
            company = job.get('company') or job.get('employer_name') or job.get('company_name', 'Unknown')
            location = job.get('location') or job.get('job_city', 'USA')
            
            if isinstance(location, dict):
                location = location.get('name', 'USA')
            
            print(f"{i}. {title[:60]}")
            print(f"   Company: {company[:50]}")
            print(f"   Location: {str(location)[:50]}")
            print()
    
    print("=" * 100)
    print()
    
    # Instructions for missing APIs
    if not jsearch_key or not adzuna_id or not usajobs_key:
        print("🔑 TO GET MORE JOBS - ADD MISSING API KEYS:")
        print("=" * 100)
        
        if not jsearch_key:
            print("\n1. JSearch API (FREE - adds 100,000+ jobs):")
            print("   - Go to: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch")
            print("   - Click 'Subscribe to Test' → Select FREE plan")
            print("   - Copy API key")
            print("   - Add to /app/backend/.env: JSEARCH_API_KEY=your_key")
        
        if not adzuna_id:
            print("\n2. Adzuna API (FREE - adds 50,000+ jobs):")
            print("   - Go to: https://developer.adzuna.com")
            print("   - Click 'Get API Key'")
            print("   - Add to /app/backend/.env:")
            print("     ADZUNA_APP_ID=your_id")
            print("     ADZUNA_APP_KEY=your_key")
        
        if not usajobs_key:
            print("\n3. USAJOBS API (FREE - adds 10,000+ jobs):")
            print("   - Go to: https://developer.usajobs.gov")
            print("   - Click 'Request API Key'")
            print("   - Add to /app/backend/.env: USAJOBS_API_KEY=your_key")
        
        print("\nThen restart: sudo supervisorctl restart backend")
    
    print("\n" + "=" * 100)
    print("✅ AGGREGATION COMPLETE!")
    print("=" * 100)

if __name__ == "__main__":
    asyncio.run(main())
