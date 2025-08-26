from datetime import datetime, timezone
from typing import List

from .dataclasses import Application
from .config.greenhouse import GREENHOUSE_DOMAIN

class FieldGroup:
    def get_headers(self) -> List[str]:
        raise NotImplementedError

    def get_values(self, Application) -> List[str]:
        raise NotImplementedError


class Identifier(FieldGroup):
    def get_headers(self) -> List[str]:
        return ["candidate_name", "greenhouse_link"]
    
    def get_values(self, application: Application) -> List[str]:
        name = application.candidate_name
        greenhouse_link = f"https://{GREENHOUSE_DOMAIN}/people/{application.candidate_id}/applications/{application.id}"
        return [name, greenhouse_link]


class StageType(FieldGroup):
    def get_headers(self) -> List[str]:
        return ["stage_type", "stage_status"]
    
    def get_values(self, application: Application) -> List[str]:
        if application.is_take_home_stage():
            stage_type = "take home"
            stage_status = application.get_take_home_status().value
        elif application.is_relevant_stage():
            stage_type = "interview"
            stage_status = application.get_stage_status().value
        else:
            stage_type = "other"
            stage_status = "Non-relevant"
        return [stage_type, stage_status]

class CurrentStage (FieldGroup):
    def get_headers(self) -> List[str]:
        return ["current_stage"]
    
    def get_values(self, application: Application) -> List[str]:
        return [application.current_stage.name]

class StageTime(FieldGroup):
    def get_headers(self) -> List[str]:
        return ["moved_to_stage_at"]

    def get_values(self, application: Application) -> List[str]:
        moved_to_stage_at = application.moved_to_stage_at.strftime('%Y-%m-%d %H:%M:%S') if application.moved_to_stage_at else None
        return [moved_to_stage_at]

 
class TakeHomeTimes(FieldGroup):
    def get_headers(self) -> List[str]:
        return ["take_home_submitted_at", "take_home_graded_at"]
    
    def get_values(self, application: Application) -> List[str]:
        take_home_graded_at = None
        take_home_submitted_at = application.take_home_submitted_at.strftime('%Y-%m-%d %H:%M:%S') if application.take_home_submitted_at else None
        if application.take_home_grading:
            take_home_graded_at = application.take_home_grading.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
        return [take_home_submitted_at, take_home_graded_at]


class InterviewTimes(FieldGroup):
    def get_headers(self) -> List[str]:
        return ["availability_requested_at", "availability_received_at", "interview_scheduled_at", "interview_date"]
    
    def get_values(self, application: Application) -> List[str]:
        availability_requested_at = application.availability_requested_at.strftime('%Y-%m-%d %H:%M:%S') if application.availability_requested_at else None
        availability_received_at = application.availability_received_at.strftime('%Y-%m-%d %H:%M:%S') if application.availability_received_at else None
        # Get interview scheduled timestamp and interview date (earliest created_at and date from interviews)
        interview_scheduled_at = None
        interview_date = None
        if application.interviews:
            valid_interviews = [i for i in application.interviews if i.created_at]
            if valid_interviews:
                earliest_interview = min(valid_interviews, key=lambda x: x.created_at)
                if earliest_interview.created_at:
                    interview_scheduled_at = earliest_interview.created_at.strftime('%Y-%m-%d %H:%M:%S')
                if earliest_interview.date:
                    interview_date = earliest_interview.date.strftime('%Y-%m-%d %H:%M:%S')
        return [availability_requested_at, availability_received_at, interview_scheduled_at, interview_date]


class InterviewCounts(FieldGroup):
    def get_headers(self) -> List[str]:
        return ["scheduled_interviews_count", "completed_interviews_count"]
    
    def get_values(self, application: Application) -> List[str]:
        # Count interviews and get interview scheduling timestamp
        scheduled_interviews_count = len(application.interviews)
        completed_interviews_count = len([i for i in application.interviews if i.status.value == "COMPLETE"])
        return [scheduled_interviews_count, completed_interviews_count]


class Dimensions(FieldGroup):
    def get_headers(self) -> List[str]:
        return ["recruiter_name", "location", "department"]
    
    def get_values(self, application: Application) -> List[str]:
        job = application.job
        recruiter_name = "unknown"
        if job.recruiters:
            primary_recruiter = job.recruiters[0]
            recruiter_name = f"{primary_recruiter.first_name} {primary_recruiter.last_name}"

         # Get location and department
        location = job.location.name if job.location else "Unknown"
        department = job.departments[0].name if job.departments else "Unknown"
        return [recruiter_name, location, department]

class TakeHomePendingGrading(FieldGroup):
    def get_headers(self) -> List[str]:
        return ["hours_pending_grading"]
    
    def get_values(self, application: Application) -> List[str]:
        # Calculate hours pending grading
        hours_pending_grading = None
        if application.take_home_submitted_at and not application.take_home_grading:
            # Calculate time elapsed since submission
            now = datetime.now(timezone.utc)
            time_elapsed = now - application.take_home_submitted_at
            hours_pending_grading = round(time_elapsed.total_seconds() / 3600, 1)

        return [hours_pending_grading]

class BlockContext(FieldGroup):

    def get_headers(self) -> List[str]:
        return ["last_event_time_reference", "blocked_hours"]
    
    def get_values(self, application: Application) -> List[str]:
        # Get application pending time information
        application_blocker = application.get_application_blocker()
        last_event_time_reference = application_blocker.relevant_time_name if application_blocker else None
        blocked_hours = round(application_blocker.time_elapsed.total_seconds() / 3600, 1) if application_blocker else None
        return [last_event_time_reference, blocked_hours]

class FieldSpec:
    Identifier = Identifier()
    CurrentStage = CurrentStage()
    StageType = StageType()
    StageTime = StageTime()
    TakeHomeTimes = TakeHomeTimes()
    InterviewTimes = InterviewTimes()
    InterviewCounts = InterviewCounts()
    Dimensions = Dimensions()
    BlockContext = BlockContext()
    TakeHomePendingGrading = TakeHomePendingGrading()

class ApplicationCSVWriter:
    def __init__(self, fields):
        self.fields = fields

    def get_headers(self):
        headers = []
        for field in self.fields:
            for header in field.get_headers():
                headers.append(header)
        return headers

    def generate_row(self, application: Application):
        row = []
        for field in self.fields:
            for value in field.get_values(application):
                row.append(value)
        return row