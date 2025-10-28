"""
Tests for the Application dataclass stage status calculation.
"""

import pytest
from datetime import datetime, timedelta
from src.analyst.dataclasses import (
    Application, Job, JobStage, Interview, User, Location, Department, Role, 
    RoleFunction, Seniority, ScheduledInterview, StageStatus, InterviewStatus, ApplicationStatus
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
            id="app1",
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            candidate_name="Test Candidate",
            candidate_id="candidate1",
            status=ApplicationStatus.ACTIVE,
            availability_requested_at=None,
            availability_received_at=None,
            take_home_submitted_at=None,
            take_home_grading=None,
            interviews=[]
        )
        
        assert application.get_stage_status() == StageStatus.PENDING_AVAILABILITY_REQUEST
    
    def test_waiting_for_availability(self):
        """Test status when availability has been requested but not received."""
        application = Application(
            id="app2",
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            candidate_name="Test Candidate",
            candidate_id="candidate2",
            status=ApplicationStatus.ACTIVE,
            availability_requested_at=self.base_time,
            availability_received_at=None,
            take_home_submitted_at=None,
            take_home_grading=None,
            interviews=[]
        )
        
        assert application.get_stage_status() == StageStatus.WAITING_FOR_AVAILABILITY
    
    def test_pending_scheduling(self):
        """Test status when availability has been received but no interviews scheduled."""
        application = Application(
            id="app3",
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            candidate_name="Test Candidate",
            candidate_id="candidate3",
            status=ApplicationStatus.ACTIVE,
            availability_requested_at=self.base_time - timedelta(hours=1),
            availability_received_at=self.base_time,
            take_home_submitted_at=None,
            take_home_grading=None,
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
            interviewers=[self.interviewer],
            scorecards=[]
        )
        
        application = Application(
            id="app4",
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            candidate_name="Test Candidate",
            candidate_id="candidate4",
            status=ApplicationStatus.ACTIVE,
            availability_requested_at=self.base_time - timedelta(hours=2),
            availability_received_at=self.base_time - timedelta(hours=1),
            take_home_submitted_at=None,
            take_home_grading=None,
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
            interviewers=[self.interviewer],
            scorecards=[]
        )
        
        application = Application(
            id="app5",
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            candidate_name="Test Candidate",
            candidate_id="candidate5",
            status=ApplicationStatus.ACTIVE,
            availability_requested_at=self.base_time - timedelta(hours=3),
            availability_received_at=self.base_time - timedelta(hours=2),
            take_home_submitted_at=None,
            take_home_grading=None,
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
            interviewers=[self.interviewer],
            scorecards=[]
        )
        
        application = Application(
            id="app6",
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            candidate_name="Test Candidate",
            candidate_id="candidate6",
            status=ApplicationStatus.ACTIVE,
            availability_requested_at=self.base_time - timedelta(hours=4),
            availability_received_at=self.base_time - timedelta(hours=3),
            take_home_submitted_at=None,
            take_home_grading=None,
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
            interviewers=[self.interviewer],
            scorecards=[]
        )
        
        # Second interview awaiting feedback
        interview2 = ScheduledInterview(
            id="sched2",
            interview=Interview(id="int2", name="Onsite", schedulable=True),
            created_at=self.base_time,
            date=self.base_time - timedelta(hours=1),
            status=InterviewStatus.AWAITING_FEEDBACK,
            interviewers=[self.interviewer],
            scorecards=[]
        )
        
        application = Application(
            id="app7",
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            candidate_name="Test Candidate",
            candidate_id="candidate7",
            status=ApplicationStatus.ACTIVE,
            availability_requested_at=self.base_time - timedelta(hours=5),
            availability_received_at=self.base_time - timedelta(hours=4),
            take_home_submitted_at=None,
            take_home_grading=None,
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
            interviewers=[self.interviewer],
            scorecards=[]
        )
        
        # Second interview also complete
        interview2 = ScheduledInterview(
            id="sched2",
            interview=Interview(id="int2", name="Onsite", schedulable=True),
            created_at=self.base_time,
            date=self.base_time - timedelta(hours=2),
            status=InterviewStatus.COMPLETE,
            interviewers=[self.interviewer],
            scorecards=[]
        )
        
        application = Application(
            id="app8",
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            candidate_name="Test Candidate",
            candidate_id="candidate8",
            status=ApplicationStatus.ACTIVE,
            availability_requested_at=self.base_time - timedelta(hours=6),
            availability_received_at=self.base_time - timedelta(hours=5),
            take_home_submitted_at=None,
            take_home_grading=None,
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
            interviewers=[self.interviewer],
            scorecards=[]
        )
        
        application = Application(
            id="app9",
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            candidate_name="Test Candidate",
            candidate_id="candidate9",
            status=ApplicationStatus.ACTIVE,
            availability_requested_at=self.base_time - timedelta(hours=2),
            availability_received_at=self.base_time - timedelta(hours=1),
            take_home_submitted_at=None,
            take_home_grading=None,
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
            interviewers=[self.interviewer],
            scorecards=[]
        )
        
        # Even with availability received, should prioritize interview status
        application = Application(
            id="app10",
            job=self.job,
            current_stage=self.stage,
            moved_to_stage_at=self.base_time,
            candidate_name="Test Candidate",
            candidate_id="candidate10",
            status=ApplicationStatus.ACTIVE,
            availability_requested_at=self.base_time - timedelta(hours=3),
            availability_received_at=self.base_time - timedelta(hours=2),
            take_home_submitted_at=None,
            take_home_grading=None,
            interviews=[scheduled_interview]
        )
        
        # Should return PENDING_SCORECARD, not PENDING_SCHEDULING
        assert application.get_stage_status() == StageStatus.PENDING_SCORECARD


