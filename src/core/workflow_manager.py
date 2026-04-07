import logging
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from src.core.api_client import get_api_client

logger = logging.getLogger(__name__)

class WorkflowManager:
    
    def __init__(self):
        self.api_client = get_api_client()
        # To map run_id (UUID) to log_id (primary key) for updates
        self._log_mapping = {}

    def get_workflow_config(self, workflow_key: str) -> Optional[dict[str, Any]]:
        if not self.api_client.token:
            return None

        # API endpoint: GET /orchestrator/workflows/key/{key}
        endpoint = f"/orchestrator/workflows/key/{workflow_key}"
        config = self.api_client.get(endpoint)
        
        if not config:
            logger.warning(f"Workflow '{workflow_key}' not found or not active via API.")
            return None
            
        return config

    def start_run(self, workflow_id: int, schedule_id: Optional[int] = None, parameters: Optional[dict] = None) -> str:
        run_id = str(uuid.uuid4())
        started_at = datetime.now().isoformat()
        
        if not self.api_client.token:
            logger.info(f"API Token missing. Skipping run logging. Simulation run_id={run_id}")
            return run_id

        payload = {
            "workflow_id": workflow_id,
            "schedule_id": schedule_id,
            "run_id": run_id,
            "status": "running",
            "started_at": started_at,
            "parameters_used": parameters
        }
        
        try:
            result = self.api_client.post("/orchestrator/logs", payload)
            if result and "id" in result:
                self._log_mapping[run_id] = result["id"]
                logger.info(f"Started workflow run {run_id} (log_id: {result['id']}) via API.")
                return run_id
            else:
                logger.warning("API did not return a valid log ID.")
                return run_id
        except Exception as e:
            logger.error(f"Failed to start workflow run via API: {e}")
            return run_id

    def update_run_status(self, run_id: str, status: str, 
                          records_processed: int = 0, 
                          records_failed: int = 0,
                          error_summary: Optional[str] = None,
                          error_details: Optional[str] = None,
                          execution_metadata: Optional[dict] = None):
        if not self.api_client.token:
            return

        log_id = self._log_mapping.get(run_id)
        if not log_id:
            logger.warning(f"No log_id found mapped to run_id {run_id}.")
            return

        payload = {
            "status": status,
            "records_processed": records_processed,
            "records_failed": records_failed,
            "error_summary": error_summary,
            "execution_metadata": execution_metadata or {}
        }
        
        if status in ['success', 'failed', 'partial_success', 'timed_out']:
            payload["finished_at"] = datetime.now().isoformat()
            
        try:
            self.api_client.put(f"/orchestrator/logs/{log_id}", payload)
            logger.info(f"Updated run {run_id} status to {status} via API.")
        except Exception as e:
            logger.error(f"Failed to update run status via API for {run_id}: {e}")

    def update_schedule_status(self, schedule_id: int):
        if not self.api_client.token or not schedule_id:
            return
            
        payload = {
            "last_run_at": datetime.now().isoformat(),
            "is_running": 0
        }
        
        try:
            self.api_client.put(f"/orchestrator/schedules/{schedule_id}", payload)
            logger.info(f"Updated schedule {schedule_id} status via API.")
        except Exception as e:
            logger.error(f"Failed to update schedule {schedule_id} via API: {e}")
