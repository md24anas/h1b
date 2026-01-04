"""
Company Career Website Scraper
Scrapes jobs directly from H1B-sponsoring company websites
"""
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import re
import asyncio

logger = logging.getLogger(__name__)

class CompanyCareerScraper:
    """Scrapes jobs from company career websites"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
    
    async def close(self):
        await self.http_client.aclose()
    
    async def scrape_google_careers(self) -> List[Dict]:
        """Scrape Google Careers API"""
        try:
            logger.info("Scraping Google Careers...")
            
            # Google has a public jobs API
            url = "https://careers.google.com/api/v3/search/"
            
            jobs = []
            for page in range(1, 6):  # Get 5 pages
                try:
                    response = await self.http_client.post(
                        url,
                        json={
                            "page": page,
                            "page_size": 20,
                            "query": "software engineer",
                            "location": "United States"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        page_jobs = data.get("jobs", [])
                        jobs.extend(page_jobs)
                        logger.info(f"Fetched {len(page_jobs)} jobs from Google (page {page})")
                        
                        if not page_jobs:
                            break
                    
                    await asyncio.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.error(f"Error scraping Google page {page}: {e}")
                    continue
            
            logger.info(f"Total Google jobs: {len(jobs)}")
            return jobs
            
        except Exception as e:
            logger.error(f"Error scraping Google Careers: {e}")
            return []
    
    async def scrape_amazon_jobs(self) -> List[Dict]:
        """Scrape Amazon Jobs API"""
        try:
            logger.info("Scraping Amazon Jobs...")
            
            url = "https://www.amazon.jobs/en/search.json"
            params = {
                "offset": 0,
                "result_limit": 100,
                "sort": "recent",
                "business_category[]": "software-development",
                "country[]": "USA"
            }
            
            response = await self.http_client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("jobs", [])
                logger.info(f"Fetched {len(jobs)} jobs from Amazon")
                return jobs
            
            return []
            
        except Exception as e:
            logger.error(f"Error scraping Amazon Jobs: {e}")
            return []
    
    async def scrape_microsoft_careers(self) -> List[Dict]:
        """Scrape Microsoft Careers API"""
        try:
            logger.info("Scraping Microsoft Careers...")
            
            url = "https://gcsservices.careers.microsoft.com/search/api/v1/search"
            
            jobs = []
            for page in range(0, 5):  # 5 pages
                try:
                    payload = {
                        "from": page * 20,
                        "size": 20,
                        "filters": {
                            "country": ["United States"]
                        },
                        "searchText": "software"
                    }
                    
                    response = await self.http_client.post(url, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        page_jobs = data.get("operationResult", {}).get("result", {}).get("jobs", [])
                        jobs.extend(page_jobs)
                        logger.info(f"Fetched {len(page_jobs)} jobs from Microsoft (page {page})")
                        
                        if not page_jobs:
                            break
                    
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error scraping Microsoft page {page}: {e}")
                    continue
            
            logger.info(f"Total Microsoft jobs: {len(jobs)}")
            return jobs
            
        except Exception as e:
            logger.error(f"Error scraping Microsoft Careers: {e}")
            return []
    
    async def scrape_meta_careers(self) -> List[Dict]:
        """Scrape Meta (Facebook) Careers"""
        try:
            logger.info("Scraping Meta Careers...")
            
            # Meta uses GraphQL API
            url = "https://www.metacareers.com/graphql"
            
            query = """
            query CareersSearchQuery($input: CareersSearchInput!) {
              careers_search(input: $input) {
                results {
                  id
                  title
                  location_names
                  canonical_url
                }
              }
            }
            """
            
            variables = {
                "input": {
                    "q": "software",
                    "locations": ["United States"],
                    "page": 1
                }
            }
            
            response = await self.http_client.post(
                url,
                json={"query": query, "variables": variables}
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("data", {}).get("careers_search", {}).get("results", [])
                logger.info(f"Fetched {len(jobs)} jobs from Meta")
                return jobs
            
            return []
            
        except Exception as e:
            logger.error(f"Error scraping Meta Careers: {e}")
            return []
    
    async def scrape_apple_jobs(self) -> List[Dict]:
        """Scrape Apple Jobs API"""
        try:
            logger.info("Scraping Apple Jobs...")
            
            url = "https://jobs.apple.com/api/role/search"
            
            payload = {
                "query": "software engineer",
                "location": "united-states",
                "page": 1
            }
            
            response = await self.http_client.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("searchResults", [])
                logger.info(f"Fetched {len(jobs)} jobs from Apple")
                return jobs
            
            return []
            
        except Exception as e:
            logger.error(f"Error scraping Apple Jobs: {e}")
            return []
    
    def normalize_google_job(self, job: Dict) -> Optional[Dict]:
        """Normalize Google job data"""
        try:
            locations = job.get("locations", [])
            location_str = locations[0].get("display", "USA") if locations else "USA"
            
            # Extract state
            state_match = re.search(r',\s*([A-Z]{2})\s*,?\s*USA', location_str)
            state = state_match.group(1) if state_match else "CA"
            
            # Get salary range
            min_salary = job.get("min_salary", 0)
            max_salary = job.get("max_salary", 0)
            base_salary = (min_salary + max_salary) / 2 if min_salary and max_salary else 150000
            
            return {
                "job_id": f"google_{job.get('id', '')}",
                "external_id": job.get("id", ""),
                "source": "google_careers",
                "external_url": f"https://careers.google.com/jobs/results/{job.get('id', '')}",
                "job_title": job.get("title", ""),
                "company_name": "Google",
                "company_id": "comp_google",
                "location": location_str,
                "state": state,
                "base_salary": float(base_salary),
                "job_description": job.get("description", "")[:5000],
                "posted_date": job.get("posted_date", datetime.now(timezone.utc).isoformat()),
                "employment_type": "Full-time",
                "is_external": True,
                "last_synced": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error normalizing Google job: {e}")
            return None
    
    def normalize_amazon_job(self, job: Dict) -> Optional[Dict]:
        """Normalize Amazon job data"""
        try:
            location = job.get("city", "") + ", " + job.get("state", "WA")
            
            return {
                "job_id": f"amazon_{job.get('id_icims', '')}",
                "external_id": str(job.get("id_icims", "")),
                "source": "amazon_jobs",
                "external_url": f"https://www.amazon.jobs{job.get('job_path', '')}",
                "job_title": job.get("title", ""),
                "company_name": "Amazon",
                "company_id": "comp_amazon",
                "location": location,
                "state": job.get("state", "WA"),
                "base_salary": 140000,  # Amazon average
                "job_description": job.get("basic_qualifications", "")[:5000],
                "posted_date": job.get("posted_date", datetime.now(timezone.utc).isoformat()),
                "employment_type": "Full-time",
                "is_external": True,
                "last_synced": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error normalizing Amazon job: {e}")
            return None
    
    def normalize_microsoft_job(self, job: Dict) -> Optional[Dict]:
        """Normalize Microsoft job data"""
        try:
            location = job.get("properties", {}).get("location", "Redmond, WA")
            state_match = re.search(r',\s*([A-Z]{2})', location)
            state = state_match.group(1) if state_match else "WA"
            
            return {
                "job_id": f"msft_{job.get('jobId', '')}",
                "external_id": job.get("jobId", ""),
                "source": "microsoft_careers",
                "external_url": f"https://careers.microsoft.com/us/en/job/{job.get('jobId', '')}",
                "job_title": job.get("title", ""),
                "company_name": "Microsoft",
                "company_id": "comp_microsoft",
                "location": location,
                "state": state,
                "base_salary": 160000,  # Microsoft average
                "job_description": job.get("description", "")[:5000],
                "posted_date": job.get("postingDate", datetime.now(timezone.utc).isoformat()),
                "employment_type": "Full-time",
                "is_external": True,
                "last_synced": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error normalizing Microsoft job: {e}")
            return None

# Global instance
company_scraper = CompanyCareerScraper()
