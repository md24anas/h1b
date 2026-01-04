"""
Background Job Scheduler
Runs job aggregation every minute
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class JobScheduler:
    """Manages background job scheduling"""
    
    def __init__(self, job_aggregator):
        self.aggregator = job_aggregator
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule job sync to run every 60 seconds
        self.scheduler.add_job(
            func=self.aggregator.sync_jobs,
            trigger=IntervalTrigger(seconds=60),
            id='job_sync',
            name='Sync jobs from external APIs',
            replace_existing=True
        )
        
        logger.info("Starting job scheduler - jobs will sync every 60 seconds")
        self.scheduler.start()
        self.is_running = True
        
        # Run initial sync immediately
        logger.info("Running initial job sync...")
        self.scheduler.add_job(
            func=self.aggregator.sync_jobs,
            id='initial_sync',
            name='Initial job sync',
            replace_existing=True
        )
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        logger.info("Stopping job scheduler...")
        self.scheduler.shutdown()
        self.is_running = False
    
    def get_status(self):
        """Get scheduler status"""
        jobs = []
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            if next_run and next_run.tzinfo is None:
                next_run = next_run.replace(tzinfo=timezone.utc)
            
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run.isoformat() if next_run else None
            })
        
        return {
            "running": self.is_running,
            "jobs": jobs
        }