class TestJobTakeHomeSubmission:
    """Test cases for Job.at_or_after_take_home_submission method."""
    
    def setup_method(self):
        """Set up common test data."""
        # Create test interviews
        self.schedulable_interview = Interview(id="int1", name="Phone Screen", schedulable=True)
        self.non_schedulable_interview = Interview(id="int2", name="Take Home Test", schedulable=False)
        
        # Create test stages
        self.phone_screen_stage = JobStage(
            id="stage1",
            name="Phone Screen",
            interviews=[self.schedulable_interview]
        )
        
        self.take_home_stage = JobStage(
            id="stage2", 
            name="Take Home Test",
            interviews=[self.non_schedulable_interview]
        )
        
        self.final_interview_stage = JobStage(
            id="stage3",
            name="Final Interview",
            interviews=[self.schedulable_interview]
        )
        
        self.onsite_stage = JobStage(
            id="stage4",
            name="Onsite Interview",
            interviews=[self.schedulable_interview]
        )
        
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
    
    def test_no_take_home_stage(self):
        """Test when job has no take-home stage."""
        # Job with only schedulable stages
        self.job.stages = [self.phone_screen_stage, self.final_interview_stage]
        
        # Should return False for any stage
        assert not self.job.at_or_after_take_home_submission(self.phone_screen_stage)
        assert not self.job.at_or_after_take_home_submission(self.final_interview_stage)
    
    def test_take_home_stage_itself(self):
        """Test when checking the take-home stage itself."""
        self.job.stages = [self.phone_screen_stage, self.take_home_stage, self.final_interview_stage]
        
        # Should return True for the take-home stage itself
        assert self.job.at_or_after_take_home_submission(self.take_home_stage)
    
    def test_stage_after_take_home(self):
        """Test when checking stages that come after take-home."""
        self.job.stages = [self.phone_screen_stage, self.take_home_stage, self.final_interview_stage, self.onsite_stage]
        
        # Should return True for stages after take-home
        assert self.job.at_or_after_take_home_submission(self.final_interview_stage)
        assert self.job.at_or_after_take_home_submission(self.onsite_stage)
        
        # Should return False for stages before take-home
        assert not self.job.at_or_after_take_home_submission(self.phone_screen_stage)
    
    def test_stage_before_take_home(self):
        """Test when checking stages that come before take-home."""
        self.job.stages = [self.phone_screen_stage, self.take_home_stage, self.final_interview_stage]
        
        # Should return False for stages before take-home
        assert not self.job.at_or_after_take_home_submission(self.phone_screen_stage)
    
    def test_multiple_take_home_stages(self):
        """Test when job has multiple take-home stages (edge case)."""
        # Create another take-home stage
        another_take_home_stage = JobStage(
            id="stage5",
            name="Another Take Home Test",
            interviews=[self.non_schedulable_interview]
        )
        
        self.job.stages = [self.phone_screen_stage, self.take_home_stage, another_take_home_stage, self.final_interview_stage]
        
        # Should return True for both take-home stages
        assert self.job.at_or_after_take_home_submission(self.take_home_stage)
        assert self.job.at_or_after_take_home_submission(another_take_home_stage)
        
        # Should return True for stages after the first take-home
        assert self.job.at_or_after_take_home_submission(self.final_interview_stage)
        
        # Should return False for stages before the first take-home
        assert not self.job.at_or_after_take_home_submission(self.phone_screen_stage)
    
    def test_stage_not_in_job(self):
        """Test when checking a stage that doesn't belong to the job."""
        self.job.stages = [self.phone_screen_stage, self.take_home_stage, self.final_interview_stage]
        
        # Create a stage that's not in the job
        external_stage = JobStage(
            id="external_stage",
            name="External Stage",
            interviews=[self.schedulable_interview]
        )
        
        # Should return False for external stage
        assert not self.job.at_or_after_take_home_submission(external_stage)
    
    def test_empty_stages_list(self):
        """Test when job has no stages."""
        self.job.stages = []
        
        # Should return False for any stage
        assert not self.job.at_or_after_take_home_submission(self.take_home_stage)
    
    def test_take_home_at_beginning(self):
        """Test when take-home stage is the first stage."""
        self.job.stages = [self.take_home_stage, self.phone_screen_stage, self.final_interview_stage]
        
        # Should return True for take-home stage
        assert self.job.at_or_after_take_home_submission(self.take_home_stage)
        
        # Should return True for all subsequent stages
        assert self.job.at_or_after_take_home_submission(self.phone_screen_stage)
        assert self.job.at_or_after_take_home_submission(self.final_interview_stage)
    
    def test_take_home_at_end(self):
        """Test when take-home stage is the last stage."""
        self.job.stages = [self.phone_screen_stage, self.final_interview_stage, self.take_home_stage]
        
        # Should return False for stages before take-home
        assert not self.job.at_or_after_take_home_submission(self.phone_screen_stage)
        assert not self.job.at_or_after_take_home_submission(self.final_interview_stage)
        
        # Should return True for take-home stage
        assert self.job.at_or_after_take_home_submission(self.take_home_stage)
    
    def test_single_take_home_stage(self):
        """Test when job has only one take-home stage."""
        self.job.stages = [self.take_home_stage]
        
        # Should return True for the take-home stage
        assert self.job.at_or_after_take_home_submission(self.take_home_stage)
