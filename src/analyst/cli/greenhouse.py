"""
Greenhouse CLI commands for Recruiting Analyst.
"""

import click
from ..client.greenhouse import GreenhouseClient


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

if __name__ == '__main__':
    check_greenhouse_integration()
