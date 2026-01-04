#!/usr/bin/env python3
"""
H1B Company Career Page Scraper
Scrapes jobs from all H1B-sponsoring companies in database
"""
import asyncio
import sys
import re
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import httpx
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional

load_dotenv('/app/backend/.env')

# Company career page patterns
CAREER_URL_PATTERNS = [
    'careers',
    'jobs',
    'work-with-us',
    'join-us',
    'opportunities',
    'employment',
    'hiring'
]

# Common ATS platforms
ATS_PATTERNS = {
    'greenhouse': 'greenhouse.io',
    'lever': 'lever.co',
    'workday': 'myworkdayjobs.com',
    'smartrecruiters': 'smartrecruiters.com',
    'icims': 'icims.com',
    'taleo': 'taleo.net',
    'jobvite': 'jobvite.com',
    'ashbyhq': 'ashbyhq.com',
    'breezy': 'breezy.hr'
}

class CompanyCareerScraper:
    """Scrapes jobs from company career pages"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        self.scraped_jobs = []
        self.successful_companies = []
        self.failed_companies = []
    
    async def close(self):
        await self.http_client.aclose()
    
    def guess_career_url(self, company_name: str, website: str = None) -> List[str]:
        """Generate possible career page URLs for a company"""
        urls = []
        
        if website:
            base_url = website.rstrip('/')
            # Try common career page paths
            for pattern in CAREER_URL_PATTERNS:
                urls.append(f"{base_url}/{pattern}")
                urls.append(f"{base_url}/{pattern}/")
        
        # Common domain patterns
        clean_name = company_name.lower().replace(' ', '').replace(',', '').replace('.', '')
        for suffix in ['com', 'io', 'ai']:
            urls.append(f"https://{clean_name}.{suffix}/careers")
            urls.append(f"https://careers.{clean_name}.{suffix}")
            urls.append(f"https://jobs.{clean_name}.{suffix}")
        
        return urls
    
    async def detect_ats_platform(self, url: str) -> Optional[str]:
        """Detect which ATS platform a company uses"""
        try:
            response = await self.http_client.get(url)
            if response.status_code == 200:
                html = response.text.lower()
                final_url = str(response.url).lower()
                
                for ats_name, ats_domain in ATS_PATTERNS.items():
                    if ats_domain in final_url or ats_domain in html:
                        return ats_name
        except:
            pass
        return None
    
    async def scrape_greenhouse_company(self, company_name: str, board_token: str) -> List[Dict]:
        """Scrape jobs from Greenhouse"""
        try:
            url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
            response = await self.http_client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('jobs', [])
                
                normalized = []
                for job in jobs:
                    normalized.append({
                        'company': company_name,
                        'title': job.get('title', ''),
                        'location': job.get('location', {}).get('name', 'Remote'),
                        'url': job.get('absolute_url', ''),
                        'id': job.get('id', ''),
                        'ats': 'greenhouse'
                    })
                
                return normalized
        except:
            pass
        return []
    
    async def scrape_lever_company(self, company_name: str, lever_name: str) -> List[Dict]:
        """Scrape jobs from Lever"""
        try:
            url = f"https://api.lever.co/v0/postings/{lever_name}?mode=json"
            response = await self.http_client.get(url)
            
            if response.status_code == 200:
                jobs = response.json()
                
                normalized = []
                for job in jobs:
                    normalized.append({
                        'company': company_name,
                        'title': job.get('text', ''),
                        'location': job.get('categories', {}).get('location', 'Remote'),
                        'url': job.get('hostedUrl', ''),
                        'id': job.get('id', ''),
                        'ats': 'lever'
                    })
                
                return normalized
        except:
            pass
        return []
    
    async def scrape_generic_career_page(self, company_name: str, url: str) -> List[Dict]:
        """Generic scraper for career pages"""
        try:
            response = await self.http_client.get(url)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            jobs = []
            
            # Look for job listings with common patterns
            job_elements = []
            
            # Pattern 1: Links with "job" or "position" in href/class
            job_elements.extend(soup.find_all('a', href=re.compile(r'job|position|opening', re.I)))
            
            # Pattern 2: Divs with job-related classes
            job_elements.extend(soup.find_all(['div', 'li', 'article'], class_=re.compile(r'job|position|role|opening', re.I)))
            
            # Pattern 3: JSON-LD structured data
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                        jobs.append({
                            'company': company_name,
                            'title': data.get('title', ''),
                            'location': data.get('jobLocation', {}).get('address', {}).get('addressLocality', 'Remote'),
                            'url': data.get('url', url),
                            'id': data.get('identifier', {}).get('value', ''),
                            'ats': 'generic'
                        })
                except:
                    continue
            
            # Extract from HTML elements
            for elem in job_elements[:50]:  # Limit to 50 per page
                try:
                    title_elem = elem.find(['h2', 'h3', 'h4', 'span', 'strong'], class_=re.compile(r'title|name|heading', re.I))
                    if not title_elem:
                        title_elem = elem
                    
                    title = title_elem.get_text(strip=True)
                    
                    # Skip if not a real job title
                    if len(title) < 5 or len(title) > 100:
                        continue
                    
                    # Get URL
                    job_url = elem.get('href') if elem.name == 'a' else None
                    if job_url:
                        job_url = urljoin(url, job_url)
                    
                    # Get location
                    location_elem = elem.find(['span', 'div', 'p'], class_=re.compile(r'location|city', re.I))
                    location = location_elem.get_text(strip=True) if location_elem else 'Remote'
                    
                    if title and any(keyword in title.lower() for keyword in ['engineer', 'developer', 'scientist', 'analyst', 'manager', 'architect', 'designer']):
                        jobs.append({
                            'company': company_name,
                            'title': title,
                            'location': location,
                            'url': job_url or url,
                            'id': f"{company_name}_{len(jobs)}",
                            'ats': 'generic'
                        })
                except:
                    continue
            
            return jobs[:20]  # Max 20 jobs per company
            
        except Exception as e:
            return []
    
    async def scrape_company(self, company_name: str, website: str = None) -> List[Dict]:
        """Scrape jobs from a single company"""
        jobs = []
        
        # Generate possible career URLs
        career_urls = self.guess_career_url(company_name, website)
        
        for url in career_urls[:5]:  # Try first 5 URLs
            try:
                # Detect ATS
                ats = await self.detect_ats_platform(url)
                
                if ats == 'greenhouse':
                    # Extract board token from URL
                    match = re.search(r'boards?[/-]?([a-zA-Z0-9_-]+)', url)
                    if match:
                        board_token = match.group(1)
                        jobs = await self.scrape_greenhouse_company(company_name, board_token)
                        if jobs:
                            break
                
                elif ats == 'lever':
                    # Extract lever name
                    match = re.search(r'lever\.co/([a-zA-Z0-9_-]+)', url)
                    if match:
                        lever_name = match.group(1)
                        jobs = await self.scrape_lever_company(company_name, lever_name)
                        if jobs:
                            break
                
                # Try generic scraping
                if not jobs:
                    jobs = await self.scrape_generic_career_page(company_name, url)
                    if jobs:
                        break
                
                await asyncio.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                continue
        
        return jobs

async def main():
    print("=" * 100)
    print("🏢 H1B COMPANY CAREER PAGE SCRAPER")
    print("=" * 100)
    print()
    
    # Connect to database
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Get all H1B companies
    print("📊 Fetching H1B-sponsoring companies from database...")
    companies = await db.companies.find({}, {"_id": 0, "name": 1, "website": 1}).to_list(None)
    print(f"✅ Found {len(companies)} H1B-sponsoring companies")
    print()
    
    # Create scraper
    scraper = CompanyCareerScraper()
    
    print("🔍 Starting to scrape company career pages...")
    print("This will take several minutes...")
    print()
    
    all_jobs = []
    successful = 0
    failed = 0
    
    # Scrape each company
    for i, company in enumerate(companies[:100], 1):  # Limit to first 100 for demo
        company_name = company.get('name', '')
        website = company.get('website')
        
        try:
            print(f"[{i}/{min(100, len(companies))}] Scraping: {company_name[:50]}...", end=' ', flush=True)
            
            jobs = await scraper.scrape_company(company_name, website)
            
            if jobs:
                all_jobs.extend(jobs)
                successful += 1
                print(f"✅ {len(jobs)} jobs")
            else:
                failed += 1
                print("❌ No jobs")
            
            # Rate limiting
            await asyncio.sleep(1)
            
        except Exception as e:
            failed += 1
            print(f"❌ Error: {str(e)[:50]}")
    
    await scraper.close()
    
    print()
    print("=" * 100)
    print("📊 SCRAPING RESULTS")
    print("=" * 100)
    print(f"✅ Successful: {successful} companies")
    print(f"❌ Failed: {failed} companies")
    print(f"📋 Total jobs found: {len(all_jobs)}")
    print()
    
    if all_jobs:
        print("=" * 100)
        print("📋 JOBS LIST (First 100)")
        print("=" * 100)
        print()
        
        for i, job in enumerate(all_jobs[:100], 1):
            print(f"{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   URL: {job['url'][:80]}...")
            print(f"   Source: {job['ats']}")
            print()
        
        if len(all_jobs) > 100:
            print(f"... and {len(all_jobs) - 100} more jobs")
            print()
        
        # Save to file
        with open('/app/backend/h1b_company_jobs.json', 'w') as f:
            json.dump(all_jobs, f, indent=2)
        print(f"✅ All jobs saved to: /app/backend/h1b_company_jobs.json")
        
        # Company statistics
        print()
        print("=" * 100)
        print("🏆 TOP COMPANIES BY JOB COUNT")
        print("=" * 100)
        from collections import Counter
        company_counts = Counter([job['company'] for job in all_jobs])
        for company, count in company_counts.most_common(20):
            print(f"{count:3d} jobs - {company}")
    
    print()
    print("=" * 100)
    print("✅ SCRAPING COMPLETE!")
    print("=" * 100)

if __name__ == "__main__":
    asyncio.run(main())
