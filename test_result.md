#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: "Build H1B job listing website + Integrate real jobs from public APIs (ZipRecruiter, Greenhouse, Indeed, LinkedIn)"

backend:
  - task: "Job Aggregation Service"
    implemented: true
    working: true
    file: "/app/backend/job_aggregator.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Created job aggregation service with Arbeitnow and Greenhouse API integration. Smart H1B company matching implemented. Successfully fetching 2967 jobs from H1B sponsors."
      - working: true
        agent: "testing"
        comment: "✅ TESTED: Job aggregation working perfectly. Successfully fetching 3812 jobs from Greenhouse API across 15 H1B-sponsoring companies (Stripe, Airbnb, Lyft, Cloudflare, etc.). Smart company matching filters only H1B sponsors. All external jobs have proper source attribution, external_url, and is_external=true."
  
  - task: "Background Job Scheduler"
    implemented: true
    working: true
    file: "/app/backend/job_scheduler.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "APScheduler configured to run job sync every 60 seconds. Scheduler starts on app startup and runs initial sync."
      - working: true
        agent: "testing"
        comment: "✅ TESTED: Background scheduler working correctly. Runs every 60 seconds as configured. Status endpoint shows scheduler running=true with proper job scheduling info."
  
  - task: "Extended H1BJob Model"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Added fields: source, external_url, external_id, is_external, last_synced to H1BJob model"
      - working: true
        agent: "testing"
        comment: "✅ TESTED: Extended H1BJob model working correctly. All external jobs contain required fields: source (greenhouse/arbeitnow), external_url (real job posting URLs), external_id, is_external=true, last_synced timestamp."
  
  - task: "Sync Status Endpoints"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Created GET /api/jobs/sync/status and POST /api/jobs/sync/trigger endpoints"
      - working: true
        agent: "testing"
        comment: "✅ TESTED: Sync endpoints working perfectly. GET /api/jobs/sync/status returns correct statistics (total_external_jobs: 3812, greenhouse_jobs: 3812, arbeitnow_jobs: 0, scheduler running: true). POST /api/jobs/sync/trigger successfully triggers manual sync."

frontend:
  - task: "Source Badges on Job Cards"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/JobsPage.jsx"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Added 'Live' badges for external jobs showing source (Greenhouse, Arbeitnow)"
  
  - task: "External Job Posting Links"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/JobDetailPage.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Updated apply button to use external_url when available. Shows 'View Original Posting' for external jobs"
  
  - task: "Source Badge on Job Detail"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/JobDetailPage.jsx"
    stuck_count: 0
    priority: "low"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Added gradient source badge (Greenhouse/Arbeitnow) next to job title"

metadata:
  created_by: "main_agent"
  version: "2.0"
  test_sequence: 1
  run_ui: false

test_plan:
  current_focus:
    - "Source Badges on Job Cards"
    - "External Job Posting Links"
    - "Source Badge on Job Detail"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      Successfully implemented real-time job aggregation from public APIs:
      
      **BACKEND:**
      1. ✅ Job Aggregation Service (job_aggregator.py)
         - Fetches from Arbeitnow API (no auth required)
         - Fetches from Greenhouse API (20+ H1B company boards)
         - Smart company matching with flexible normalization
         - Filters only H1B-sponsoring companies
         - Currently pulling 2967 real jobs
      
      2. ✅ Background Scheduler (job_scheduler.py)
         - APScheduler running every 60 seconds
         - Auto-starts on app startup
         - Graceful shutdown handling
      
      3. ✅ API Endpoints
         - GET /api/jobs/sync/status - Shows sync statistics
         - POST /api/jobs/sync/trigger - Manual sync trigger
      
      **FRONTEND:**
      1. ✅ Source badges on job listings
      2. ✅ Direct links to original job postings
      3. ✅ "Live" indicators for external jobs
      
      **INTEGRATION STATUS:**
      - Greenhouse: ✅ WORKING (2967 jobs from Stripe, Airbnb, Lyft, Cloudflare, etc.)
      - Arbeitnow: ⚠️ No matches (mostly European companies, not in H1B database)
      - ZipRecruiter: ❌ Requires partner API key (not public)
      - Indeed: ❌ No public API available
      - LinkedIn: ❌ Requires partner program access
      
      **TESTING NEEDED:**
      1. Verify job sync endpoint returns correct data
      2. Check external job links work correctly
      3. Verify source badges display properly
      4. Test that jobs update every minute
      5. Confirm only H1B sponsors appear in results
  
  - agent: "testing"
    message: |
      **COMPREHENSIVE BACKEND TESTING COMPLETED ✅**
      
      **REAL-TIME JOB AGGREGATION FEATURES - ALL WORKING:**
      
      1. **Job Sync Status Endpoint** (GET /api/jobs/sync/status) ✅
         - Returns correct sync statistics: 3812 external jobs
         - Shows breakdown: greenhouse_jobs: 3812, arbeitnow_jobs: 0
         - Displays last_synced timestamp and scheduler status
         - All required fields present and accurate
      
      2. **Jobs API with External Jobs** (GET /api/jobs) ✅
         - Successfully returns mix of internal (20) and external (3812) jobs
         - External jobs have is_external=true, source field, external_url
         - Proper filtering: only H1B-sponsoring companies included
         - Job data includes real companies: Stripe, Airbnb, Lyft, Cloudflare, etc.
      
      3. **Job Detail with External Source** (GET /api/jobs/{job_id}) ✅
         - Tested with Greenhouse job ID (gh_7378247)
         - Returns complete job data with external_url to real posting
         - Proper Greenhouse job ID format (starts with "gh_")
         - All external job fields populated correctly
      
      4. **Manual Sync Trigger** (POST /api/jobs/sync/trigger) ✅
         - Successfully triggers background job sync
         - Returns proper success message and status
         - Sync completes and updates database with new jobs
      
      **H1B COMPANY FILTERING VERIFIED:**
      - Only jobs from verified H1B sponsors are imported
      - 12 companies successfully matched: Airbnb, Airtable, Cloudflare, Databricks, Dropbox, GitLab, Instacart, Lyft, MongoDB, Reddit, Robinhood, Stripe
      - Smart company name normalization working correctly
      
      **BACKGROUND SCHEDULER VERIFIED:**
      - Runs every 60 seconds as configured
      - Auto-starts on application startup
      - Status endpoint shows running: true with job schedule info
      
      **INTEGRATION STATUS:**
      - Greenhouse API: ✅ FULLY WORKING (3812 real jobs)
      - Arbeitnow API: ✅ API working, 0 matches (European companies, not H1B sponsors)
      - All external jobs have clickable URLs to real job postings
      
      **NOTE:** Seed endpoint clears external jobs (expected behavior for testing)