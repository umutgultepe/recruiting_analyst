"""
Greenhouse CLI commands for Recruiting Analyst.
"""

import click
from ..client.greenhouse import GreenhouseClient
from ..job_manager import JobManager


@click.command()
def check_greenhouse_integration():
    client = GreenhouseClient()
    response = client.session.get(f"{client.base_url}/users/me")
    print(response.json())


@click.command()
@click.option('--department', '-d', help='Department name to filter by')
@click.option('--include-closed', is_flag=True, help='Include closed jobs')
@click.option('--limit', '-l', default=5, help='Number of jobs to display (default: 5)')
def get_jobs(department, include_closed, limit):
    """
    Fetch and display jobs from Greenhouse.
    
    This command fetches jobs from the Greenhouse API and displays the first few results.
    """
    try:
        client = GreenhouseClient()
        jobs = client.get_jobs(department_name=department, include_closed=include_closed)
        
        if not jobs:
            click.echo("No jobs found matching the criteria.")
            return
        
        click.echo(f"Found {len(jobs)} job(s):")
        click.echo("=" * 80)
        
        # Display the first 'limit' jobs
        for i, job in enumerate(jobs[:limit], 1):
            click.echo(f"{i}. {job.name}")
            click.echo(f"   ID: {job.id}")
            click.echo(f"   Location: {job.location.name}")
            click.echo(f"   Created: {job.created_at.strftime('%Y-%m-%d')}")
            if job.opened_at:
                click.echo(f"   Opened: {job.opened_at.strftime('%Y-%m-%d')}")
            
            # Display role information
            click.echo(f"   Role: {job.role.function.value} - {job.role.seniority.value}")
            
            # Display departments
            if job.departments:
                dept_names = [dept.name for dept in job.departments]
                click.echo(f"   Departments: {', '.join(dept_names)}")
            
            # Display hiring managers
            if job.hiring_managers:
                manager_names = [f"{user.first_name} {user.last_name}" for user in job.hiring_managers]
                click.echo(f"   Hiring Managers: {', '.join(manager_names)}")
            
            click.echo()
        
        if len(jobs) > limit:
            click.echo(f"... and {len(jobs) - limit} more job(s)")
            
    except ValueError as e:
        click.echo(f"❌ Error: {e}")
    except Exception as e:
        click.echo(f"❌ Failed to fetch jobs: {e}")

@click.command()
@click.option('--cache-path', default="src/analyst/config/jobs.yaml", help='Path to save the job cache')
def refresh_job_cache(cache_path):
    """
    Refresh the job cache by fetching jobs from all relevant departments.
    
    This command fetches jobs from Greenhouse API, fills their stages and interviews,
    and saves the complete data to a YAML cache file.
    """
    click.echo("🔄 Refreshing job cache...")
    
    # Initialize client and job manager
    client = GreenhouseClient()
    job_manager = JobManager(cache_path)
    
    # Refresh the cache
    job_manager.refresh_cache(client)
    
    click.echo("✅ Job cache refreshed successfully!")
    click.echo(f"📁 Cache saved to: {cache_path}")


