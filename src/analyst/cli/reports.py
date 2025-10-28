"""
Reports module for generating recruiting analytics reports.
"""

import csv
import sys
import click
from typing import List

from ..dataclasses import Application
from ..client.greenhouse import GreenhouseClient
from ..job_manager import JobManager
from ..reporter import Reporter
from ..application_csv_writer import ApplicationCSVWriter, FieldSpec

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
    relevant_applications = [application for application in applications if application.is_relevant_stage()]

    application_writer = ApplicationCSVWriter([
        FieldSpec.Identifier,
        FieldSpec.CurrentStage,
        FieldSpec.StageType,
        FieldSpec.StageTime,
        FieldSpec.InterviewTimes,
        FieldSpec.TakeHomeTimes,
        FieldSpec.InterviewCounts,
        FieldSpec.Dimensions
    ])

    _write_applications_to_stdout(relevant_applications, application_writer)
    

def get_reporter(cache_path: str) -> Reporter:
    job_manager = JobManager(cache_path)
    client = GreenhouseClient()
    return Reporter(job_manager, client)

def _write_applications_to_stdout(applications: List[Application], application_writer: ApplicationCSVWriter):
    # Create CSV writer
    writer = csv.writer(sys.stdout)
    
    # Write CSV header
    headers = application_writer.get_headers()
    writer.writerow(headers)

    # Process each application and write to CSV
    for application in applications:
        row = application_writer.generate_row(application)
        writer.writerow(row)


@click.command()
@click.option('--cache-path', default="src/analyst/config/jobs.yaml", help='Path to the job cache file')
def report_takehome_snapshot(cache_path):
    """
    Generate a CSV report on all applications currently at take-home stages.
    
    Analyzes all jobs and outputs a CSV with take-home application details.
    """
    reporter = get_reporter(cache_path)
    take_home_applications = reporter.take_home_pipeline_snapshot()
    application_writer = ApplicationCSVWriter([
        FieldSpec.Identifier,
        FieldSpec.CurrentStage,
        FieldSpec.StageType,
        FieldSpec.StageTime,
        FieldSpec.TakeHomeTimes,
        FieldSpec.TakeHomePendingGrading,
        FieldSpec.Dimensions
    ])
    _write_applications_to_stdout(take_home_applications, application_writer)

@click.command()
@click.option('--cache-path', default="src/analyst/config/jobs.yaml", help='Path to the job cache file')
def report_takehome_statistics(cache_path):
    """
    Generate a CSV report on all applications currently at take-home stages.
    
    Analyzes all jobs and outputs a CSV with take-home application details.
    """
    reporter = get_reporter(cache_path)
    applications = reporter.take_home_statistics()
    application_writer = ApplicationCSVWriter([
        FieldSpec.Identifier,
        FieldSpec.Status,
        FieldSpec.CurrentStage,
        FieldSpec.StageType,
        FieldSpec.StageTime,
        FieldSpec.TakeHomeTimes,
        FieldSpec.TakeHomePendingGrading,
        FieldSpec.Dimensions
    ])
    _write_applications_to_stdout(applications, application_writer)

@click.command()
@click.option('--cache-path', default="src/analyst/config/jobs.yaml", help='Path to the job cache file')
def blocked_interview_snapshot(cache_path):
    """
    Generate a CSV report on all applications currently at interview stages.
    
    Analyzes all jobs and outputs a CSV with interview application details.
    """
    reporter = get_reporter(cache_path)
    interview_applications = reporter.blocked_interview_snapshot()
    application_writer = ApplicationCSVWriter([
        FieldSpec.Identifier,
        FieldSpec.CurrentStage,
        FieldSpec.StageType,
        FieldSpec.BlockContext,
        FieldSpec.StageTime,
        FieldSpec.InterviewTimes,
        FieldSpec.InterviewCounts,
        FieldSpec.Dimensions
    ])
    _write_applications_to_stdout(interview_applications, application_writer)