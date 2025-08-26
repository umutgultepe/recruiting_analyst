from collections import defaultdict

from .job_manager import JobManager
from .client.greenhouse import GreenhouseClient


class Reporter:

    def __init__(self, job_manager: JobManager, client: GreenhouseClient):
        self.job_manager = job_manager
        self.client = client

    def take_home_pipeline_snapshot(self):
        jobs = self.job_manager.get_all_jobs()
        ai_enabled_jobs = [job for job in jobs if job.is_ai_enabled()]
        jobs_with_take_homes = [job for job in ai_enabled_jobs if job.has_take_home_stage()]

        applications_at_take_home_stage = []


        for job in jobs_with_take_homes:
            applications = self.client.get_applications_for_job(job)
            for application in applications:
                if application.is_take_home_stage():
                    applications_at_take_home_stage.append(application)
    
        return applications_at_take_home_stage
                



