import pandas as pd
import asyncio
import random
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone, timedelta
import uuid

# Job titles by industry
JOB_TITLES = {
    "54 - Professional, Scientific, and Technical Services": [
        "Software Engineer", "Senior Software Engineer", "Staff Software Engineer", "Principal Engineer",
        "Data Scientist", "Machine Learning Engineer", "DevOps Engineer", "Cloud Architect",
        "Solutions Architect", "Technical Program Manager", "Engineering Manager", "Product Manager",
        "Data Engineer", "Backend Engineer", "Frontend Engineer", "Full Stack Developer",
        "Systems Engineer", "Security Engineer", "Site Reliability Engineer", "QA Engineer"
    ],
    "51 - Information": [
        "Software Developer", "Senior Developer", "Tech Lead", "Platform Engineer",
        "Infrastructure Engineer", "Database Administrator", "Network Engineer", "IT Manager",
        "Application Developer", "Systems Analyst", "Business Analyst", "Project Manager"
    ],
    "31-33 - Manufacturing": [
        "Hardware Engineer", "Electrical Engineer", "Mechanical Engineer", "Process Engineer",
        "Manufacturing Engineer", "Quality Engineer", "Supply Chain Analyst", "Operations Manager",
        "R&D Engineer", "Design Engineer", "Test Engineer", "Automation Engineer"
    ],
    "62 - Health Care and Social Assistance": [
        "Physician", "Surgeon", "Registered Nurse", "Pharmacist", "Physical Therapist",
        "Medical Researcher", "Clinical Data Analyst", "Healthcare IT Specialist",
        "Biostatistician", "Research Scientist", "Lab Technician", "Medical Director"
    ],
    "52 - Finance and Insurance": [
        "Financial Analyst", "Quantitative Analyst", "Risk Analyst", "Investment Banker",
        "Portfolio Manager", "Actuarial Analyst", "Compliance Officer", "Financial Engineer",
        "Data Analyst", "Business Intelligence Analyst", "Fraud Analyst", "Credit Analyst"
    ],
    "61 - Educational Services": [
        "Professor", "Research Associate", "Postdoctoral Researcher", "Academic Advisor",
        "Curriculum Developer", "Instructional Designer", "Education Consultant", "Dean"
    ],
    "44-45 - Retail Trade": [
        "Software Engineer", "Data Scientist", "Product Manager", "Supply Chain Analyst",
        "E-commerce Manager", "Logistics Analyst", "Merchandising Analyst", "UX Designer"
    ],
    "55 - Management of Companies and Enterprises": [
        "Management Consultant", "Strategy Analyst", "Operations Analyst", "Financial Analyst",
        "Business Development Manager", "Project Manager", "Program Manager", "Director of Operations"
    ]
}

# Salary ranges by wage level (annual)
SALARY_RANGES = {
    1: (70000, 100000),   # Entry level
    2: (100000, 150000),  # Qualified
    3: (150000, 200000),  # Experienced
    4: (200000, 350000),  # Expert
}

# Prevailing wage percentages by level
PREVAILING_PERCENTAGES = {
    1: 0.70,  # 17th percentile
    2: 0.78,  # 34th percentile
    3: 0.85,  # 50th percentile
    4: 0.90,  # 67th percentile
}

REQUIREMENTS_POOL = [
    "Bachelor's degree in Computer Science or related field",
    "Master's degree preferred",
    "PhD in relevant field",
    "5+ years of professional experience",
    "3+ years of relevant experience",
    "8+ years of industry experience",
    "10+ years of experience",
    "Strong communication skills",
    "Experience with agile methodologies",
    "Python programming",
    "Java/Kotlin proficiency",
    "JavaScript/TypeScript",
    "React/Vue/Angular experience",
    "Cloud platforms (AWS/GCP/Azure)",
    "SQL and NoSQL databases",
    "Machine learning frameworks",
    "Data analysis skills",
    "Leadership experience",
    "Cross-functional collaboration",
    "Problem-solving abilities",
]

BENEFITS_POOL = [
    "Health insurance", "Dental and vision", "401(k) matching", "Stock options/RSUs",
    "Unlimited PTO", "Flexible work hours", "Remote work options", "Signing bonus",
    "Relocation assistance", "Professional development", "Gym membership", "Free meals",
    "Parental leave", "Commuter benefits", "Life insurance", "Disability coverage"
]

