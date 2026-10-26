import hmac
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from pydantic import BaseModel

from . import (
    agent,
    calendar_ics,
    config,
    db,
    memory,
    rag,
    scheduler,
    settings,
    skills,
    telegram_bot,
    tools,
)

USER = config.DEFAULT_USER

# What the "clear data" endpoint is allowed to wipe (fixed table names, never user input).
CLEARABLE = {
    "memories": "memories",
    "chat": "messages",
    "notes": "chunks",
    "notifications": "notifications",
}


@asynccontextmanager
async def lifespan(app):
    scheduler.start()
    telegram_bot.start()
    yield
    telegram_bot.stop()
    scheduler.stop()


app = FastAPI(title="StudyPilot", lifespan=lifespan)


class ChatIn(BaseModel):
    message: str


class MemoryIn(BaseModel):
    text: str


class DeadlineIn(BaseModel):
    title: str
    due_date: str  # YYYY-MM-DD


class SettingsIn(BaseModel):
    model: Optional[str] = None
    brief_hour: Optional[int] = None
    brief_minute: Optional[int] = None
    notifications_enabled: Optional[bool] = None
    theme: Optional[str] = None


@app.get("/health")
def health():
    return {
        "ok": True,
        "model": settings.model(),
        "nebius_key_set": bool(config.NEBIUS_API_KEY),
        "tavily_key_set": bool(config.TAVILY_API_KEY),
        "telegram_enabled": bool(config.TELEGRAM_BOT_TOKEN),
        "telegram_chats": len(telegram_bot.chats()),
    }


@app.get("/settings")
def get_settings():
    return settings.as_dict()


@app.put("/settings")
def put_settings(body: SettingsIn):
    try:
        result = settings.update(body.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(400, str(e))
    scheduler.reschedule()
    return result


@app.post("/data/clear/{what}")
def clear_data(what: str):
    table = CLEARABLE.get(what)
    if not table:
        raise HTTPException(404, f"Unknown data type. Use one of: {', '.join(CLEARABLE)}.")
    with db.conn() as c:
        c.execute(f"DELETE FROM {table} WHERE user_id=?", (USER,))
    return {"ok": True, "cleared": what}


@app.get("/skills")
def get_skills():
    return skills.catalog()


@app.post("/chat")
def chat(body: ChatIn):
    try:
        return agent.chat(USER, body.message)
    except Exception as e:
        raise HTTPException(502, f"LLM error: {e}")


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    n = rag.ingest(USER, file.filename, data)
    if n == 0:
        raise HTTPException(400, "Couldn't extract any text from that file.")
    return {"file": file.filename, "chunks": n}


@app.get("/documents")
def documents():
    return rag.list_documents(USER)


@app.get("/memories")
def memories():
    return memory.list_all(USER)


@app.post("/memories")
def add_memory(body: MemoryIn):
    return {"id": memory.add(USER, body.text)}


@app.delete("/memories/{mem_id}")
def delete_memory(mem_id: int):
    memory.delete(USER, mem_id)
    return {"ok": True}


@app.get("/deadlines")
def deadlines():
    return tools.list_deadlines(USER)


@app.post("/deadlines")
def add_deadline(body: DeadlineIn):
    try:
        return {"id": tools.add_deadline(USER, body.title, body.due_date)}
    except ValueError:
        raise HTTPException(400, "due_date must be in YYYY-MM-DD format.")


@app.post("/deadlines/{dl_id}/done")
def done(dl_id: int):
    tools.complete_deadline(USER, dl_id)
    return {"ok": True}


@app.get("/brief")
def brief():
    try:
        return {"brief": agent.chat(USER, "/brief", remember_facts=False)["reply"]}
    except Exception:
        return {"brief": scheduler.plain_brief(USER)}


@app.get("/notifications")
def notifications(unread: bool = True):
    q = "SELECT * FROM notifications WHERE user_id=?"
    if unread:
        q += " AND read=0"
    q += " ORDER BY id DESC LIMIT 20"
    with db.conn() as c:
        return [dict(r) for r in c.execute(q, (USER,)).fetchall()]


@app.post("/notifications/read")
def mark_read():
    with db.conn() as c:
        c.execute("UPDATE notifications SET read=1 WHERE user_id=?", (USER,))
    return {"ok": True}


# ---------- calendar ----------
@app.get("/calendar/info")
def calendar_info():
    return {"url": f"{config.PUBLIC_URL}/calendar/{calendar_ics.feed_token()}.ics"}


@app.get("/calendar/{token}.ics")
def calendar_feed(token: str):
    if not hmac.compare_digest(token, calendar_ics.feed_token()):
        raise HTTPException(404, "Calendar not found.")
    return Response(calendar_ics.build_ics(USER), media_type="text/calendar")


@app.post("/calendar/import")
async def calendar_import(file: UploadFile = File(...)):
    text = (await file.read()).decode("utf-8", errors="ignore")
    return {"added": calendar_ics.import_ics(USER, text)}
