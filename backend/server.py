from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="H1B Job Board API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import job aggregator and scheduler
from job_aggregator import JobAggregator
from job_scheduler import JobScheduler

# Initialize job aggregator and scheduler (will be started on app startup)
job_aggregator = None
job_scheduler = None

# ================== MODELS ==================

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class H1BJob(BaseModel):
    model_config = ConfigDict(extra="ignore")
    job_id: str = Field(default_factory=lambda: f"job_{uuid.uuid4().hex[:12]}")
    job_title: str
    company_name: str
    company_id: str
    location: str
    state: str
    wage_level: int  # 1-4
    base_salary: float
    prevailing_wage: float
    job_description: str
    requirements: List[str] = []
    benefits: List[str] = []
    visa_sponsorship: bool = True
    posted_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    employment_type: str = "Full-time"
    lca_case_number: Optional[str] = None
    # External job fields
    source: Optional[str] = None  # arbeitnow, greenhouse, linkedin, indeed, etc.
    external_url: Optional[str] = None  # Original job posting URL
    external_id: Optional[str] = None  # Unique ID from source
    is_external: Optional[bool] = False  # True for jobs from external APIs
    last_synced: Optional[str] = None  # Last sync timestamp

class Company(BaseModel):
    model_config = ConfigDict(extra="ignore")
    company_id: str = Field(default_factory=lambda: f"comp_{uuid.uuid4().hex[:12]}")
    name: str
    logo_url: Optional[str] = None
    industry: str
    size: str
    location: str
    description: str
    h1b_approvals: int = 0
    h1b_denials: int = 0
    avg_salary: float = 0
    founded_year: Optional[int] = None
    website: Optional[str] = None

class SavedJob(BaseModel):
    model_config = ConfigDict(extra="ignore")
    saved_id: str = Field(default_factory=lambda: f"saved_{uuid.uuid4().hex[:12]}")
    user_id: str
    job_id: str
    saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JobApplication(BaseModel):
    model_config = ConfigDict(extra="ignore")
    application_id: str = Field(default_factory=lambda: f"app_{uuid.uuid4().hex[:12]}")
    user_id: str
    job_id: str
    status: str = "Applied"  # Applied, In Review, Interview, Offer, Rejected
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ================== AUTH HELPERS ==================

async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from session token (cookie or header)"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        return None
    
    session_doc = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    if not session_doc:
        return None
    
    # Check expiry
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    
    user_doc = await db.users.find_one(
        {"user_id": session_doc["user_id"]},
        {"_id": 0}
    )
    if not user_doc:
        return None
    
    return User(**user_doc)

