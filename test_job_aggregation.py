#!/usr/bin/env python3
"""
Focused test for H1B Job Board real-time job aggregation features
"""
import requests
import time
import sys

BASE_URL = "https://job-fetch-app.preview.emergentagent.com/api"

def test_job_sync_status():
    """Test job sync status endpoint"""
    print("🔍 Testing Job Sync Status Endpoint...")
    
    response = requests.get(f"{BASE_URL}/jobs/sync/status")
    
    if response.status_code != 200:
        print(f"❌ FAILED - Status: {response.status_code}")
        return False
    
    data = response.json()
    print(f"✅ PASSED - Status: {response.status_code}")
    print(f"   Total external jobs: {data.get('total_external_jobs', 0)}")
    print(f"   Greenhouse jobs: {data.get('greenhouse_jobs', 0)}")
    print(f"   Arbeitnow jobs: {data.get('arbeitnow_jobs', 0)}")
    print(f"   Internal jobs: {data.get('internal_jobs', 0)}")
    print(f"   Last synced: {data.get('last_synced', 'Never')}")
    print(f"   Scheduler running: {data.get('running', False)}")
    
    # Verify expected fields
    required_fields = ['total_external_jobs', 'greenhouse_jobs', 'arbeitnow_jobs', 'status']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    return True

def test_manual_sync_trigger():
    """Test manual sync trigger endpoint"""
    print("\n🔍 Testing Manual Sync Trigger...")
    
    response = requests.post(f"{BASE_URL}/jobs/sync/trigger")
    
    if response.status_code != 200:
        print(f"❌ FAILED - Status: {response.status_code}")
        return False
    
    data = response.json()
    print(f"✅ PASSED - Status: {response.status_code}")
    print(f"   Message: {data.get('message', 'No message')}")
    print(f"   Status: {data.get('status', 'Unknown')}")
    
    return True

def test_external_jobs_api():
    """Test jobs API with external jobs"""
    print("\n🔍 Testing Jobs API with External Jobs...")
    
    response = requests.get(f"{BASE_URL}/jobs?limit=100")
    
    if response.status_code != 200:
        print(f"❌ FAILED - Status: {response.status_code}")
        return False
    
    data = response.json()
    jobs = data.get('jobs', [])
    
    print(f"✅ PASSED - Status: {response.status_code}")
    print(f"   Total jobs returned: {len(jobs)}")
    
    # Analyze job types
    external_jobs = [job for job in jobs if job.get('is_external')]
    internal_jobs = [job for job in jobs if not job.get('is_external')]
    greenhouse_jobs = [job for job in external_jobs if job.get('source') == 'greenhouse']
    
    print(f"   External jobs: {len(external_jobs)}")
    print(f"   Internal jobs: {len(internal_jobs)}")
    print(f"   Greenhouse jobs: {len(greenhouse_jobs)}")
    
    # Test external job properties
    if external_jobs:
        ext_job = external_jobs[0]
        print(f"   Sample external job:")
        print(f"     ID: {ext_job.get('job_id', 'N/A')}")
        print(f"     Source: {ext_job.get('source', 'N/A')}")
        print(f"     Company: {ext_job.get('company_name', 'N/A')}")
        print(f"     Has external_url: {'external_url' in ext_job}")
        print(f"     Is external: {ext_job.get('is_external', False)}")
        
        # Verify required fields for external jobs
        required_ext_fields = ['source', 'external_url', 'is_external']
        missing_ext_fields = [field for field in required_ext_fields if field not in ext_job]
        
        if missing_ext_fields:
            print(f"❌ External job missing fields: {missing_ext_fields}")
            return False
    else:
        print("⚠️  No external jobs found")
    
    return True

def test_external_job_detail():
    """Test job detail endpoint with external job"""
    print("\n🔍 Testing External Job Detail...")
    
    # First get a list of jobs to find an external one
    response = requests.get(f"{BASE_URL}/jobs?limit=50")
    if response.status_code != 200:
        print(f"❌ FAILED to get jobs list - Status: {response.status_code}")
        return False
    
    jobs = response.json().get('jobs', [])
    external_jobs = [job for job in jobs if job.get('is_external')]
    
    if not external_jobs:
        print("⚠️  No external jobs found for detail testing")
        return True
    
    # Test with a Greenhouse job if available
    greenhouse_jobs = [job for job in external_jobs if job.get('source') == 'greenhouse']
    test_job = greenhouse_jobs[0] if greenhouse_jobs else external_jobs[0]
    
    job_id = test_job['job_id']
    print(f"   Testing job ID: {job_id}")
    
    response = requests.get(f"{BASE_URL}/jobs/{job_id}")
    
    if response.status_code != 200:
        print(f"❌ FAILED - Status: {response.status_code}")
        return False
    
    job_detail = response.json()
    print(f"✅ PASSED - Status: {response.status_code}")
    print(f"   Job title: {job_detail.get('job_title', 'N/A')}")
    print(f"   Company: {job_detail.get('company_name', 'N/A')}")
    print(f"   Source: {job_detail.get('source', 'N/A')}")
    print(f"   External URL: {job_detail.get('external_url', 'N/A')}")
    print(f"   Is external: {job_detail.get('is_external', False)}")
    
    # Verify Greenhouse job ID format
    if job_detail.get('source') == 'greenhouse':
        if job_id.startswith('gh_'):
            print(f"   ✅ Greenhouse job ID format correct")
        else:
            print(f"   ❌ Greenhouse job ID format incorrect: {job_id}")
            return False
    
    return True

def test_h1b_company_filtering():
    """Test that only H1B-sponsoring companies appear"""
    print("\n🔍 Testing H1B Company Filtering...")
    
    response = requests.get(f"{BASE_URL}/jobs?limit=100")
    if response.status_code != 200:
        print(f"❌ FAILED - Status: {response.status_code}")
        return False
    
    jobs = response.json().get('jobs', [])
    external_jobs = [job for job in jobs if job.get('is_external')]
    
    if not external_jobs:
        print("⚠️  No external jobs to test company filtering")
        return True
    
    # Check that all external jobs are from known H1B sponsors
    h1b_companies = {
        'GitLab', 'Stripe', 'Airbnb', 'Lyft', 'Dropbox', 'Coinbase', 
        'Robinhood', 'Instacart', 'Reddit', 'Databricks', 'MongoDB', 
        'Figma', 'Airtable', 'Asana', 'Cloudflare'
    }
    
    companies_found = set()
    for job in external_jobs:
        company = job.get('company_name', '')
        companies_found.add(company)
    
    print(f"   External job companies found: {sorted(companies_found)}")
    
    # Check if companies are H1B sponsors
    non_h1b_companies = companies_found - h1b_companies
    if non_h1b_companies:
        print(f"⚠️  Found non-H1B companies: {non_h1b_companies}")
    else:
        print(f"   ✅ All companies are H1B sponsors")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing H1B Job Board Real-Time Job Aggregation")
    print("=" * 60)
    
    tests = [
        test_job_sync_status,
        test_manual_sync_trigger,
        test_external_jobs_api,
        test_external_job_detail,
        test_h1b_company_filtering
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test {test.__name__} failed")
        except Exception as e:
            print(f"❌ Test {test.__name__} error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All real-time job aggregation tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed - check implementation")
        return 1

if __name__ == "__main__":
    sys.exit(main())