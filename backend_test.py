import requests
import sys
from datetime import datetime

class H1BJobBoardTester:
    def __init__(self, base_url="https://h1bwageguide.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        if 'jobs' in response_data:
                            print(f"   Found {len(response_data.get('jobs', []))} jobs")
                        elif 'companies' in response_data:
                            print(f"   Found {len(response_data.get('companies', []))} companies")
                        elif 'message' in response_data:
                            print(f"   Message: {response_data['message']}")
                    elif isinstance(response_data, list):
                        print(f"   Found {len(response_data)} items")
                except:
                    print(f"   Response length: {len(response.text)} chars")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'endpoint': endpoint
                })

            return success, response.json() if success else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                'name': name,
                'error': str(e),
                'endpoint': endpoint
            })
            return False, {}

    def test_health_endpoints(self):
        """Test basic health endpoints"""
        print("\n=== TESTING HEALTH ENDPOINTS ===")
        self.run_test("Root endpoint", "GET", "", 200)
        self.run_test("Health check", "GET", "health", 200)

    def test_jobs_endpoints(self):
        """Test job-related endpoints"""
        print("\n=== TESTING JOBS ENDPOINTS ===")
        
        # Test basic jobs endpoint
        success, jobs_data = self.run_test("Get all jobs", "GET", "jobs", 200)
        if success and jobs_data.get('jobs'):
            job_id = jobs_data['jobs'][0]['job_id']
            print(f"   Using job_id: {job_id} for detailed test")
            
            # Test single job endpoint
            self.run_test("Get single job", "GET", f"jobs/{job_id}", 200)
        
        # Test jobs with filters
        self.run_test("Jobs with search filter", "GET", "jobs?search=Software", 200)
        self.run_test("Jobs with state filter", "GET", "jobs?state=CA", 200)
        self.run_test("Jobs with wage level filter", "GET", "jobs?wage_level=4", 200)
        self.run_test("Jobs with salary filter", "GET", "jobs?min_salary=150000", 200)
        
        # Test wage level stats
        self.run_test("Wage level statistics", "GET", "jobs/stats/wage-levels", 200)
        self.run_test("State statistics", "GET", "jobs/stats/by-state", 200)

    def test_companies_endpoints(self):
        """Test company-related endpoints"""
        print("\n=== TESTING COMPANIES ENDPOINTS ===")
        
        # Test basic companies endpoint
        success, companies_data = self.run_test("Get all companies", "GET", "companies", 200)
        if success and companies_data.get('companies'):
            company_id = companies_data['companies'][0]['company_id']
            print(f"   Using company_id: {company_id} for detailed test")
            
            # Test single company endpoint
            self.run_test("Get single company", "GET", f"companies/{company_id}", 200)
        
        # Test companies with search
        self.run_test("Companies with search", "GET", "companies?search=Google", 200)

    def test_seed_endpoint(self):
        """Test data seeding"""
        print("\n=== TESTING SEED ENDPOINT ===")
        self.run_test("Seed data", "POST", "seed", 200)

    def test_auth_endpoints(self):
        """Test authentication endpoints (without actual auth)"""
        print("\n=== TESTING AUTH ENDPOINTS ===")
        
        # These should fail without proper auth
        self.run_test("Get current user (no auth)", "GET", "auth/me", 401)
        self.run_test("Get saved jobs (no auth)", "GET", "saved-jobs", 401)
        self.run_test("Get applications (no auth)", "GET", "applications", 401)

    def test_error_cases(self):
        """Test error handling"""
        print("\n=== TESTING ERROR CASES ===")
        
        # Test non-existent job
        self.run_test("Non-existent job", "GET", "jobs/nonexistent", 404)
        
        # Test non-existent company
        self.run_test("Non-existent company", "GET", "companies/nonexistent", 404)

def main():
    print("🚀 Starting H1B Job Board API Tests")
    print("=" * 50)
    
    tester = H1BJobBoardTester()
    
    # Run all test suites
    tester.test_health_endpoints()
    tester.test_seed_endpoint()  # Seed first to ensure data exists
    tester.test_jobs_endpoints()
    tester.test_companies_endpoints()
    tester.test_auth_endpoints()
    tester.test_error_cases()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.failed_tests:
        print(f"\n❌ FAILED TESTS ({len(tester.failed_tests)}):")
        for test in tester.failed_tests:
            print(f"  - {test['name']}: {test.get('error', f'Expected {test.get(\"expected\")}, got {test.get(\"actual\")}')}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())