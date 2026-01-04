#!/usr/bin/env python3
"""
Test LinkedIn Scraper
Run this to scrape LinkedIn jobs and display results
"""
import asyncio
import sys
sys.path.append('/app/backend')

from linkedin_scraper import linkedin_scraper

async def main():
    print("=" * 80)
    print("🔍 LINKEDIN JOBS SCRAPER")
    print("=" * 80)
    print()
    
    try:
        # Scrape LinkedIn jobs
        print("Starting LinkedIn scrape...")
        print("Searching: software engineer, data scientist, developer roles")
        print("Location: United States")
        print()
        
        jobs = await linkedin_scraper.scrape_multiple_searches()
        
        print("=" * 80)
        print(f"✅ SCRAPING COMPLETE - Found {len(jobs)} jobs")
        print("=" * 80)
        print()
        
        if jobs:
            print("📋 JOBS LIST:")
            print()
            
            for i, job in enumerate(jobs[:50], 1):  # Show first 50
                print(f"{i}. {job.get('title', 'N/A')}")
                print(f"   Company: {job.get('company', 'N/A')}")
                print(f"   Location: {job.get('location', 'N/A')}")
                print(f"   URL: {job.get('url', 'N/A')[:80]}...")
                print()
            
            if len(jobs) > 50:
                print(f"... and {len(jobs) - 50} more jobs")
                print()
            
            # Save to file
            import json
            with open('/app/backend/linkedin_jobs.json', 'w') as f:
                json.dump(jobs, f, indent=2)
            print(f"✅ Jobs saved to: /app/backend/linkedin_jobs.json")
            
        else:
            print("⚠️ No jobs found. LinkedIn may be blocking requests.")
            print()
            print("Possible issues:")
            print("1. LinkedIn requires authentication for API access")
            print("2. Rate limiting or anti-bot detection")
            print("3. HTML structure changed")
            print()
            print("Alternative: Use JSearch API (aggregates LinkedIn jobs)")
            print("See: /app/API_SETUP_GUIDE.md")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await linkedin_scraper.close()
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
