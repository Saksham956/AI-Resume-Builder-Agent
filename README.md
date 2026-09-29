
# AI Resume Builder Agent

An AI-powered job monitoring and resume tailoring system that automatically processes placement and job opportunity emails, analyzes job descriptions, generates role-specific resume content, validates the output, and delivers the generated resume through Telegram.

## Overview

The AI Resume Builder Agent automates the repetitive workflow of identifying job opportunities and preparing a tailored resume for each role.

The system monitors a Gmail inbox for unread placement/job opportunity emails, extracts the relevant job description, analyzes the requirements using Gemini, generates structured resume content, validates the generated content against predefined rules, builds a formatted DOCX resume, and sends the result through Telegram.

## Workflow

Gmail / Placement Email
          |
          v
     Email Ingestion
          |
          v
       JD Extraction
          |
          v
     Gemini JD Analysis
          |
          v
   Structured Resume Data
          |
          v
   Resume Validation
          |
          v
    DOCX Resume Builder
          |
          v
    Telegram Notification
          |
          v
      Generated Resume

## Key Features

* Monitors Gmail for unread placement and job opportunity emails.
* Extracts job descriptions and relevant hiring information.
* Uses Google Gemini for structured job-description analysis.
* Identifies technical requirements, workflows, engineering practices, and functional keywords.
* Generates role-specific resume content and project concepts.
* Separates project titles from technology stacks.
* Uses structured Pydantic models for LLM output validation.
* Applies resume content guardrails to reduce unsupported claims.
* Validates generated summaries, projects, skills, and bullet points.
* Generates formatted DOCX resumes programmatically.
* Maintains local processing state to avoid duplicate processing.
* Sends generated resume notifications through Telegram.
* Supports continuous background execution on Windows.

## Tech Stack

### Programming

* Python

### AI / LLM

* Google Gemini API
* Pydantic
* Structured LLM outputs

### Email Processing

* Gmail IMAP
* Python `imaplib`

### Document Generation

* `python-docx`

### Notifications

* Telegram Bot API

### Automation

* Windows batch scripts
* Windows background execution

### State Management

* SQLite

### Development Tools

* Git
* GitHub
* Python virtual environments

## Project Structure

AI-Resume-Builder-Agent/
│
├── main.py
├── llm_tailor.py
├── document_builder.py
├── config.py
├── errors.py
├── requirements.txt
├── README.md
├── .gitignore
├── start_agent.bat
└── start_agent_hidden.vbs


## Component Responsibilities

### `main.py`

Controls the overall workflow of the agent, including email polling, job processing, resume generation, notification, and state handling.

### `llm_tailor.py`

Handles job-description analysis and structured Gemini responses used to generate tailored resume content.

### `document_builder.py`

Builds the formatted DOCX resume from the structured output produced by the tailoring pipeline.

### `config.py`

Loads and manages application configuration and environment variables.

### `errors.py`

Contains application-specific error handling.

### `start_agent.bat`

Provides a Windows startup script for launching the agent.

### `start_agent_hidden.vbs`

Provides a background execution option for running the agent without keeping a visible command window open.

## Environment Variables

Create a local `.env` file containing the required credentials:

`env
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL=gemini-3.5-flash-lite

EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

MAX_EMAILS=1
BACKOFF=3600
``

**Never commit the `.env` file to GitHub.**

Sensitive credentials are intentionally excluded from version control using `.gitignore`.

## Installation

Clone the repository:

`bash
git clone https://github.com/Saksham956/AI-Resume-Builder-Agent.git
``

Enter the project directory:

``bash
cd AI-Resume-Builder-Agent
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```cmd
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the `.env` file and configure the required credentials.

## Running the Agent

Run directly with Python:

```bash
python main.py
```

Alternatively, use the Windows startup script:

```text
start_agent.bat
```

The agent can also be configured to start automatically with Windows using Windows Task Scheduler.

## Resume Generation Pipeline

The system follows a structured generation process:

1. Detect a new unread job opportunity email.
2. Extract the job description.
3. Analyze the role and identify relevant requirements.
4. Classify requirements according to candidate evidence and project targets.
5. Generate structured resume content.
6. Validate generated content against resume guardrails.
7. Build the DOCX resume.
8. Deliver the generated resume through Telegram.
9. Store processing state to prevent duplicate handling.

## Resume Safety & Validation

The generation pipeline includes validation rules designed to prevent common problems in AI-generated resumes.

Examples include:

* Preventing unsupported completed-work claims.
* Separating project titles from technology lists.
* Validating project structure.
* Checking bullet-point formatting.
* Enforcing action-oriented bullet writing.
* Preventing placeholder language.
* Protecting fixed candidate information.
* Keeping generated content aligned with the target job description.

## Security

Sensitive configuration is intentionally excluded from version control.

The `.gitignore` excludes:

```text
.env
state.db
generated_resumes/
__pycache__/
*.pyc
```

API keys, email credentials, Telegram credentials, and generated private resumes should never be committed to the repository.

## Current Architecture

```text
                    +----------------------+
                    |    Gmail Inbox       |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |   Email Ingestion    |
                    |      IMAP/Python     |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |   JD Processing      |
                    |      Gemini API      |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Resume Tailoring     |
                    | Structured Output    |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Validation Engine    |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | DOCX Resume Builder  |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Telegram Notification|
                    +----------------------+
```

## Future Improvements

* Cloud-based continuous execution.
* Automated application submission with user approval.
* Web-based monitoring dashboard.
* Resume version tracking.
* Application history and analytics.
* Additional document formats such as PDF.
* Multi-account email support.
* Role-specific resume templates.

````


