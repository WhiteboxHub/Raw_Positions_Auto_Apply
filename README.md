# Raw_Positions_Auto_Apply - AI-Powered Job Application Email Generator

Automated email generation and sending for job applications using local Ollama LLM and Gmail API.

## Features

- 📧 **Automated Email Generation** — Uses local Ollama LLM to generate personalized application emails.
- 🤖 **LLM-Powered Personalization** — Matches your skills and experience to job requirements automatically. Features robust multi-attempt fallbacks.
- 📨 **Gmail API Integration** — Sends emails via Google OAuth2 (HTML formatted) with anti-spam jitter and daily limits.
- 📎 **Resume Attachment** — Automatically attaches your PDF resume.
- 🔗 **Social Links & Metadata** — Appends LinkedIn & GitHub from your resume JSON, injects experience automatically.
- 🎯 **Batch & API Processing** — Process multiple job postings from CSV or dynamically fetch them each day via the Whitebox Learning API.
- 👥 **Multi-Profile Support** — Run the system seamlessly for multiple users (e.g., `python run.py --user John`).
- ⏱️ **Real-time Progress Tracking** — Terminal output now includes live **ETA and Remaining Time** estimates for every run.
- 📊 **Premium Reporting** — Generates a high-end, consolidated HTML report with metric cards (Success, Failed, Extracted, Inserted), recruiter contact tracking (grouped by candidate), and unique Run IDs.
- 🌐 **Web-Based Orchestration** — Automatically pulls candidate profiles and credentials via API based on the `Run Raw Positions Workflow` flag on the marketing portal.
- ✨ **AI/ML Validation** — Automatically skips job postings that do not pass AI/ML relevance checks.
- 📎 **Resilient PDF Attachments** — Uses SMTP-standard CRLF line endings and proper MIME headers to guarantee that resumes never appear as corrupted in recruiter inboxes.

## Quick Start

### 1. Install Dependencies

```bash
python3 -m venv venv
# On Windows: venv\Scripts\activate
# On Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 2. Setup User Profiles

You can set up profiles for multiple users by creating subfolders in the `resume/` directory:

```bash
mkdir -p resume/Your_Name
cp resume/resume_template.json resume/Your_Name/resume.json
```

Place your generated PDF resume in the `resume/Your_Name/` folder as well. Auto-detection handles finding the correct files when using the `--user` flag. If using a single global profile, files can sit at the `resume/` root.

### 3. Setup Gmail Credentials

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Gmail API
3. Create OAuth2 credentials → download `credentials.json`
4. Place `credentials.json` in your user folder (e.g., `resume/Your_Name/credentials.json`) for user-specific sender accounts, or project root for a shared account.
5. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

### 4. Configure

Edit `config.yaml` to match your environment. Key settings:

```yaml
data_fetcher:
  api_url: "https://api.whitebox-learning.com/api/email-positions/paginated"
  output_filename: "daily_jobs.csv" # Auto-links to input.csv_filename

email_processing:
  daily_cap: 250 # max emails per day
  user_confirmation_before_send: false # Set to true to approve each email

ollama:
  model: llama3.2:3b # Default fast LLM
  llm_quality_retries: 3
```

## Execution Modes

The tool supports several ways to run the automation pipeline, depending on whether you are running for yourself or orchestrating multiple profiles.

### 1. Individual Local Run

Use this to run the pipeline for a specific candidate whose resume and tokens are stored in `resume/<USER_NAME>/`.

```bash
# Fetch fresh jobs and run for a specific user
python run.py --user abcd --fetch

# Preview only (no emails sent)
python run.py --user abcd --fetch --dry-run
```

### 2. Distributed Multi-User Run (Load Balancing)

Split the daily workload evenly across multiple profiles to avoid rate limiting and maximize reach. The tool divides the valid job list by the number of users.

```bash
# Automatically detect all folders in resume/ and split jobs among them
python run.py --run-all --fetch

# Run for a specific subset of profiles
python run.py --users name,name --fetch
```

### 3. Web-Based Orchestration (Whitebox Integration)

This mode connects to the Whitebox Learning API to identify which candidates have the **"Run Raw Positions Workflow"** flag enabled on the marketing page.

```bash
# Fetch enabled candidates from the marketing portal and run sequentially
python run.py --web

