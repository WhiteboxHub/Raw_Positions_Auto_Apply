import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator import SmartApplyOrchestrator
from src.core.reporter import SmartApplyReporter
from src.main import parse_arguments

def test_user_names():
    args = parse_arguments()
    args.fetch = False
    args.run_all = True
    args.dry_run = True
    
    users = ["Bavish", "Ramana", "Ravi"]
    
    # We will mock SmartApplyReporter to capture what it receives
    captured_names = []
    
    original_init = SmartApplyReporter.__init__
    
    def mock_init(self, stats, results_list, user_name="Unknown User"):
        captured_names.append(user_name)
        original_init(self, stats, results_list, user_name)
        
    def mock_send_email(self, subject, html_body):
        print(f"Would send email with Subject: {subject}")
        return True

    with patch.object(SmartApplyReporter, '__init__', new=mock_init):
        with patch.object(SmartApplyReporter, '_send_email', new=mock_send_email):
            # Also mock the _execute_pipeline to finish immediately and return 0
            with patch.object(SmartApplyOrchestrator, '_execute_pipeline', return_value=0):
                # But wait, if we mock _execute_pipeline, self._user_name won't be set!
                # We need to let it run but mock the LLM and CSV to just return instantly.
                pass
            
            # Let's override actual method instead of mock, so we can see real flow
            original_exec = SmartApplyOrchestrator._execute_pipeline
            def mock_exec(self, args):
                # Just do the resume loading part
                resume_json_path = self.config.get("resume", {}).get("json_path")
                if not resume_json_path:
                    # Do the fallback logic
                    pass
                from src.core.resume_handler import ResumeHandler
                try:
                    resume = ResumeHandler.load_resume(resume_json_path)
                    self._user_name = resume.data.name
                except:
                    pass
                return 0
                
            with patch.object(SmartApplyOrchestrator, '_execute_pipeline', new=mock_exec):
                for user in users:
                    args.user = user
                    orchestrator = SmartApplyOrchestrator(config_file="config.yaml")
                    orchestrator.run(args)
                    
    print(f"Captured names passed to Reporter: {captured_names}")

if __name__ == "__main__":
    test_user_names()
