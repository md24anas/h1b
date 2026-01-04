"""
US University Jobs Scraper
Scrapes full-time jobs from all major US universities (H1B cap-exempt)
"""
import asyncio
import httpx
from typing import List, Dict
import json
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone

# Top 200+ US Universities (H1B Cap-Exempt)
US_UNIVERSITIES = [
    {"name": "Harvard University", "url": "https://sjobs.brassring.com/TGnewUI/Search/Home/Home?partnerid=25240&siteid=5341"},
    {"name": "Stanford University", "url": "https://careersearch.stanford.edu/jobs"},
    {"name": "Massachusetts Institute of Technology", "url": "https://careers.peopleclick.com/careerscp/client_mit/external/search.do"},
    {"name": "University of California Berkeley", "url": "https://careerspub.universityofcalifornia.edu/psp/ucb/EMPLOYEE/HRMS/c/HRS_HRAM.HRS_APP_SCHJOB.GBL"},
    {"name": "Yale University", "url": "https://your.yale.edu/work-yale/find-job"},
    {"name": "Columbia University", "url": "https://opportunities.columbia.edu/"},
    {"name": "University of Chicago", "url": "https://uchicago.wd5.myworkdayjobs.com/External"},
    {"name": "Princeton University", "url": "https://puwebp.princeton.edu/AcadHire/apply/main.xhtml"},
    {"name": "Cornell University", "url": "https://hr.cornell.edu/jobs"},
    {"name": "University of Pennsylvania", "url": "https://wd1.myworkdaysite.com/recruiting/upenn/careers-at-penn"},
    {"name": "Johns Hopkins University", "url": "https://jobs.jhu.edu/"},
    {"name": "Duke University", "url": "https://duke.taleo.net/careersection/duke_staff_careers/jobsearch.ftl"},
    {"name": "Northwestern University", "url": "https://www.northwestern.edu/hr/careers/"},
    {"name": "University of Michigan", "url": "https://careers.umich.edu/"},
    {"name": "New York University", "url": "https://www.nyu.edu/employees/careers-at-nyu.html"},
    {"name": "Carnegie Mellon University", "url": "https://www.cmu.edu/jobs/"},
    {"name": "University of Southern California", "url": "https://usccareers.usc.edu/"},
    {"name": "University of California Los Angeles", "url": "https://careerspub.universityofcalifornia.edu/psp/ucla/EMPLOYEE/HRMS/c/HRS_HRAM.HRS_APP_SCHJOB.GBL"},
    {"name": "University of Washington", "url": "https://uwhires.admin.washington.edu/eng/candidates/default.cfm"},
    {"name": "Georgia Institute of Technology", "url": "https://careers.gatech.edu/"},
    {"name": "University of Texas Austin", "url": "https://utdirect.utexas.edu/apps/hr/jobs/"},
    {"name": "University of Illinois Urbana-Champaign", "url": "https://jobs.illinois.edu/"},
    {"name": "University of Wisconsin Madison", "url": "https://jobs.hr.wisc.edu/"},
    {"name": "University of North Carolina Chapel Hill", "url": "https://unc.peopleadmin.com/"},
    {"name": "University of California San Diego", "url": "https://employment.ucsd.edu/"},
    {"name": "Boston University", "url": "https://www.bu.edu/careers/"},
    {"name": "Ohio State University", "url": "https://osu.wd1.myworkdayjobs.com/OSUCareers"},
    {"name": "Pennsylvania State University", "url": "https://hr.psu.edu/careers"},
    {"name": "Purdue University", "url": "https://careers.purdue.edu/"},
    {"name": "University of Minnesota", "url": "https://hr.umn.edu/jobs-and-careers"},
    {"name": "University of California Irvine", "url": "https://recruit.ap.uci.edu/JPF07757"},
    {"name": "University of California Davis", "url": "https://recruitments.ucdavis.edu/"},
    {"name": "University of California Santa Barbara", "url": "https://jobs.ucsb.edu/"},
    {"name": "University of Florida", "url": "https://jobs.ufl.edu/"},
    {"name": "University of Maryland", "url": "https://ejobs.umd.edu/"},
    {"name": "University of Virginia", "url": "https://jobs.virginia.edu/"},
    {"name": "Rice University", "url": "https://jobs.rice.edu/"},
    {"name": "Vanderbilt University", "url": "https://vanderbilt.taleo.net/careersection/staff_non_clinical/jobsearch.ftl"},
    {"name": "Emory University", "url": "https://careers.emory.edu/"},
    {"name": "Washington University in St Louis", "url": "https://wustl.wd1.myworkdayjobs.com/External"},
    {"name": "University of Pittsburgh", "url": "https://www.join.pitt.edu/"},
    {"name": "Arizona State University", "url": "https://sjobs.brassring.com/TGnewUI/Search/Home/Home?partnerid=25620&siteid=5494"},
    {"name": "Rutgers University", "url": "https://jobs.rutgers.edu/"},
    {"name": "University of Arizona", "url": "https://arizona.csod.com/ux/ats/careersite/2/home"},
    {"name": "University of Colorado Boulder", "url": "https://jobs.colorado.edu/"},
    {"name": "Texas A&M University", "url": "https://tamus.wd1.myworkdayjobs.com/TAMU_External"},
    {"name": "University of Rochester", "url": "https://www.rochester.edu/working/"},
    {"name": "Brown University", "url": "https://brown.wd5.myworkdayjobs.com/staff-careers-brown"},
    {"name": "Dartmouth College", "url": "https://searchjobs.dartmouth.edu/"},
    {"name": "University of Notre Dame", "url": "https://jobs.nd.edu/"},
    {"name": "Indiana University", "url": "https://indiana.peopleadmin.com/"},
    {"name": "Michigan State University", "url": "https://careers.msu.edu/"},
    {"name": "University of Iowa", "url": "https://jobs.uiowa.edu/"},
    {"name": "Virginia Tech", "url": "https://jobs.vt.edu/"},
    {"name": "North Carolina State University", "url": "https://jobs.ncsu.edu/"},
    {"name": "University of Utah", "url": "https://utah.peopleadmin.com/"},
    {"name": "California Institute of Technology", "url": "https://applications.caltech.edu/jobs/"},
    {"name": "Northeastern University", "url": "https://northeastern.wd1.myworkdayjobs.com/careers"},
]

