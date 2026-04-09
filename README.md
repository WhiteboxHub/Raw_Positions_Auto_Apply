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
- 📊 **Tracking & Orchestrator API** — Prevents duplicate emails across all runs by tracking recipient emails. Logs workflow metrics, skips, and failures directly to the central Orchestrator dashboard.
- 🌐 **Web-Based Orchestration** — Automatically pulls candidate profiles and credentials via API, downloads resumes, and runs the entire pipeline with a single command based on candidate-specific flags.
- ✨ **AI/ML Validation** — Automatically skips job postings that do not pass AI/ML relevance checks.

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
python run.py --user Bavish --fetch

# Preview only (no emails sent)
python run.py --user Bavish --fetch --dry-run
```

### 2. Distributed Multi-User Run (Load Balancing)
Split the daily workload evenly across multiple profiles to avoid rate limiting and maximize reach. The tool divides the valid job list by the number of users.

```bash
# Automatically detect all folders in resume/ and split jobs among them
python run.py --run-all --fetch

# Run for a specific subset of profiles
python run.py --users Bavish,Ravi,Ramana --fetch
```

### 3. Web-Based Orchestration (Whitebox Integration)
This mode connects to the Whitebox Learning API to identify which candidates have the **"Run Raw Positions Workflow"** flag enabled on the marketing page.

```bash
# Fetch enabled candidates from the marketing portal and run sequentially
python run.py --web
```
*This mode automatically downloads resumes, fetches candidate-specific tokens, and cleans up temporary files after execution.*

### 4. Utility Commands
```bash
# Fetch fresh jobs from API without running the full pipeline
python run.py --fetch

# Run with custom config file
python run.py --config my_custom_config.yaml
```

## Web-Based Automation Workflow

The system supports a fully automated web workflow designed for recruiters and marketing managers:

1. **Flag-Based Triggering:** The tool fetches all marketing candidates and filters for those with the `Run Raw Positions Workflow` field set to **True** (or 'Yes').
2. **Dynamic Data Fetching:** For each enabled candidate, the tool automatically:
   - Downloads the latest **Resume PDF**.
   - Parses the **Candidate JSON** profile.
   - Retrieves specific email and LinkedIn credentials.
3. **Isolated Environments:** To prevent credential leakage, the tool creates a temporary isolated environment for each candidate. This includes separate Google OAuth tokens, ensuring that the automation runs as the candidate themselves.
4. **End-to-End Orchestration:** The pipeline runs automatically for all enabled candidates in a single execution, reporting individual success and failure metrics back to the central Whitebox dashboard.

## Resume JSON Format

Use `resume/resume_template.json` as your starting point. Key structure:

```json
{
  "cv": {
    "name": "Your Full Name",
    "email": "your@email.com",
    "phone": "+1 (000) 000-0000",
    "total_experience": "5 Years",
    "social_networks": [
      { "network": "LinkedIn", "username": "your-username" },
      { "network": "GitHub", "username": "your-username" }
    ],
    "sections": {
      "experience": [...],
      "skills": [...],
      "education": [...]
    }
  }
}
```

## How It Works

1. **Job Fetching:** Pulls daily job postings via Whitebox API (or reads a predefined CSV).
2. **Filtering:** Applies sanitization filters to job titles (ignoring noise) and verifies AI/ML keywords. Removes duplicate recipient emails.
3. **Data Assembly:** Auto-detects your resume (JSON + PDF) based on the current `--user`.
4. **Generation:** Sends job descriptions + resume data to the local Ollama LLM. The LLM generates a personalized email matching your skills to the job, injecting `total_experience`.
5. **Validation:** Checks if the generated email is professional, complete, and contains no hallucinated placeholders. Repeats/downgrades complexity on failure.
6. **Sending:** Sends via Gmail API as HTML with the resume PDF attached, enforcing daily limits and anti-spam delays.
7. **Tracking:** Logs the recipient's email in `data/sent_emails.json` to prevent duplicates on future runs. Broadcasts success/fail metrics to Orchestrator API.

## Project Structure

```
Raw_Positions_Auto_Apply/
├── src/
│   ├── main.py               # CLI entry point
│   ├── orchestrator.py       # Pipeline & API logging orchestration
│   ├── config_loader.py      # YAML config loading
│   ├── validators.py         # Pre-flight validation
│   ├── core/
│   │   ├── resume_handler.py    # Resume JSON parsing
│   │   ├── workflow_manager.py  # Whitebox API Integration
│   │   └── smart_apply_reporter.py
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
│   └── resume_template.json   # Template for new users
├── input/                     # CSV files with job postings
├── logs/                      # Executable app logs & output CSVs
├── data/                      # Sent emails database (deduplication)
├── tests/                     # Unit test suite
├── config.yaml                # Configuration registry
├── run.py                     # Convenience bootstrapper
└── run.py                     # Convenience bootstrapper
```

## Configuration Reference

| Setting | Description | Default |
|---|---|---|
| `data_fetcher.api_url` | Endpoint for fetching fresh roles | required |
| `input.csv_filename` | Fallback CSV filename if no API | `sample_jobs.csv` |
| `email_processing.daily_cap` | Max emails per day to avoid bans | `250` |
| `email_processing.user_confirmation_before_send`| Ask Y/N before each send | `false` |
| `ollama.model` | Local model (e.g., llama3.2:3b) | `llama3.2:3b` |
| `ollama.timeout_seconds` | Strict max generation time | `40` |
| `gmail.cooldown_every_n_emails` | Anti-rate limiting chunks | `10` |
| `web_extraction.enabled_field` | API field to trigger workflow | `run_raw_positions_workflow` |
| `resume.json_path` / `pdf_path` | Resume paths | `null` (auto) |

## Troubleshooting

### Ollama Not Available
```bash
ollama serve          # Start Ollama service
ollama pull llama3.2:3b # Download required model
```

### Gmail Authentication Failed
- Verify `credentials.json` exists in `resume/User_Name/` or the project root.
- First run opens your browser to request OAuth2 consent.
- Delete `token.pickle` inside the folder to force Re-Authentication.

### No Valid Rows Found / All Duplicates
- If the application reports 0 emails sent, verify the jobs inside `daily_jobs.csv` haven't already been emailed. 
- You can check `data/sent_emails.json` to see previously contacted email addresses.
- Ensure the job titles/descriptions contain AI/ML related keywords, otherwise they are skipped automatically.
