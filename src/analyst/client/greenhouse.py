"""
Greenhouse API client for fetching recruiting data.
"""

import requests
import base64
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
        
        # Encode API key for Basic authentication
        encoded_key = base64.b64encode(f"{self.api_key}:".encode()).decode()
        self.session.headers.update({
            'Authorization': f'Basic {encoded_key}',
            'Content-Type': 'application/json'
        })