"""
Main CLI entry point for Recruiting Analyst.
"""

import click
from .greenhouse import check_greenhouse_integration, get_jobs


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


if __name__ == '__main__':
    analyst()
