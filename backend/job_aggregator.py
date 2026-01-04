"""
Job Aggregation Service
Fetches jobs from multiple public APIs and filters for H1B-sponsoring companies
"""
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
import asyncio
import re

logger = logging.getLogger(__name__)

class JobAggregator:
    """Aggregates jobs from multiple sources"""
    
    def __init__(self, db):
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
    
    async def get_h1b_companies(self) -> set:
        """Get list of H1B-sponsoring company names from database"""
        try:
            companies = await self.db.companies.find({}, {"_id": 0, "name": 1}).to_list(None)
            # Create set of normalized company names for matching
            company_names = set()
            for comp in companies:
                name = comp.get("name", "").lower().strip()
                if name:
                    company_names.add(name)
                    # Also add variations without common suffixes
                    for suffix in [" inc", " inc.", " llc", " corp", " corporation", " ltd", " limited"]:
                        if name.endswith(suffix):
                            company_names.add(name.replace(suffix, "").strip())
            
            logger.info(f"Loaded {len(company_names)} H1B-sponsoring company names")
            return company_names
        except Exception as e:
            logger.error(f"Error loading H1B companies: {e}")
            return set()
    
    def normalize_company_name(self, name: str) -> str:
        """Normalize company name for matching"""
        if not name:
            return ""
        name = name.lower().strip()
        # Remove common suffixes
        for suffix in [" inc", " inc.", " llc", " corp", " corporation", " ltd", " limited", " co.", " co"]:
            if name.endswith(suffix):
                name = name.replace(suffix, "").strip()
        return name
    
    def is_h1b_sponsor(self, company_name: str, h1b_companies: set) -> bool:
        """Check if company sponsors H1B"""
        normalized = self.normalize_company_name(company_name)
        return normalized in h1b_companies
    
    async def fetch_arbeitnow_jobs(self) -> List[Dict]:
        """Fetch jobs from Arbeitnow API (no auth required)"""
        try:
            logger.info("Fetching jobs from Arbeitnow...")
            response = await self.http_client.get("https://www.arbeitnow.com/api/job-board-api")
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("data", [])
                logger.info(f"Fetched {len(jobs)} jobs from Arbeitnow")
                return jobs
            else:
                logger.error(f"Arbeitnow API error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching from Arbeitnow: {e}")
            return []
    
    async def fetch_greenhouse_jobs(self, board_tokens: List[str]) -> List[Dict]:
        """Fetch jobs from Greenhouse Job Board API"""
        all_jobs = []
        
        for token in board_tokens:
            try:
                logger.info(f"Fetching jobs from Greenhouse board: {token[:10]}...")
                url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
                response = await self.http_client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get("jobs", [])
                    logger.info(f"Fetched {len(jobs)} jobs from Greenhouse board {token[:10]}")
                    
                    # Add board token to each job for reference
                    for job in jobs:
                        job["board_token"] = token
                    
                    all_jobs.extend(jobs)
                else:
                    logger.warning(f"Greenhouse API error for token {token[:10]}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error fetching from Greenhouse board {token[:10]}: {e}")
        
        logger.info(f"Total Greenhouse jobs fetched: {len(all_jobs)}")
        return all_jobs
    
    def normalize_arbeitnow_job(self, job: Dict, h1b_companies: set) -> Optional[Dict]:
        """Normalize Arbeitnow job to our schema"""
        try:
            company_name = job.get("company_name", "")
            
            # Filter for H1B sponsors
            if not self.is_h1b_sponsor(company_name, h1b_companies):
                return None
            
            # Extract location info
            location = job.get("location", "Remote")
            state = self.extract_state(location)
            
            # Normalize job data
            normalized = {
                "job_id": f"arbeit_{job.get('slug', '')}",
                "external_id": job.get("slug", ""),
                "source": "arbeitnow",
                "external_url": job.get("url", ""),
                "job_title": job.get("title", ""),
                "company_name": company_name,
                "company_id": f"comp_{self.normalize_company_name(company_name).replace(' ', '_')}",
                "location": location,
                "state": state,
                "wage_level": 2,  # Default to level 2
                "base_salary": 0,  # Not provided by Arbeitnow
                "prevailing_wage": 0,
                "job_description": job.get("description", "")[:5000],  # Limit length
                "requirements": self.extract_requirements(job.get("description", "")),
                "benefits": [],
                "visa_sponsorship": True,
                "posted_date": self.parse_date(job.get("created_at")),
                "employment_type": job.get("job_types", ["Full-time"])[0] if job.get("job_types") else "Full-time",
                "lca_case_number": None,
                "is_external": True,
                "last_synced": datetime.now(timezone.utc).isoformat()
            }
            
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing Arbeitnow job: {e}")
            return None
    
    def normalize_greenhouse_job(self, job: Dict, h1b_companies: set) -> Optional[Dict]:
        """Normalize Greenhouse job to our schema"""
        try:
            company_name = job.get("company", {}).get("name", "") if isinstance(job.get("company"), dict) else ""
            
            # Filter for H1B sponsors
            if not self.is_h1b_sponsor(company_name, h1b_companies):
                return None
            
            # Extract location info
            location_obj = job.get("location", {})
            if isinstance(location_obj, dict):
                location = location_obj.get("name", "Remote")
            else:
                location = str(location_obj) if location_obj else "Remote"
            
            state = self.extract_state(location)
            
            # Get job content
            content = job.get("content", {}) or {}
            description = content.get("description", "") if isinstance(content, dict) else ""
            
            normalized = {
                "job_id": f"gh_{job.get('id', '')}",
                "external_id": str(job.get("id", "")),
                "source": "greenhouse",
                "external_url": job.get("absolute_url", ""),
                "job_title": job.get("title", ""),
                "company_name": company_name,
                "company_id": f"comp_{self.normalize_company_name(company_name).replace(' ', '_')}",
                "location": location,
                "state": state,
                "wage_level": 2,  # Default to level 2
                "base_salary": 0,  # Not provided by Greenhouse
                "prevailing_wage": 0,
                "job_description": description[:5000],
                "requirements": self.extract_requirements(description),
                "benefits": [],
                "visa_sponsorship": True,
                "posted_date": self.parse_date(job.get("updated_at")),
                "employment_type": "Full-time",
                "lca_case_number": None,
                "is_external": True,
                "last_synced": datetime.now(timezone.utc).isoformat()
            }
            
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing Greenhouse job: {e}")
            return None
    
    def extract_state(self, location: str) -> str:
        """Extract US state from location string"""
        if not location:
            return "Remote"
        
        # Common US state abbreviations
        states = {
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        }
        
        # Try to find state abbreviation
        location_upper = location.upper()
        for state in states:
            if f" {state}" in f" {location_upper}" or location_upper.endswith(state):
                return state
        
        # Check for "Remote"
        if "remote" in location.lower():
            return "Remote"
        
        return "Various"
    
    def extract_requirements(self, description: str) -> List[str]:
        """Extract key requirements from job description"""
        if not description:
            return []
        
        requirements = []
        
        # Look for common requirement patterns
        patterns = [
            r"(?:require|requirement|must have|need).*?(?:degree|bachelor|master|phd)",
            r"(?:\d+\+?\s*years?.*?experience)",
            r"(?:proficient in|experience with|knowledge of)\s+[\w\s,]+",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            requirements.extend(matches[:3])  # Limit to 3 per pattern
        
        return requirements[:10]  # Max 10 requirements
    
    def parse_date(self, date_str) -> str:
        """Parse date string to ISO format"""
        if not date_str:
            return datetime.now(timezone.utc).isoformat()
        
        try:
            if isinstance(date_str, str):
                # Try parsing ISO format
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.isoformat()
        except:
            pass
        
        return datetime.now(timezone.utc).isoformat()
    
    async def sync_jobs(self):
        """Main sync function - fetches and stores jobs from all sources"""
        try:
            logger.info("=" * 60)
            logger.info("Starting job sync...")
            
            # Get H1B companies
            h1b_companies = await self.get_h1b_companies()
            
            if not h1b_companies:
                logger.warning("No H1B companies found in database. Skipping sync.")
                return
            
            all_normalized_jobs = []
            
            # Fetch from Arbeitnow
            arbeitnow_jobs = await self.fetch_arbeitnow_jobs()
            for job in arbeitnow_jobs:
                normalized = self.normalize_arbeitnow_job(job, h1b_companies)
                if normalized:
                    all_normalized_jobs.append(normalized)
            
            # Fetch from Greenhouse with public board tokens
            # Using some well-known company board tokens (these are public)
            greenhouse_tokens = [
                "gitlab",  # GitLab
                "stripe",  # Stripe
                "shopify", # Shopify
                "netflix", # Netflix
                "airbnb",  # Airbnb
                "uber",    # Uber
                "lyft",    # Lyft
                "twitter", # Twitter/X
                "meta",    # Meta
                "google",  # Google
            ]
            
            greenhouse_jobs = await self.fetch_greenhouse_jobs(greenhouse_tokens)
            for job in greenhouse_jobs:
                normalized = self.normalize_greenhouse_job(job, h1b_companies)
                if normalized:
                    all_normalized_jobs.append(normalized)
            
            # Deduplicate jobs by external_id + source
            unique_jobs = {}
            for job in all_normalized_jobs:
                key = f"{job['source']}_{job['external_id']}"
                unique_jobs[key] = job
            
            logger.info(f"Total unique jobs after filtering: {len(unique_jobs)}")
            
            # Upsert jobs to database
            inserted_count = 0
            updated_count = 0
            
            for job in unique_jobs.values():
                existing = await self.db.jobs.find_one(
                    {"job_id": job["job_id"]},
                    {"_id": 0}
                )
                
                if existing:
                    # Update existing job
                    await self.db.jobs.update_one(
                        {"job_id": job["job_id"]},
                        {"$set": job}
                    )
                    updated_count += 1
                else:
                    # Insert new job
                    await self.db.jobs.insert_one(job)
                    inserted_count += 1
            
            logger.info(f"Job sync complete: {inserted_count} inserted, {updated_count} updated")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error in job sync: {e}", exc_info=True)
    
    async def get_sync_status(self) -> Dict:
        """Get status of last sync"""
        try:
            # Count external jobs by source
            arbeitnow_count = await self.db.jobs.count_documents({"source": "arbeitnow"})
            greenhouse_count = await self.db.jobs.count_documents({"source": "greenhouse"})
            internal_count = await self.db.jobs.count_documents({"is_external": {"$ne": True}})
            
            # Get last sync time
            last_job = await self.db.jobs.find_one(
                {"is_external": True},
                {"_id": 0, "last_synced": 1},
                sort=[("last_synced", -1)]
            )
            
            last_synced = last_job.get("last_synced") if last_job else None
            
            return {
                "total_external_jobs": arbeitnow_count + greenhouse_count,
                "arbeitnow_jobs": arbeitnow_count,
                "greenhouse_jobs": greenhouse_count,
                "internal_jobs": internal_count,
                "last_synced": last_synced,
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {"status": "error", "error": str(e)}
