# SmartApply - AI-Powered Job Application Email Generator

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

### 5. Run

```bash
# Fetch fresh jobs from API and send emails for the default setup
python run.py

# Run for a specific user profile (ideal for scheduled tasks)
python run.py --user Your_Name

# Preview emails without sending (dry-run mode)
python run.py --user Your_Name --dry-run
```

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
SmartApply/
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
