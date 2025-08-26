"""
Greenhouse API client for fetching recruiting data.
"""

import requests
import base64
import time
from datetime import datetime
from typing import Dict, List, Optional

from ..config.greenhouse import API_KEY, DEPARTMENT_MAP
from ..dataclasses import Job, Department, Location, User, Role, RoleFunction, Seniority, JobStage, Interview, Application, TakeHomeGrading, ScheduledInterview, InterviewStatus, Scorecard, ScorecardDecision


class GreenhouseClient:
    """Client for interacting with the Greenhouse API."""
    
    def __init__(self, api_key: str = None, base_url: str = "https://harvest.greenhouse.io/v1"):
        """
        Initialize the Greenhouse client.
        
        Args:
            api_key: Greenhouse API key (optional, will use config if not provided)
            base_url: Base URL for the Greenhouse API
        """
        self.api_key = api_key or API_KEY
        self.base_url = base_url
        self.session = requests.Session()
        
        # Encode API key for Basic authentication
        encoded_key = base64.b64encode(f"{self.api_key}:".encode()).decode()
        self.session.headers.update({
            'Authorization': f'Basic {encoded_key}',
            'Content-Type': 'application/json'
        })
    
    def _make_rate_limited_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make a rate-limited request with exponential backoff for 429 errors.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments for requests
            
        Returns:
            requests.Response object
            
        Raises:
            Exception: If max retries exceeded
        """
        max_retries = 5
        base_delay = 1  # Start with 1 second delay
        
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                
                if response.status_code == 429:
                    # Rate limited - calculate delay with exponential backoff
                    delay = base_delay * (2 ** attempt)  # 1, 2, 4, 8, 16 seconds
                    
                    # Check if response has Retry-After header
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            delay = int(retry_after)
                        except ValueError:
                            pass  # Use calculated delay if header is invalid
                    
                    print(f"Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {delay} seconds...")
                    time.sleep(delay)
                    continue
                
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Request failed after {max_retries} attempts: {e}")
                
                delay = base_delay * (2 ** attempt)
                print(f"Request failed (attempt {attempt + 1}/{max_retries}). Retrying in {delay} seconds...")
                time.sleep(delay)
        
        raise Exception(f"Max retries ({max_retries}) exceeded for request to {url}")
    
    def get_jobs(self, department_name: str = None, include_closed: bool = False) -> List[Job]:
        """
        Fetch jobs from Greenhouse API.
        
        Args:
            department_name: Optional department name to filter by
            include_closed: Whether to include closed jobs (default: False)
            
        Returns:
            List of Job objects
        """
        params = {"per_page": 100}
        
        # Add department filter if provided
        if department_name:
            if department_name not in DEPARTMENT_MAP:
                raise ValueError(f"Unknown department: {department_name}. Available: {list(DEPARTMENT_MAP.keys())}")
            params["department_id"] = DEPARTMENT_MAP[department_name]
        
        # Add status filter unless include_closed is True
        if not include_closed:
            params["status"] = "open"
        
        response = self._make_rate_limited_request("GET", f"{self.base_url}/jobs", params=params)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch jobs: {response.status_code} - {response.text}")
        
        jobs_data = response.json()
        jobs = []
        
        for job_data in jobs_data:
            # Extract location data from offices
            offices_data = job_data.get("offices", [])
            location = Location(id="", name="")
            
            if offices_data:
                # Use the first office as the primary location
                office_data = offices_data[0]
                location = Location(
                    id=str(office_data.get("id", "")),
                    name=office_data.get("name", "")
                )
            
            # Extract departments data
            departments = []
            for dept_data in job_data.get("departments", []):
                department = Department(
                    id=str(dept_data.get("id", "")),
                    name=dept_data.get("name", "")
                )
                departments.append(department)
            
            # Extract users data (hiring managers, recruiters, etc.)
            def extract_users(user_list):
                users = []
                for user_data in user_list:
                    user = User(
                        id=str(user_data.get("id", "")),
                        first_name=user_data.get("first_name", ""),
                        last_name=user_data.get("last_name", "")
                    )
                    users.append(user)
                return users
            
            # Parse role from job name and openings data
            role = self._parse_role_from_job_name(job_data.get("name", ""), job_data.get("openings", []))
            
            # Create Job object
            job = Job(
                id=str(job_data.get("id", "")),
                name=job_data.get("name", ""),
                location=location,
                created_at=datetime.fromisoformat(job_data.get("created_at", "").replace("Z", "+00:00")),
                opened_at=datetime.fromisoformat(job_data.get("opened_at", "").replace("Z", "+00:00")) if job_data.get("opened_at") else None,
                hiring_managers=extract_users(job_data.get("hiring_team", {}).get("hiring_managers", [])),
                recruiters=extract_users(job_data.get("hiring_team", {}).get("recruiters", [])),
                coordinators=extract_users(job_data.get("hiring_team", {}).get("coordinators", [])),
                sourcers=extract_users(job_data.get("hiring_team", {}).get("sourcers", [])),
                departments=departments,
                role=role,
                stages=None
            )
            jobs.append(job)
        
        return jobs
    
    def _parse_role_from_job_name(self, job_name: str, openings_data: list = None) -> Role:
        """
        Parse role information from job name and openings data.
        
        Args:
            job_name: The name of the job
            openings_data: List of openings data from the job
            
        Returns:
            Role object with function and seniority
            
        Raises:
            ValueError: If function is Engineer but seniority cannot be determined
        """
        job_name_lower = job_name.lower()
        
        # Determine function
        if "software engineer" in job_name_lower or "swe" in job_name_lower:
            function = RoleFunction.Engineer
        else:
            function = RoleFunction.Other
        
        # If function is not Engineer, seniority is Unknown
        if function != RoleFunction.Engineer:
            return Role(function=function, seniority=Seniority.Unknown)
        
        # For Engineer function, try to determine seniority from job name first
        try:
            if any(phrase in job_name_lower for phrase in ["software engineer 3", "swe3", "engineer 3", "software engineer iii", "senior software engineer", "senior swe", "senior engineer"]):
                seniority = Seniority.Senior  # Map SWE3 to Senior
            elif any(phrase in job_name_lower for phrase in ["software engineer 2", "swe2", "engineer 2", "software engineer ii"]):
                seniority = Seniority.SWE2
            elif any(phrase in job_name_lower for phrase in ["software engineer 1", "swe1", "engineer 1", "software engineer i"]):
                seniority = Seniority.SWE1
            elif any(phrase in job_name_lower for phrase in ["staff software engineer", "staff swe", "staff engineer"]):
                seniority = Seniority.Staff
            else:
                # If name parsing fails, try to get level from openings custom fields
                if openings_data:
                    for opening in openings_data:
                        custom_fields = opening.get("custom_fields", {})
                        level = custom_fields.get("level")
                        if level:
                            # Map level to seniority
                            if level == "P2":
                                seniority = Seniority.SWE1
                            elif level == "P3":
                                seniority = Seniority.SWE2
                            elif level == "P4":
                                seniority = Seniority.Senior
                            elif level == "P5":
                                seniority = Seniority.Staff
                            else:
                                continue  # Try next opening if level doesn't match
                            break  # Found a valid level, break out of openings loop
                    else:
                        # No valid level found in any opening
                        raise ValueError(f"Cannot determine seniority for Engineer role in job: {job_name}")
                else:
                    raise ValueError(f"Cannot determine seniority for Engineer role in job: {job_name}")
        except ValueError:
            # Re-raise the ValueError with the original message
            raise ValueError(f"Cannot determine seniority for Engineer role in job: {job_name}")
        
        return Role(function=function, seniority=seniority)
    
    def fill_stages(self, job: Job) -> Job:
        """
        Fill stages and interviews for a job by calling the Greenhouse API.
        
        Args:
            job: Job object to fill stages for
            
        Returns:
            Job object with stages populated
        """
        # Get stages for the job
        response = self._make_rate_limited_request("GET", f"{self.base_url}/jobs/{job.id}/stages")
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch stages for job {job.id}: {response.status_code} - {response.text}")
        
        stages_data = response.json()
        stages = []
        
        for stage_data in stages_data:
            # Extract interviews from the stage data (already included in response)
            interviews = []
            interviews_data = stage_data.get("interviews", [])
            
            for interview_data in interviews_data:
                interview = Interview(
                    id=str(interview_data.get("id", "")),
                    name=interview_data.get("name", ""),
                    schedulable=interview_data.get("schedulable", False)
                )
                interviews.append(interview)
            
            # Create JobStage object
            stage = JobStage(
                id=str(stage_data.get("id", "")),
                name=stage_data.get("name", ""),
                interviews=interviews
            )
            stages.append(stage)
        
        # Update the job with stages
        job.stages = stages
        return job
    
    def _hydrate_application(self, app_data: dict, job: 'Job', current_stage: 'JobStage') -> 'Application':
        """
        Hydrate an application with detailed data from activity feed, interviews, and scorecards.
        
        Args:
            app_data: Raw application data from Greenhouse API
            job: Job object for this application
            current_stage: Current stage object for this application
            
        Returns:
            Hydrated Application object
        """
        application_id = str(app_data.get("id"))
        candidate_id = str(app_data.get("candidate_id"))
        
        # Check if current stage is relevant
        if not current_stage.is_schedulable and not current_stage.is_take_home:
            # Return basic application without further processing
            return Application(
                id=application_id,
                job=job,
                current_stage=current_stage,
                moved_to_stage_at=None,
                candidate_name=None,
                candidate_id=candidate_id,
                availability_requested_at=None,
                availability_received_at=None,
                take_home_submitted_at=None,
                take_home_grading=None,
                interviews=[]
            )
        

        
        # Get activity stream for the candidate
        activity_response = self._make_rate_limited_request("GET", f"{self.base_url}/candidates/{candidate_id}/activity_feed")
        
        if activity_response.status_code != 200:
            raise Exception(f"Failed to fetch activity feed for candidate {candidate_id}: {activity_response.status_code} - {activity_response.text}")
        
        activity_data = activity_response.json()
        activities = activity_data.get("activities", [])
        notes = activity_data.get("notes", [])
        
        # Find moved_to_stage_at and candidate name from activity stream
        moved_to_stage_at = None
        candidate_name = None
        for activity in activities:
            body = activity.get("body", "")
            if f"was moved into {current_stage.name} for" in body:
                moved_to_stage_at = datetime.fromisoformat(activity.get("created_at", "").replace("Z", "+00:00"))
                # Extract candidate name from the activity body
                # Format: "<candidate_name> was moved into <stage_name> for <job_name>"
                candidate_name = body.split(" was moved into ")[0].strip()
                break
        
        # Handle take-home stage
        if current_stage.is_take_home:
            # Find take home submission time from activity stream
            take_home_submitted_at = None
            for activity in activities:
                body = activity.get("body", "")
                if "submitted a take home test" in body:
                    take_home_submitted_at = datetime.fromisoformat(activity.get("created_at", "").replace("Z", "+00:00"))
                    break
            
            # Get scorecards for the application
            scorecards_response = self._make_rate_limited_request("GET", f"{self.base_url}/applications/{application_id}/scorecards")
            
            take_home_grading = None
            if scorecards_response.status_code == 200:
                scorecards = scorecards_response.json()
                
                # Find scorecard for the take-home interview
                for scorecard in scorecards:
                    interview_step = scorecard.get("interview_step", {})
                    interview_id = str(interview_step.get("id"))
                    
                    # Check if this scorecard is for the take-home interview
                    for interview in current_stage.interviews:
                        if interview.id == interview_id:
                            # Create TakeHomeGrading object
                            submitted_by_data = scorecard.get("submitted_by", {})
                            submitted_by = User(
                                id=str(submitted_by_data.get("id", "")),
                                first_name=submitted_by_data.get("first_name", ""),
                                last_name=submitted_by_data.get("last_name", "")
                            )
                            
                            take_home_grading = TakeHomeGrading(
                                id=str(scorecard.get("id", "")),
                                submitted_at=datetime.fromisoformat(scorecard.get("submitted_at", "").replace("Z", "+00:00")),
                                by=submitted_by
                            )
                            break
            
            return Application(
                id=application_id,
                job=job,
                current_stage=current_stage,
                moved_to_stage_at=moved_to_stage_at,
                candidate_name=candidate_name,
                candidate_id=candidate_id,
                availability_requested_at=None,
                availability_received_at=None,
                take_home_submitted_at=take_home_submitted_at,
                take_home_grading=take_home_grading,
                interviews=[]
            )
        
        # For non-take-home stages, process scheduled interviews and availability
        # Get scheduled interviews for the application
        interviews_response = self._make_rate_limited_request("GET", f"{self.base_url}/applications/{application_id}/scheduled_interviews")
        
        # Get all scorecards for the application (if any interviews are complete)
        all_scorecards = {}
        scorecards_response = self._make_rate_limited_request("GET", f"{self.base_url}/applications/{application_id}/scorecards")
        if scorecards_response.status_code == 200:
            scorecards_data = scorecards_response.json()
            for scorecard_data in scorecards_data:
                scorecard_id = str(scorecard_data.get("id", ""))
                # Create User object for the scorecard submitter
                submitted_by_data = scorecard_data.get("submitted_by", {})
                submitted_by = User(
                    id=str(submitted_by_data.get("id", "")),
                    first_name=submitted_by_data.get("first_name", ""),
                    last_name=submitted_by_data.get("last_name", "")
                )
                
                # Create Scorecard object
                scorecard = Scorecard(
                    id=scorecard_id,
                    submitted_at=datetime.fromisoformat(scorecard_data.get("submitted_at", "").replace("Z", "+00:00")),
                    by=submitted_by,
                    decision=ScorecardDecision(scorecard_data.get("overall_recommendation", "NO_DECISION").upper())
                )
                all_scorecards[scorecard_id] = scorecard
        
        interviews = []
        if interviews_response.status_code == 200:
            scheduled_interviews_data = interviews_response.json()
            
            for scheduled_interview_data in scheduled_interviews_data:
                # Check if this interview is for the current stage
                interview_data = scheduled_interview_data.get("interview", {})
                interview_id = str(interview_data.get("id"))
                
                # Find matching interview in current stage
                matching_interview = None
                for interview in current_stage.interviews:
                    if interview.id == interview_id:
                        matching_interview = interview
                        break
                
                if matching_interview:
                    # Extract interviewers
                    interviewers = []
                    scorecards = []
                    
                    for interviewer_data in scheduled_interview_data.get("interviewers", []):
                        # Parse name into first and last name
                        full_name = interviewer_data.get("name", "")
                        name_parts = full_name.split(" ", 1)
                        first_name = name_parts[0] if name_parts else ""
                        last_name = name_parts[1] if len(name_parts) > 1 else ""
                        
                        interviewer = User(
                            id=str(interviewer_data.get("id", "")),
                            first_name=first_name,
                            last_name=last_name
                        )
                        interviewers.append(interviewer)
                        
                        # If interview is complete, find matching scorecard
                        if scheduled_interview_data.get("status", "").lower() == "complete":
                            scorecard_id = interviewer_data.get("scorecard_id")
                            if scorecard_id and str(scorecard_id) in all_scorecards:
                                scorecards.append(all_scorecards[str(scorecard_id)])
                    
                    # Find interview scheduling timestamp from notes
                    interview_scheduled_at = None
                    for note in notes:
                        body = note.get("body", "")
                        # Look for scheduling note: "... scheduled <candidate_name>'s <stage name> interviews for ..."
                        if "scheduled" in body and f"{current_stage.name} interviews for" in body:
                            interview_scheduled_at = datetime.fromisoformat(note.get("created_at", "").replace("Z", "+00:00"))
                            break
                    
                    # Fallback: look for confirmation sent in actions array
                    if interview_scheduled_at is None:
                        for action in activities:
                            body = action.get("body", "")
                            # Look for confirmation sent: "... availability from Received to Confirmation sent for ... (<stage name>)"
                            if "availability from Received to Confirmation sent for" in body and f"({current_stage.name})" in body:
                                interview_scheduled_at = datetime.fromisoformat(action.get("created_at", "").replace("Z", "+00:00"))
                                break
                    
                    # Create ScheduledInterview object
                    start_data = scheduled_interview_data.get("start", {})
                    start_datetime = start_data.get("date_time", "")
                    
                    scheduled_interview = ScheduledInterview(
                        id=str(scheduled_interview_data.get("id", "")),
                        interview=matching_interview,
                        created_at=interview_scheduled_at,
                        date=datetime.fromisoformat(start_datetime.replace("Z", "+00:00")),
                        status=InterviewStatus(scheduled_interview_data.get("status", "scheduled").upper()),
                        interviewers=interviewers,
                        scorecards=scorecards
                    )
                    interviews.append(scheduled_interview)
        
        # Look for availability request in activity feed
        availability_requested_at = None
        availability_received_at = None
        
        for activity in activities:
            body = activity.get("body", "")
            
            # Check for availability request
            if f"manually updated" in body and "availability from Not requested to Requested for" in body and f"({current_stage.name})" in body:
                availability_requested_at = datetime.fromisoformat(activity.get("created_at", "").replace("Z", "+00:00"))
            
            # Check for availability submission
            if "submitted their availability for" in body and f"({current_stage.name})" in body:
                availability_received_at = datetime.fromisoformat(activity.get("created_at", "").replace("Z", "+00:00"))
        
        return Application(
            id=application_id,
            job=job,
            current_stage=current_stage,
            moved_to_stage_at=moved_to_stage_at,
            candidate_name=candidate_name,
            candidate_id=candidate_id,
            availability_requested_at=availability_requested_at,
            availability_received_at=availability_received_at,
            take_home_submitted_at=None,
            take_home_grading=None,
            interviews=interviews
        )

    def get_application(self, application_id: str, job_manager: "JobManager") -> 'Application':
        """
        Get application details from Greenhouse API.
        
        Args:
            application_id: The application ID to fetch
            job_manager: JobManager instance to get job details
            
        Returns:
            Application object with populated data
            
        Raises:
            NotImplementedError: For non-take-home stages (not yet implemented)
        """
        
        # Get application data
        response = self._make_rate_limited_request("GET", f"{self.base_url}/applications/{application_id}")
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch application {application_id}: {response.status_code} - {response.text}")
        
        app_data = response.json()
        
        # Get the job from job manager
        # Extract job ID from the jobs array
        jobs_data = app_data.get("jobs", [])
        if not jobs_data:
            raise ValueError(f"No job found in application {application_id}")
        
        job_id = str(jobs_data[0].get("id"))
        job = job_manager.get_by_id(job_id)
        
        if not job:
            raise ValueError(f"Job {job_id} not found in job manager for application {application_id}")
        
        # Find current stage
        current_stage_data = app_data.get("current_stage", {})
        current_stage_id = str(current_stage_data.get("id"))
        current_stage = None
        
        for stage in job.stages:
            if stage.id == current_stage_id:
                current_stage = stage
                break
        
        if not current_stage:
            raise ValueError(f"Current stage {current_stage_id} not found in job {job_id}")
        
        # Use the shared hydration logic
        return self._hydrate_application(app_data, job, current_stage)

    def get_applications_for_job(self, job: 'Job') -> List['Application']:
        """
        Get all active applications for a specific job from Greenhouse API.
        
        Args:
            job: Job object to fetch applications for
            
        Returns:
            List of Application objects with populated data
        """
        # Get applications for the job
        params = {"job_id": job.id, "status": "active"}
        response = self._make_rate_limited_request("GET", f"{self.base_url}/applications", params=params)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch applications for job {job.id}: {response.status_code} - {response.text}")
        
        applications_data = response.json()
        applications = []
        
        for app_data in applications_data:
            if app_data.get("prospect"):
                continue
            current_stage_data = app_data.get("current_stage", {})
            current_stage_id = str(current_stage_data.get("id"))
            current_stage = None
            
            for stage in job.stages:
                if stage.id == current_stage_id:
                    current_stage = stage
                    break
            
            if not current_stage:
                # Skip applications with unknown stages
                continue
            
            # Hydrate the application using shared logic
            try:
                application = self._hydrate_application(app_data, job, current_stage)
                applications.append(application)
            except Exception as e:
                # Log error but continue processing other applications
                print(f"Warning: Failed to hydrate application {app_data.get('id')}: {e}")
                continue
        
        return applications