async def import_data():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("Loading Excel data...")
    df = pd.read_excel('/app/employer_data.xlsx')
    
    # Clean data
    df = df.dropna(subset=['Employer (Petitioner) Name'])
    
    # Calculate totals
    df['Total_Approvals'] = (
        df['New Employment Approval'] + df['Continuation Approval'] + 
        df['Change with Same Employer Approval'] + df['New Concurrent Approval'] + 
        df['Change of Employer Approval'] + df['Amended Approval']
    )
    df['Total_Denials'] = (
        df['New Employment Denial'] + df['Continuation Denial'] + 
        df['Change with Same Employer Denial'] + df['New Concurrent Denial'] + 
        df['Change of Employer Denial'] + df['Amended Denial']
    )
    
    # Get top 500 sponsors
    top_sponsors = df.nlargest(500, 'Total_Approvals')
    
    print(f"Processing {len(top_sponsors)} top H1B sponsors...")
    
    # Clear existing data
    await db.companies.delete_many({})
    await db.jobs.delete_many({})
    
    companies_created = 0
    jobs_created = 0
    
    for _, row in top_sponsors.iterrows():
        company_name = str(row['Employer (Petitioner) Name']).strip()
        if not company_name or company_name == 'nan':
            continue
            
        company_id = f"comp_{uuid.uuid4().hex[:12]}"
        industry = str(row['Industry (NAICS) Code']) if pd.notna(row['Industry (NAICS) Code']) else "54 - Professional, Scientific, and Technical Services"
        city = str(row['Petitioner City']).strip() if pd.notna(row['Petitioner City']) else "Unknown"
        state = str(row['Petitioner State']).strip() if pd.notna(row['Petitioner State']) else "CA"
        approvals = int(row['Total_Approvals'])
        denials = int(row['Total_Denials'])
        
        # Clean company name for logo URL
        clean_name = company_name.lower().replace(' ', '').replace(',', '').replace('.', '').replace('inc', '').replace('llc', '').replace('corp', '').replace('ltd', '')[:20]
        
        # Estimate average salary based on approvals (higher approvals = bigger company = higher salaries)
        base_salary = 120000 + min(approvals * 5, 100000)
        
        # Determine company size
        if approvals > 5000:
            size = "10,000+"
        elif approvals > 1000:
            size = "5,000-10,000"
        elif approvals > 500:
            size = "1,000-5,000"
        elif approvals > 100:
            size = "500-1,000"
        else:
            size = "100-500"
        
        # Create company
        company_doc = {
            "company_id": company_id,
            "name": company_name,
            "logo_url": f"https://logo.clearbit.com/{clean_name}.com",
            "industry": industry.split(' - ')[-1] if ' - ' in industry else industry,
            "size": size,
            "location": f"{city}, {state}",
            "description": f"{company_name} is an active H1B sponsor with {approvals} approved petitions in FY2025.",
            "h1b_approvals": approvals,
            "h1b_denials": denials,
            "avg_salary": base_salary,
            "founded_year": None,
            "website": f"https://{clean_name}.com"
        }
        
        await db.companies.insert_one(company_doc)
        companies_created += 1
        
        # Generate jobs for this company (more jobs for bigger sponsors)
        num_jobs = min(max(approvals // 500, 1), 10)
        
        # Get relevant job titles
        job_titles = JOB_TITLES.get(industry, JOB_TITLES["54 - Professional, Scientific, and Technical Services"])
        
        for _ in range(num_jobs):
            job_title = random.choice(job_titles)
            
            # Determine wage level based on job title
            if "Senior" in job_title or "Lead" in job_title or "Manager" in job_title:
                wage_level = random.choice([3, 4])
            elif "Principal" in job_title or "Staff" in job_title or "Director" in job_title or "Architect" in job_title:
                wage_level = 4
            elif "Junior" in job_title or "Associate" in job_title or "Entry" in job_title:
                wage_level = 1
            else:
                wage_level = random.choice([2, 3])
            
            salary_min, salary_max = SALARY_RANGES[wage_level]
            base_salary = random.randint(salary_min, salary_max)
            prevailing_wage = int(base_salary * PREVAILING_PERCENTAGES[wage_level])
            
            job_doc = {
                "job_id": f"job_{uuid.uuid4().hex[:12]}",
                "job_title": job_title,
                "company_name": company_name,
                "company_id": company_id,
                "location": f"{city}, {state}",
                "state": state,
                "wage_level": wage_level,
                "base_salary": base_salary,
                "prevailing_wage": prevailing_wage,
                "job_description": f"Join {company_name} as a {job_title}. We are an active H1B sponsor with a strong track record of visa approvals. This role offers competitive compensation and benefits.",
                "requirements": random.sample(REQUIREMENTS_POOL, k=random.randint(4, 7)),
                "benefits": random.sample(BENEFITS_POOL, k=random.randint(5, 8)),
                "visa_sponsorship": True,
                "posted_date": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))).isoformat(),
                "employment_type": "Full-time",
                "lca_case_number": f"I-200-25{random.randint(100, 999)}-{random.randint(100000, 999999)}"
            }
            
            await db.jobs.insert_one(job_doc)
            jobs_created += 1
    
    # Create indexes
    await db.companies.create_index("company_id")
    await db.companies.create_index("name")
    await db.companies.create_index("h1b_approvals")
    
    await db.jobs.create_index("job_id")
    await db.jobs.create_index("company_id")
    await db.jobs.create_index("company_name")
    await db.jobs.create_index("state")
    await db.jobs.create_index("wage_level")
    await db.jobs.create_index("base_salary")
    
    print(f"\n✅ Import complete!")
    print(f"   Companies created: {companies_created}")
    print(f"   Jobs created: {jobs_created}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(import_data())
