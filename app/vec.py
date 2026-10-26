import json
import re

import numpy as np

from . import llm


def tokens(s):
    return re.findall(r"\w+", s.lower())


def keyword_score(query, text):
    qt = set(tokens(query))
    tt = tokens(text)
    if not qt or not tt:
        return 0.0
    hits = sum(1 for w in tt if w in qt)
    return hits / (len(tt) ** 0.5)


def rank(query, rows, k=4):
    """rows: sqlite rows with 'text' and 'embedding'. Cosine similarity if embeddings exist, else keyword score."""
    rows = list(rows)
    if not rows:
        return []
    qv = None
    if all(r["embedding"] for r in rows):
        e = llm.embed([query])
        if e:
            qv = np.array(e[0])
    scored = []
    if qv is not None:
        for r in rows:
            v = np.array(json.loads(r["embedding"]))
            s = float(v @ qv / (np.linalg.norm(v) * np.linalg.norm(qv) + 1e-9))
            scored.append((s, r))
    else:
        scored = [(keyword_score(query, r["text"]), r) for r in rows]
    scored.sort(key=lambda x: -x[0])
    return [r for s, r in scored[:k] if s > 0]


def embed_many(texts, batch=32):
    out = []
    for i in range(0, len(texts), batch):
        e = llm.embed(texts[i : i + batch])
        if not e:
            return [None] * len(texts)
        out.extend(e)
    return out
