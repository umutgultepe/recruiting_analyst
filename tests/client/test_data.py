from datetime import datetime
from unittest.mock import Mock
from src.analyst.dataclasses import (
    Job, JobStage, Interview, User, Location, Department, Role, 
    RoleFunction, Seniority, ScheduledInterview, InterviewStatus
)
from src.analyst.job_manager import JobManager

SAMPLE_APPLICATION_JSON = {
    "id": 156728361,
    "candidate_id": 138678330,
    "prospect": False,
    "applied_at": "2025-06-24T16:42:01.206Z",
    "rejected_at": None,
    "last_activity_at": "2025-08-19T11:09:00.231Z",
    "location": None,
    "rejection_reason": None,
    "rejection_details": None,
    "jobs": [
        {
            "id": 5179819,
            "name": "Software Engineer 2"
        }
    ],
    "job_post_id": 6593852,
    "status": "active",
    "current_stage": {
        "id": 12862064,
        "name": "Evaluation Stage 3"
    },
    "moved_to_stage_at": "2025-08-19T11:09:00.231Z"
}

SAMPLE_ACTIVITY_FEED_JSON = {
    "activities": [
        {
            "id": 123456,
            "created_at": "2025-08-19T11:09:00.231Z",
            "subject": None,
            "body": "John Doe was moved into Evaluation Stage 3 for Software Engineer 2",
            "user": {
                "id": 5308623,
                "first_name": "John",
                "last_name": "Doe",
                "name": "John Doe",
                "employee_id": "1527"
            }
        },
        {
            "id": 123457,
            "created_at": "2025-08-20T10:00:00.000Z",
            "subject": None,
            "body": "Jane Smith manually updated John Doe's availability from Not requested to Requested for Technical Phone Screen (Evaluation Stage 3)",
            "user": {
                "id": 5308623004,
                "first_name": "Jane",
                "last_name": "Smith",
                "name": "Jane Smith",
                "employee_id": "1528"
            }
        },
        {
            "id": 123458,
            "created_at": "2025-08-20T14:30:00.000Z",
            "subject": None,
            "body": "John Doe submitted their availability for Technical Phone Screen (Evaluation Stage 3)",
            "user": {
                "id": 5308623005,
                "first_name": "System",
                "last_name": "User",
                "name": "System User",
                "employee_id": "1529"
            }
        }
    ]
}

SAMPLE_SCHEDULED_INTERVIEWS_JSON = [
    {
        "id": 987654,
        "application_id": 156728361,
        "start": {
            "date_time": "2025-08-21T16:00:00.000Z"
        },
        "end": {
            "date_time": "2025-08-21T17:00:00.000Z"
        },
        "status": "complete",
        "created_at": "2025-08-20T15:00:00.000Z",
        "updated_at": "2025-08-20T15:00:00.000Z",
        "interview": {
            "id": 111111,
            "name": "Technical Phone Screen"
        },
        "interviewers": [
            {
                "id": 222222,
                "employee_id": "1656",
                "name": "John Doe",
                "email": "john.doe@company.com",
                "response_status": "accepted",
                "scorecard_id": 26419635
            },
            {
                "id": 333333,
                "employee_id": "1657",
                "name": "Jane Smith",
                "email": "jane.smith@company.com",
                "response_status": "accepted",
                "scorecard_id": 26419635004
            }
        ]
    }
]

SAMPLE_SCORECARDS_JSON = [
    {
        "id": 26419635,
        "submitted_at": "2025-08-21T17:30:00.000Z",
        "submitted_by": {
            "id": 222222,
            "first_name": "John",
            "last_name": "Doe",
            "name": "John Doe",
            "employee_id": "1656"
        },
        "overall_recommendation": "YES"
    },
    {
        "id": 26419635004,
        "submitted_at": "2025-08-21T18:00:00.000Z",
        "submitted_by": {
            "id": 333333,
            "first_name": "Jane",
            "last_name": "Smith",
            "name": "Jane Smith",
            "employee_id": "1657"
        },
        "overall_recommendation": "STRONG_YES"
    }
]

SAMPLE_JOB_STAGES_JSON = [
    {
        "id": 12862064,
        "name": "Evaluation Stage 3",
        "interviews": [
            {
                "id": 111111,
                "name": "Technical Phone Screen",
                "schedulable": True
            },
            {
                "id": 222222,
                "name": "System Design",
                "schedulable": True
            }
        ]
    }
]

def create_dummy_job_manager():
    """Create a dummy JobManager for testing."""
    # Create mock job manager
    job_manager = Mock(spec=JobManager)
    
    # Create sample job
    job = Job(
        id="5179819",
        name="Software Engineer 2",
        location=Location(id="4030182", name="Remote - Canada"),
        created_at=datetime(2025, 6, 24, 16, 42, 1),
        opened_at=datetime(2025, 6, 24, 16, 42, 1),
        hiring_managers=[],
        recruiters=[],
        coordinators=[],
        sourcers=[],
        departments=[Department(id="4004041", name="R&D")],
        role=Role(function=RoleFunction.Engineer, seniority=Seniority.SWE2),
        stages=[]
    )
    
    # Create sample stage
    stage = JobStage(
        id="12862064",
        name="Evaluation Stage 3",
        interviews=[
            Interview(id="111111", name="Technical Phone Screen", schedulable=True),
            Interview(id="222222", name="System Design", schedulable=True)
        ]
    )
    
    # Add the stage to the job
    job.stages = [stage]
    
    # Set up the mock to return the job
    job_manager.get_by_id.return_value = job
    
    return job_manager