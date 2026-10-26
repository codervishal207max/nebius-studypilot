import os

from dotenv import load_dotenv

load_dotenv()

NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "")
NEBIUS_BASE_URL = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "nvidia/Llama-3_1-Nemotron-Ultra-253B-v1")
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-multilingual-gemma2")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
DB_PATH = os.getenv("DB_PATH", "data/assistant.db")
BRIEF_HOUR = int(os.getenv("BRIEF_HOUR", "8"))
BRIEF_MINUTE = int(os.getenv("BRIEF_MINUTE", "0"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

# Single-user app: everything is stored under this one user id.
DEFAULT_USER = "default"

# Telegram bot (optional). Get a token from @BotFather.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# Comma-separated chat IDs allowed to use the bot. If empty, the first chat that
# messages the bot becomes its owner and everyone else is refused.
TELEGRAM_ALLOWED_CHAT_IDS = {
    x.strip() for x in os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").split(",") if x.strip()
}

# Public URL of the deployment (the calendar subscribe link is built from it)
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:8000").rstrip("/")
