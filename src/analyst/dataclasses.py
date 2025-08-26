from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
from typing import List, Optional


class RoleFunction(Enum):
    Engineer = "Engineer"
    Other = "Other"


class Seniority(Enum):
    SWE1 = "SWE1"
    SWE2 = "SWE2"
    Senior = "Senior"
    Staff = "Staff"
    Unknown = "Unknown"


@dataclass
class Role:
    function: RoleFunction
    seniority: Seniority


@dataclass
class Department:
    id: str
    name: str


@dataclass
class Location:
    """Represented as Office in Greenhouse"""
    id: str
    name: str


@dataclass
class Interview:
    id: str
    name: str
    schedulable: bool


@dataclass
class JobStage:
    id: str
    name: str
    interviews: List[Interview]

    @property
    def is_schedulable(self) -> bool:
        return any(interview.schedulable for interview in self.interviews)

    @property
    def is_take_home(self) -> bool:
        return not self.is_schedulable and "Take Home" in self.name


@dataclass
class User:
    id: str
    first_name: str
    last_name: str


@dataclass
class Job:
    id: str
    name: str
    location: Location
    created_at: datetime
    opened_at: Optional[datetime]
    hiring_managers: List[User]
    recruiters: List[User]
    coordinators: List[User]
    sourcers: List[User]
    departments: List[Department]
    role: Role
    stages: List[JobStage]

    def has_take_home_stage(self) -> bool:
        return any(stage.is_take_home for stage in self.stages)

    def is_ai_eligible(self) -> bool:
        """
        Check if a job is eligible for AI-enabled features based on role criteria.
        """
        return self.role.function == RoleFunction.Engineer

    def is_ai_enabled(self) -> bool:
        """
        Check if a job has AI-enabled features based on role and stage criteria.
        
        Returns:
            True if AI is enabled, False otherwise
        """
        # Check if the role is for an engineer
        if self.role.function != RoleFunction.Engineer:
            return False

        # Check for SWE1 or SWE2 level with "Take Home Test" stage
        if self.role.seniority in [Seniority.SWE1, Seniority.SWE2]:
            for stage in self.stages:
                if "Take Home Test" in stage.name:
                    return True
        
        # Check for Senior level with "DevAI Technical Screen" interview
        if self.role.seniority == Seniority.Senior:
            for stage in self.stages:
                for interview in stage.interviews:
                    if "DevAI Technical Screen" in interview.name:
                        return True
        
        return False


class TakeHomeStatus(Enum):
    PENDING_SUBMISSION = "PENDING_SUBMISSION"
    PENDING_GRADING = "PENDING_GRADING"
    PENDING_DECISION = "PENDING_DECISION"


class StageStatus(Enum):
    PENDING_AVAILABILITY_REQUEST = "PENDING_AVAILABILITY_REQUEST"
    WAITING_FOR_AVAILABILITY = "WAITING_FOR_AVAILABILITY"
    PENDING_SCHEDULING = "PENDING_SCHEDULING"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    PENDING_SCORECARD = "PENDING_SCORECARD"
    PENDING_DECISION = "PENDING_DECISION"


class InterviewStatus(Enum):
    SCHEDULED = "SCHEDULED"
    AWAITING_FEEDBACK = "AWAITING_FEEDBACK"
    COMPLETE = "COMPLETE"


class ScorecardDecision(Enum):
    DEFINITELY_NOT = "DEFINITELY_NOT"
    NO = "NO"
    NO_DECISION = "NO_DECISION"
    YES = "YES"
    STRONG_YES = "STRONG_YES"

@dataclass
class Scorecard:
    id: str
    submitted_at: datetime
    by: User
    decision: ScorecardDecision

@dataclass
class ScheduledInterview:
    id: str
    interview: Interview
    created_at: datetime
    date: datetime
    status: InterviewStatus
    interviewers: List[User]
    scorecards: List[Scorecard]


@dataclass
class TakeHomeGrading:
    id: str
    submitted_at: datetime
    by: User


@dataclass
class ApplicationBlocker:
    status: StageStatus
    relevant_time_name: str
    relevant_time: datetime

    @property
    def time_elapsed(self) -> datetime:
        return datetime.now(timezone.utc) - self.relevant_time


@dataclass
class Application:
    id: str
    job: Job
    current_stage: JobStage
    moved_to_stage_at: datetime
    candidate_name: str
    candidate_id: str
    availability_requested_at: Optional[datetime]
    availability_received_at: Optional[datetime]
    take_home_submitted_at: Optional[datetime]
    take_home_grading: Optional[TakeHomeGrading]
    interviews: List[ScheduledInterview]

    def is_relevant_stage(self) -> bool:
        return self.current_stage.is_schedulable or self.is_take_home_stage()

    def is_take_home_stage(self) -> bool:
        return self.current_stage.is_take_home

    def get_take_home_status(self) -> TakeHomeStatus:
        if self.take_home_grading:
            return TakeHomeStatus.PENDING_DECISION
        elif self.take_home_submitted_at:
            return TakeHomeStatus.PENDING_GRADING
        else:
            return TakeHomeStatus.PENDING_SUBMISSION

    def get_stage_status(self) -> StageStatus:
        if self.interviews:
            if all(interview.status == InterviewStatus.COMPLETE for interview in self.interviews):
                return StageStatus.PENDING_DECISION
            elif any(interview.status == InterviewStatus.AWAITING_FEEDBACK for interview in self.interviews):
                return StageStatus.PENDING_SCORECARD
            else:
                return StageStatus.INTERVIEW_SCHEDULED
        else:
            if self.availability_received_at:
                return StageStatus.PENDING_SCHEDULING
            elif self.availability_requested_at:
                return StageStatus.WAITING_FOR_AVAILABILITY
            else:
                return StageStatus.PENDING_AVAILABILITY_REQUEST
        
    def get_application_blocker(self) -> Optional[ApplicationBlocker]:
        relevant_time_name = None
        relevant_time = None
        if self.get_stage_status() == StageStatus.PENDING_AVAILABILITY_REQUEST:
            relevant_time_name = "moved_to_stage_at"
            relevant_time = self.moved_to_stage_at
        elif self.get_stage_status() == StageStatus.WAITING_FOR_AVAILABILITY:
            relevant_time_name = "availability_requested_at"
            relevant_time = self.availability_requested_at
        elif self.get_stage_status() == StageStatus.PENDING_SCHEDULING:
            relevant_time_name = "availability_received_at"
            relevant_time = self.availability_received_at
        elif self.get_stage_status() in [StageStatus.PENDING_SCORECARD, StageStatus.PENDING_DECISION]:
            relevant_time_name = "interview_date"
            earliest_interview = min(self.interviews, key=lambda x: x.created_at)
            relevant_time = earliest_interview.date
        if relevant_time:
            return ApplicationBlocker(
                status=self.get_stage_status(),
                relevant_time_name=relevant_time_name,
                relevant_time=relevant_time
            )