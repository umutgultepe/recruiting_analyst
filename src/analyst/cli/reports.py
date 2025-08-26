"""
Reports module for generating recruiting analytics reports.
"""

import csv
import sys
import click
from ..client.greenhouse import GreenhouseClient
from ..dataclasses import Job, RoleFunction, Seniority, TakeHomeStatus
from ..job_manager import JobManager
from ..reporter import Reporter
from datetime import datetime, timezone


@click.command()
@click.option('--cache-path', default="src/analyst/config/jobs.yaml", help='Path to the job cache file')
def report_ai_rollout(cache_path):
    """
    Generate a CSV report on AI rollout status across all jobs.
    
    Analyzes all jobs in the JobManager and outputs a CSV with AI eligibility and enabled status.
    """
    # Load job manager
    job_manager = JobManager(cache_path)
    
    # Get all jobs
    all_jobs = list(job_manager.by_id.values())
    
    # Create CSV writer
    writer = csv.writer(sys.stdout)
    
    # Write CSV header
    writer.writerow([
        'job_name',
        'job_id', 
        'ai_eligible',
        'ai_enabled',
        'recruiter_name',
        'location',
        'department',
        'level'
    ])
    
    # Process each job and write to CSV
    for job in all_jobs:
        # Determine AI eligibility
        ai_eligible = job.is_ai_eligible()
        
        # Determine AI enabled status (only if eligible)
        ai_enabled = job.is_ai_enabled() if ai_eligible else False
        
        # Get recruiter name
        if job.recruiters:
            primary_recruiter = job.recruiters[0]
            recruiter_name = f"{primary_recruiter.first_name} {primary_recruiter.last_name}"
        else:
            recruiter_name = "No Recruiter Assigned"
        
        # Get location
        location = job.location.name if job.location else "Unknown"
        
        # Get level
        level = job.role.seniority.value if job.role.seniority else "Unknown"
        
        # Get department
        department = job.departments[0].name if job.departments else "Unknown"
        
        # Write row to CSV
        writer.writerow([
            job.name,
            job.id,
            ai_eligible,
            ai_enabled,
            recruiter_name,
            location,
            department,
            level
        ])

