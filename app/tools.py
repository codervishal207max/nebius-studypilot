import datetime
import json

import requests

from . import config, db, memory, rag

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "Search the user's uploaded notes/PDFs for relevant passages (RAG).",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Live web search (jobs, trends, tech news, roadmaps).",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_schedule",
            "description": "List pending deadlines/exams and how many days are left.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_deadline",
            "description": "Add a new deadline/exam/interview. due_date format: YYYY-MM-DD.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "due_date": {"type": "string"},
                },
                "required": ["title", "due_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_deadline",
            "description": "Mark a deadline as done (by id).",
            "parameters": {
                "type": "object",
                "properties": {"id": {"type": "integer"}},
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": "Remember an important fact about the user.",
            "parameters": {
                "type": "object",
                "properties": {"fact": {"type": "string"}},
                "required": ["fact"],
            },
        },
    },
]


def list_deadlines(user_id, include_done=False):
    q = "SELECT * FROM deadlines WHERE user_id=?"
    if not include_done:
        q += " AND done=0"
    q += " ORDER BY due_date"
    with db.conn() as c:
        rows = c.execute(q, (user_id,)).fetchall()
    today = datetime.date.today()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["days_left"] = (datetime.date.fromisoformat(r["due_date"]) - today).days
        except ValueError:
            d["days_left"] = None
        out.append(d)
    return out


def add_deadline(user_id, title, due_date):
    datetime.date.fromisoformat(due_date)  # validate
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO deadlines (user_id, title, due_date) VALUES (?,?,?)",
            (user_id, title, due_date),
        )
        return cur.lastrowid


def complete_deadline(user_id, dl_id):
    with db.conn() as c:
        c.execute("UPDATE deadlines SET done=1 WHERE user_id=? AND id=?", (user_id, dl_id))


def web_search(query):
    if not config.TAVILY_API_KEY:
        return "Web search is off (TAVILY_API_KEY is not set)."
    r = requests.post(
        "https://api.tavily.com/search",
        headers={"Authorization": f"Bearer {config.TAVILY_API_KEY}"},
        json={"query": query, "max_results": 5, "include_answer": True},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    lines = []
    if data.get("answer"):
        lines.append("Summary: " + data["answer"])
    for item in data.get("results", [])[:5]:
        lines.append(f"- {item.get('title')}: {item.get('content', '')[:300]} ({item.get('url')})")
    return "\n".join(lines) or "No results found."


def run_tool(user_id, name, args):
    try:
        if name == "search_notes":
            hits = rag.search(user_id, args["query"])
            if not hits:
                return "Nothing relevant found in your notes (maybe no file has been uploaded)."
            return "\n\n".join(f"[{h['source']}] {h['text']}" for h in hits)
        if name == "web_search":
            return web_search(args["query"])
        if name == "get_schedule":
            items = list_deadlines(user_id)
            if not items:
                return "No pending deadlines."
            return "\n".join(
                f"#{d['id']} {d['title']} - {d['due_date']} ({d['days_left']} days left)" for d in items
            )
        if name == "add_deadline":
            i = add_deadline(user_id, args["title"], args["due_date"])
            return f"Deadline added (id {i})."
        if name == "complete_deadline":
            complete_deadline(user_id, int(args["id"]))
            return "Marked as done."
        if name == "remember":
            memory.add(user_id, args["fact"])
            return "Remembered."
        return f"Unknown tool: {name}"
    except Exception as e:  # show tool errors to the LLM instead of crashing
        return f"Tool error ({name}): {e}"


def parse_args(raw):
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
