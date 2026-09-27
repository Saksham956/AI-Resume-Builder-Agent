from __future__ import annotations

import email
import email.header
import imaplib
import logging
import signal
import sqlite3
import time
from datetime import datetime, timezone

from email.message import Message
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from docx import Document

import config
from errors import QuotaExceeded
from llm_tailor import ResumeTailor, TailoredResume


STOP = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("ai-job-resume-agent")


def stop(signum, _):
    global STOP
    STOP = True
    log.info("Shutdown signal received (%s).", signum)


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)


def dec(v):
    if not v:
        return ""
    out = []
    for x, enc in email.header.decode_header(v):
        out.append(
            x.decode(enc or "utf-8", "replace") if isinstance(x, bytes) else x
        )
    return "".join(out).strip()


def pdf_text(b):
    import io

    reader = PdfReader(io.BytesIO(b))
    return "\n".join((page.extract_text() or "") for page in reader.pages[:20])


def docx_text(b):
    import io

    doc = Document(io.BytesIO(b))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def body(msg: Message):
    plain = []
    html = []
    attachments = []

    parts = msg.walk() if msg.is_multipart() else [msg]

    for part in parts:
        disposition = (part.get("Content-Disposition") or "").lower()
        name = part.get_filename() or ""
        payload = part.get_payload(decode=True)

        if "attachment" in disposition and payload:
            try:
                if name.lower().endswith(".pdf"):
                    attachments.append(pdf_text(payload))
                elif name.lower().endswith(".docx"):
                    attachments.append(docx_text(payload))
            except Exception:
                pass
            continue

        if not payload:
            continue

        text = payload.decode(
            part.get_content_charset() or "utf-8",
            "replace",
        )

        if part.get_content_type() == "text/plain":
            plain.append(text)
        elif part.get_content_type() == "text/html":
            html.append(text)

    if plain:
        text = "\n".join(plain)
    elif html:
        text = BeautifulSoup(
            "\n".join(html),
            "html.parser",
        ).get_text("\n")
    else:
        text = ""

    text += "\n\n" + "\n\n".join(attachments)

    return "\n".join(
        line.strip() for line in text.splitlines() if line.strip()
    ).strip()


def parse(raw):
    msg = email.message_from_bytes(raw)

    return {
        "subject": dec(msg.get("Subject")),
        "sender": dec(msg.get("From")),
        "date": dec(msg.get("Date")),
        "message_id": dec(msg.get("Message-ID")),
        "body": body(msg),
    }


def job(record):
    if not any(
        sender in record["sender"].lower()
        for sender in config.ALLOWED_SENDERS
    ):
        return False

    text = (
        record["subject"]
        + "\n"
        + record["body"][:12000]
    ).lower()

    if any(keyword in text for keyword in config.NON_JOB_KEYWORDS):
        return False

    return any(keyword in text for keyword in config.JOB_KEYWORDS)


class Mail:
    def __init__(self):
        self.mail = None

    def connect(self):
        self.close()

        self.mail = imaplib.IMAP4_SSL(
            config.EMAIL_HOST,
            config.EMAIL_PORT,
        )

        self.mail.login(
            config.EMAIL_USERNAME,
            config.EMAIL_PASSWORD,
        )

        status, _ = self.mail.select(
            config.EMAIL_FOLDER,
            readonly=False,
        )

        if status != "OK":
            raise RuntimeError("Could not select mailbox")

        log.info(
            "Connected to %s/%s",
            config.EMAIL_HOST,
            config.EMAIL_FOLDER,
        )

    def close(self):
        if not self.mail:
            return

        try:
            self.mail.close()
        except Exception:
            pass

        try:
            self.mail.logout()
        except Exception:
            pass

        self.mail = None

    def uids(self, since_date):
        """
        Return unread placement emails received on/after the
        persistent agent start date.

        The start date is NOT reset when Windows restarts.
        Therefore, if the PC is off for several days, emails
        received during that period are still eligible.
        """

        since = since_date.strftime("%d-%b-%Y")

        # Use the configured placement sender. The current setup
        # uses srm@haveloc.com, matching the existing agent behavior.
        sender = "srm@haveloc.com"

        status, data = self.mail.uid(
            "search",
            None,
            "FROM",
            sender,
            "UNSEEN",
            "SINCE",
            since,
        )

        if status != "OK":
            raise RuntimeError(
                f"IMAP search failed: {data!r}"
            )

        ids = data[0].split() if data and data[0] else []

        # Newest first.
        ids = list(reversed(ids))

        return ids[: config.MAX_EMAILS_PER_CYCLE]

    def fetch(self, uid):
        status, data = self.mail.uid(
            "fetch",
            uid,
            "(BODY.PEEK[])",
        )

        if status != "OK":
            raise RuntimeError("Could not fetch email")

        for item in data:
            if isinstance(item, tuple) and isinstance(item[1], bytes):
                return item[1]

        raise RuntimeError("No message body returned")

    def read(self, uid):
        status, _ = self.mail.uid(
            "store",
            uid,
            "+FLAGS",
            "(\\Seen)",
        )

        if status != "OK":
            raise RuntimeError("Could not mark read")