@click.command()
@click.argument('job_id', type=str)
@click.option('--cache-path', default="src/analyst/config/jobs.yaml", help='Path to the job cache file')
def report_job_pipeline(job_id, cache_path):
    """
    Generate a CSV report on all applications in a job's pipeline.
    
    Analyzes all active applications for a specific job and outputs a CSV with pipeline status.
    """
    # Load job manager and client
    job_manager = JobManager(cache_path)
    client = GreenhouseClient()
    
    # Get the job from cache
    job = job_manager.get_by_id(job_id)
    if not job:
        click.echo(f"Job {job_id} not found in cache", err=True)
        return
    
    # Get all applications for the job
    applications = client.get_applications_for_job(job)
    
    # Create CSV writer
    writer = csv.writer(sys.stdout)
    
    # Write CSV header
    writer.writerow([
        'application_id',
        'current_stage',
        'stage_type',
        'stage_status',
        'moved_to_stage_at',
        'availability_requested_at',
        'availability_received_at',
        'interview_scheduled_at',
        'interview_date',
        'take_home_submitted_at',
        'take_home_graded_at',
        'scheduled_interviews_count',
        'completed_interviews_count',
        'recruiter_name',
        'location',
        'department'
    ])
    
    # Process each application and write to CSV
    for application in applications:
        # Get stage status
        
        # Determine stage type
        if application.is_take_home_stage():
            stage_type = "take home"
            stage_status = application.get_take_home_status().value
        elif application.is_relevant_stage():
            stage_type = "interview"
            stage_status = application.get_stage_status().value
        else:
            stage_type = "other"
            stage_status = "Non-relevant"

        if stage_type == "other":
            continue
        
        # Get take home grading timestamp
        take_home_graded_at = None
        if application.take_home_grading:
            take_home_graded_at = application.take_home_grading.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
        
        # Count interviews and get interview scheduling timestamp
        scheduled_interviews_count = len(application.interviews)
        completed_interviews_count = len([i for i in application.interviews if i.status.value == "COMPLETE"])
        
        # Get interview scheduled timestamp and interview date (earliest created_at and date from interviews)
        interview_scheduled_at = None
        interview_date = None
        if application.interviews:
            earliest_interview = min(application.interviews, key=lambda x: x.created_at)
            if earliest_interview.created_at:
                interview_scheduled_at = earliest_interview.created_at.strftime('%Y-%m-%d %H:%M:%S')
            if earliest_interview.date:
                interview_date = earliest_interview.date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Get recruiter name
        recruiter_name = "Unknown"
        if job.recruiters:
            primary_recruiter = job.recruiters[0]
            recruiter_name = f"{primary_recruiter.first_name} {primary_recruiter.last_name}"
        
        # Get location and department
        location = job.location.name if job.location else "Unknown"
        department = job.departments[0].name if job.departments else "Unknown"
        
        # Format timestamps
        moved_to_stage_at = application.moved_to_stage_at.strftime('%Y-%m-%d %H:%M:%S') if application.moved_to_stage_at else None
        availability_requested_at = application.availability_requested_at.strftime('%Y-%m-%d %H:%M:%S') if application.availability_requested_at else None
        availability_received_at = application.availability_received_at.strftime('%Y-%m-%d %H:%M:%S') if application.availability_received_at else None
        take_home_submitted_at = application.take_home_submitted_at.strftime('%Y-%m-%d %H:%M:%S') if application.take_home_submitted_at else None
        
        # Write row to CSV
        writer.writerow([
            application.id,  # Use the actual application ID
            application.current_stage.name,
            stage_type,
            stage_status,
            moved_to_stage_at,
            availability_requested_at,
            availability_received_at,
            interview_scheduled_at,
            interview_date,
            take_home_submitted_at,
            take_home_graded_at,
            scheduled_interviews_count,
            completed_interviews_count,
            recruiter_name,
            location,
            department
        ])


@click.command()
@click.option('--cache-path', default="src/analyst/config/jobs.yaml", help='Path to the job cache file')
def report_takehome_snapshot(cache_path):
    """
    Generate a CSV report on all applications currently at take-home stages.
    
    Analyzes all jobs and outputs a CSV with take-home application details.
    """
    # Load job manager and client
    job_manager = JobManager(cache_path)
    client = GreenhouseClient()
    
    # Create reporter and get take-home applications
    reporter = Reporter(job_manager, client)
    take_home_applications = reporter.take_home_pipeline_snapshot()
    
    # Create CSV writer
    writer = csv.writer(sys.stdout)
    
    # Write CSV header
    writer.writerow([
        'candidate_name',
        'greenhouse_link',
        'current_take_home_stage',
        'stage_status',
        'moved_to_stage_at',
        'take_home_submitted_at',
        'take_home_graded_at',
        'hours_pending_grading',
        'recruiter_name',
        'location',
        'department'
    ])
    
    # Process each take-home application and write to CSV
    for application in take_home_applications:
        # Generate Greenhouse link
        greenhouse_link = f"https://abnormal.greenhouse.io/people/{application.candidate_id}/applications/{application.id}"
        
        # Calculate hours pending grading
        hours_pending_grading = None
        if application.take_home_submitted_at and not application.take_home_grading:
            # Calculate time elapsed since submission
            now = datetime.now(timezone.utc)
            time_elapsed = now - application.take_home_submitted_at
            hours_pending_grading = round(time_elapsed.total_seconds() / 3600, 1)
        
        # Get recruiter name
        recruiter_name = "Unknown"
        if application.job.recruiters:
            primary_recruiter = application.job.recruiters[0]
            recruiter_name = f"{primary_recruiter.first_name} {primary_recruiter.last_name}"
        
        # Get location and department
        location = application.job.location.name if application.job.location else "Unknown"
        department = application.job.departments[0].name if application.job.departments else "Unknown"
        
        # Format timestamps
        moved_to_stage_at = application.moved_to_stage_at.strftime('%Y-%m-%d %H:%M:%S') if application.moved_to_stage_at else None
        take_home_submitted_at = application.take_home_submitted_at.strftime('%Y-%m-%d %H:%M:%S') if application.take_home_submitted_at else None
        take_home_graded_at = application.take_home_grading.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if application.take_home_grading else None
        
        # Write row to CSV
        writer.writerow([
            application.candidate_name,
            greenhouse_link,
            application.current_stage.name,
            application.get_take_home_status().value,
            moved_to_stage_at,
            take_home_submitted_at,
            take_home_graded_at,
            hours_pending_grading,
            recruiter_name,
            location,
            department
        ])


