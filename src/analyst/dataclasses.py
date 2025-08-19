from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Department:
    id: str
    name: str


@dataclass
class Location:
    """Represented as Office in Greenhouse"""
    id: str
    name: str


@dataclass
class User:
    id: str
    first_name: str
    last_name: str

@dataclass
class Job:
    id: str
    name: str
    location: Location
    created_at: datetime
    opened_at: Optional[datetime]
    hiring_managers: List[User]
    recruiters: List[User]
    coordinators: List[User]
    sourcers: List[User]
    departments: List[Department]