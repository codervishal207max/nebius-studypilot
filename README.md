# 🎓 StudyPilot: Personal Study & Career Assistant
Nebius x NVIDIA Global AI Hackathon 2026, **Personal AI track**

A private, always-on assistant with **memory**, **reusable skills** and **user-controlled tools**.
It runs from a web UI and from Telegram, and always replies in clear English.

## Features
| Feature | Where |
|---|---|
| Persistent memory (auto-extracted, editable) | `app/memory.py` |
| RAG over your notes and PDFs (embeddings, keyword fallback) | `app/rag.py`, `app/vec.py` |
| Tools: search_notes, web_search (Tavily), deadlines, remember | `app/tools.py` |
| Skills: `/brief /plan /career /quiz /summarize` | `app/skills.py` |
| Daily brief and a reminder 2 days before each deadline (in-app + Telegram) | `app/scheduler.py` |
| Private Telegram bot (long polling) | `app/telegram_bot.py` |
| Calendar sync (ICS feed and ICS import) | `app/calendar_ics.py` |
| Settings tab: model name, daily brief time, notifications on/off, clear data | `app/settings.py` |
| Light and dark theme (switch in the sidebar) | `ui.py` |
| Nemotron via Nebius Token Factory (OpenAI-compatible) | `app/llm.py` |

There is no login: it is a single-user app. If you deploy it publicly, put it behind your own access control.

## Where to put your API keys
**Only in the `.env` file** in the project folder. No key is ever written in the code.

```bash
cp .env.example .env             # Windows: copy .env.example .env
```

| Variable in `.env` | What it is | Where to get it |
|---|---|---|
| `NEBIUS_API_KEY` | Required. Used for the chat model and embeddings | Nebius Token Factory console, API keys |
| `LLM_MODEL` | Required. The exact Nemotron model name | Token Factory console, Models |
| `TAVILY_API_KEY` | Web search (`/career`, live info) | tavily.com |
| `TELEGRAM_BOT_TOKEN` | Optional. Telegram bot | @BotFather in Telegram |

How the code uses them:
- `app/config.py` reads `.env` (via python-dotenv) into `NEBIUS_API_KEY`, `LLM_MODEL`, `TAVILY_API_KEY`, `TELEGRAM_BOT_TOKEN`.
- `app/llm.py` builds the client (`OpenAI(api_key=config.NEBIUS_API_KEY, base_url=config.NEBIUS_BASE_URL)`) and calls the model.
- `app/tools.py` sends `TAVILY_API_KEY` as a bearer token to Tavily.

Restart the API after editing `.env`. The **Settings > API keys** panel in the app shows whether each key is set (never the value).
Never commit `.env` or share it. It is already in `.gitignore`. If a key leaks, rotate it in the provider's console.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
Then create `.env` as described above.

## Run
Open two terminals in the project folder (activate the venv in both):
```bash
uvicorn app.main:app --port 8000
streamlit run ui.py
```
Then open http://localhost:8501.
Tests (no API key needed): `pytest -q`

## Settings tab
- **Model name:** change the model without editing `.env` (it overrides `LLM_MODEL`).
- **Daily brief time:** applied immediately, no restart needed.
- **Notifications:** turn the daily brief and reminders off and on. Reminders that were missed while paused are sent when you turn them back on.
- **Data and privacy:** clear chat history, memories, notes or notifications. Deadlines are never cleared from here.
- **Dark mode:** the switch at the top of the sidebar. Your choice is saved.

## Telegram bot
1. In Telegram, talk to **@BotFather**, send `/newbot` and copy the token.
2. Put it in `.env` as `TELEGRAM_BOT_TOKEN=...` and restart the API (the bot starts with it).
3. Open your bot and send `/start`. **The first chat to message the bot becomes its owner**, and everyone else is refused.
4. To allow more chats, send `/id` to the bot and add the IDs to `TELEGRAM_ALLOWED_CHAT_IDS` (comma-separated).
5. Chat normally, or use `/brief`, `/plan DSA`, `/deadlines`. The daily brief and reminders are pushed to the owner's chats.

## Calendar
- **App to Google Calendar:** the Integrations tab shows a private feed URL. In Google Calendar open *Other calendars > From URL* and paste it. Your deadlines appear with a reminder one day before.
  - It is **one-way and read-only**, and it only works when the app is **publicly deployed** (set `PUBLIC_URL`). Google refreshes subscribed calendars every few hours.
  - Apple Calendar and Outlook can subscribe to the same URL.
- **Calendar to app:** export an `.ics` file from any calendar and import it in the Integrations tab. Future events become deadlines (duplicates are skipped).

## Deploy (Nebius Serverless / Docker)
```bash
docker build -t studypilot .
docker run -p 8000:8000 -p 8501:8501 --env-file .env studypilot
```
Push the image to a registry and deploy it on Nebius Serverless. Expose ports 8000 (API) and 8501 (UI),
set `PUBLIC_URL` to the public API URL, and mount a volume at `/srv/data` for SQLite.
Pass the keys as environment variables or secrets in the platform, not inside the image.

## Demo script (2-3 minutes)
1. Upload a notes PDF, then run `/summarize <topic>`
2. Say "My DSA exam is on 30 November": the deadline is added and your goal is remembered
3. `/plan DSA`: a plan built from your notes and deadlines
4. `/career ML engineer`: a roadmap with live web search
5. Show the same assistant on Telegram
6. Show the deadline in your calendar, flip to dark mode, then show Settings and the Memory tab

## Submission checklist (deadline: 30 Oct 2026, 10:00 AM PDT)
- [ ] Register on Devpost and submit the project
- [ ] Mention Nebius Token Factory and NVIDIA Nemotron in the write-up
- [ ] Public GitHub repo with this README (check that `.env` is NOT in it)
- [ ] Demo video (2-3 minutes)
- [ ] Track: Personal AI

## Limitations
- Single user, no login. SQLite is meant for a single instance.
- The Telegram bot uses long polling, so run only one instance.
