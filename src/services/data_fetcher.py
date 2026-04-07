import csv
import json
import logging
import os
import requests
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class DataFetcherService:
    """Service to fetch daily job data from Whitebox Learning API."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize DataFetcherService."""
        self.config = config
        self.fetcher_config = config.get("data_fetcher", {})
        self.api_url = self.fetcher_config.get("api_url", "https://whitebox-learning.com/api/email-positions/paginated")
        self.page_size = self.fetcher_config.get("page_size", 5000)
        self.output_filename = self.fetcher_config.get("output_filename", "daily_jobs.csv")
        
        self.input_dir = Path(config.get("file_paths", {}).get("input_dir", "input"))
        self.bearer_token = os.environ.get("WHITEBOX_BEARER_TOKEN")

    def fetch_daily_data(self) -> bool:
        """Fetch today's job data and save it to the daily CSV."""
        if not self.bearer_token:
            logger.error(
                "No WHITEBOX_BEARER_TOKEN found in environment variables. "
                "Please add it to your .env file. See instructions in the terminal to find it."
            )
            return False

        logger.info(f"Fetching daily data from {self.api_url}")
        
        # Prepare output path
        self.input_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.input_dir / self.output_filename
        
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Origin": "https://whitebox-learning.com",
            "Referer": "https://whitebox-learning.com/"
        }
        
        # Request parameters
        params = {
            "page": 1,
            "page_size": self.page_size
        }
        
        all_jobs = []
        today_date = date.today().isoformat() # E.g., '2026-04-06'
        
        try:
            while True:
                response = requests.get(self.api_url, params=params, headers=headers, timeout=30)
                
                if response.status_code == 401:
                    logger.error("Authentication failed. Your session token might be expired.")
                    return False
                
                response.raise_for_status()
                data = response.json()
                
                items = data.get("items") or data.get("data") or []
                if not isinstance(items, list):
                    items = data if isinstance(data, list) else []
                
                if not items:
                    break
                    
                for item in items:
                    # Check extraction date (fields vary, so we check multiple common ones)
                    extracted_at = item.get("extracted_at") or item.get("extraction_date") or item.get("processed_at") or ""
                    
                    # If it starts with today's date, we keep it
                    if extracted_at.startswith(today_date):
                        all_jobs.append(item)
                
                # Pagination
                # Normally there is a "has_next" or we just check if we got full page
                if isinstance(data, dict) and not data.get("has_next", False):
                    break
                elif len(items) < self.page_size:
                    break
                    
                params["page"] += 1

            if not all_jobs:
                logger.warning(f"No new jobs found for today ({today_date}).")
                return False

            self._save_to_csv(all_jobs, output_path)
            logger.info(f"Successfully saved {len(all_jobs)} daily jobs to {output_path}")
            
            # Automatically update the config to point to this new file
            self.config.setdefault("input", {})["csv_filename"] = self.output_filename
            return True

        except requests.RequestException as e:
            logger.error(f"Error fetching data from API: {e}")
            return False
            
    def _save_to_csv(self, jobs: List[Dict[str, Any]], output_path: Path):
        """Save job items to CSV with the format expected by CSVService."""
        # Define expected headers from sample_jobs.csv
        headers = [
            "ID", "Title", "Company", "Location", "Source", "Source UID", 
            "Candidate ID", "Zip", "Contact Info", "Payload", "Extractor Version", 
            "Error Message", "Extracted At", "Processed At", "Description", "Notes"
        ]
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for job in jobs:
                # The API returns lowercase items, we need to map them back to the headers SmartApply expects.
                mapped_job = {
                    "ID": job.get("id", ""),
                    "Title": job.get("job_title") or job.get("title") or "",
                    "Company": job.get("company", ""),
                    "Location": job.get("location", ""),
                    "Source": job.get("source", ""),
                    "Source UID": job.get("source_uid", ""),
                    "Candidate ID": job.get("candidate_id", ""),
                    "Zip": job.get("zip") or job.get("raw_zip") or "",
                    # The API might separate contact email/phone or provide it in a string
                    "Contact Info": job.get("contact_info") or f"Email: {job.get('contact_email', '')}, Phone: {job.get('contact_phone', '')}".strip(" ,:"),
                    "Extractor Version": job.get("extractor_version", ""),
                    "Error Message": job.get("error_message", ""),
                    "Extracted At": job.get("extracted_at") or job.get("extraction_date") or "",
                    "Processed At": job.get("processed_at", ""),
                    "Description": job.get("description") or job.get("post_text_preview") or "",
                    "Notes": job.get("notes", "")
                }
                
                # Payload requires special handling since it's JSON in the original CSV
                # And since we construct the dictionary here, Python's csv.DictWriter will correctly quote it
                payload_data = job.get("payload")
                if payload_data:
                    if isinstance(payload_data, dict):
                        mapped_job["Payload"] = json.dumps(payload_data)
                    else:
                        mapped_job["Payload"] = str(payload_data)
                else:
                    mapped_job["Payload"] = ""
                    
                writer.writerow(mapped_job)
