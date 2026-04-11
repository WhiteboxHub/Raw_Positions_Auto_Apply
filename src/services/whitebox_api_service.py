"""Service to interact with Whitebox Learning Candidate API."""

import json
import logging
import os
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class WhiteboxAPIService:
    """Service to fetch candidate profiles and credentials from Whitebox API."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize WhiteboxAPIService."""
        self.config = config
        self.web_config = config.get("web_extraction", {})
        self.api_url = self.web_config.get("api_url", "https://api.whitebox-learning.com/api/candidate/marketing")
        self.enabled_field = self.web_config.get("enabled_field", "run_smartapply")
        self.bearer_token = os.environ.get("WBL_API_TOKEN") or os.environ.get("WHITEBOX_BEARER_TOKEN")
        
        self.tmp_dir = Path("tmp/web_profiles")
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def fetch_enabled_candidates(self) -> List[Dict[str, Any]]:
        """
        Fetch all candidates and filter those who have the enabled field set to 'Yes' or True.
        """
        if not self.bearer_token:
            logger.error("No WBL_API_TOKEN or WHITEBOX_BEARER_TOKEN found in environment variables.")
            return []

        logger.info(f"Fetching candidates from {self.api_url}")
        
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Origin": "https://whitebox-learning.com",
            "Referer": "https://whitebox-learning.com/"
        }
        
        try:
            # We fetch a large limit to get all marketing candidates
            response = requests.get(self.api_url, params={"limit": 500}, headers=headers, timeout=30)
            response.raise_for_status()
            candidates = response.json()
            
            if not isinstance(candidates, list):
                # Handle cases where response might be wrapped in 'data' or 'items'
                candidates = candidates.get("data") or candidates.get("items") or []
                
            enabled_candidates = []
            for c in candidates:
                # Check the enabled field. We handle 'Yes', True, 'true' (string), or 1 (integer)
                val = c.get(self.enabled_field)
                if val in ["Yes", True, "true", "YES", 1, "1"]:
                    enabled_candidates.append(c)
            
            logger.info(f"Found {len(enabled_candidates)} enabled candidates out of {len(candidates)}")
            return enabled_candidates

        except requests.RequestException as e:
            logger.error(f"Error fetching candidates from API: {e}")
            return []

    def download_resume(self, url: str, candidate_name: str) -> Optional[Path]:
        """Download resume PDF to temporary directory."""
        if not url:
            return None
            
        try:
            sanitized_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_').lower()
            dest_path = self.tmp_dir / f"{sanitized_name}_resume.pdf"
            
            logger.info(f"Downloading resume for {candidate_name} from {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(dest_path, "wb") as f:
                f.write(response.content)
            
            return dest_path
        except Exception as e:
            logger.error(f"Failed to download resume for {candidate_name}: {e}")
            return None

    def cleanup(self):
        """Clean up temporary files."""
        try:
            if self.tmp_dir.exists():
                for f in self.tmp_dir.glob("*"):
                    f.unlink()
                logger.debug("Cleaned up temporary web profiles")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary directory: {e}")
