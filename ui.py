import datetime
import html
import os

import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="StudyPilot", page_icon="🎓", layout="wide")

# ---------- theme ----------
LIGHT_VARS = """
--bg:#f5f6fb; --card:#ffffff; --border:#e8eaf2; --text:#111827; --muted:#6b7280; --input:#ffffff;
--note-bg:#eef2ff; --empty-bg:#fbfcff; --empty-border:#d7dbe8; --shadow:rgba(16,24,40,.04);
--red-bg:#fee2e2; --red-fg:#b91c1c; --amber-bg:#fef3c7; --amber-fg:#92400e;
--green-bg:#dcfce7; --green-fg:#166534; --gray-bg:#f3f4f6; --gray-fg:#374151;
--blue-bg:#e0e7ff; --blue-fg:#3730a3; --stripe:#d1d5db;
"""
DARK_VARS = """
--bg:#0e1120; --card:#171b2e; --border:#2a3050; --text:#e8eaf2; --muted:#9aa3b8; --input:#10142a;
--note-bg:#1f2650; --empty-bg:#131730; --empty-border:#2f3659; --shadow:rgba(0,0,0,.35);
--red-bg:#4c1d1d; --red-fg:#fca5a5; --amber-bg:#4a3512; --amber-fg:#fcd34d;
--green-bg:#14351f; --green-fg:#86efac; --gray-bg:#262b45; --gray-fg:#cbd5e1;
--blue-bg:#262d5c; --blue-fg:#a5b4fc; --stripe:#3a4163;
"""

BASE_CSS = """
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1180px; }

.hero {
    background: linear-gradient(120deg, #4f46e5 0%, #7c3aed 55%, #0ea5a4 100%);
    color: #fff; border-radius: 20px; padding: 1.7rem 2rem; margin-bottom: 1.1rem;
    box-shadow: 0 10px 30px rgba(79, 70, 229, .25);
}
.hero-title { font-size: 2rem; font-weight: 800; letter-spacing: -.5px; line-height: 1.15; color: #fff; }
.hero-sub { margin-top: .35rem; font-size: 1rem; opacity: .92; color: #fff; }
.badges { margin-top: .9rem; display: flex; gap: .5rem; flex-wrap: wrap; }
.badge {
    background: rgba(255,255,255,.18); border: 1px solid rgba(255,255,255,.3); color: #fff !important;
    padding: 3px 12px; border-radius: 999px; font-size: .78rem; font-weight: 600;
}

.stat { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 14px 18px;
        box-shadow: 0 1px 2px var(--shadow); }
.stat-label { font-size: .72rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }
.stat-value { font-size: 1.65rem; font-weight: 800; color: var(--text); margin-top: 2px;
              white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stat-hint { font-size: .8rem; color: var(--muted); margin-top: 1px; }

.dl { background: var(--card); border: 1px solid var(--border); border-left: 5px solid var(--stripe);
      border-radius: 14px; padding: 12px 16px; margin-bottom: 4px; }
.dl.red { border-left-color: #ef4444; }
.dl.amber { border-left-color: #f59e0b; }
.dl.green { border-left-color: #22c55e; }
.dl-title { font-weight: 700; color: var(--text); }
.dl-date { color: var(--muted); font-size: .85rem; margin-top: 2px; }

.chip { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: .74rem; font-weight: 700; margin-left: 8px; }
.chip.red { background: var(--red-bg); color: var(--red-fg); }
.chip.amber { background: var(--amber-bg); color: var(--amber-fg); }
.chip.green { background: var(--green-bg); color: var(--green-fg); }
.chip.gray { background: var(--gray-bg); color: var(--gray-fg); }
.chip.blue { background: var(--blue-bg); color: var(--blue-fg); }

.card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 16px 18px; margin-bottom: 10px; color: var(--text); }
.card-title { font-weight: 700; color: var(--text); margin-bottom: 4px; }
.muted { color: var(--muted); font-size: .88rem; }
.note { background: var(--note-bg); border-left: 4px solid #4f46e5; border-radius: 10px;
        padding: 10px 14px; margin-bottom: 8px; font-size: .88rem; color: var(--text); }
.empty { border: 2px dashed var(--empty-border); border-radius: 16px; padding: 28px; text-align: center;
         color: var(--muted); background: var(--empty-bg); }
.empty b { color: var(--text); }
.keyrow { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border); color: var(--text); }

.stTabs [role="tablist"] { gap: 8px; flex-wrap: wrap; }
.stTabs [role="tablist"]::before, .stTabs [role="tablist"]::after { display: none !important; }
.stTabs [role="tab"] { background: var(--card); border: 1px solid var(--border); border-radius: 999px; padding: 6px 18px; height: auto; }
.stTabs [role="tab"] > div + div { display: none; }
.stTabs [role="tab"][aria-selected="true"] { background: #4f46e5; border-color: #4f46e5; }
.stTabs [role="tab"][aria-selected="true"] p { color: #fff !important; }
.stApp [data-baseweb="input"]:focus-within, .stApp [data-baseweb="textarea"]:focus-within { border-color: #6366f1 !important; }
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"] { display: none !important; }
.stat-value.sm { font-size: 1.1rem; line-height: 1.3; white-space: normal; margin-top: 6px;
                 display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }

[data-testid="stChatMessage"] { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 12px 14px; }
.stButton > button, .stFormSubmitButton > button { border-radius: 10px; font-weight: 600; }
[data-testid="stSidebar"] { border-right: 1px solid var(--border); }
"""

