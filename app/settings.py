"""User-editable settings, stored in the database.

Secrets (API keys, tokens) are NOT stored here. They live in the .env file.
Values saved here override the defaults from .env.
"""
from . import config, db

THEMES = ("light", "dark")


def _get(key, default):
    v = db.get_setting(key)
    return default if v is None or v == "" else v


def model():
    return str(_get("llm_model", config.LLM_MODEL))


def brief_time():
    try:
        h = int(_get("brief_hour", config.BRIEF_HOUR))
        m = int(_get("brief_minute", config.BRIEF_MINUTE))
    except ValueError:
        h, m = config.BRIEF_HOUR, config.BRIEF_MINUTE
    return h, m


def notifications_enabled():
    return str(_get("notifications_enabled", "1")) == "1"


def theme():
    t = str(_get("theme", "light"))
    return t if t in THEMES else "light"


def as_dict():
    h, m = brief_time()
    return {
        "model": model(),
        "brief_hour": h,
        "brief_minute": m,
        "notifications_enabled": notifications_enabled(),
        "theme": theme(),
        "timezone": config.TIMEZONE,
    }


def update(data):
    """Validates everything first, then saves. Raises ValueError on bad input."""
    out = {}
    if "model" in data:
        v = str(data["model"]).strip()
        if not v or len(v) > 200:
            raise ValueError("Model name can't be empty.")
        out["llm_model"] = v
    if "brief_hour" in data:
        h = int(data["brief_hour"])
        if not 0 <= h <= 23:
            raise ValueError("Hour must be between 0 and 23.")
        out["brief_hour"] = str(h)
    if "brief_minute" in data:
        m = int(data["brief_minute"])
        if not 0 <= m <= 59:
            raise ValueError("Minute must be between 0 and 59.")
        out["brief_minute"] = str(m)
    if "notifications_enabled" in data:
        out["notifications_enabled"] = "1" if data["notifications_enabled"] else "0"
    if "theme" in data:
        if data["theme"] not in THEMES:
            raise ValueError("Theme must be 'light' or 'dark'.")
        out["theme"] = data["theme"]
    for k, v in out.items():
        db.set_setting(k, v)
    return as_dict()
