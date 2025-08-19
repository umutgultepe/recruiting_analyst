"""
Greenhouse API client for fetching recruiting data.
"""

import requests
import base64
from datetime import datetime
from typing import Dict, List, Optional

from ..config.greenhouse import API_KEY, DEPARTMENT_MAP
from ..dataclasses import Job, Department, Location, User, Role, RoleFunction, Seniority


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
                role=role
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