# Streamlit's own widgets follow the base (light) theme, so dark mode restyles them explicitly.
DARK_OVERRIDES = """
.stApp { background: var(--bg); color: var(--text); }
[data-testid="stSidebar"] { background: var(--card); }
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp label, .stApp li,
.stApp [data-testid="stMarkdownContainer"], .stApp summary, .stApp summary span { color: var(--text); }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--muted) !important; }
.stApp input, .stApp textarea { background: var(--input) !important; color: var(--text) !important; }
.stApp input::placeholder, .stApp textarea::placeholder { color: var(--muted) !important; opacity: 1; }
.stApp [data-testid="stTextInputRootElement"], .stApp [data-testid="stTextAreaRootElement"],
.stApp [data-testid="stNumberInputContainer"], .stApp [data-testid="stDateInputField"],
.stApp [data-testid="stTimeInputField"], .stApp [data-testid="stTimeInput"] [data-baseweb="input"],
.stApp [data-testid="stDateInput"] [data-baseweb="input"] {
    background: var(--input) !important; border-color: var(--border) !important; color: var(--text) !important; }
.stApp [data-testid="stTextInputRootElement"]:focus-within, .stApp [data-testid="stTextAreaRootElement"]:focus-within,
.stApp [data-testid="stDateInputField"]:focus-within, .stApp [data-testid="stTimeInputField"]:focus-within {
    border-color: #6366f1 !important; }
.stApp [data-testid="stTimeInputTimeDisplay"] { background: var(--input) !important; border-color: var(--border) !important; }
.stApp [data-testid="stDateInputField"] span, .stApp [data-testid="stTimeInputField"] span,
.stApp [data-testid="stTimeInputTimeDisplay"] span { color: var(--text) !important; }
[data-testid="stChatInput"] textarea { background: transparent !important; }
.stApp [data-baseweb="input"], .stApp [data-baseweb="textarea"], .stApp [data-baseweb="base-input"],
.stApp [data-baseweb="select"] > div { background: var(--input) !important; border-color: var(--border) !important; color: var(--text) !important; }
.stApp [data-baseweb="select"] span, .stApp [data-baseweb="select"] div { color: var(--text); }
.stApp .stButton > button[kind="secondary"], .stApp .stFormSubmitButton > button[kind="secondaryFormSubmit"],
.stApp [data-testid="stBaseButton-secondary"], .stApp [data-testid="stBaseButton-secondaryFormSubmit"] {
    background: var(--input); color: var(--text); border: 1px solid var(--border);
}
.stApp [data-testid="stExpander"], .stApp [data-testid="stForm"] { background: var(--card); border-color: var(--border); }
.stApp [data-testid="stFileUploaderDropzone"] { background: var(--input); border-color: var(--border); }
.stApp [data-testid="stFileUploaderDropzone"] * { color: var(--muted); }
.stApp [data-testid="stCode"], .stApp [data-testid="stCode"] pre { background: var(--input); }
.stApp [data-testid="stCode"] code, .stApp [data-testid="stCode"] span { color: var(--text) !important; }
[data-testid="stBottom"], [data-testid="stBottom"] > div { background: var(--bg); }
[data-testid="stChatInput"], [data-testid="stChatInput"] > div { background: var(--card); border-color: var(--border); }
"""


