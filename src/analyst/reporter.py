from datetime import datetime, timezone

from .dataclasses import Application, ApplicationBlocker, StageStatus
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
                
    def interview_snapshot(self):
        jobs = self.job_manager.get_all_jobs()
        applications = []
        for job in jobs:
            job_applications = self.client.get_applications_for_job(job)
            for application in job_applications:
                if not application.is_relevant_stage():
                    continue
                applications.append(application)
        return applications

    def get_application_blocker(self, application: Application):
        relevant_time_name = None
        relevant_time = None
        if application.get_stage_status() == StageStatus.PENDING_AVAILABILITY_REQUEST:
            relevant_time_name = "moved_to_stage_at"
            relevant_time = application.moved_to_stage_at
        elif application.get_stage_status() == StageStatus.WAITING_FOR_AVAILABILITY:
            relevant_time_name = "availability_requested_at"
            relevant_time = application.availability_requested_at
        elif application.get_stage_status() == StageStatus.PENDING_SCHEDULING:
            relevant_time_name = "availability_received_at"
            relevant_time = application.availability_received_at
        elif application.get_stage_status() in [StageStatus.PENDING_SCORECARD, StageStatus.PENDING_DECISION]:
            relevant_time_name = "interview_date"
            earliest_interview = min(application.interviews, key=lambda x: x.created_at)
            relevant_time = earliest_interview.date
        if relevant_time:
            return ApplicationBlocker(
                status=application.get_stage_status(),
                relevant_time_name=relevant_time_name,
                relevant_time=relevant_time
            )