class State:
    def __init__(self):
        self.c = sqlite3.connect(config.STATE_DB)

        self.c.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs(
                uid TEXT PRIMARY KEY,
                message_id TEXT,
                status TEXT,
                tailoring_json TEXT,
                resume_path TEXT,
                summary_sent INTEGER DEFAULT 0,
                document_sent INTEGER DEFAULT 0,
                updated_at TEXT
            )
            """
        )

        # Persistent metadata table.
        # This stores the first date on which this version of the
        # agent is started, so Windows restarts do NOT reset it.
        self.c.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_meta(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        self.c.commit()

    def get_or_create_start_date(self):
        row = self.c.execute(
            "SELECT value FROM agent_meta WHERE key=?",
            ("agent_start_date",),
        ).fetchone()

        if row and row[0]:
            try:
                return datetime.strptime(
                    row[0],
                    "%Y-%m-%d",
                ).date()
            except ValueError:
                pass

        # First run of this updated agent:
        # start from TODAY and persist that date permanently.
        start_date = datetime.now().date()

        self.c.execute(
            """
            INSERT OR REPLACE INTO agent_meta(key, value)
            VALUES(?, ?)
            """,
            (
                "agent_start_date",
                start_date.isoformat(),
            ),
        )

        self.c.commit()

        log.info(
            "Agent start date initialized to %s. "
            "Only placement emails from this date onward will be eligible.",
            start_date.isoformat(),
        )

        return start_date

    def get(self, uid):
        row = self.c.execute(
            """
            SELECT uid,message_id,status,tailoring_json,resume_path,
                   summary_sent,document_sent
            FROM jobs
            WHERE uid=?
            """,
            (uid,),
        ).fetchone()

        if not row:
            return None

        return {
            "uid": row[0],
            "message_id": row[1],
            "status": row[2],
            "tailoring_json": row[3],
            "resume_path": row[4],
            "summary_sent": bool(row[5]),
            "document_sent": bool(row[6]),
        }

    def save(self, uid, msgid, res, path):
        self.c.execute(
            """
            INSERT INTO jobs(
                uid,
                message_id,
                status,
                tailoring_json,
                resume_path,
                updated_at
            )
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(uid) DO UPDATE SET
                message_id=excluded.message_id,
                status=excluded.status,
                tailoring_json=excluded.tailoring_json,
                resume_path=excluded.resume_path,
                updated_at=excluded.updated_at
            """,
            (
                uid,
                msgid,
                "processing",
                res.model_dump_json(),
                str(path),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.c.commit()

    def summary(self, uid):
        self.c.execute(
            """
            UPDATE jobs
            SET summary_sent=1, updated_at=?
            WHERE uid=?
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                uid,
            ),
        )
        self.c.commit()

    def document(self, uid):
        self.c.execute(
            """
            UPDATE jobs
            SET document_sent=1,
                status='complete',
                updated_at=?
            WHERE uid=?
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                uid,
            ),
        )
        self.c.commit()

    def close(self):
        self.c.close()


class Telegram:
    def __init__(self):
        self.base = (
            "https://api.telegram.org/bot"
            + config.TELEGRAM_BOT_TOKEN
        )
        self.s = requests.Session()

    def msg(self, text):
        response = self.s.post(
            self.base + "/sendMessage",
            json={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": text,
            },
            timeout=config.TELEGRAM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        if not response.json().get("ok"):
            raise RuntimeError("Telegram message failed")

    def doc(self, path, caption):
        with path.open("rb") as file:
            response = self.s.post(
                self.base + "/sendDocument",
                data={
                    "chat_id": config.TELEGRAM_CHAT_ID,
                    "caption": caption,
                },
                files={
                    "document": (
                        path.name,
                        file,
                        "application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document",
                    )
                },
                timeout=config.TELEGRAM_TIMEOUT_SECONDS,
            )

        response.raise_for_status()

        if not response.json().get("ok"):
            raise RuntimeError("Telegram document failed")


def process(uid, raw, tailor, tg, state):
    record = parse(raw)

    if not job(record):
        log.info(
            "Skipping non-job email: %s",
            record["subject"],
        )
        return False

    uid_text = uid.decode(errors="ignore")

    log.info(
        "Processing placement email UID %s from %s: %s",
        uid_text,
        record["sender"],
        record["subject"],
    )

    existing = state.get(uid_text)
    result = None
    path = None

    if existing and existing.get("tailoring_json"):
        try:
            result = TailoredResume.model_validate_json(
                existing["tailoring_json"]
            )

            existing_path = (
                Path(existing["resume_path"])
                if existing.get("resume_path")
                else None
            )

            path = (
                existing_path
                if existing_path and existing_path.exists()
                else None
            )

        except Exception:
            result = None
            path = None

    if result is None:
        jobtext = (
            "SUBJECT:\n"
            + record["subject"]
            + "\n\nFROM:\n"
            + record["sender"]
            + "\n\nDATE:\n"
            + record["date"]
            + "\n\nJOB EMAIL / JD:\n"
            + record["body"][: config.MAX_EMAIL_CHARS]
        )

        result = tailor.tailor(jobtext)

        path = __import__(
            "document_builder"
        ).build_resume(result)

        state.save(
            uid_text,
            record["message_id"],
            result,
            path,
        )

    elif path is None:
        path = __import__(
            "document_builder"
        ).build_resume(result)

    existing = state.get(uid_text)

    if not existing or not existing["summary_sent"]:
        tg.msg(
            "📄 New placement opportunity\n"
            f"Company: {result.company_name}\n"
            f"Role: {result.job_role}\n"
            f"Location: {result.location}\n"
            f"Type: {result.job_type}\n"
            f"Compensation: {result.compensation}\n"
            f"Deadline: {result.application_deadline}\n\n"
            "✅ Tailored resume generated."
        )

        state.summary(uid_text)

    existing = state.get(uid_text)

    if not existing or not existing["document_sent"]:
        tg.doc(
            path,
            f"Tailored resume — "
            f"{result.company_name} | {result.job_role}",
        )
        state.document(uid_text)

    return True


def poll_once():
    mail = Mail()
    state = State()

    try:
        # IMPORTANT:
        # The start date is created once and stored in SQLite.
        # It will NOT change when Windows restarts.
        start_date = state.get_or_create_start_date()

        mail.connect()

        ids = mail.uids(start_date)

        log.info(
            "Found %d unread placement candidate email(s) "
            "from %s onward.",
            len(ids),
            start_date.isoformat(),
        )

        if not ids:
            return

        tailor = ResumeTailor()
        telegram = Telegram()

        for uid in ids:
            try:
                if process(
                    uid,
                    mail.fetch(uid),
                    tailor,
                    telegram,
                    state,
                ):
                    mail.read(uid)

                    log.info(
                        "Completed UID %s and marked it READ.",
                        uid.decode(errors="ignore"),
                    )

                    # Keep the existing one-email-per-cycle behavior.
                    break

            except QuotaExceeded as exc:
                log.error(
                    "Gemini quota/rate limit reached: %s",
                    exc,
                )
                return

            except Exception:
                log.exception(
                    "Failed to process UID %s; leaving it unread for retry.",
                    uid,
                )

    finally:
        mail.close()
        state.close()


def main():
    config.validate_config()

    log.info(
        "AI Job Alert & Resume Tailoring Agent - Gemini edition started."
    )

    log.info(
        "Gemini model: %s",
        config.GEMINI_MODEL,
    )

    log.info(
        "Placement sender(s): %s",
        ", ".join(config.ALLOWED_SENDERS),
    )

    log.info(
        "Polling every %ds.",
        config.POLL_INTERVAL_SECONDS,
    )

    while not STOP:
        try:
            poll_once()
        except Exception:
            log.exception("Polling cycle failed.")

        if not STOP:
            time.sleep(config.POLL_INTERVAL_SECONDS)

    log.info("Agent stopped.")


if __name__ == "__main__":
    main()
