"""
Tests for the Greenhouse API client.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from src.analyst.client.greenhouse import GreenhouseClient
from src.analyst.dataclasses import (
    Application, Job, JobStage, Interview, User, Location, Department, Role,
    RoleFunction, Seniority, ScheduledInterview, InterviewStatus, StageStatus
)
from .test_data import (
    SAMPLE_APPLICATION_JSON, SAMPLE_ACTIVITY_FEED_JSON, 
    SAMPLE_SCHEDULED_INTERVIEWS_JSON, SAMPLE_SCORECARDS_JSON, SAMPLE_JOB_STAGES_JSON,
    create_dummy_job_manager
)


class TestGreenhouseClient:
    """Test cases for GreenhouseClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = GreenhouseClient()
        self.job_manager = create_dummy_job_manager()

    @patch('src.analyst.client.greenhouse.GreenhouseClient._make_rate_limited_request')
    def test_get_application_schedulable_stage(self, mock_request):
        """Test get_application for a schedulable stage with interviews."""
        # Mock API responses
        mock_request.side_effect = [
            Mock(status_code=200, json=lambda: SAMPLE_APPLICATION_JSON),
            Mock(status_code=200, json=lambda: SAMPLE_ACTIVITY_FEED_JSON),
            Mock(status_code=200, json=lambda: SAMPLE_SCHEDULED_INTERVIEWS_JSON),
            Mock(status_code=200, json=lambda: SAMPLE_SCORECARDS_JSON)
        ]

        # Get the application
        application = self.client.get_application("156728361", self.job_manager)

        # Verify the application was created correctly
        assert isinstance(application, Application)
        assert application.job.id == "5179819"
        assert application.current_stage.id == "12862064"
        assert application.current_stage.name == "Evaluation Stage 3"
        assert application.candidate_name == "John Doe"
        assert application.candidate_id == "138678330"
        
        # Verify moved_to_stage_at was parsed from activity feed
        expected_time = datetime(2025, 8, 19, 11, 9, 0, 231000).replace(tzinfo=timezone.utc)
        assert application.moved_to_stage_at == expected_time
        
        # Verify availability timestamps were parsed
        availability_requested = datetime(2025, 8, 20, 10, 0, 0).replace(tzinfo=timezone.utc)
        availability_received = datetime(2025, 8, 20, 14, 30, 0).replace(tzinfo=timezone.utc)
        assert application.availability_requested_at == availability_requested
        assert application.availability_received_at == availability_received
        
        # Verify take-home fields are None for schedulable stage
        assert application.take_home_submitted_at is None
        assert application.take_home_grading is None
        
        # Verify scheduled interviews were created
        assert len(application.interviews) == 1
        interview = application.interviews[0]
        assert interview.id == "987654"
        assert interview.interview.name == "Technical Phone Screen"
        assert interview.status == InterviewStatus.COMPLETE
        assert len(interview.interviewers) == 2
        assert interview.interviewers[0].first_name == "John"
        assert interview.interviewers[0].last_name == "Doe"
        assert interview.interviewers[1].first_name == "Jane"
        assert interview.interviewers[1].last_name == "Smith"
        
        # Verify scorecards were fetched and attached
        assert len(interview.scorecards) == 2
        scorecard1 = interview.scorecards[0]
        assert scorecard1.id == "26419635"
        assert scorecard1.by.first_name == "John"
        assert scorecard1.by.last_name == "Doe"
        assert scorecard1.decision.value == "YES"
        
        scorecard2 = interview.scorecards[1]
        assert scorecard2.id == "26419635004"
        assert scorecard2.by.first_name == "Jane"
        assert scorecard2.by.last_name == "Smith"
        assert scorecard2.decision.value == "STRONG_YES"