async def require_auth(request: Request) -> User:
    """Require authentication"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# ================== AUTH ROUTES ==================

@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    """Exchange session_id for session_token"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Call Emergent auth service
    async with httpx.AsyncClient() as client:
        try:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            if auth_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session_id")
            
            auth_data = auth_response.json()
        except Exception as e:
            logger.error(f"Auth error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    session_token = auth_data.get("session_token")
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": auth_data["email"]}, {"_id": 0})
    if existing_user:
        user_id = existing_user["user_id"]
    else:
        # Create new user
        user_doc = {
            "user_id": user_id,
            "email": auth_data["email"],
            "name": auth_data.get("name", ""),
            "picture": auth_data.get("picture", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
    
    # Store session
    session_doc = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + __import__('datetime').timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.user_sessions.insert_one(session_doc)
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7*24*60*60
    )
    
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user_doc

@api_router.get("/auth/me")
async def get_me(request: Request):
    """Get current user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user.model_dump()

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    response.delete_cookie("session_token", path="/", samesite="none", secure=True)
    return {"message": "Logged out"}

# ================== JOB ROUTES ==================

@api_router.get("/jobs")
async def get_jobs(
    search: Optional[str] = None,
    state: Optional[str] = None,
    wage_level: Optional[int] = None,
    min_salary: Optional[float] = None,
    max_salary: Optional[float] = None,
    company: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get jobs with filters"""
    query = {}
    
    if search:
        query["$or"] = [
            {"job_title": {"$regex": search, "$options": "i"}},
            {"company_name": {"$regex": search, "$options": "i"}},
            {"location": {"$regex": search, "$options": "i"}}
        ]
    
    if state:
        query["state"] = state
    
    if wage_level:
        query["wage_level"] = wage_level
    
    if min_salary:
        query["base_salary"] = {"$gte": min_salary}
    
    if max_salary:
        if "base_salary" in query:
            query["base_salary"]["$lte"] = max_salary
        else:
            query["base_salary"] = {"$lte": max_salary}
    
    if company:
        query["company_name"] = {"$regex": company, "$options": "i"}
    
    # Sort by: 1) external jobs first (is_external DESC), 2) posted_date DESC
    cursor = db.jobs.find(query, {"_id": 0}).skip(skip).limit(limit).sort([
        ("is_external", -1),  # External jobs first
        ("posted_date", -1)   # Then by date
    ])
    jobs = await cursor.to_list(length=limit)
    
    total = await db.jobs.count_documents(query)
    
    return {"jobs": jobs, "total": total, "skip": skip, "limit": limit}

@api_router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get single job"""
    job = await db.jobs.find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@api_router.get("/jobs/stats/wage-levels")
async def get_wage_stats():
    """Get wage level statistics"""
    pipeline = [
        {
            "$group": {
                "_id": "$wage_level",
                "count": {"$sum": 1},
                "avg_salary": {"$avg": "$base_salary"},
                "min_salary": {"$min": "$base_salary"},
                "max_salary": {"$max": "$base_salary"}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    stats = await db.jobs.aggregate(pipeline).to_list(None)
    return stats

@api_router.get("/jobs/stats/by-state")
async def get_state_stats():
    """Get jobs by state statistics"""
    pipeline = [
        {
            "$group": {
                "_id": "$state",
                "count": {"$sum": 1},
                "avg_salary": {"$avg": "$base_salary"}
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    stats = await db.jobs.aggregate(pipeline).to_list(None)
    return stats

# ================== COMPANY ROUTES ==================

@api_router.get("/companies")
async def get_companies(
    search: Optional[str] = None,
    industry: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """Get companies"""
    query = {}
    
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    if industry:
        query["industry"] = industry
    
    cursor = db.companies.find(query, {"_id": 0}).skip(skip).limit(limit).sort("h1b_approvals", -1)
    companies = await cursor.to_list(length=limit)
    
    total = await db.companies.count_documents(query)
    
    return {"companies": companies, "total": total}

@api_router.get("/companies/{company_id}")
async def get_company(company_id: str):
    """Get single company with job listings"""
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company's jobs
    jobs = await db.jobs.find({"company_id": company_id}, {"_id": 0}).limit(10).to_list(length=10)
    
    return {"company": company, "jobs": jobs}

# ================== SAVED JOBS ROUTES ==================

@api_router.get("/saved-jobs")
async def get_saved_jobs(request: Request):
    """Get user's saved jobs"""
    user = await require_auth(request)
    
    saved = await db.saved_jobs.find({"user_id": user.user_id}, {"_id": 0}).to_list(100)
    
    # Get full job details
    job_ids = [s["job_id"] for s in saved]
    jobs = await db.jobs.find({"job_id": {"$in": job_ids}}, {"_id": 0}).to_list(100)
    
    return {"saved_jobs": saved, "jobs": jobs}

@api_router.post("/saved-jobs/{job_id}")
async def save_job(job_id: str, request: Request):
    """Save a job"""
    user = await require_auth(request)
    
    # Check if already saved
    existing = await db.saved_jobs.find_one({"user_id": user.user_id, "job_id": job_id})
    if existing:
        raise HTTPException(status_code=400, detail="Job already saved")
    
    saved = SavedJob(user_id=user.user_id, job_id=job_id)
    doc = saved.model_dump()
    doc["saved_at"] = doc["saved_at"].isoformat()
    await db.saved_jobs.insert_one(doc)
    
    return {"message": "Job saved", "saved_id": saved.saved_id}

@api_router.delete("/saved-jobs/{job_id}")
async def unsave_job(job_id: str, request: Request):
    """Remove saved job"""
    user = await require_auth(request)
    
    result = await db.saved_jobs.delete_one({"user_id": user.user_id, "job_id": job_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Saved job not found")
    
    return {"message": "Job removed from saved"}

# ================== APPLICATION ROUTES ==================

@api_router.get("/applications")
async def get_applications(request: Request):
    """Get user's job applications"""
    user = await require_auth(request)
    
    applications = await db.applications.find({"user_id": user.user_id}, {"_id": 0}).to_list(100)
    
    # Get job details
    job_ids = [a["job_id"] for a in applications]
    jobs = await db.jobs.find({"job_id": {"$in": job_ids}}, {"_id": 0}).to_list(100)
    
    return {"applications": applications, "jobs": jobs}

@api_router.post("/applications/{job_id}")
async def create_application(job_id: str, request: Request):
    """Create job application"""
    user = await require_auth(request)
    
    # Check if already applied
    existing = await db.applications.find_one({"user_id": user.user_id, "job_id": job_id})
    if existing:
        raise HTTPException(status_code=400, detail="Already applied to this job")
    
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    
    application = JobApplication(
        user_id=user.user_id,
        job_id=job_id,
        notes=body.get("notes")
    )
    doc = application.model_dump()
    doc["applied_at"] = doc["applied_at"].isoformat()
    doc["updated_at"] = doc["updated_at"].isoformat()
    await db.applications.insert_one(doc)
    
    return {"message": "Application submitted", "application_id": application.application_id}

@api_router.put("/applications/{application_id}")
async def update_application(application_id: str, request: Request):
    """Update application status"""
    user = await require_auth(request)
    body = await request.json()
    
    result = await db.applications.update_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"$set": {
            "status": body.get("status"),
            "notes": body.get("notes"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {"message": "Application updated"}

# ================== SEED DATA ==================

@api_router.post("/seed")
async def seed_data():
    """Seed initial data"""
    # Clear existing data
    await db.jobs.delete_many({})
    await db.companies.delete_many({})
    
    # Create companies
    companies = [
        Company(
            company_id="comp_google",
            name="Google",
            logo_url="https://logo.clearbit.com/google.com",
            industry="Technology",
            size="10,000+",
            location="Mountain View, CA",
            description="A multinational technology company specializing in Internet-related services and products.",
            h1b_approvals=8500,
            h1b_denials=120,
            avg_salary=185000,
            founded_year=1998,
            website="https://google.com"
        ),
        Company(
            company_id="comp_meta",
            name="Meta",
            logo_url="https://logo.clearbit.com/meta.com",
            industry="Technology",
            size="10,000+",
            location="Menlo Park, CA",
            description="A technology conglomerate focusing on social networking and virtual reality.",
            h1b_approvals=5200,
            h1b_denials=85,
            avg_salary=178000,
            founded_year=2004,
            website="https://meta.com"
        ),
        Company(
            company_id="comp_amazon",
            name="Amazon",
            logo_url="https://logo.clearbit.com/amazon.com",
            industry="E-Commerce/Technology",
            size="10,000+",
            location="Seattle, WA",
            description="The world's largest online marketplace and cloud computing platform.",
            h1b_approvals=12000,
            h1b_denials=280,
            avg_salary=165000,
            founded_year=1994,
            website="https://amazon.com"
        ),
        Company(
            company_id="comp_microsoft",
            name="Microsoft",
            logo_url="https://logo.clearbit.com/microsoft.com",
            industry="Technology",
            size="10,000+",
            location="Redmond, WA",
            description="A technology corporation that develops, manufactures, licenses, and sells computer software and electronics.",
            h1b_approvals=9800,
            h1b_denials=150,
            avg_salary=175000,
            founded_year=1975,
            website="https://microsoft.com"
        ),
        Company(
            company_id="comp_apple",
            name="Apple",
            logo_url="https://logo.clearbit.com/apple.com",
            industry="Technology",
            size="10,000+",
            location="Cupertino, CA",
            description="A technology company that designs, develops, and sells consumer electronics, software, and online services.",
            h1b_approvals=4500,
            h1b_denials=60,
            avg_salary=190000,
            founded_year=1976,
            website="https://apple.com"
        ),
        Company(
            company_id="comp_netflix",
            name="Netflix",
            logo_url="https://logo.clearbit.com/netflix.com",
            industry="Entertainment/Technology",
            size="5,000-10,000",
            location="Los Gatos, CA",
            description="A streaming entertainment service with millions of paid memberships globally.",
            h1b_approvals=850,
            h1b_denials=25,
            avg_salary=220000,
            founded_year=1997,
            website="https://netflix.com"
        ),
        Company(
            company_id="comp_salesforce",
            name="Salesforce",
            logo_url="https://logo.clearbit.com/salesforce.com",
            industry="Cloud Computing",
            size="10,000+",
            location="San Francisco, CA",
            description="A cloud-based software company providing customer relationship management services.",
            h1b_approvals=3200,
            h1b_denials=55,
            avg_salary=168000,
            founded_year=1999,
            website="https://salesforce.com"
        ),
        Company(
            company_id="comp_uber",
            name="Uber",
            logo_url="https://logo.clearbit.com/uber.com",
            industry="Transportation/Technology",
            size="10,000+",
            location="San Francisco, CA",
            description="A technology company offering ride-hailing, food delivery, and freight transport services.",
            h1b_approvals=1800,
            h1b_denials=40,
            avg_salary=172000,
            founded_year=2009,
            website="https://uber.com"
        ),
    ]
    
    for company in companies:
        doc = company.model_dump()
        await db.companies.insert_one(doc)
    
    # Create jobs
    jobs_data = [
        # Google Jobs
        {"job_title": "Senior Software Engineer", "company_name": "Google", "company_id": "comp_google", "location": "Mountain View, CA", "state": "CA", "wage_level": 4, "base_salary": 210000, "prevailing_wage": 145000, "job_description": "Design and implement large-scale distributed systems. Lead technical projects and mentor junior engineers.", "requirements": ["8+ years experience", "Python/Java/Go", "Distributed systems", "Machine learning"], "benefits": ["Health insurance", "401k matching", "Stock options", "Unlimited PTO"], "lca_case_number": "I-200-24001-123456"},
        {"job_title": "Software Engineer III", "company_name": "Google", "company_id": "comp_google", "location": "New York, NY", "state": "NY", "wage_level": 3, "base_salary": 185000, "prevailing_wage": 130000, "job_description": "Build and maintain core infrastructure services. Collaborate with cross-functional teams.", "requirements": ["5+ years experience", "C++/Python", "Cloud platforms", "API design"], "benefits": ["Health insurance", "401k matching", "Stock options", "Gym membership"], "lca_case_number": "I-200-24001-234567"},
        {"job_title": "Data Scientist", "company_name": "Google", "company_id": "comp_google", "location": "Seattle, WA", "state": "WA", "wage_level": 3, "base_salary": 178000, "prevailing_wage": 125000, "job_description": "Analyze large datasets to drive product decisions. Build ML models for search ranking.", "requirements": ["MS in CS/Statistics", "Python/R", "TensorFlow/PyTorch", "SQL"], "benefits": ["Health insurance", "401k matching", "Stock options"], "lca_case_number": "I-200-24001-345678"},
        
        # Meta Jobs
        {"job_title": "Machine Learning Engineer", "company_name": "Meta", "company_id": "comp_meta", "location": "Menlo Park, CA", "state": "CA", "wage_level": 4, "base_salary": 225000, "prevailing_wage": 150000, "job_description": "Develop and deploy ML models for content recommendation and ad targeting systems.", "requirements": ["7+ years ML experience", "PyTorch", "Distributed training", "PhD preferred"], "benefits": ["Health insurance", "RSUs", "Free meals", "Childcare"], "lca_case_number": "I-200-24002-123456"},
        {"job_title": "Frontend Engineer", "company_name": "Meta", "company_id": "comp_meta", "location": "Austin, TX", "state": "TX", "wage_level": 2, "base_salary": 145000, "prevailing_wage": 105000, "job_description": "Build user interfaces for Facebook and Instagram. Optimize performance for billions of users.", "requirements": ["3+ years React", "TypeScript", "Performance optimization", "A11y"], "benefits": ["Health insurance", "RSUs", "Remote work"], "lca_case_number": "I-200-24002-234567"},
        {"job_title": "Product Manager", "company_name": "Meta", "company_id": "comp_meta", "location": "New York, NY", "state": "NY", "wage_level": 3, "base_salary": 195000, "prevailing_wage": 140000, "job_description": "Lead product strategy for WhatsApp Business features. Drive roadmap and execution.", "requirements": ["5+ years PM experience", "B2B products", "Data-driven", "MBA preferred"], "benefits": ["Health insurance", "RSUs", "Stock options"], "lca_case_number": "I-200-24002-345678"},
        
        # Amazon Jobs
        {"job_title": "Software Development Engineer II", "company_name": "Amazon", "company_id": "comp_amazon", "location": "Seattle, WA", "state": "WA", "wage_level": 2, "base_salary": 155000, "prevailing_wage": 110000, "job_description": "Build scalable services for AWS. Design and implement new features for cloud computing platform.", "requirements": ["4+ years experience", "Java/Python", "AWS services", "System design"], "benefits": ["Health insurance", "RSUs", "Signing bonus"], "lca_case_number": "I-200-24003-123456"},
        {"job_title": "Senior Solutions Architect", "company_name": "Amazon", "company_id": "comp_amazon", "location": "San Francisco, CA", "state": "CA", "wage_level": 4, "base_salary": 205000, "prevailing_wage": 148000, "job_description": "Design cloud architectures for enterprise clients. Lead technical discussions and POCs.", "requirements": ["10+ years experience", "AWS certified", "Enterprise sales", "Public speaking"], "benefits": ["Health insurance", "RSUs", "Travel perks"], "lca_case_number": "I-200-24003-234567"},
        {"job_title": "Data Engineer", "company_name": "Amazon", "company_id": "comp_amazon", "location": "Arlington, VA", "state": "VA", "wage_level": 2, "base_salary": 148000, "prevailing_wage": 108000, "job_description": "Build data pipelines for business intelligence. Optimize ETL processes at scale.", "requirements": ["3+ years experience", "Spark/Hadoop", "SQL", "Python"], "benefits": ["Health insurance", "RSUs", "Relocation"], "lca_case_number": "I-200-24003-345678"},
        
        # Microsoft Jobs
        {"job_title": "Principal Software Engineer", "company_name": "Microsoft", "company_id": "comp_microsoft", "location": "Redmond, WA", "state": "WA", "wage_level": 4, "base_salary": 235000, "prevailing_wage": 155000, "job_description": "Lead architecture for Azure AI services. Drive technical vision and roadmap.", "requirements": ["12+ years experience", "C#/.NET", "Cloud architecture", "AI/ML"], "benefits": ["Health insurance", "401k", "Stock options", "Sabbatical"], "lca_case_number": "I-200-24004-123456"},
        {"job_title": "Software Engineer", "company_name": "Microsoft", "company_id": "comp_microsoft", "location": "Atlanta, GA", "state": "GA", "wage_level": 1, "base_salary": 115000, "prevailing_wage": 85000, "job_description": "Develop features for Microsoft 365. Participate in agile development processes.", "requirements": ["1+ years experience", "C#/TypeScript", "Git", "Agile"], "benefits": ["Health insurance", "401k", "Stock purchase"], "lca_case_number": "I-200-24004-234567"},
        {"job_title": "Cloud Solutions Engineer", "company_name": "Microsoft", "company_id": "comp_microsoft", "location": "Chicago, IL", "state": "IL", "wage_level": 3, "base_salary": 175000, "prevailing_wage": 125000, "job_description": "Help enterprise customers adopt Azure. Design and implement cloud solutions.", "requirements": ["6+ years experience", "Azure certified", "Networking", "Security"], "benefits": ["Health insurance", "401k", "Remote work"], "lca_case_number": "I-200-24004-345678"},
        
        # Apple Jobs
        {"job_title": "iOS Engineer", "company_name": "Apple", "company_id": "comp_apple", "location": "Cupertino, CA", "state": "CA", "wage_level": 3, "base_salary": 195000, "prevailing_wage": 138000, "job_description": "Develop core iOS features. Work on performance optimization and new capabilities.", "requirements": ["5+ years iOS", "Swift/Objective-C", "UIKit/SwiftUI", "Performance tuning"], "benefits": ["Health insurance", "RSUs", "Product discounts"], "lca_case_number": "I-200-24005-123456"},
        {"job_title": "Hardware Engineer", "company_name": "Apple", "company_id": "comp_apple", "location": "San Diego, CA", "state": "CA", "wage_level": 4, "base_salary": 215000, "prevailing_wage": 150000, "job_description": "Design custom silicon for Apple devices. Work on chip architecture and verification.", "requirements": ["8+ years experience", "Verilog/VHDL", "ASIC design", "Low power"], "benefits": ["Health insurance", "RSUs", "Relocation"], "lca_case_number": "I-200-24005-234567"},
        
        # Netflix Jobs
        {"job_title": "Senior Backend Engineer", "company_name": "Netflix", "company_id": "comp_netflix", "location": "Los Gatos, CA", "state": "CA", "wage_level": 4, "base_salary": 280000, "prevailing_wage": 165000, "job_description": "Build streaming infrastructure serving millions of users. Optimize video delivery systems.", "requirements": ["8+ years experience", "Java/Python", "Microservices", "High scale systems"], "benefits": ["Unlimited PTO", "Top-of-market pay", "Stock options"], "lca_case_number": "I-200-24006-123456"},
        {"job_title": "Data Platform Engineer", "company_name": "Netflix", "company_id": "comp_netflix", "location": "Los Gatos, CA", "state": "CA", "wage_level": 3, "base_salary": 235000, "prevailing_wage": 145000, "job_description": "Build real-time data pipelines. Support analytics for content and business teams.", "requirements": ["5+ years experience", "Spark/Flink", "Kafka", "Python"], "benefits": ["Unlimited PTO", "Top-of-market pay"], "lca_case_number": "I-200-24006-234567"},
        
        # Salesforce Jobs
        {"job_title": "Full Stack Engineer", "company_name": "Salesforce", "company_id": "comp_salesforce", "location": "San Francisco, CA", "state": "CA", "wage_level": 2, "base_salary": 158000, "prevailing_wage": 115000, "job_description": "Build features for Salesforce platform. Develop both frontend and backend components.", "requirements": ["4+ years experience", "React/Node.js", "REST APIs", "SQL"], "benefits": ["Health insurance", "401k", "Volunteer time"], "lca_case_number": "I-200-24007-123456"},
        {"job_title": "DevOps Engineer", "company_name": "Salesforce", "company_id": "comp_salesforce", "location": "Indianapolis, IN", "state": "IN", "wage_level": 2, "base_salary": 142000, "prevailing_wage": 102000, "job_description": "Manage CI/CD pipelines. Automate infrastructure deployment and monitoring.", "requirements": ["3+ years experience", "Kubernetes", "Terraform", "AWS/GCP"], "benefits": ["Health insurance", "401k", "Remote work"], "lca_case_number": "I-200-24007-234567"},
        
        # Uber Jobs
        {"job_title": "Staff Software Engineer", "company_name": "Uber", "company_id": "comp_uber", "location": "San Francisco, CA", "state": "CA", "wage_level": 4, "base_salary": 245000, "prevailing_wage": 160000, "job_description": "Lead technical initiatives for rider experience. Architect systems for global scale.", "requirements": ["10+ years experience", "Go/Java", "Distributed systems", "Technical leadership"], "benefits": ["Uber credits", "RSUs", "Health insurance"], "lca_case_number": "I-200-24008-123456"},
        {"job_title": "Mobile Engineer - Android", "company_name": "Uber", "company_id": "comp_uber", "location": "New York, NY", "state": "NY", "wage_level": 2, "base_salary": 162000, "prevailing_wage": 118000, "job_description": "Build features for Uber driver and rider apps. Optimize battery and network usage.", "requirements": ["3+ years Android", "Kotlin", "RxJava", "Clean architecture"], "benefits": ["Uber credits", "RSUs", "Gym membership"], "lca_case_number": "I-200-24008-234567"},
    ]
    
    for job_data in jobs_data:
        job = H1BJob(**job_data)
        doc = job.model_dump()
        doc["posted_date"] = doc["posted_date"].isoformat()
        await db.jobs.insert_one(doc)
    
    return {"message": f"Seeded {len(companies)} companies and {len(jobs_data)} jobs"}

# ================== HEALTH CHECK ==================

@api_router.get("/")
async def root():
    return {"message": "H1B Job Board API", "status": "healthy"}

@api_router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@api_router.get("/jobs/sync/status")
async def get_sync_status():
    """Get job sync status"""
    if not job_aggregator:
        return {"status": "not_initialized"}
    
    agg_status = await job_aggregator.get_sync_status()
    
    if job_scheduler:
        scheduler_status = job_scheduler.get_status()
        agg_status.update(scheduler_status)
    
    return agg_status

@api_router.post("/jobs/sync/trigger")
async def trigger_sync():
    """Manually trigger job sync"""
    if not job_aggregator:
        raise HTTPException(status_code=503, detail="Job aggregator not initialized")
    
    # Run sync in background
    import asyncio
    asyncio.create_task(job_aggregator.sync_jobs())
    
    return {"message": "Job sync triggered", "status": "running"}

@api_router.get("/jobs/wage-prediction")
async def predict_wage_level(
    job_title: str,
    state: str = "CA",
    salary: float = 0
):
    """AI-powered wage level prediction"""
    from wage_predictor import wage_predictor
    
    # Load data if not already loaded
    if not wage_predictor.loaded:
        wage_predictor.load_data()
    
    # Predict wage level
    predicted_level = wage_predictor.predict_wage_level(job_title, state, salary)
    
    # Get suggested salary range for the predicted level
    min_salary, max_salary = wage_predictor.get_suggested_salary_range(job_title, state, predicted_level)
    
    # Get OFLC wage data
    wage_levels = wage_predictor.get_wage_levels_for_job(job_title, state)
    
    return {
        "job_title": job_title,
        "state": state,
        "provided_salary": salary,
        "predicted_level": predicted_level,
        "suggested_salary_range": {
            "min": round(min_salary, 2),
            "max": round(max_salary, 2)
        },
        "oflc_wage_levels": {
            "level1": round(wage_levels.get('level1', 0), 2) if wage_levels else 0,
            "level2": round(wage_levels.get('level2', 0), 2) if wage_levels else 0,
            "level3": round(wage_levels.get('level3', 0), 2) if wage_levels else 0,
            "level4": round(wage_levels.get('level4', 0), 2) if wage_levels else 0,
        } if wage_levels else None
    }

# Include the router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize and start job aggregator on startup"""
    global job_aggregator, job_scheduler
    
    logger.info("Starting H1B Job Board API...")
    logger.info("Initializing job aggregator and scheduler...")
    
    job_aggregator = JobAggregator(db)
    job_scheduler = JobScheduler(job_aggregator)
    
    # Start the scheduler
    job_scheduler.start()
    
    logger.info("Job aggregator and scheduler initialized successfully!")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Cleanup on shutdown"""
    global job_aggregator, job_scheduler
    
    logger.info("Shutting down...")
    
    if job_scheduler:
        job_scheduler.stop()
    
    if job_aggregator:
        await job_aggregator.close()
    
    client.close()
    logger.info("Shutdown complete")
