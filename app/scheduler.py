from apscheduler.schedulers.background import BackgroundScheduler

from . import agent, config, db, settings, telegram_bot, tools

_scheduler = None
USER = config.DEFAULT_USER
BRIEF_JOB_ID = "daily_brief"


def plain_brief(user_id=USER):
    items = tools.list_deadlines(user_id)
    if not items:
        return "No pending deadlines today. Do a short revision session!"
    lines = [f"- {d['title']} ({d['due_date']}, {d['days_left']} days left)" for d in items[:7]]
    return "Pending deadlines:\n" + "\n".join(lines)


def push(kind, text, user_id=USER):
    """In-app notification plus a Telegram message to the owner's chats."""
    db.add_notification(user_id, kind, text)
    try:
        telegram_bot.notify(text)
    except Exception:
        pass


def daily_brief_job():
    if not settings.notifications_enabled():
        return
    try:
        text = agent.chat(USER, "/brief", remember_facts=False)["reply"]
    except Exception:
        text = plain_brief(USER)
    push("daily_brief", text)


def deadline_reminder_job():
    """Send one reminder when a deadline is 2 days away or less."""
    if not settings.notifications_enabled():
        return  # not marked as reminded, so it is sent once notifications are back on
    for d in tools.list_deadlines(USER):
        if d["days_left"] is not None and d["days_left"] <= 2 and not d["reminded"]:
            when = "today" if d["days_left"] <= 0 else f"in {d['days_left']} day(s)"
            push("reminder", f"Reminder: '{d['title']}' is {when} ({d['due_date']}).")
            with db.conn() as c:
                c.execute("UPDATE deadlines SET reminded=1 WHERE id=?", (d["id"],))


def start():
    global _scheduler
    if _scheduler:
        return _scheduler
    hour, minute = settings.brief_time()
    _scheduler = BackgroundScheduler(timezone=config.TIMEZONE)
    _scheduler.add_job(
        daily_brief_job, "cron", hour=hour, minute=minute, id=BRIEF_JOB_ID, replace_existing=True
    )
    _scheduler.add_job(deadline_reminder_job, "interval", hours=1)
    _scheduler.start()
    return _scheduler


def reschedule():
    """Apply a new daily brief time right away (called after Settings are saved)."""
    if not _scheduler:
        return
    hour, minute = settings.brief_time()
    _scheduler.reschedule_job(BRIEF_JOB_ID, trigger="cron", hour=hour, minute=minute)


def stop():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
