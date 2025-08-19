from dataclasses import dataclass
from enum import Enum
from datetime import datetime
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


@dataclass
class ScheduledInterview:
    id: str
    interview: Interview
    created_at: datetime
    date: datetime
    status: InterviewStatus
    interviewers: List[User]


@dataclass
class Application:
    job: Job
    current_stage: JobStage
    moved_to_stage_at: datetime
    availability_requested_at: Optional[datetime]
    availability_received_at: Optional[datetime]
    interviews: List[ScheduledInterview]

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