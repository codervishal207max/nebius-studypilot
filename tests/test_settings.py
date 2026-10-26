import datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    from app import config, llm

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "s.db"))
    monkeypatch.setattr(config, "TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setattr(llm, "embed", lambda texts: None)
    from app.main import app

    return TestClient(app)


def test_defaults_and_update(client):
    s = client.get("/settings").json()
    assert s["theme"] == "light" and s["notifications_enabled"] is True
    r = client.put(
        "/settings",
        json={"model": "nvidia/my-nemotron", "brief_hour": 21, "brief_minute": 30,
              "notifications_enabled": False, "theme": "dark"},
    )
    assert r.status_code == 200
    s = client.get("/settings").json()  # persisted
    assert s["model"] == "nvidia/my-nemotron"
    assert (s["brief_hour"], s["brief_minute"]) == (21, 30)
    assert s["notifications_enabled"] is False and s["theme"] == "dark"
    assert client.get("/health").json()["model"] == "nvidia/my-nemotron"


def test_invalid_settings_are_rejected_and_nothing_is_saved(client):
    assert client.put("/settings", json={"brief_hour": 25}).status_code == 400
    assert client.put("/settings", json={"brief_minute": 60}).status_code == 400
    assert client.put("/settings", json={"theme": "blue"}).status_code == 400
    assert client.put("/settings", json={"model": "   "}).status_code == 400
    # a bad value must not partially apply the valid ones
    assert client.put("/settings", json={"theme": "dark", "brief_hour": 99}).status_code == 400
    assert client.get("/settings").json()["theme"] == "light"


def test_model_setting_is_used_for_chat_calls(tmp_path, monkeypatch):
    from app import config, llm, settings

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "m.db"))
    seen = []

    def create(**kw):
        seen.append(kw)
        return SimpleNamespace(choices=[SimpleNamespace(message="ok")])

    fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(llm, "get_client", lambda: fake)
    llm.chat([{"role": "user", "content": "hi"}])
    assert seen[-1]["model"] == config.LLM_MODEL  # default from .env
    settings.update({"model": "custom/model"})
    llm.chat([{"role": "user", "content": "hi"}])
    assert seen[-1]["model"] == "custom/model"  # override from Settings


def test_notifications_toggle_pauses_reminders(client):
    from app import scheduler, tools

    soon = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    tools.add_deadline("default", "Quiz", soon)
    client.put("/settings", json={"notifications_enabled": False})
    scheduler.deadline_reminder_job()
    scheduler.daily_brief_job()
    assert client.get("/notifications").json() == []
    client.put("/settings", json={"notifications_enabled": True})
    scheduler.deadline_reminder_job()
    notes = client.get("/notifications").json()
    assert len(notes) == 1 and "Quiz" in notes[0]["content"]  # not lost while paused


def test_brief_time_reschedules_the_job(client):
    from app import scheduler

    sch = scheduler.start()
    try:
        client.put("/settings", json={"brief_hour": 9, "brief_minute": 45})
        trigger = str(sch.get_job(scheduler.BRIEF_JOB_ID).trigger)
        assert "hour='9'" in trigger and "minute='45'" in trigger
    finally:
        scheduler.stop()


def test_clear_data(client):
    client.post("/memories", json={"text": "Likes ML"})
    client.post("/upload", files={"file": ("n.txt", b"Some notes about sorting algorithms and more. " * 4)})
    client.post("/deadlines", json={"title": "Keep me", "due_date": "2099-01-01"})
    assert client.post("/data/clear/memories").status_code == 200
    assert client.post("/data/clear/notes").status_code == 200
    assert client.post("/data/clear/chat").status_code == 200
    assert client.get("/memories").json() == []
    assert client.get("/documents").json() == []
    assert len(client.get("/deadlines").json()) == 1  # deadlines are never cleared here
    assert client.post("/data/clear/deadlines").status_code == 404
    assert client.post("/data/clear/users;drop").status_code == 404


def test_key_flags_never_expose_secrets(client, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "NEBIUS_API_KEY", "super-secret-value")
    h = client.get("/health").json()
    assert h["nebius_key_set"] is True
    assert "super-secret-value" not in str(h)
