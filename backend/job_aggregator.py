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
                    normalized = self.normalize_company_name(name)
                    company_names.add(normalized)
                    # Also add the original (in case it's already clean)
                    company_names.add(name)
            
            logger.info(f"Loaded {len(company_names)} H1B-sponsoring company name variations")
            return company_names
        except Exception as e:
            logger.error(f"Error loading H1B companies: {e}")
            return set()
    
    def normalize_company_name(self, name: str) -> str:
        """Normalize company name for matching - more aggressive normalization"""
        if not name:
            return ""
        
        name = name.lower().strip()
        
        # Remove common legal suffixes and variations
        suffixes = [
            " incorporated", " inc.", " inc", 
            " limited liability company", " llc", " l.l.c.", " l.l.c",
            " corporation", " corp.", " corp",
            " limited", " ltd.", " ltd",
            " company", " co.", " co",
            " llp", " l.l.p.",
            " technologies", " technology",
            " platforms", " platform",
            " services", " service"
        ]
        
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()
        
        # Remove special characters and extra spaces
        name = name.replace(",", "").replace(".", "").replace("-", " ")
        name = " ".join(name.split())  # Normalize whitespace
        
        return name
    
    def is_h1b_sponsor(self, company_name: str, h1b_companies: set) -> bool:
        """Check if company sponsors H1B - uses flexible matching"""
        if not company_name:
            return False
            
        # Try exact match first
        normalized = self.normalize_company_name(company_name)
        if normalized in h1b_companies:
            return True
        
        # Try with original casing
        if company_name.lower().strip() in h1b_companies:
            return True
        
        # Try partial match - if normalized name is a substring of any H1B company
        # or vice versa (for companies like "Google" vs "Google LLC")
        for h1b_company in h1b_companies:
            if len(normalized) >= 4 and len(h1b_company) >= 4:  # Avoid very short matches
                if normalized in h1b_company or h1b_company in normalized:
                    # Additional check: the match should be substantial (at least 70% of the shorter name)
                    shorter = min(len(normalized), len(h1b_company))
                    longer = max(len(normalized), len(h1b_company))
                    if shorter / longer >= 0.7:
                        return True
        
        return False
    
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
                logger.debug(f"Skipping Arbeitnow job - company '{company_name}' not an H1B sponsor")
                return None
            
            logger.info(f"✓ Matched Arbeitnow job from H1B sponsor: {company_name}")
            
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
            # Greenhouse doesn't include company name in JSON, derive from board_token
            board_token = job.get("board_token", "")
            
            # Map board tokens to proper company names
            token_to_company = {
                "gitlab": "GitLab",
                "stripe": "Stripe",
                "airbnb": "Airbnb",
                "lyft": "Lyft",
                "dropbox": "Dropbox",
                "coinbase": "Coinbase",
                "square": "Square",
                "robinhood": "Robinhood",
                "doordash": "DoorDash",
                "instacart": "Instacart",
                "reddit": "Reddit",
                "databricks": "Databricks",
                "snowflake": "Snowflake",
                "mongodb": "MongoDB",
                "plaid": "Plaid",
                "notion": "Notion",
                "figma": "Figma",
                "airtable": "Airtable",
                "asana": "Asana",
                "cloudflare": "Cloudflare",
            }
            
            company_name = token_to_company.get(board_token.lower(), board_token.title())
            
            # Filter for H1B sponsors
            if not self.is_h1b_sponsor(company_name, h1b_companies):
                logger.debug(f"Skipping Greenhouse job - company '{company_name}' not an H1B sponsor")
                return None
            
            logger.info(f"✓ Matched Greenhouse job from H1B sponsor: {company_name}")
            
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
            # Using well-known H1B-sponsoring companies that use Greenhouse
            greenhouse_tokens = [
                "gitlab",    # GitLab
                "stripe",    # Stripe
                "airbnb",    # Airbnb
                "lyft",      # Lyft
                "dropbox",   # Dropbox
                "coinbase",  # Coinbase
                "square",    # Square/Block
                "robinhood", # Robinhood
                "doordash",  # DoorDash
                "instacart", # Instacart
                "reddit",    # Reddit
                "databricks",# Databricks
                "snowflake", # Snowflake
                "mongodb",   # MongoDB
                "plaid",     # Plaid
                "notion",    # Notion
                "figma",     # Figma
                "airtable",  # Airtable
                "asana",     # Asana
                "cloudflare",# Cloudflare
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
