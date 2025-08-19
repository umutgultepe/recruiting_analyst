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

if __name__ == '__main__':
    check_greenhouse_integration()
