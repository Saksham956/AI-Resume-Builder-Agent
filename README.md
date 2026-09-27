# AI Job Alert & Resume Tailoring Agent — Gemini V3

This version follows the strict seven-section resume specification:

1. HEADER
2. PROFESSIONAL SUMMARY
3. WORK EXPERIENCE
4. INDIVIDUAL PROJECTS
5. EDUCATION
6. CERTIFICATIONS AND ACHIEVEMENTS
7. SKILLS

The generated resume uses fixed identity/contact values, a three-sentence JD-driven summary, four projects with technology-only pipe headers, and eight fixed skill categories.

## Gemini

- Model: `gemini-3.5-flash-lite`
- SDK: `google-genai>=2.25,<3.0`
- Google Search is disabled by default for Free Tier compatibility. Set `ENABLE_GOOGLE_SEARCH=true` only when the project has Search grounding access.

## Run

1. Rename `.env.example` to `.env`.
2. Fill the Gmail, Gemini, and Telegram secrets.
3. Run `python main.py`.

The agent scans unread emails from the configured placement sender, tailors the resume, generates a compact DOCX, sends the notification/document to Telegram, and only then marks the email read.
