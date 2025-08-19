"""
Tests for the Application dataclass stage status calculation.
"""

import pytest
from datetime import datetime, timedelta
from src.analyst.dataclasses import (
    Application, Job, JobStage, Interview, User, Location, Department, Role, 
    RoleFunction, Seniority, ScheduledInterview, StageStatus, InterviewStatus
)


class TestApplicationStageStatus:
    """Test cases for Application stage status calculation."""
    
    def setup_method(self):
        """Set up common test data."""
        # Create a basic job for testing
        self.job = Job(
            id="123",
            name="Test Job",
            location=Location(id="loc1", name="Remote"),
            created_at=datetime.now(),
            opened_at=datetime.now(),
            hiring_managers=[],
            recruiters=[],
            coordinators=[],
            sourcers=[],
            departments=[],
            role=Role(function=RoleFunction.Engineer, seniority=Seniority.SWE2),
            stages=[]
        )
        
        # Create a basic stage for testing
        self.stage = JobStage(
            id="stage1",
            name="Phone Screen",
            interviews=[
                Interview(id="int1", name="Technical Phone Screen", schedulable=True)
            ]
        )
        
        # Create test users
        self.interviewer = User(id="user1", first_name="John", last_name="Doe")
        
        # Create test interview
        self.interview = Interview(id="int1", name="Technical Phone Screen", schedulable=True)
        
        # Base time for testing
        self.base_time = datetime.now()
    
    def test_pending_availability_request(self):
        """Test status when no availability has been requested."""
        application = Application(
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            availability_requested_at=None,
            availability_received_at=None,
            interviews=[]
        )
        
        assert application.get_stage_status() == StageStatus.PENDING_AVAILABILITY_REQUEST
    
    def test_waiting_for_availability(self):
        """Test status when availability has been requested but not received."""
        application = Application(
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            availability_requested_at=self.base_time,
            availability_received_at=None,
            interviews=[]
        )
        
        assert application.get_stage_status() == StageStatus.WAITING_FOR_AVAILABILITY
    
    def test_pending_scheduling(self):
        """Test status when availability has been received but no interviews scheduled."""
        application = Application(
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            availability_requested_at=self.base_time - timedelta(hours=1),
            availability_received_at=self.base_time,
            interviews=[]
        )
        
        assert application.get_stage_status() == StageStatus.PENDING_SCHEDULING
    
    def test_interview_scheduled(self):
        """Test status when interviews are scheduled but not completed."""
        scheduled_interview = ScheduledInterview(
            id="sched1",
            interview=self.interview,
            created_at=self.base_time,
            date=self.base_time + timedelta(days=1),
            status=InterviewStatus.SCHEDULED,
            interviewers=[self.interviewer]
        )
        
        application = Application(
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            availability_requested_at=self.base_time - timedelta(hours=2),
            availability_received_at=self.base_time - timedelta(hours=1),
            interviews=[scheduled_interview]
        )
        
        assert application.get_stage_status() == StageStatus.INTERVIEW_SCHEDULED
    
    def test_pending_scorecard(self):
        """Test status when interviews are awaiting feedback."""
        scheduled_interview = ScheduledInterview(
            id="sched1",
            interview=self.interview,
            created_at=self.base_time,
            date=self.base_time - timedelta(hours=1),  # Past interview
            status=InterviewStatus.AWAITING_FEEDBACK,
            interviewers=[self.interviewer]
        )
        
        application = Application(
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            availability_requested_at=self.base_time - timedelta(hours=3),
            availability_received_at=self.base_time - timedelta(hours=2),
            interviews=[scheduled_interview]
        )
        
        assert application.get_stage_status() == StageStatus.PENDING_SCORECARD
    
    def test_pending_decision(self):
        """Test status when all interviews are complete."""
        scheduled_interview = ScheduledInterview(
            id="sched1",
            interview=self.interview,
            created_at=self.base_time,
            date=self.base_time - timedelta(hours=2),  # Past interview
            status=InterviewStatus.COMPLETE,
            interviewers=[self.interviewer]
        )
        
        application = Application(
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            availability_requested_at=self.base_time - timedelta(hours=4),
            availability_received_at=self.base_time - timedelta(hours=3),
            interviews=[scheduled_interview]
        )
        
        assert application.get_stage_status() == StageStatus.PENDING_DECISION
    
    def test_multiple_interviews_mixed_status(self):
        """Test status with multiple interviews in different states."""
        # First interview complete
        interview1 = ScheduledInterview(
            id="sched1",
            interview=self.interview,
            created_at=self.base_time,
            date=self.base_time - timedelta(hours=2),
            status=InterviewStatus.COMPLETE,
            interviewers=[self.interviewer]
        )
        
        # Second interview awaiting feedback
        interview2 = ScheduledInterview(
            id="sched2",
            interview=Interview(id="int2", name="Onsite", schedulable=True),
            created_at=self.base_time,
            date=self.base_time - timedelta(hours=1),
            status=InterviewStatus.AWAITING_FEEDBACK,
            interviewers=[self.interviewer]
        )
        
        application = Application(
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            availability_requested_at=self.base_time - timedelta(hours=5),
            availability_received_at=self.base_time - timedelta(hours=4),
            interviews=[interview1, interview2]
        )
        
        # Should return PENDING_SCORECARD since one interview is awaiting feedback
        assert application.get_stage_status() == StageStatus.PENDING_SCORECARD
    
    def test_multiple_interviews_all_complete(self):
        """Test status when all interviews are complete."""
        # First interview complete
        interview1 = ScheduledInterview(
            id="sched1",
            interview=self.interview,
            created_at=self.base_time,
            date=self.base_time - timedelta(hours=3),
            status=InterviewStatus.COMPLETE,
            interviewers=[self.interviewer]
        )
        
        # Second interview also complete
        interview2 = ScheduledInterview(
            id="sched2",
            interview=Interview(id="int2", name="Onsite", schedulable=True),
            created_at=self.base_time,
            date=self.base_time - timedelta(hours=2),
            status=InterviewStatus.COMPLETE,
            interviewers=[self.interviewer]
        )
        
        application = Application(
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            availability_requested_at=self.base_time - timedelta(hours=6),
            availability_received_at=self.base_time - timedelta(hours=5),
            interviews=[interview1, interview2]
        )
        
        # Should return PENDING_DECISION since all interviews are complete
        assert application.get_stage_status() == StageStatus.PENDING_DECISION
    
    def test_interviews_with_scheduled_status(self):
        """Test status when interviews are scheduled (not yet taken)."""
        scheduled_interview = ScheduledInterview(
            id="sched1",
            interview=self.interview,
            created_at=self.base_time,
            date=self.base_time + timedelta(days=1),  # Future interview
            status=InterviewStatus.SCHEDULED,
            interviewers=[self.interviewer]
        )
        
        application = Application(
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            availability_requested_at=self.base_time - timedelta(hours=2),
            availability_received_at=self.base_time - timedelta(hours=1),
            interviews=[scheduled_interview]
        )
        
        assert application.get_stage_status() == StageStatus.INTERVIEW_SCHEDULED
    
    def test_priority_order_with_interviews(self):
        """Test that interview status takes priority over availability status."""
        scheduled_interview = ScheduledInterview(
            id="sched1",
            interview=self.interview,
            created_at=self.base_time,
            date=self.base_time - timedelta(hours=1),
            status=InterviewStatus.AWAITING_FEEDBACK,
            interviewers=[self.interviewer]
        )
        
        # Even with availability received, should prioritize interview status
        application = Application(
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            availability_requested_at=self.base_time - timedelta(hours=3),
            availability_received_at=self.base_time - timedelta(hours=2),
            interviews=[scheduled_interview]
        )
        
        # Should return PENDING_SCORECARD, not PENDING_SCHEDULING
        assert application.get_stage_status() == StageStatus.PENDING_SCORECARD
