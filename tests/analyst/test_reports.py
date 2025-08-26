"""
Tests for the reports module.
"""

import pytest
from datetime import datetime
from src.analyst.dataclasses import (
    Job, JobStage, Interview, User, Location, Department, Role,
    RoleFunction, Seniority
)


class TestReports:
    """Test cases for reports functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create common test objects
        self.location = Location(id="123", name="Remote")
        self.department = Department(id="456", name="Engineering")
        self.user = User(id="789", first_name="John", last_name="Doe")
        
        # Create take home test stage
        self.take_home_stage = JobStage(
            id="stage1",
            name="Take Home Test",
            interviews=[
                Interview(id="int1", name="Take Home Test", schedulable=False)
            ]
        )
        
        # Create regular interview stage
        self.regular_stage = JobStage(
            id="stage2",
            name="Technical Interview",
            interviews=[
                Interview(id="int2", name="Technical Interview", schedulable=True)
            ]
        )
    
    def test_is_ai_enabled_swe1_with_take_home(self):
        """Test AI enabled for SWE1 with Take Home Test stage."""
        job = Job(
            id="job1",
            name="Software Engineer 1",
            location=self.location,
            created_at=datetime.now(),
            opened_at=datetime.now(),
            hiring_managers=[self.user],
            recruiters=[self.user],
            coordinators=[self.user],
            sourcers=[self.user],
            departments=[self.department],
            role=Role(function=RoleFunction.Engineer, seniority=Seniority.SWE1),
            stages=[self.take_home_stage]
        )
        
        assert job.is_ai_enabled() == True
    
    def test_is_ai_enabled_swe2_with_take_home(self):
        """Test AI enabled for SWE2 with Take Home Test stage."""
        job = Job(
            id="job2",
            name="Software Engineer 2",
            location=self.location,
            created_at=datetime.now(),
            opened_at=datetime.now(),
            hiring_managers=[self.user],
            recruiters=[self.user],
            coordinators=[self.user],
            sourcers=[self.user],
            departments=[self.department],
            role=Role(function=RoleFunction.Engineer, seniority=Seniority.SWE2),
            stages=[self.take_home_stage]
        )
        
        assert job.is_ai_enabled() == True
    
    def test_is_ai_enabled_senior_with_devai_screen(self):
        """Test AI enabled for Senior with DevAI Technical Screen interview."""
        devai_stage = JobStage(
            id="stage3",
            name="Technical Interview",
            interviews=[
                Interview(id="int3", name="DevAI Technical Screen", schedulable=True)
            ]
        )
        
        job = Job(
            id="job3",
            name="Senior Software Engineer",
            location=self.location,
            created_at=datetime.now(),
            opened_at=datetime.now(),
            hiring_managers=[self.user],
            recruiters=[self.user],
            coordinators=[self.user],
            sourcers=[self.user],
            departments=[self.department],
            role=Role(function=RoleFunction.Engineer, seniority=Seniority.Senior),
            stages=[devai_stage]
        )
        
        assert job.is_ai_enabled() == True
    
    def test_is_ai_enabled_swe1_without_take_home(self):
        """Test AI disabled for SWE1 without Take Home Test stage."""
        job = Job(
            id="job4",
            name="Software Engineer 1",
            location=self.location,
            created_at=datetime.now(),
            opened_at=datetime.now(),
            hiring_managers=[self.user],
            recruiters=[self.user],
            coordinators=[self.user],
            sourcers=[self.user],
            departments=[self.department],
            role=Role(function=RoleFunction.Engineer, seniority=Seniority.SWE1),
            stages=[self.regular_stage]
        )
        
        assert job.is_ai_enabled() == False
    
    def test_is_ai_enabled_staff_with_take_home(self):
        """Test AI disabled for Staff level even with Take Home Test stage."""
        job = Job(
            id="job5",
            name="Staff Software Engineer",
            location=self.location,
            created_at=datetime.now(),
            opened_at=datetime.now(),
            hiring_managers=[self.user],
            recruiters=[self.user],
            coordinators=[self.user],
            sourcers=[self.user],
            departments=[self.department],
            role=Role(function=RoleFunction.Engineer, seniority=Seniority.Staff),
            stages=[self.take_home_stage]
        )
        
        assert job.is_ai_enabled() == False
    
    def test_is_ai_enabled_non_engineer_role(self):
        """Test AI disabled for non-engineer roles."""
        job = Job(
            id="job6",
            name="Product Manager",
            location=self.location,
            created_at=datetime.now(),
            opened_at=datetime.now(),
            hiring_managers=[self.user],
            recruiters=[self.user],
            coordinators=[self.user],
            sourcers=[self.user],
            departments=[self.department],
            role=Role(function=RoleFunction.Other, seniority=Seniority.Unknown),
            stages=[self.take_home_stage]
        )
        
        assert job.is_ai_enabled() == False
    
    def test_is_ai_enabled_multiple_stages_with_take_home(self):
        """Test AI enabled when Take Home Test is one of multiple stages."""
        job = Job(
            id="job7",
            name="Software Engineer 2",
            location=self.location,
            created_at=datetime.now(),
            opened_at=datetime.now(),
            hiring_managers=[self.user],
            recruiters=[self.user],
            coordinators=[self.user],
            sourcers=[self.user],
            departments=[self.department],
            role=Role(function=RoleFunction.Engineer, seniority=Seniority.SWE2),
            stages=[self.regular_stage, self.take_home_stage]
        )
        
        assert job.is_ai_enabled() == True
    
    def test_is_ai_enabled_partial_take_home_name(self):
        """Test AI enabled when stage name contains 'Take Home Test'."""
        partial_take_home_stage = JobStage(
            id="stage3",
            name="Take Home Test - Advanced",
            interviews=[
                Interview(id="int3", name="Take Home Test", schedulable=False)
            ]
        )
        
        job = Job(
            id="job8",
            name="Software Engineer 1",
            location=self.location,
            created_at=datetime.now(),
            opened_at=datetime.now(),
            hiring_managers=[self.user],
            recruiters=[self.user],
            coordinators=[self.user],
            sourcers=[self.user],
            departments=[self.department],
            role=Role(function=RoleFunction.Engineer, seniority=Seniority.SWE1),
            stages=[partial_take_home_stage]
        )
        
        assert job.is_ai_enabled() == True
    
    def test_is_ai_enabled_senior_without_devai_screen(self):
        """Test AI disabled for Senior without DevAI Technical Screen interview."""
        regular_stage = JobStage(
            id="stage4",
            name="Technical Interview",
            interviews=[
                Interview(id="int4", name="Regular Technical Screen", schedulable=True)
            ]
        )
        
        job = Job(
            id="job9",
            name="Senior Software Engineer",
            location=self.location,
            created_at=datetime.now(),
            opened_at=datetime.now(),
            hiring_managers=[self.user],
            recruiters=[self.user],
            coordinators=[self.user],
            sourcers=[self.user],
            departments=[self.department],
            role=Role(function=RoleFunction.Engineer, seniority=Seniority.Senior),
            stages=[regular_stage]
        )
        
        assert job.is_ai_enabled() == False
