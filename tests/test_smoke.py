import datetime
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


def tool_call(name, args):
    return SimpleNamespace(
        content=None,
        tool_calls=[
            SimpleNamespace(id="call1", function=SimpleNamespace(name=name, arguments=json.dumps(args)))
        ],
    )


def final(text):
    return SimpleNamespace(content=text, tool_calls=None)


@pytest.fixture
def client(tmp_path, monkeypatch):
    from app import config, llm

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setattr(config, "PUBLIC_URL", "http://testserver")
    monkeypatch.setattr(config, "TELEGRAM_ALLOWED_CHAT_IDS", set())
    monkeypatch.setattr(llm, "embed", lambda texts: None)  # keyword fallback
    seen = []

    def fake_chat(messages, tools=None, **kw):
        if tools is None:  # memory extraction
            return final('["User is an AI/ML student"]')
        seen.append(messages[0]["content"])
        if any(m.get("role") == "tool" for m in messages):
            return final("Deadline added. All the best!")
        if "deadline" in messages[-1]["content"].lower():
            return tool_call("add_deadline", {"title": "DSA exam", "due_date": "2099-01-10"})
        return final("Hello!")

    monkeypatch.setattr(llm, "chat", fake_chat)
    from app.main import app

    c = TestClient(app)
    c.seen = seen
    return c


def test_health_and_no_login(client):
    h = client.get("/health").json()
    assert h["ok"] and "auth_required" not in h
    assert client.get("/deadlines").status_code == 200  # no login needed
    assert client.post("/auth/login", json={"username": "a", "password": "b"}).status_code == 404


def test_chat_tool_and_memory(client):
    r = client.post("/chat", json={"message": "My DSA exam deadline is 2099-01-10, please add it"}).json()
    assert "Deadline" in r["reply"]
    assert r["tools_used"][0]["tool"] == "add_deadline"
    assert "User is an AI/ML student" in r["memories_saved"]
    assert client.get("/deadlines").json()[0]["title"] == "DSA exam"
    assert any("AI/ML" in m["text"] for m in client.get("/memories").json())


def test_system_prompt_requires_english(client):
    client.post("/chat", json={"message": "hello"})
    prompt = client.seen[-1]
    assert "proper English" in prompt
    assert "Hinglish" in prompt  # explicitly told not to reply in it


def test_rag_upload_and_search(client):
    text = "Binary search is a divide and conquer algorithm that works on a sorted array. " * 5
    r = client.post("/upload", files={"file": ("dsa.txt", text.encode())})
    assert r.status_code == 200 and r.json()["chunks"] >= 1
    from app import tools

    assert "dsa.txt" in tools.run_tool("default", "search_notes", {"query": "binary search"})
    assert tools.run_tool("nobody", "search_notes", {"query": "binary search"}).startswith("Nothing relevant")
    assert client.get("/documents").json()[0]["source"] == "dsa.txt"


def test_skill_expansion():
    from app import skills

    assert "DSA" in skills.expand("/plan DSA")
    assert skills.expand("hello") == "hello"


def test_reminder_brief_and_telegram_push(client, monkeypatch):
    from app import config, scheduler, telegram_bot, tools

    sent = []
    monkeypatch.setattr(config, "TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.setattr(telegram_bot, "_call", lambda method, **p: sent.append((method, p)) or {})
    assert telegram_bot.is_allowed(123)  # first chat claims the bot
    soon = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    tools.add_deadline("default", "Quiz", soon)
    scheduler.deadline_reminder_job()
    scheduler.deadline_reminder_job()  # must not send a second reminder
    notes = client.get("/notifications").json()
    assert len(notes) == 1 and "Quiz" in notes[0]["content"]
    assert len(sent) == 1 and str(sent[0][1]["chat_id"]) == "123" and "Quiz" in sent[0][1]["text"]
    assert "Quiz" in scheduler.plain_brief()


def test_telegram_is_private(client, monkeypatch):
    from app import config, telegram_bot

    sent = []
    monkeypatch.setattr(telegram_bot, "_call", lambda method, **p: sent.append(p) or {})

    assert "/brief" in telegram_bot.handle_text(555, "/help")  # first chat becomes the owner
    assert "private" in telegram_bot.handle_text(777, "hello").lower()  # everyone else is refused
    assert "777" in telegram_bot.handle_text(777, "/id")  # but can look up their ID

    client.post("/deadlines", json={"title": "Viva", "due_date": "2099-03-03"})
    assert "Viva" in telegram_bot.handle_text(555, "/deadlines")
    assert telegram_bot.handle_text(555, "hello") == "Hello!"
    telegram_bot.handle_update({"update_id": 1, "message": {"chat": {"id": 555}, "text": "hello"}})
    assert sent[-1]["text"] == "Hello!"

    monkeypatch.setattr(config, "TELEGRAM_ALLOWED_CHAT_IDS", {"888"})
    assert telegram_bot.handle_text(888, "hello") == "Hello!"  # allow-listed
    assert "private" in telegram_bot.handle_text(999, "hello").lower()


def test_calendar_export_import(client):
    from app import calendar_ics

    client.post("/deadlines", json={"title": "Exam, Part 1", "due_date": "2099-05-20"})
    url = client.get("/calendar/info").json()["url"]
    assert url.startswith("http://testserver/calendar/") and url.endswith(".ics")
    ics = client.get(url.replace("http://testserver", "")).text
    assert "BEGIN:VEVENT" in ics and "DTSTART;VALUE=DATE:20990520" in ics and "Exam\\, Part 1" in ics
    assert client.get("/calendar/wrong-token.ics").status_code == 404
    assert client.get("/calendar/info").json()["url"] == url  # token is stable

    sample = (
        "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nSUMMARY:Interview\r\nDTSTART:20990601T090000Z\r\nEND:VEVENT\r\n"
        "BEGIN:VEVENT\r\nSUMMARY:Old thing\r\nDTSTART;VALUE=DATE:20200101\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
    )
    r = client.post("/calendar/import", files={"file": ("c.ics", sample.encode())})
    assert r.json()["added"] == 1  # the past event is skipped
    r = client.post("/calendar/import", files={"file": ("c.ics", sample.encode())})
    assert r.json()["added"] == 0  # duplicates are skipped
    assert calendar_ics.parse_ics(ics)[0] == ("Exam, Part 1", "2099-05-20")
