"""
Raw_Positions_Auto_Apply - Main Entry Point
Email automation tool for job applications using local LLM and Gmail.

Usage:
    python run.py              # Send emails configured in config.yaml
    python run.py --dry-run    # Preview emails without sending
"""

import argparse
import sys
import uuid
from pathlib import Path

# Force UTF-8 encoding for standard output across all platforms to avoid emoji crashes
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator import RawPositionsAutoApplyOrchestrator
from src.services import DataFetcherService
from src.config_loader import load_config
from src.core.reporter import RawPositionsAutoApplyReporter
from src.utils.sorting_utils import sort_candidates


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Raw_Positions_Auto_Apply - Automated email generation and sending for job applications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage:
  python run.py              # Send emails configured in config.yaml
  python run.py --dry-run    # Preview emails without sending
        """
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config file (default: config.yaml)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without sending emails"
    )

    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch daily user data before running the pipeline"
    )

    parser.add_argument(
        "--user",
        help="Run for a specific user (looks in resume/<USER>/ for credentials and resume files)"
    )

    parser.add_argument(
        "--web",
        action="store_true",
        help="Run for profiles enabled on the Whitebox marketing page"
    )

    parser.add_argument(
        "--users",
        help="Comma-separated list of users to run in a distributed load (e.g. Bavish,Ravi,John)"
    )

    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Automatically detect all users in the resume/ directory and run distributed load across them"
    )

    parser.add_argument(
        "--workflow-key",
        default="raw_positions_auto_apply",
        help="Workflow key for reporting API (default: 'raw_positions_auto_apply')"
    )

    parser.add_argument(
        "--web-field",
        help="Specific database field to check for enabled status (e.g. run_raw_positions_workflow)"
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()

    # Check for .env file
    env_path = Path(".env")
    if not env_path.exists():
        print("Warning: .env file not found. Using environment variables or prompting at runtime.")
    else:
        from dotenv import load_dotenv
        load_dotenv()
        
    run_id = str(uuid.uuid4())

    try:
        config_dict = None
        if args.fetch:
            print("Running initial fetch based on config/env...")
            config_dict = load_config(args.config).to_dict()
            fetcher = DataFetcherService(config_dict)
            if not fetcher.fetch_daily_data():
                print("Data fetch failed. Proceeding with existing input file if present.")
        
        # Determine users to run
        users = []
        if args.run_all:
            resume_dir = Path("resume")
            if resume_dir.exists():
                users = [d.name for d in resume_dir.iterdir() if d.is_dir() and d.name.strip()]
        elif args.users:
            users = [u.strip() for u in args.users.split(",") if u.strip()]
        elif args.user:
            users = [args.user]
        elif args.web:
            users = [None] # We run once in web mode which handles its own candidate fetching
        else:
            users = [None] # global config run
            
        # Apply sorting to users if many are detected
        if len(users) > 1 and all(isinstance(u, str) for u in users):
            config_dict = config_dict or load_config(args.config).to_dict()
            priority_order = config_dict.get("resume", {}).get("candidate_order", [])
            if priority_order:
                users = sort_candidates(users, priority_order)
                print(f"Sorted users based on priority: {users}")

        total_users = len(users)
        consolidated_data = []
        
        for idx, user in enumerate(users):
            if total_users > 1:
                print(f"\n========================================================")
                print(f"Starting distributed run for user: {user} ({idx + 1}/{total_users})")
                print(f"========================================================")
                
            # Override args.user for this specific iteration
            args.user = user
                
            orchestrator = RawPositionsAutoApplyOrchestrator(config_file=args.config)
            
            # Carry over the updated csv_filename from the fetcher
            if args.fetch and config_dict:
                 fetched_csv = config_dict.get("input", {}).get("csv_filename")
                 if fetched_csv:
                     orchestrator.config.setdefault("input", {})["csv_filename"] = fetched_csv

            orchestrator.config["workflow_key"] = args.workflow_key

            # Pass the partition state down
            orchestrator.config["partition"] = {
                "index": idx,
                "total": total_users
            }

            exit_code = orchestrator.run(args)
            
            # Store data for consolidated report
            consolidated_data.append({
                "user_name": orchestrator._user_name,
                "user_email": orchestrator.config.get("gmail", {}).get("user_email", "Unknown"),
                "stats": orchestrator._stats,
                "results": orchestrator._csv_results
            })
            
            if exit_code != 0 and total_users == 1:
                # If it's a single run and it errored, send report now
                reporter = RawPositionsAutoApplyReporter(consolidated_data)
                reporter.send_report()
                sys.exit(exit_code)
                
        # Dispatch consolidated report
        if consolidated_data:
            reporter = RawPositionsAutoApplyReporter(consolidated_data, run_id=run_id)
            reporter.send_report()
            
        if total_users > 1:
            print("\nAll distributed runs completed successfully.")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
