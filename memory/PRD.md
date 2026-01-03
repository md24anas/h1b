# H1B Job Listing Website - PRD

## Original Problem Statement
Build a professional H1B job listing website which displays wage levels.

## User Requirements
- Integration with external job APIs (seed data for demo)
- Search bar and major filters
- Save/bookmark favorite jobs with user authentication
- Job application tracking
- Company profiles with visa sponsorship history
- DOL wage levels (Level 1-4) with salary ranges AND comparison charts
- Emergent-managed Google social login
- Modern tech-forward design

## User Personas
1. **H1B Job Seekers** - International professionals looking for US jobs with visa sponsorship
2. **Job Researchers** - People comparing salary data across companies and wage levels
3. **Career Changers** - Those exploring H1B opportunities in different industries

## Core Requirements (Static)
- Display H1B job listings with wage level information (Level 1-4)
- Show prevailing wage vs actual salary comparison
- Company profiles with H1B sponsorship history and approval rates
- User authentication via Google OAuth
- Save jobs and track applications (authenticated users)

## What's Been Implemented (January 2025)

### Backend (FastAPI + MongoDB)
- [x] User authentication with Emergent Google OAuth
- [x] H1B Jobs API with filters (search, state, wage_level, salary range)
- [x] Companies API with H1B sponsorship stats
- [x] Saved jobs CRUD (authenticated users)
- [x] Job applications with status tracking
- [x] Wage level statistics endpoint
- [x] Seed data with 20 jobs and 8 major tech companies

### Frontend (React + Tailwind + Recharts)
- [x] Landing page with hero search bar
- [x] Wage level breakdown section with bar chart
- [x] Featured jobs section
- [x] Jobs listing page with glassmorphism filter sidebar
- [x] Job detail page with wage level info and comparison chart
- [x] Companies listing page with H1B approval stats
- [x] Company detail page with open positions
- [x] User dashboard (saved jobs, application tracking)
- [x] Responsive design with modern UI

### Authentication
- [x] Google OAuth via Emergent Auth
- [x] Session management with httpOnly cookies
- [x] Protected routes for dashboard

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Recharts, Shadcn/UI
- **Backend**: FastAPI, Motor (async MongoDB driver)
- **Database**: MongoDB
- **Auth**: Emergent Google OAuth

## Prioritized Backlog

### P0 (Critical - Completed)
- [x] Job listings with wage levels
- [x] Search and filter functionality
- [x] Wage level visualization
- [x] Company profiles

### P1 (High Priority - Future)
- [ ] Real DOL data integration (replace seed data)
- [ ] Advanced analytics (salary trends over time)
- [ ] Email notifications for new jobs matching criteria
- [ ] Resume upload and management

### P2 (Medium Priority - Future)
- [ ] Job alerts based on saved searches
- [ ] Compare companies side-by-side
- [ ] H1B lottery statistics and predictions
- [ ] Mobile app (React Native)

### P3 (Low Priority - Future)
- [ ] Community forums for H1B discussions
- [ ] Immigration attorney directory
- [ ] Green card processing timeline tracker

## API Endpoints
- `GET /api/jobs` - List jobs with filters
- `GET /api/jobs/{job_id}` - Get job details
- `GET /api/jobs/stats/wage-levels` - Wage level statistics
- `GET /api/companies` - List companies
- `GET /api/companies/{company_id}` - Get company with jobs
- `POST /api/auth/session` - Exchange session_id for token
- `GET /api/auth/me` - Get current user
- `POST /api/saved-jobs/{job_id}` - Save a job
- `DELETE /api/saved-jobs/{job_id}` - Unsave a job
- `POST /api/applications/{job_id}` - Apply to job
- `PUT /api/applications/{application_id}` - Update application status

## Next Tasks
1. Add more seed data for different industries
2. Implement job alerts via email
3. Add salary comparison tool
4. Integrate real DOL disclosure data