@click.command()
@click.option('--cache-path', default="src/analyst/config/jobs.yaml", help='Path to the job cache file')
def report_interview_snapshot(cache_path):
    """
    Generate a CSV report on all applications currently at interview stages.
    
    Analyzes all jobs and outputs a CSV with interview application details.
    """
    # Load job manager and client
    job_manager = JobManager(cache_path)
    client = GreenhouseClient()
    
    # Create reporter and get interview applications
    reporter = Reporter(job_manager, client)
    interview_applications = reporter.interview_snapshot()
    
    # Create CSV writer
    writer = csv.writer(sys.stdout)
    
    # Write CSV header
    writer.writerow([
        'candidate_name',
        'greenhouse_link',
        'stage_status',
        'last_event_time_reference',
        'blocked_hours',
        'moved_to_stage_at',
        'availability_requested_at',
        'availability_received_at',
        'interview_scheduled_at',
        'interview_date',
        'scheduled_interviews_count',
        'completed_interviews_count',
        'recruiter_name',
        'location',
        'department'
    ])
    
    # Process each interview application and write to CSV
    for application in interview_applications:
        # Generate Greenhouse link
        greenhouse_link = f"https://abnormal.greenhouse.io/people/{application.candidate_id}/applications/{application.id}"
        
        # Get application pending time information
        application_blocker = reporter.get_application_blocker(application)
        last_event_time_reference = application_blocker.relevant_time_name if application_blocker else None
        blocked_hours = round(application_blocker.time_elapsed.total_seconds() / 3600, 1) if application_blocker else None
        
        # Get recruiter name
        recruiter_name = "Unknown"
        if application.job.recruiters:
            primary_recruiter = application.job.recruiters[0]
            recruiter_name = f"{primary_recruiter.first_name} {primary_recruiter.last_name}"
        
        # Get location and department
        location = application.job.location.name if application.job.location else "Unknown"
        department = application.job.departments[0].name if application.job.departments else "Unknown"
        
        # Count interviews and get interview scheduling timestamp
        scheduled_interviews_count = len(application.interviews)
        completed_interviews_count = len([i for i in application.interviews if i.status.value == "COMPLETE"])
        
        # Get interview scheduled timestamp and interview date
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
        
        # Format timestamps
        moved_to_stage_at = application.moved_to_stage_at.strftime('%Y-%m-%d %H:%M:%S') if application.moved_to_stage_at else None
        availability_requested_at = application.availability_requested_at.strftime('%Y-%m-%d %H:%M:%S') if application.availability_requested_at else None
        availability_received_at = application.availability_received_at.strftime('%Y-%m-%d %H:%M:%S') if application.availability_received_at else None
        
        # Write row to CSV
        writer.writerow([
            application.candidate_name,
            greenhouse_link,
            application.get_stage_status().value,
            last_event_time_reference,
            blocked_hours,
            moved_to_stage_at,
            availability_requested_at,
            availability_received_at,
            interview_scheduled_at,
            interview_date,
            scheduled_interviews_count,
            completed_interviews_count,
            recruiter_name,
            location,
            department
        ])