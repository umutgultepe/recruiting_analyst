"""
Main CLI entry point for Recruiting Analyst.
"""

import click
from .greenhouse import check_greenhouse_integration, get_jobs, refresh_job_cache, print_job_from_cache, get_application
from .reports import report_ai_rollout, report_job_pipeline, report_takehome_snapshot, report_interview_snapshot


@click.group()
@click.version_option(version="0.1.0", prog_name="Recruiting Analyst")
def analyst():
    """
    Recruiting Analyst - A tool for pulling data from Greenhouse API to calculate metrics & generate datasets.
    """
    pass


# Add subcommands
analyst.add_command(check_greenhouse_integration, name="check-greenhouse-integration")
analyst.add_command(get_jobs, name="get-jobs")
analyst.add_command(refresh_job_cache, name="refresh-job-cache")
analyst.add_command(print_job_from_cache, name="print-job-from-cache")
analyst.add_command(get_application, name="get-application")
analyst.add_command(report_ai_rollout, name="report-ai-rollout")
analyst.add_command(report_job_pipeline, name="report-job-pipeline")
analyst.add_command(report_takehome_snapshot, name="report-takehome-snapshot")
analyst.add_command(report_interview_snapshot, name="report-interview-snapshot")


if __name__ == '__main__':
    analyst()
