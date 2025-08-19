"""
Greenhouse API client for fetching recruiting data.
"""

import requests
import base64
from datetime import datetime
from typing import Dict, List, Optional

from ..config.greenhouse import API_KEY, DEPARTMENT_MAP
from ..dataclasses import Job, Department, Location, User


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
        
        response = self.session.get(f"{self.base_url}/jobs", params=params)
        
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
                departments=departments
            )
            jobs.append(job)
        
        return jobs