"""
LinkedIn Jobs Scraper
Scrapes jobs from LinkedIn using public search URLs
"""
import httpx
import logging
import re
import json
from typing import List, Dict, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import quote

logger = logging.getLogger(__name__)

class LinkedInScraper:
    """Scrapes jobs from LinkedIn"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        self.base_url = "https://www.linkedin.com"
    
    async def close(self):
        await self.http_client.aclose()
    
    async def scrape_linkedin_jobs(self, keywords: str = "software engineer", location: str = "United States", max_pages: int = 10) -> List[Dict]:
        """
        Scrape jobs from LinkedIn public job search
        
        Args:
            keywords: Job search keywords
            location: Job location
            max_pages: Number of pages to scrape (25 jobs per page)
        """
        try:
            logger.info(f"Scraping LinkedIn jobs for: {keywords} in {location}")
            
            all_jobs = []
            
            for page in range(max_pages):
                start = page * 25
                
                # LinkedIn public job search URL
                search_url = f"{self.base_url}/jobs/search/"
                params = {
                    'keywords': keywords,
                    'location': location,
                    'start': start,
                    'f_TP': '1',  # Past 24 hours
                    'position': 1,
                    'pageNum': page
                }
                
                try:
                    logger.info(f"Fetching LinkedIn page {page + 1}/{max_pages} (start={start})")
                    
                    response = await self.http_client.get(search_url, params=params)
                    
                    if response.status_code == 200:
                        html = response.text
                        
                        # Parse jobs from HTML
                        jobs = self.parse_jobs_from_html(html)
                        
                        if not jobs:
                            logger.warning(f"No jobs found on page {page + 1}")
                            break
                        
                        all_jobs.extend(jobs)
                        logger.info(f"Extracted {len(jobs)} jobs from page {page + 1}")
                        
                        # Rate limiting
                        await asyncio.sleep(2)
                        
                    elif response.status_code == 429:
                        logger.error("LinkedIn rate limit hit - stopping")
                        break
                    else:
                        logger.error(f"LinkedIn returned status {response.status_code}")
                        break
                        
                except Exception as e:
                    logger.error(f"Error fetching LinkedIn page {page}: {e}")
                    continue
            
            logger.info(f"Total LinkedIn jobs scraped: {len(all_jobs)}")
            return all_jobs
            
        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {e}")
            return []
    
    def parse_jobs_from_html(self, html: str) -> List[Dict]:
        """Parse job listings from LinkedIn HTML"""
        jobs = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Method 1: Try to find JSON data embedded in HTML
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                        job = self.parse_json_job(data)
                        if job:
                            jobs.append(job)
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'JobPosting':
                                job = self.parse_json_job(item)
                                if job:
                                    jobs.append(job)
                except:
                    continue
            
            # Method 2: Parse job cards from HTML
            if not jobs:
                job_cards = soup.find_all('div', class_=re.compile(r'base-card'))
                
                for card in job_cards:
                    try:
                        # Extract job ID from card
                        job_id = None
                        if card.get('data-entity-urn'):
                            job_id = card['data-entity-urn'].split(':')[-1]
                        
                        # Extract title
                        title_elem = card.find('h3', class_=re.compile(r'base-search-card__title'))
                        title = title_elem.text.strip() if title_elem else None
                        
                        # Extract company
                        company_elem = card.find('h4', class_=re.compile(r'base-search-card__subtitle'))
                        company = company_elem.text.strip() if company_elem else None
                        
                        # Extract location
                        location_elem = card.find('span', class_=re.compile(r'job-search-card__location'))
                        location = location_elem.text.strip() if location_elem else None
                        
                        # Extract link
                        link_elem = card.find('a', class_=re.compile(r'base-card__full-link'))
                        job_url = link_elem['href'] if link_elem and link_elem.get('href') else None
                        
                        if title and company and job_id:
                            jobs.append({
                                'id': job_id,
                                'title': title,
                                'company': company,
                                'location': location or 'United States',
                                'url': job_url or f"{self.base_url}/jobs/view/{job_id}",
                                'description': ''
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing job card: {e}")
                        continue
            
            # Method 3: Try API-like data
            if not jobs:
                # LinkedIn sometimes includes data in script tags
                for script in soup.find_all('script'):
                    if script.string and 'jobPosting' in script.string.lower():
                        try:
                            # Try to extract JSON from script
                            match = re.search(r'\{[^}]*"jobPosting"[^}]*\}', script.string)
                            if match:
                                data = json.loads(match.group(0))
                                # Process data...
                        except:
                            continue
            
        except Exception as e:
            logger.error(f"Error parsing LinkedIn HTML: {e}")
        
        return jobs
    
    def parse_json_job(self, data: Dict) -> Optional[Dict]:
        """Parse job from JSON-LD format"""
        try:
            return {
                'id': data.get('identifier', {}).get('value', ''),
                'title': data.get('title', ''),
                'company': data.get('hiringOrganization', {}).get('name', ''),
                'location': data.get('jobLocation', {}).get('address', {}).get('addressLocality', ''),
                'url': data.get('url', ''),
                'description': data.get('description', ''),
                'salary': data.get('baseSalary', {}).get('value', {}).get('value', 0)
            }
        except:
            return None
    
    async def scrape_multiple_searches(self) -> List[Dict]:
        """Scrape jobs for multiple H1B-relevant searches"""
        all_jobs = []
        
        searches = [
            {"keywords": "software engineer", "location": "United States"},
            {"keywords": "data scientist", "location": "United States"},
            {"keywords": "software developer", "location": "United States"},
            {"keywords": "full stack developer", "location": "United States"},
            {"keywords": "backend engineer", "location": "United States"},
            {"keywords": "frontend engineer", "location": "United States"},
            {"keywords": "machine learning engineer", "location": "United States"},
            {"keywords": "devops engineer", "location": "United States"},
        ]
        
        for search in searches:
            try:
                jobs = await self.scrape_linkedin_jobs(
                    keywords=search['keywords'],
                    location=search['location'],
                    max_pages=3  # 3 pages = 75 jobs per search
                )
                all_jobs.extend(jobs)
                
                # Rate limiting between searches
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in search {search}: {e}")
                continue
        
        # Deduplicate
        unique_jobs = {}
        for job in all_jobs:
            if job.get('id'):
                unique_jobs[job['id']] = job
        
        return list(unique_jobs.values())
    
    def normalize_linkedin_job(self, job: Dict) -> Optional[Dict]:
        """Normalize LinkedIn job to our schema"""
        try:
            # Extract state from location
            location = job.get('location', 'United States')
            state_match = re.search(r',\s*([A-Z]{2})\s*(?:,|\s|$)', location)
            state = state_match.group(1) if state_match else 'CA'
            
            # Estimate salary based on title
            title = job.get('title', '').lower()
            if 'senior' in title or 'staff' in title:
                base_salary = 150000
            elif 'junior' in title or 'entry' in title:
                base_salary = 90000
            else:
                base_salary = 120000
            
            return {
                "job_id": f"li_{job.get('id', '')}",
                "external_id": job.get('id', ''),
                "source": "linkedin",
                "external_url": job.get('url', ''),
                "job_title": job.get('title', ''),
                "company_name": job.get('company', ''),
                "company_id": f"comp_{job.get('company', '').lower().replace(' ', '_')}",
                "location": location,
                "state": state,
                "base_salary": base_salary,
                "job_description": job.get('description', '')[:5000],
                "posted_date": datetime.now(timezone.utc).isoformat(),
                "employment_type": "Full-time",
                "is_external": True,
                "last_synced": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error normalizing LinkedIn job: {e}")
            return None

# Global instance
linkedin_scraper = LinkedInScraper()