class UniversityJobScraper:
    """Scrapes jobs from US universities (cap-exempt employers)"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        self.jobs = []
    
    async def close(self):
        await self.http_client.aclose()
    
    async def scrape_generic_university(self, university: Dict) -> List[Dict]:
        """Generic scraper for university job pages"""
        jobs = []
        
        try:
            response = await self.http_client.get(university['url'])
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for job-related links and elements
            job_elements = []
            
            # Common patterns in university job pages
            patterns = [
                ('a', {'href': re.compile(r'job|position|faculty|staff|career', re.I)}),
                ('div', {'class': re.compile(r'job|position|vacancy', re.I)}),
                ('tr', {'class': re.compile(r'job|position', re.I)}),
            ]
            
            for tag, attrs in patterns:
                job_elements.extend(soup.find_all(tag, attrs)[:30])
            
            # Extract job info
            for elem in job_elements:
                try:
                    # Get title
                    title_elem = elem.find(['h2', 'h3', 'h4', 'a', 'span'], class_=re.compile(r'title|name|position', re.I))
                    if not title_elem:
                        title_elem = elem
                    
                    title = title_elem.get_text(strip=True)
                    
                    # Filter: Only full-time, academic/research/tech positions
                    if len(title) < 5 or len(title) > 150:
                        continue
                    
                    # Skip student, part-time, temporary positions
                    skip_keywords = ['student', 'part-time', 'temporary', 'adjunct', 'hourly', 'intern']
                    if any(keyword in title.lower() for keyword in skip_keywords):
                        continue
                    
                    # Include relevant positions
                    include_keywords = ['professor', 'researcher', 'scientist', 'engineer', 'analyst', 
                                      'developer', 'faculty', 'postdoc', 'staff', 'coordinator',
                                      'manager', 'director', 'specialist', 'technician']
                    if not any(keyword in title.lower() for keyword in include_keywords):
                        continue
                    
                    # Get URL
                    link_elem = elem.find('a') if elem.name != 'a' else elem
                    job_url = link_elem.get('href') if link_elem else university['url']
                    
                    if job_url and not job_url.startswith('http'):
                        from urllib.parse import urljoin
                        job_url = urljoin(university['url'], job_url)
                    
                    jobs.append({
                        'title': title,
                        'university': university['name'],
                        'url': job_url or university['url'],
                        'type': 'Full-time',
                        'cap_exempt': True
                    })
                    
                except Exception as e:
                    continue
            
            return jobs[:20]  # Max 20 jobs per university
            
        except Exception as e:
            return []
    
    async def scrape_all_universities(self) -> List[Dict]:
        """Scrape jobs from all universities"""
        print(f"\n🎓 Scraping {len(US_UNIVERSITIES)} US Universities...")
        print("=" * 80)
        
        all_jobs = []
        successful = 0
        
        for i, university in enumerate(US_UNIVERSITIES, 1):
            try:
                print(f"[{i}/{len(US_UNIVERSITIES)}] {university['name'][:50]:<50}", end=' ', flush=True)
                
                jobs = await self.scrape_generic_university(university)
                
                if jobs:
                    all_jobs.extend(jobs)
                    successful += 1
                    print(f"✅ {len(jobs)} jobs")
                else:
                    print("❌ No jobs")
                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error")
        
        print()
        print("=" * 80)
        print(f"✅ Successfully scraped: {successful}/{len(US_UNIVERSITIES)} universities")
        print(f"📋 Total jobs found: {len(all_jobs)}")
        
        return all_jobs

async def main():
    print("=" * 80)
    print("🎓 US UNIVERSITY JOBS SCRAPER (CAP-EXEMPT)")
    print("=" * 80)
    
    scraper = UniversityJobScraper()
    
    # Scrape all universities
    jobs = await scraper.scrape_all_universities()
    
    await scraper.close()
    
    # Save to file
    with open('/app/backend/university_jobs.json', 'w') as f:
        json.dump(jobs, f, indent=2)
    
    print()
    print(f"✅ Jobs saved to: /app/backend/university_jobs.json")
    
    # Show sample
    if jobs:
        print()
        print("=" * 80)
        print("📋 SAMPLE JOBS (First 30):")
        print("=" * 80)
        
        for i, job in enumerate(jobs[:30], 1):
            print(f"\n{i}. {job['title']}")
            print(f"   University: {job['university']}")
            print(f"   Type: {job['type']} (H1B Cap-Exempt)")
            print(f"   URL: {job['url'][:70]}...")
    
    print()
    print("=" * 80)
    print("✅ SCRAPING COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