def esc(x):
    return html.escape(str(x))


def api(method, path, quiet=False, **kw):
    try:
        r = requests.request(method, API + path, timeout=120, **kw)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        if not quiet:
            try:
                st.error(e.response.json().get("detail", str(e)))
            except Exception:
                st.error(f"API error: {e}")
    except Exception as e:
        if not quiet:
            st.error(f"Can't reach the API: {e}")
    return None


def urgency(days):
    if days is None:
        return "gray", "No date"
    if days < 0:
        return "red", f"Overdue by {-days}d"
    if days == 0:
        return "red", "Due today"
    if days <= 2:
        return "red", f"{days}d left"
    if days <= 7:
        return "amber", f"{days}d left"
    return "green", f"{days}d left"


def stat(label, value, hint="", small=False):
    cls = "stat-value sm" if small else "stat-value"
    return (
        f'<div class="stat"><div class="stat-label">{esc(label)}</div>'
        f'<div class="{cls}" title="{esc(value)}">{esc(value)}</div>'
        f'<div class="stat-hint">{esc(hint)}</div></div>'
    )


def empty(icon, title, text):
    st.markdown(
        f'<div class="empty"><div style="font-size:2rem">{icon}</div><b>{esc(title)}</b><br>{esc(text)}</div>',
        unsafe_allow_html=True,
    )


# ---------- load settings and apply the theme ----------
health = api("GET", "/health", quiet=True)
settings = api("GET", "/settings", quiet=True) if health else None
dark = bool(settings and settings.get("theme") == "dark")

css = f"<style>:root{{{DARK_VARS if dark else LIGHT_VARS}}}{BASE_CSS}{DARK_OVERRIDES if dark else ''}</style>"
st.markdown(css, unsafe_allow_html=True)

