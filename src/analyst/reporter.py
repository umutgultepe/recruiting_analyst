from typing import List

from .dataclasses import Application, StageStatus
from .job_manager import JobManager
from .client.greenhouse import GreenhouseClient


class Reporter:

    def __init__(self, job_manager: JobManager, client: GreenhouseClient):
        self.job_manager = job_manager
        self.client = client


    def take_home_statistics(self) -> List[Application]:
        jobs = self.job_manager.get_all_jobs()
        ai_enabled_jobs = [job for job in jobs if job.is_ai_enabled()]
        jobs_with_take_homes = [job for job in ai_enabled_jobs if job.has_take_home_stage()]

        all_applications = []

        for job in jobs_with_take_homes:
            applications = self.client.get_take_home_stage_of_applications_for_job(job)
            all_applications.extend(applications)

        return all_applications

    def take_home_pipeline_snapshot(self) -> List[Application]:
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
                
    def blocked_interview_snapshot(self) -> List[Application]:
        jobs = self.job_manager.get_all_jobs()
        applications = []
        for job in jobs:
            job_applications = self.client.get_applications_for_job(job)
            for application in job_applications:
                if not application.is_relevant_stage():
                    continue
                if application.is_take_home_stage():
                    continue
                if application.get_stage_status() == StageStatus.INTERVIEW_SCHEDULED:
                    continue
                applications.append(application)
        return applications