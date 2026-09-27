from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

LOCKED_IDENTITY = {
    "name": "Saksham Nehra",
    "display_name": "SAKSHAM NEHRA",
    "email": "ayunav23@gmail.com",
    "phone": "+91 98778 82442",
    "linkedin": "www.linkedin.com/in/saksham-nehra-7392932b4",
    "github": "https://github.com/Saksham956",
    "location": "Chennai, India",
}

LOCKED_EDUCATION = {
    "institution": "SRM Institute of Science and Technology, Chennai",
    "degree": "B.Tech. in Artificial Intelligence",
    "dates": "Aug 2023 – May 2027",
    "cgpa": "8.14/10",
}

OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "generated_resumes")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_DB = BASE_DIR / os.getenv("STATE_DB", "state.db")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
ENABLE_GOOGLE_SEARCH = os.getenv("ENABLE_GOOGLE_SEARCH", "false").strip().lower() in {"1", "true", "yes", "on"}

EMAIL_HOST = os.getenv("EMAIL_HOST", "imap.gmail.com").strip()
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "993"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "").strip()
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "").strip()
EMAIL_FOLDER = os.getenv("EMAIL_FOLDER", "INBOX").strip()
ALLOWED_SENDERS = tuple(x.strip().lower() for x in os.getenv("ALLOWED_SENDERS", "srm@haveloc.com").split(",") if x.strip())
LOOKBACK_DAYS = max(1, int(os.getenv("LOOKBACK_DAYS", "7")))
MAX_EMAILS_PER_CYCLE = max(1, int(os.getenv("MAX_EMAILS_PER_CYCLE", "1")))
MAX_EMAIL_CHARS = max(5000, int(os.getenv("MAX_EMAIL_CHARS", "14000")))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
TELEGRAM_TIMEOUT_SECONDS = int(os.getenv("TELEGRAM_TIMEOUT_SECONDS", "30"))

POLL_INTERVAL_SECONDS = max(10, int(os.getenv("POLL_INTERVAL_SECONDS", "60")))
PROJECT_MODE = os.getenv("PROJECT_MODE", "IDEAS").strip().upper()
if PROJECT_MODE not in {"IDEAS", "RESUME"}:
    PROJECT_MODE = "IDEAS"

# Locked factual content from the candidate resume. The agent never rewrites it.
LOCKED_EXPERIENCE = {
    "company": "Blue Star Logistics",
    "role": "Software Developer Intern",
    "dates": "Jun 2025 – Jul 2025",
    "bullets": [
        "Architected and deployed a comprehensive, responsive website to digitize logistics operations, improving online presence.",
        "Engineered the front-end using React, HTML5, and CSS3 to ensure a seamless user experience across mobile and desktop devices.",
    ],
}

CERTIFICATIONS = [
    "Oracle Certified Professional: Autonomous Database Cloud | Oracle University",
    "Python Programming Certification | Intel Unnati",
    "Certificate of Appreciation: Project Expo 2026 | SRM Institute of Science and Technology",
]

CANDIDATE_CONTEXT = {
    "identity": LOCKED_IDENTITY,
    "education": LOCKED_EDUCATION,
    "locked_experience": LOCKED_EXPERIENCE,
    "certifications": CERTIFICATIONS,
    "candidate_stack_for_project_ideas": [
        "Python", "C++", "SQL", "Java", "JavaScript", "TypeScript", "HTML", "CSS",
        "PySpark", "Apache Spark", "Azure Databricks", "Delta Lake", "MySQL", "PostgreSQL",
        "Oracle", "PyTorch", "TensorFlow", "LangChain", "LangGraph", "OpenCV", "DeepSORT",
        "FastAPI", "Flask", "Docker", "Git", "REST APIs",
    ],
}

JOB_KEYWORDS = (
    "new job", "job opportunity", "job opening", "hiring", "internship", "placement",
    "recruitment", "software engineer", "software developer", "developer", "engineer",
    "associate", "analyst", "data engineer", "data scientist", "product engineer",
    "technical", "technology", "assessment", "interview", "shortlisted",
)
NON_JOB_KEYWORDS = (
    "class invitation", "assignment", "ppt", "workshop", "lecture", "attendance",
    "exam", "quiz", "faculty", "course registration", "fee payment", "maintenance activity",
    "holiday notification", "survey methodology",
)


def validate_config() -> None:
    missing = [
        k for k, v in {
            "GOOGLE_API_KEY": GOOGLE_API_KEY,
            "EMAIL_USERNAME": EMAIL_USERNAME,
            "EMAIL_PASSWORD": EMAIL_PASSWORD,
            "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
            "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
        }.items() if not v
    ]
    if missing:
        raise RuntimeError("Missing required environment variables: " + ", ".join(missing))
