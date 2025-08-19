import os
import yaml
from datetime import datetime
from typing import Dict, List

from .client.greenhouse import GreenhouseClient
from .config.greenhouse import RELEVANT_DEPARTMENTS
from .dataclasses import Job, Location, Department, User, Role, RoleFunction, Seniority, JobStage, Interview


class JobManager:
    def __init__(self, client: GreenhouseClient, cache_path: str = "src/analyst/config/jobs.yaml"):
        self.client = client
        self.cache_path = cache_path
        self.by_id = {}
        if os.path.exists(cache_path):
            self._load_cache()

    def refresh_cache(self):
        """
        Refresh the job cache by fetching jobs from all relevant departments
        and filling their stages. Saves the results to YAML and updates internal containers.
        """
        all_jobs = []
        
        # Fetch jobs from each relevant department
        for department in RELEVANT_DEPARTMENTS:
            jobs = self.client.get_jobs(department_name=department, include_closed=False)
            
            # Fill stages for each job
            for job in jobs:
                job_with_stages = self.client.fill_stages(job)
                all_jobs.append(job_with_stages)
        
        # Convert jobs to YAML-serializable format
        jobs_data = []
        for job in all_jobs:
            job_dict = {
                'id': job.id,
                'name': job.name,
                'location': {
                    'id': job.location.id,
                    'name': job.location.name
                },
                'created_at': job.created_at.isoformat(),
                'opened_at': job.opened_at.isoformat() if job.opened_at else None,
                'hiring_managers': [
                    {'id': user.id, 'first_name': user.first_name, 'last_name': user.last_name}
                    for user in job.hiring_managers
                ],
                'recruiters': [
                    {'id': user.id, 'first_name': user.first_name, 'last_name': user.last_name}
                    for user in job.recruiters
                ],
                'coordinators': [
                    {'id': user.id, 'first_name': user.first_name, 'last_name': user.last_name}
                    for user in job.coordinators
                ],
                'sourcers': [
                    {'id': user.id, 'first_name': user.first_name, 'last_name': user.last_name}
                    for user in job.sourcers
                ],
                'departments': [
                    {'id': dept.id, 'name': dept.name}
                    for dept in job.departments
                ],
                'role': {
                    'function': job.role.function.value,
                    'seniority': job.role.seniority.value
                },
                'stages': [
                    {
                        'name': stage.name,
                        'interviews': [
                            {'name': interview.name, 'schedulable': interview.schedulable}
                            for interview in stage.interviews
                        ]
                    }
                    for stage in job.stages
                ] if job.stages else []
            }
            jobs_data.append(job_dict)
        
        # Save to YAML file
        with open(self.cache_path, 'w') as f:
            yaml.dump(jobs_data, f, default_flow_style=False, sort_keys=False)
        
        # Update internal containers
        self.by_id = {job.id: job for job in all_jobs}
        
        print(f"Cache refreshed: {len(all_jobs)} jobs saved to {self.cache_path}")

    def get_by_id(self, id: str):
        """Get a job by its ID."""
        return self.by_id.get(id)

    def _load_cache(self):
        """
        Load jobs from the YAML cache file and populate the by_id maps.
        """
        with open(self.cache_path, "r") as f:
            jobs_data = yaml.safe_load(f)
        
        if not jobs_data:
            print(f"Warning: No jobs found in cache file {self.cache_path}")
            return
        
        # Reconstruct Job objects from YAML data
        for job_data in jobs_data:
            try:
                # Reconstruct Location
                location_data = job_data.get('location', {})
                location = Location(
                    id=location_data.get('id', ''),
                    name=location_data.get('name', '')
                )
                
                # Reconstruct Users
                def reconstruct_users(users_data):
                    users = []
                    for user_data in users_data:
                        user = User(
                            id=user_data.get('id', ''),
                            first_name=user_data.get('first_name', ''),
                            last_name=user_data.get('last_name', '')
                        )
                        users.append(user)
                    return users
                
                # Reconstruct Departments
                departments = []
                for dept_data in job_data.get('departments', []):
                    department = Department(
                        id=dept_data.get('id', ''),
                        name=dept_data.get('name', '')
                    )
                    departments.append(department)
                
                # Reconstruct Role
                role_data = job_data.get('role', {})
                role = Role(
                    function=RoleFunction(role_data.get('function', 'Other')),
                    seniority=Seniority(role_data.get('seniority', 'Unknown'))
                )
                
                # Reconstruct Stages and Interviews
                stages = []
                for stage_data in job_data.get('stages', []):
                    interviews = []
                    for interview_data in stage_data.get('interviews', []):
                        interview = Interview(
                            name=interview_data.get('name', ''),
                            schedulable=interview_data.get('schedulable', False)
                        )
                        interviews.append(interview)
                    
                    stage = JobStage(
                        name=stage_data.get('name', ''),
                        interviews=interviews
                    )
                    stages.append(stage)
                
                # Reconstruct Job object
                job = Job(
                    id=job_data.get('id', ''),
                    name=job_data.get('name', ''),
                    location=location,
                    created_at=datetime.fromisoformat(job_data.get('created_at', '')),
                    opened_at=datetime.fromisoformat(job_data.get('opened_at', '')) if job_data.get('opened_at') else None,
                    hiring_managers=reconstruct_users(job_data.get('hiring_managers', [])),
                    recruiters=reconstruct_users(job_data.get('recruiters', [])),
                    coordinators=reconstruct_users(job_data.get('coordinators', [])),
                    sourcers=reconstruct_users(job_data.get('sourcers', [])),
                    departments=departments,
                    role=role,
                    stages=stages
                )
                
                # Add to maps
                self.by_id[job.id] = job
                
            except Exception as e:
                print(f"Warning: Could not load job {job_data.get('id', 'unknown')}: {e}")
                continue
        
        print(f"Loaded {len(self.by_id)} jobs from cache file {self.cache_path}")