# Override the specific field name used for enabling
python run.py --web --web-field my_custom_toggle
```

_This mode automatically downloads resumes, fetches candidate-specific tokens, and cleans up temporary files after execution._

```bash
# Run with custom config file
python run.py --config my_custom_config.yaml
```

## Automation & Scheduling

The project includes a PowerShell wrapper script designed to be run by the **Windows Task Scheduler** for hands-off daily automation.

### Daily Schedule Script (`scripts/daily_schedule.ps1`)

This script performs a full daily cycle for all local candidates:
1.  **Token Refresh**: Runs `auto_login.py` to ensure Whitebox API sessions are active.
2.  **Distributed Run**: Executes `run.py --fetch --run-all` which downloads the latest jobs and splits the workload across all candidate profiles in the `resume/` directory.
3.  **Logging**: Appends execution status to `logs/scheduler.log`.

To automate this:
1. Open **Task Scheduler** on Windows.
2. Create a new task that runs `powershell.exe -File "C:\path\to\project\scripts\daily_schedule.ps1"`.
3. Set it to trigger daily at your preferred time (e.g., 9:00 AM).

## How It Works

1. **Job Fetching:** Pulls daily job postings via Whitebox API (or reads a predefined CSV).
2. **Filtering:** Applies sanitization filters to job titles (ignoring noise) and verifies AI/ML keywords. Removes duplicate recipient emails.
3. **Progress Initialization:** Starts a timer and calculates a conservative ETA based on your batch size.
4. **Data Assembly:** Auto-detects your resume (JSON + PDF) based on the current `--user` or API data.
5. **Generation:** Sends job descriptions + resume data to the local Ollama LLM. The LLM generates a personalized email matching your skills to the job.
6. **Validation:** Checks if the generated email is professional, complete, and contains no hallucinated placeholders. 
7. **Sending:** Sends via Gmail API as HTML with the resume PDF attached, enforcing daily limits and anti-spam delays.
8. **Reporting:** Generates a premium HTML report and sends it to your configured report recipients.

## Project Structure

```
Raw_Positions_Auto_Apply/
├── src/
│   ├── main.py               # CLI entry point
│   ├── orchestrator.py       # Pipeline & ETA orchestration
│   ├── config_loader.py      # YAML config loading
│   ├── validators.py         # Pre-flight validation
│   ├── core/
│   │   ├── resume_handler.py    # Resume JSON parsing
│   │   ├── workflow_manager.py  # Whitebox API Integration
│   │   └── reporter.py          # Premium HTML reporting engine
│   ├── services/
│   │   ├── gmail_service.py         # Gmail API sender
│   │   ├── ollama_service.py        # Ollama LLM client
│   │   ├── csv_service.py           # CSV reading & duplicate tracking
│   │   ├── email_generator_service.py  # Robust LLM Generation
│   │   ├── email_validator_service.py  # LLM Output Validation
│   │   └── prompt_builder.py        # Dynamic prompt construction
│   ├── models/                # Pydantic data models
│   └── utils/                 # Utilities
├── resume/                    # Your resume files (JSON + PDF)
├── input/                     # CSV files with job postings
├── logs/                      # Executable app logs & output CSVs
├── data/                      # Sent emails database (deduplication)
├── config.yaml                # Configuration registry
├── run.py                     # Convenience bootstrapper
└── requirements.txt           # Dependency list
```

## Configuration Reference

| Setting                                          | Description                       | Default                      |
| ------------------------------------------------ | --------------------------------- | ---------------------------- |
| `data_fetcher.api_url`                           | Endpoint for fetching fresh roles | required                     |
| `input.csv_filename`                             | Fallback CSV filename if no API   | `sample_jobs.csv`            |
| `email_processing.daily_cap`                     | Max emails per day to avoid bans  | `250`                        |
| `email_processing.user_confirmation_before_send` | Ask Y/N before each send          | `false`                      |
| `ollama.model`                                   | Local model (e.g., llama3.2:3b)   | `llama3.2:3b`                |
| `ollama.timeout_seconds`                         | Strict max generation time        | `40`                         |
| `gmail.cooldown_every_n_emails`                  | Anti-rate limiting chunks         | `10`                         |
| `web_extraction.enabled_field`                   | API field to trigger workflow     | `run_raw_positions_workflow` |

## Troubleshooting

### Progress Tracking
If the ETA seems unusually high at first, don't worry—the system uses a conservative "warm-up" estimate that automatically corrects itself as soon as the first email is processed.

### No Valid Rows Found
- Verify the jobs inside your CSV haven't already been emailed (check `data/sent_emails.json`).
- Ensure the job titles/descriptions contain AI/ML related keywords, otherwise they are skipped automatically.
- Check that the `Extracted At` date matches the current date if your SQL query filters by `CURDATE()`.
