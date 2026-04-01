# SmartApply - AI-Powered Job Application Email Generator

Automated email generation and sending for job applications using local Ollama LLM and Gmail API.

## Features

- 📧 **Automated Email Generation** — Uses local Ollama LLM to generate personalized application emails
- 🤖 **LLM-Powered Personalization** — Matches your skills to job requirements automatically
- 📨 **Gmail API Integration** — Sends emails via Google OAuth2 (HTML formatted)
- 📎 **Resume Attachment** — Automatically attaches your PDF resume
- 🔗 **Social Links** — Appends LinkedIn & GitHub from your resume JSON
- 🎯 **Batch Processing** — Process multiple job postings from CSV
- ⚙️ **Config-Driven** — All settings in `config.yaml`, auto-detects resume files
- 📊 **Tracking** — Prevents duplicate emails, logs all activity
- 🔒 **Secure** — OAuth2 authentication, local LLM (data never leaves your machine)

## Quick Start

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Setup Resume

You can set up profiles for multiple users by creating subfolders in the `resume/` directory:

```bash
mkdir -p resume/Your_Name
cp resume/resume_template.json resume/Your_Name/resume.json
```

Place your generated PDF resume in the `resume/Your_Name/` folder as well. Auto-detection handles finding the correct files when using the `--user` flag.

### 3. Setup Gmail Credentials

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Gmail API
3. Create OAuth2 credentials → download `credentials.json`
4. Place `credentials.json` either in the project root (shared) OR in your user folder (e.g., `resume/Your_Name/credentials.json`) for user-specific sender accounts.
5. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

### 4. Configure

Edit `config.yaml` — most defaults work out of the box:

```yaml
input:
  csv_filename: your_jobs.csv
  column_mapping:
    email: "Contact Info"
    title: "Title"
    description: "Description"

resume:
  json_path: null  # auto-detects first .json in resume/
  pdf_path: null   # auto-detects first .pdf in resume/
```

### 5. Run

```bash
# Send emails for the default setup
python run.py

# Send emails for a specific user profile
python run.py --user Your_Name

# Preview emails for a user (dry-run, no sending)
python run.py --user Your_Name --dry-run

# Force resend to previously sent addresses
python run.py --force-resend
```

## Resume JSON Format

Use `resume/resume_template.json` as your starting point. Key structure:

```json
{
  "cv": {
    "name": "Your Full Name",
    "email": "your@email.com",
    "phone": "+1 (000) 000-0000",
    "social_networks": [
      { "network": "LinkedIn", "username": "your-username" },
      { "network": "GitHub", "username": "your-username" }
    ],
    "sections": {
      "experience": [
        {
          "company": "Company",
          "position": "Role",
          "date": { "start_date": "YYYY-MM", "end_date": null },
          "highlights": ["Achievement 1", "Achievement 2"]
        }
      ],
      "skills": [
        { "label": "Programming Languages", "details": "Python, Java, SQL" },
        { "label": "Cloud & DevOps", "details": "AWS, Docker, Kubernetes" }
      ],
      "education": [...],
      "certifications": [...]
    }
  }
}
```

## CSV Format

The CSV should have columns matching `config.yaml` → `input.column_mapping`. Example:

| Contact Info | Title | Description | Company |
|---|---|---|---|
| `Email: john@co.com` | Data Scientist | Job posting text... | Acme Corp |

## Project Structure

```
SmartApply/
├── src/
│   ├── main.py               # CLI entry point
│   ├── orchestrator.py        # Pipeline orchestration
│   ├── config_loader.py       # YAML config loading
│   ├── validators.py          # Pre-flight validation
│   ├── core/
│   │   └── resume_handler.py  # Resume JSON parsing
│   ├── services/
│   │   ├── gmail_service.py         # Gmail API sender
│   │   ├── ollama_service.py        # Ollama LLM client
│   │   ├── csv_service.py           # CSV reading & tracking
│   │   ├── email_generator_service.py  # Email generation
│   │   ├── email_validator_service.py  # Email validation
│   │   └── prompt_builder.py        # LLM prompt construction
│   ├── models/                # Data models
│   └── utils/                 # Utilities (regex, etc.)
├── resume/                    # Your resume files (JSON + PDF)
│   └── resume_template.json   # Template for new users
├── input/                     # CSV files with job postings
├── logs/                      # Output logs & result CSVs
├── data/                      # Sent email tracking
├── tests/                     # Test suite
├── config.yaml                # Configuration
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
└── run.py                     # Convenience runner
```

## Configuration Reference

| Setting | Description | Default |
|---|---|---|
| `input.csv_filename` | CSV file in `input/` | required |
| `input.column_mapping` | Map CSV columns | required |
| `email_processing.email_limit` | Max emails (`null` = all) | `null` |
| `email_processing.dry_run` | Preview without sending | `false` |
| `email_processing.user_confirmation_before_send` | Ask Y/N before each send | `true` |
| `ollama.model` | Ollama LLM model name | `llama3` |
| `resume.json_path` | Resume JSON (`null` = auto) | `null` |
| `resume.pdf_path` | Resume PDF (`null` = auto) | `null` |

## How It Works

1. Reads job postings from CSV
2. Auto-detects your resume (JSON + PDF) from `resume/`
3. Extracts recruiter name from contact email
4. Sends job description + resume to local Ollama LLM
5. LLM generates personalized email matching your skills to the job
6. Appends LinkedIn/GitHub links from resume
7. Sends via Gmail API as HTML with resume PDF attached
8. Tracks sent emails to prevent duplicates

## Security

- **OAuth2** — No passwords stored, uses Google OAuth2 tokens
- **Minimal Permissions** — Only `gmail.send` scope requested
- **Git-Ignored** — `.env`, `credentials.json`, `token.pickle`, and personal resume files are never committed
- **Local LLM** — All data stays on your machine via Ollama

## Troubleshooting

### Ollama Not Available
```bash
ollama serve          # Start Ollama
ollama pull llama3    # Download model
```

### Gmail Authentication Failed
- Verify `credentials.json` exists in project root
- First run opens browser for OAuth2 consent
- Delete `token.pickle` to re-authenticate

### No Valid Rows Found
- Check CSV exists in `input/` and `csv_filename` matches in config
- Verify `column_mapping` matches your CSV column headers exactly
- Check `data/sent_emails.json` — emails may already be tracked as sent

## License

Personal Use