st.markdown(
    """
<div class="hero">
  <div class="hero-title">🎓 StudyPilot</div>
  <div class="hero-sub">Your private study and career assistant. It remembers you, reads your notes and keeps you on schedule.</div>
  <div class="badges">
    <span class="badge">Nebius Token Factory</span><span class="badge">NVIDIA Nemotron</span>
    <span class="badge">Memory</span><span class="badge">Notes (RAG)</span><span class="badge">Telegram</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

if not health or not settings:
    st.error("The API isn't running yet. Start it in another terminal, then refresh this page:")
    st.code("uvicorn app.main:app --port 8000", language="bash")
    st.stop()

# ---------- data ----------
deadlines = api("GET", "/deadlines") or []
documents = api("GET", "/documents") or []
memories = api("GET", "/memories") or []
notifications = api("GET", "/notifications") or []
skills = api("GET", "/skills") or {}

if "chat" not in st.session_state:
    st.session_state.chat = []


def ask(text):
    st.session_state.chat.append({"role": "user", "content": text})
    with st.spinner("Thinking..."):
        res = api("POST", "/chat", json={"message": text})
    if res:
        st.session_state.chat.append(
            {
                "role": "assistant",
                "content": res["reply"],
                "tools": [t["tool"] for t in res["tools_used"]],
                "memories": res["memories_saved"],
            }
        )
    else:
        st.session_state.chat.append(
            {"role": "assistant", "content": "Sorry, I couldn't get a response. Check the API terminal and your Nebius key."}
        )


# ---------- sidebar ----------
with st.sidebar:
    st.markdown("### 🎓 StudyPilot")
    st.caption(f"Model: {health.get('model', '')}")

    want_dark = st.toggle("🌙 Dark mode", value=dark)
    if want_dark != dark:
        api("PUT", "/settings", json={"theme": "dark" if want_dark else "light"})
        st.rerun()

    st.markdown("---")
    st.markdown("**Quick actions**")
    if st.button("☀️ Daily brief", use_container_width=True):
        st.session_state.queued = ("/brief", "sidebar")
    if st.button("📅 What's due soon?", use_container_width=True):
        st.session_state.queued = ("What deadlines do I have coming up, and what should I focus on first?", "sidebar")
    if st.button("🧠 What do you know about me?", use_container_width=True):
        st.session_state.queued = ("Summarize what you know about me and my goals.", "sidebar")

    st.markdown("---")
    st.markdown("**Notifications**")
    if notifications:
        for n in notifications:
            st.markdown(f'<div class="note">{esc(n["content"])}</div>', unsafe_allow_html=True)
        if st.button("Mark all as read", use_container_width=True):
            api("POST", "/notifications/read")
            st.rerun()
    else:
        st.caption("You're all caught up.")

# ---------- banner + stats ----------
if not health.get("nebius_key_set"):
    st.warning("NEBIUS_API_KEY is missing. Add it to your .env file, then restart the API. Chat won't work without it.")

nxt = deadlines[0] if deadlines else None
c1, c2, c3, c4 = st.columns(4)
c1.markdown(stat("Pending deadlines", len(deadlines), "Tracked for you"), unsafe_allow_html=True)
c2.markdown(
    stat(
        "Next up",
        nxt["title"] if nxt else "Nothing yet",
        urgency(nxt["days_left"])[1] if nxt else "Add a deadline",
        small=True,
    ),
    unsafe_allow_html=True,
)
c3.markdown(stat("Notes", len(documents), "Files in your library"), unsafe_allow_html=True)
c4.markdown(stat("Memories", len(memories), "Facts I remember"), unsafe_allow_html=True)
st.write("")

tab_chat, tab_dl, tab_notes, tab_mem, tab_int, tab_set = st.tabs(
    ["💬 Chat", "⏰ Deadlines", "📚 Notes", "🧠 Memory", "🔌 Integrations", "⚙️ Settings"]
)

# ---------- chat ----------
with tab_chat:
    queued = st.session_state.pop("queued", None)
    if queued:
        ask(queued[0])
        if queued[1] == "sidebar":
            st.toast("Reply ready in the Chat tab", icon="💬")

    if skills:
        with st.expander("⚡ Run a skill"):
            s1, s2, s3 = st.columns([2, 5, 1])
            name = s1.selectbox("Skill", list(skills), format_func=lambda n: f"/{n}", label_visibility="collapsed")
            arg = s2.text_input("Topic", placeholder=skills[name], label_visibility="collapsed", key="skill_arg")
            if s3.button("Run", use_container_width=True):
                st.session_state.queued = (f"/{name} {arg}".strip(), "chat")
                st.rerun()

    if not st.session_state.chat:
        empty("💬", "Ask me anything", "Try: \"My DSA exam is on 30 November\" or \"/plan Operating Systems\".")
    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            meta = []
            if m.get("tools"):
                meta.append("🔧 " + ", ".join(m["tools"]))
            if m.get("memories"):
                meta.append("🧠 Remembered: " + "; ".join(m["memories"]))
            if meta:
                st.caption("  ·  ".join(meta))

    if prompt := st.chat_input("Message StudyPilot..."):
        st.session_state.queued = (prompt, "chat")
        st.rerun()

# ---------- deadlines ----------
with tab_dl:
    left, right = st.columns([1, 2], gap="large")
    with left:
        st.markdown('<div class="card-title">Add a deadline</div>', unsafe_allow_html=True)
        with st.form("add_deadline", clear_on_submit=True):
            title = st.text_input("Title", placeholder="DSA exam, internship interview...")
            due = st.date_input("Date", datetime.date.today() + datetime.timedelta(days=7))
            if st.form_submit_button("Add deadline", use_container_width=True) and title.strip():
                api("POST", "/deadlines", json={"title": title.strip(), "due_date": due.isoformat()})
                st.rerun()
        st.caption("You can also just tell the assistant in chat, for example: \"Add my viva on 12 December\".")
    with right:
        if not deadlines:
            empty("🎯", "No pending deadlines", "Add one on the left, or tell the assistant in chat.")
        for d in deadlines:
            tone, label = urgency(d["days_left"])
            a, b = st.columns([6, 1.3])
            a.markdown(
                f'<div class="dl {tone}"><div class="dl-title">{esc(d["title"])}'
                f'<span class="chip {tone}">{esc(label)}</span></div>'
                f'<div class="dl-date">{esc(d["due_date"])}</div></div>',
                unsafe_allow_html=True,
            )
            if b.button("Done", key=f"done{d['id']}", use_container_width=True):
                api("POST", f"/deadlines/{d['id']}/done")
                st.rerun()

# ---------- notes ----------
with tab_notes:
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown('<div class="card-title">Upload your notes</div>', unsafe_allow_html=True)
        files = st.file_uploader("PDF, TXT or Markdown", type=["pdf", "txt", "md"], accept_multiple_files=True)
        if files and st.button("Process files", type="primary"):
            with st.spinner("Reading and indexing..."):
                for f in files:
                    res = api("POST", "/upload", files={"file": (f.name, f.getvalue())})
                    if res:
                        st.success(f"{res['file']}: {res['chunks']} chunks indexed")
            st.rerun()
        st.caption("Then ask things like \"Summarize my notes on sorting\" or use /quiz <topic>.")
    with right:
        st.markdown('<div class="card-title">Your library</div>', unsafe_allow_html=True)
        if not documents:
            empty("📄", "No notes yet", "Upload a file to start asking questions about it.")
        for d in documents:
            st.markdown(
                f'<div class="card"><b>📄 {esc(d["source"])}</b>'
                f'<span class="chip blue">{d["chunks"]} chunks</span></div>',
                unsafe_allow_html=True,
            )

# ---------- memory ----------
with tab_mem:
    st.markdown(
        '<div class="muted">This is what the assistant knows about you. Delete anything you don\'t want it to keep.</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    with st.form("add_memory", clear_on_submit=True):
        m1, m2 = st.columns([5, 1])
        fact = m1.text_input(
            "New fact", placeholder="I'm a 3rd-year AI/ML student aiming for a GenAI role", label_visibility="collapsed"
        )
        if m2.form_submit_button("Add", use_container_width=True) and fact.strip():
            api("POST", "/memories", json={"text": fact.strip()})
            st.rerun()
    if not memories:
        empty("🧠", "Nothing remembered yet", "Chat naturally and I'll pick up your goals and preferences.")
    for m in memories:
        a, b = st.columns([7, 1])
        a.markdown(f'<div class="card" style="margin-bottom:4px">{esc(m["text"])}</div>', unsafe_allow_html=True)
        if b.button("Delete", key=f"mem{m['id']}", use_container_width=True):
            api("DELETE", f"/memories/{m['id']}")
            st.rerun()

# ---------- integrations ----------
with tab_int:
    left, right = st.columns(2, gap="large")
    with left:
        enabled = health.get("telegram_enabled")
        chip = '<span class="chip green">Enabled</span>' if enabled else '<span class="chip gray">Off</span>'
        st.markdown(
            f'<div class="card"><div class="card-title">📱 Telegram {chip}</div>'
            f'<div class="muted">Chat with StudyPilot from your phone and get your daily brief and reminders there.</div></div>',
            unsafe_allow_html=True,
        )
        if enabled:
            n = health.get("telegram_chats", 0)
            if n:
                st.success(f"{n} chat connected.")
            else:
                st.info("Open your bot in Telegram and send /start. The first chat becomes the owner.")
            st.caption("Send /id to the bot to get your chat ID, and use TELEGRAM_ALLOWED_CHAT_IDS to allow more chats.")
        else:
            st.markdown(
                "1. Create a bot with **@BotFather** and copy the token\n"
                "2. Put it in `.env` as `TELEGRAM_BOT_TOKEN`\n"
                "3. Restart the API, then send `/start` to your bot"
            )
    with right:
        st.markdown(
            '<div class="card"><div class="card-title">📅 Calendar</div>'
            '<div class="muted">Show your deadlines in Google, Apple or Outlook Calendar.</div></div>',
            unsafe_allow_html=True,
        )
        info = api("GET", "/calendar/info")
        if info:
            st.write("Paste this private URL into Google Calendar, under *Other calendars > From URL*:")
            st.code(info["url"])
            st.caption(
                "Read-only, with a reminder one day before. It only works once the app is deployed publicly, "
                "and Google can take a few hours to refresh."
            )
        ics = st.file_uploader("Import an .ics file (future events become deadlines)", type=["ics"])
        if ics and st.button("Import calendar file"):
            res = api("POST", "/calendar/import", files={"file": (ics.name, ics.getvalue())})
            if res:
                st.success(f"{res['added']} deadlines added.")
                st.rerun()

# ---------- settings ----------
with tab_set:
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="card-title">Assistant & notifications</div>', unsafe_allow_html=True)
        with st.form("settings_form"):
            model = st.text_input(
                "Model name",
                value=settings["model"],
                help="Use the exact Nemotron model name from Nebius Token Factory > Models.",
            )
            brief_time = st.time_input(
                f"Daily brief time ({settings['timezone']})",
                value=datetime.time(settings["brief_hour"], settings["brief_minute"]),
            )
            notif = st.toggle("Send daily brief and deadline reminders", value=settings["notifications_enabled"])
            if st.form_submit_button("Save settings", type="primary", use_container_width=True):
                res = api(
                    "PUT",
                    "/settings",
                    json={
                        "model": model,
                        "brief_hour": brief_time.hour,
                        "brief_minute": brief_time.minute,
                        "notifications_enabled": notif,
                    },
                )
                if res:
                    st.success("Settings saved.")
                    st.rerun()
        st.caption("Appearance: use the Dark mode switch at the top of the sidebar.")

    with right:
        def key_row(label, ok):
            chip = '<span class="chip green">Set</span>' if ok else '<span class="chip red">Missing</span>'
            return f'<div class="keyrow"><span>{esc(label)}</span>{chip}</div>'

        st.markdown(
            '<div class="card"><div class="card-title">API keys</div>'
            '<div class="muted" style="margin-bottom:6px">Keys live in your .env file, never in the app. Restart the API after editing it.</div>'
            + key_row("NEBIUS_API_KEY (chat model)", health.get("nebius_key_set"))
            + key_row("TAVILY_API_KEY (web search)", health.get("tavily_key_set"))
            + key_row("TELEGRAM_BOT_TOKEN (optional)", health.get("telegram_enabled"))
            + "</div>",
            unsafe_allow_html=True,
        )

        with st.expander("🗑 Data & privacy"):
            options = {
                "Chat history": "chat",
                "Memories": "memories",
                "Notes library": "notes",
                "Notifications": "notifications",
            }
            choice = st.selectbox("What do you want to clear?", list(options))
            sure = st.checkbox("Yes, delete it permanently")
            if st.button("Clear selected data", disabled=not sure):
                if api("POST", f"/data/clear/{options[choice]}"):
                    if options[choice] == "chat":
                        st.session_state.chat = []
                    st.success(f"{choice} cleared.")
                    st.rerun()
