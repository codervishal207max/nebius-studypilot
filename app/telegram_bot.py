"""Telegram bot (long polling, no extra library needed).

Setup: get a token from @BotFather and set TELEGRAM_BOT_TOKEN. The bot starts with the server.

The bot is private. The first chat that messages it becomes the owner, or you can list
allowed chats in TELEGRAM_ALLOWED_CHAT_IDS. Send /id to the bot to see your chat ID.
"""
import re
import threading
import time

import requests

from . import agent, config, db, tools

_stop = threading.Event()
_thread = None

USER = config.DEFAULT_USER

HELP = (
    "I'm StudyPilot, your study and career assistant.\n\n"
    "Ask me anything, or use a skill:\n"
    "/brief - today's daily brief\n"
    "/plan <topic> - study plan\n"
    "/career <goal> - career roadmap\n"
    "/quiz <topic> - quiz from your notes\n"
    "/summarize <topic> - notes summary\n"
    "/deadlines - pending deadlines\n"
    "/id - show this chat's ID"
)

PRIVATE = "This bot is private. Ask its owner to add your chat ID to TELEGRAM_ALLOWED_CHAT_IDS."


def _call(method, **params):
    r = requests.post(
        f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/{method}",
        json=params,
        timeout=65,
    )
    return r.json()


def send(chat_id, text):
    text = text or "(empty reply)"
    for i in range(0, len(text), 4000):
        _call("sendMessage", chat_id=chat_id, text=text[i : i + 4000])


def chats():
    with db.conn() as c:
        return [r["chat_id"] for r in c.execute("SELECT chat_id FROM telegram_chats")]


def is_allowed(chat_id):
    """Known chats are allowed. Otherwise a chat is accepted if it is on the allow-list,
    or if there is no allow-list and no owner yet (first chat claims the bot)."""
    cid = str(chat_id)
    allowed = config.TELEGRAM_ALLOWED_CHAT_IDS
    with db.conn() as c:
        known = {r["chat_id"] for r in c.execute("SELECT chat_id FROM telegram_chats")}
        if cid in known:
            return True
        if (allowed and cid in allowed) or (not allowed and not known):
            c.execute("INSERT INTO telegram_chats (chat_id) VALUES (?)", (cid,))
            return True
    return False


def handle_text(chat_id, text):
    text = re.sub(r"^(/\w+)@\w+", r"\1", text.strip())  # /brief@MyBot -> /brief
    low = text.lower()
    if low == "/id":
        return f"This chat's ID is {chat_id}."
    if not is_allowed(chat_id):
        return PRIVATE
    if low in ("/start", "/help"):
        return HELP
    if low == "/deadlines":
        items = tools.list_deadlines(USER)
        if not items:
            return "No pending deadlines."
        return "\n".join(f"- {d['title']} ({d['due_date']}, {d['days_left']} days left)" for d in items)
    return agent.chat(USER, text)["reply"]


def handle_update(update):
    msg = update.get("message") or {}
    text = msg.get("text")
    if not text:
        return
    chat_id = msg["chat"]["id"]
    try:
        reply = handle_text(chat_id, text)
    except Exception as e:
        reply = f"Something went wrong: {e}"
    send(chat_id, reply)


def notify(text):
    """Send a message to the owner's Telegram chats (does nothing if no token is set)."""
    if not config.TELEGRAM_BOT_TOKEN:
        return
    for chat_id in chats():
        try:
            send(chat_id, text)
        except Exception:
            pass


def poll_loop():
    offset = 0
    while not _stop.is_set():
        try:
            data = _call("getUpdates", offset=offset, timeout=30)
            for u in data.get("result", []):
                offset = u["update_id"] + 1
                handle_update(u)
        except Exception:
            time.sleep(5)


def start():
    global _thread
    if not config.TELEGRAM_BOT_TOKEN or _thread:
        return None
    _stop.clear()
    _thread = threading.Thread(target=poll_loop, daemon=True, name="telegram-poll")
    _thread.start()
    return _thread


def stop():
    global _thread
    _stop.set()
    _thread = None