@click.command()
@click.argument('job_id', type=str)
@click.option('--cache-path', default="src/analyst/config/jobs.yaml", help='Path to the job cache file')
def print_job_from_cache(job_id, cache_path):
    """
    Print details of a job from the cache by its ID.
    
    JOB_ID: The ID of the job to display
    """
    # Initialize client and job manager
    client = GreenhouseClient()
    job_manager = JobManager(cache_path)
    
    # Get the job from cache
    job = job_manager.get_by_id(job_id)
    
    if not job:
        click.echo(f"❌ Job with ID '{job_id}' not found in cache")
        click.echo("💡 Try running 'analyst refresh-job-cache' to update the cache")
        return
    
    # Print job details
    click.echo(f"📋 Job Details for ID: {job.id}")
    click.echo("=" * 60)
    click.echo(f"Name: {job.name}")
    click.echo(f"Location: {job.location.name} (ID: {job.location.id})")
    click.echo(f"Created: {job.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if job.opened_at:
        click.echo(f"Opened: {job.opened_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    click.echo(f"Role: {job.role.function.value} - {job.role.seniority.value}")
    
    # Print departments
    if job.departments:
        dept_names = [dept.name for dept in job.departments]
        click.echo(f"Departments: {', '.join(dept_names)}")
    
    # Print team members
    if job.hiring_managers:
        manager_names = [f"{user.first_name} {user.last_name}" for user in job.hiring_managers]
        click.echo(f"Hiring Managers: {', '.join(manager_names)}")
    
    if job.recruiters:
        recruiter_names = [f"{user.first_name} {user.last_name}" for user in job.recruiters]
        click.echo(f"Recruiters: {', '.join(recruiter_names)}")
    
    if job.coordinators:
        coordinator_names = [f"{user.first_name} {user.last_name}" for user in job.coordinators]
        click.echo(f"Coordinators: {', '.join(coordinator_names)}")
    
    if job.sourcers:
        sourcer_names = [f"{user.first_name} {user.last_name}" for user in job.sourcers]
        click.echo(f"Sourcers: {', '.join(sourcer_names)}")
    
    # Print stages and interviews
    if job.stages:
        click.echo("\n📊 Hiring Stages:")
        for i, stage in enumerate(job.stages, 1):
            click.echo(f"  {i}. {stage.name}")
            if stage.interviews:
                for j, interview in enumerate(stage.interviews, 1):
                    schedulable = "✅" if interview.schedulable else "❌"
                    click.echo(f"     {j}. {interview.name} {schedulable}")
            else:
                click.echo("     (No interviews)")
    else:
        click.echo("\n📊 No stages found for this job")


@click.command()
@click.argument('application_id', type=str)
@click.option('--cache-path', default="src/analyst/config/jobs.yaml", help='Path to the job cache file')
def get_application(application_id, cache_path):
    """
    Fetch and display application details from Greenhouse by ID.
    
    APPLICATION_ID: The ID of the application to fetch
    """
    # Initialize client and job manager
    client = GreenhouseClient()
    job_manager = JobManager(cache_path)
    
    # Get the application
    application = client.get_application(application_id, job_manager)
    
    # Print application details
    click.echo(f"📋 Application Details for ID: {application_id}")
    click.echo("=" * 80)
    
    # Basic application info
    click.echo(f"Job: {application.job.name} (ID: {application.job.id})")
    click.echo(f"Current Stage: {application.current_stage.name} (ID: {application.current_stage.id})")

    if not application.is_relevant_stage():
        click.echo("Application Status: Non-relevant stage for this program")
        return

    if application.moved_to_stage_at:
        click.echo(f"Moved to Stage: {application.moved_to_stage_at.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        click.echo("Moved to Stage information not available")
    
    # Stage type and status
    if application.current_stage.is_schedulable:
        click.echo("Stage Type: Schedulable Interview")
    elif application.current_stage.is_take_home:
        click.echo("Stage Type: Take Home")
    else:
        click.echo("Stage Type: Other")
    
    # Take-home specific information
    if application.current_stage.is_take_home:
        if application.take_home_submitted_at:
            click.echo(f"Take Home Submitted: {application.take_home_submitted_at.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            click.echo("Take Home Status: Not submitted")
        
        if application.take_home_grading:
            click.echo(f"Take Home Graded: {application.take_home_grading.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"Graded By: {application.take_home_grading.by.first_name} {application.take_home_grading.by.last_name}")
            click.echo(f"Take Home Status: {application.get_take_home_status().value}")
        else:
            click.echo("Take Home Status: Not graded")
    else:
        status = application.get_stage_status()
        click.echo(f"Application Status: {status.value}")
        
        # Print availability information
        if application.availability_requested_at:
            click.echo(f"Availability Requested: {application.availability_requested_at.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            click.echo("Availability Requested: Not requested")
        
        if application.availability_received_at:
            click.echo(f"Availability Received: {application.availability_received_at.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            click.echo("Availability Received: Not received")
        
        # Print scheduled interviews
        if application.interviews:
            click.echo(f"Scheduled Interviews: {len(application.interviews)}")
            for i, interview in enumerate(application.interviews, 1):
                click.echo(f"  {i}. {interview.interview.name}")
                click.echo(f"     Date: {interview.date.strftime('%Y-%m-%d %H:%M:%S')}")
                click.echo(f"     Status: {interview.status.value}")
                if interview.interviewers:
                    interviewer_names = [f"{user.first_name} {user.last_name}" for user in interview.interviewers]
                    click.echo(f"     Interviewers: {', '.join(interviewer_names)}")
                
                # Print scorecards if they exist
                if interview.scorecards:
                    click.echo(f"     Scorecards: {len(interview.scorecards)}")
                    for j, scorecard in enumerate(interview.scorecards, 1):
                        click.echo(f"       {j}. By: {scorecard.by.first_name} {scorecard.by.last_name}")
                        click.echo(f"          Submitted: {scorecard.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}")
                        click.echo(f"          Decision: {scorecard.decision.value}")
                else:
                    click.echo("     Scorecards: None")
        else:
            click.echo("Scheduled Interviews: None")


if __name__ == '__main__':
    check_greenhouse_integration()
