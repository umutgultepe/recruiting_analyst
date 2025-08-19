"""
Greenhouse API client for fetching recruiting data.
"""

import requests
from typing import Dict, List, Optional

from ..config.greenhouse import API_KEY


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
        self.session.headers.update({
            'Authorization': f'Basic {self.api_key}',
            'Content-Type': 'application/json'
        })