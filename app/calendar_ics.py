"""Calendar sync without OAuth, using the ICS standard.

Export: the app has one private feed URL. In Google Calendar: Other calendars > From URL.
Import: upload any calendar's .ics file; future events become deadlines.
"""
import datetime
import re
import secrets

from . import db, tools


def feed_token():
    """Secret token that protects the calendar feed URL (created on first use)."""
    token = db.get_setting("calendar_token")
    if not token:
        token = secrets.token_urlsafe(24)
        db.set_setting("calendar_token", token)
    return token


def _esc(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _unesc(s):
    return s.replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")


def build_ics(user_id, name="StudyPilot Deadlines"):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//StudyPilot//EN",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{_esc(name)}",
    ]
    for d in tools.list_deadlines(user_id):
        try:
            day = datetime.date.fromisoformat(d["due_date"])
        except ValueError:
            continue
        end = day + datetime.timedelta(days=1)
        lines += [
            "BEGIN:VEVENT",
            f"UID:deadline-{d['id']}@studypilot",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{day:%Y%m%d}",
            f"DTEND;VALUE=DATE:{end:%Y%m%d}",
            f"SUMMARY:{_esc(d['title'])}",
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            "DESCRIPTION:Reminder",
            "TRIGGER:-P1D",
            "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def parse_ics(text):
    """Returns [(title, 'YYYY-MM-DD'), ...]"""
    text = re.sub(r"\r?\n[ \t]", "", text)  # unfold wrapped lines
    events, cur = [], None
    for line in text.splitlines():
        s = line.strip()
        if s == "BEGIN:VEVENT":
            cur = {}
        elif s == "END:VEVENT":
            if cur and cur.get("title") and cur.get("date"):
                events.append((cur["title"], cur["date"]))
            cur = None
        elif cur is not None and ":" in s:
            key, val = s.split(":", 1)
            key = key.split(";")[0].upper()
            if key == "SUMMARY":
                cur["title"] = _unesc(val.strip())
            elif key == "DTSTART":
                m = re.match(r"(\d{4})(\d{2})(\d{2})", val.strip())
                if m:
                    cur["date"] = f"{m[1]}-{m[2]}-{m[3]}"
    return events


def import_ics(user_id, text):
    """Adds today's/future events as deadlines (skips duplicates). Returns the number added."""
    today = datetime.date.today().isoformat()
    existing = {(d["title"].lower(), d["due_date"]) for d in tools.list_deadlines(user_id, include_done=True)}
    added = 0
    for title, date in parse_ics(text):
        if date < today or (title.lower(), date) in existing:
            continue
        try:
            tools.add_deadline(user_id, title, date)
        except ValueError:
            continue
        existing.add((title.lower(), date))
        added += 1
    return added
