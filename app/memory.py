import json
import re

from . import db, llm, vec


def add(user_id, text):
    text = text.strip()
    if not text:
        return None
    with db.conn() as c:
        exists = c.execute(
            "SELECT id FROM memories WHERE user_id=? AND lower(text)=lower(?)",
            (user_id, text),
        ).fetchone()
        if exists:
            return exists["id"]
        e = llm.embed([text])
        cur = c.execute(
            "INSERT INTO memories (user_id, text, embedding) VALUES (?,?,?)",
            (user_id, text, json.dumps(e[0]) if e else None),
        )
        return cur.lastrowid


def list_all(user_id):
    with db.conn() as c:
        rows = c.execute(
            "SELECT id, text, created_at FROM memories WHERE user_id=? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def delete(user_id, mem_id):
    with db.conn() as c:
        c.execute("DELETE FROM memories WHERE user_id=? AND id=?", (user_id, mem_id))


def relevant(user_id, query, k=5, recent=4):
    """Most relevant memories plus the latest ones, deduplicated."""
    with db.conn() as c:
        rows = c.execute("SELECT * FROM memories WHERE user_id=?", (user_id,)).fetchall()
    out = {r["id"]: r["text"] for r in vec.rank(query, rows, k)}
    for r in sorted(rows, key=lambda r: -r["id"])[:recent]:
        out.setdefault(r["id"], r["text"])
    return list(out.values())


EXTRACT_PROMPT = (
    "Below is a user's message. Extract only long-lived facts worth remembering "
    "(goals, course/branch, skills, exam/interview dates, preferences). "
    "Return only a JSON array of short English strings, e.g. [\"User is an AI/ML student\"]. "
    "If there is nothing worth remembering, return []."
)


def extract_and_store(user_id, user_message):
    if len(user_message) < 15 or user_message.startswith("/"):
        return []
    try:
        msg = llm.chat(
            [
                {"role": "system", "content": EXTRACT_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
            max_tokens=300,
        )
        raw = llm.clean(msg.content)
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        facts = json.loads(m.group(0)) if m else []
    except Exception:
        return []
    saved = []
    for f in facts[:5]:
        if isinstance(f, str) and f.strip():
            add(user_id, f)
            saved.append(f)
    return saved
