import io
import json

from . import db, vec


def chunk_text(text, size=900, overlap=150):
    text = " ".join(text.split())
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i : i + size])
        i += size - overlap
    return [c for c in chunks if len(c.strip()) > 30]


def extract_text(filename, data: bytes):
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    return data.decode("utf-8", errors="ignore")


def ingest(user_id, filename, data: bytes):
    text = extract_text(filename, data)
    chunks = chunk_text(text)
    if not chunks:
        return 0
    embs = vec.embed_many(chunks)
    with db.conn() as c:
        c.execute("DELETE FROM chunks WHERE user_id=? AND source=?", (user_id, filename))
        for ch, e in zip(chunks, embs):
            c.execute(
                "INSERT INTO chunks (user_id, source, text, embedding) VALUES (?,?,?,?)",
                (user_id, filename, ch, json.dumps(e) if e else None),
            )
    return len(chunks)


def search(user_id, query, k=4):
    with db.conn() as c:
        rows = c.execute("SELECT * FROM chunks WHERE user_id=?", (user_id,)).fetchall()
    return vec.rank(query, rows, k)


def list_documents(user_id):
    with db.conn() as c:
        rows = c.execute(
            "SELECT source, COUNT(*) AS chunks FROM chunks WHERE user_id=? GROUP BY source",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]
