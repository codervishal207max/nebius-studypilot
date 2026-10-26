import datetime

from . import db, llm, memory, skills, tools

MAX_STEPS = 5

SYSTEM = """You are StudyPilot, a personal Study Assistant and Career Advisor.

Language: always reply in clear, proper English, even if the user writes in another language \
or mixes languages (for example Hinglish). Do not use Hindi or Hinglish words in your replies.
Style: concise, practical and actionable. Use short paragraphs or bullet points, no filler.
Today's date: {today}.

Use tools when needed: search_notes (the user's notes), web_search (live info), \
get_schedule / add_deadline / complete_deadline (deadlines), remember (important facts).
If the user gives a relative date ("tomorrow", "next Friday"), convert it to YYYY-MM-DD \
before calling add_deadline.
When you answer from the user's notes, mention the source file name.

What you know about the user:
{memories}
"""


def _history(user_id, n=10):
    with db.conn() as c:
        rows = c.execute(
            "SELECT role, content FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, n),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def _save(user_id, role, content):
    with db.conn() as c:
        c.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?,?,?)",
            (user_id, role, content),
        )


def chat(user_id, message, remember_facts=True):
    prompt = skills.expand(message)
    mems = memory.relevant(user_id, message)
    system = SYSTEM.format(
        today=datetime.date.today().isoformat(),
        memories="\n".join(f"- {m}" for m in mems) or "(nothing yet)",
    )
    history = _history(user_id)
    messages = [{"role": "system", "content": system}, *history, {"role": "user", "content": prompt}]
    used = []

    reply = ""
    for _ in range(MAX_STEPS):
        msg = llm.chat(messages, tools=tools.TOOL_SCHEMAS)
        calls = getattr(msg, "tool_calls", None)
        if not calls:
            reply = llm.clean(msg.content)
            break
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in calls
                ],
            }
        )
        for tc in calls:
            args = tools.parse_args(tc.function.arguments)
            result = tools.run_tool(user_id, tc.function.name, args)
            used.append({"tool": tc.function.name, "args": args})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    else:
        reply = "Sorry, I couldn't finish that. Please try again."

    _save(user_id, "user", message)
    _save(user_id, "assistant", reply)
    saved = memory.extract_and_store(user_id, message) if remember_facts else []
    return {"reply": reply, "tools_used": used, "memories_saved": saved}
