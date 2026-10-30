import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

from helpdesk.config import POLICIES_DIR

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "be", "do", "does", "did", "can", "could",
    "i", "my", "me", "we", "you", "your", "it", "of", "to", "in", "on", "at", "for",
    "and", "or", "what", "when", "how", "if", "with", "there", "this", "that", "so",
}

SYNONYMS = [
    (r"\be-?bikes?\b", "electric bike"),
    (r"\bcancel\w*", "cancel"),
    (r"\b(costs?|fees?)\b", "price"),
]


def tokenize(text: str) -> list[str]:
    text = text.lower()
    for pattern, replacement in SYNONYMS:
        text = re.sub(pattern, replacement, text)
    tokens = []
    for word in re.findall(r"[a-z0-9]+", text):
        if word in STOPWORDS:
            continue
        if len(word) > 4 and word.endswith("ing"):
            word = word[:-3]
        elif len(word) > 4 and word.endswith("ed"):
            word = word[:-2]
        elif len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        tokens.append(word)
    return tokens


def chunk_markdown(path: Path) -> list[dict]:
    chunks, heading, lines = [], None, []

    def flush():
        body = "\n".join(lines).strip()
        if heading and body:
            chunks.append({"source": path.name, "heading": heading, "text": body})

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            flush()
            heading, lines = line[3:].strip(), []
        elif line.startswith("# "):
            continue
        else:
            lines.append(line)
    flush()
    return chunks


class Index:
    def __init__(self, policies_dir: Path):
        self.chunks = []
        for path in sorted(Path(policies_dir).glob("*.md")):
            self.chunks.extend(chunk_markdown(path))
        self.docs = [Counter(tokenize(f"{c['heading']} {c['heading']} {c['text']}")) for c in self.chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = (sum(self.lengths) / len(self.lengths)) if self.lengths else 0
        self.doc_freq = Counter(t for d in self.docs for t in d)

    def search(self, query: str, top_k: int = 3, k1: float = 1.5, b: float = 0.75) -> list[dict]:
        n = len(self.docs)
        query_terms = set(tokenize(query))
        scored = []
        for i, doc in enumerate(self.docs):
            score = 0.0
            for term in query_terms:
                tf = doc.get(term, 0)
                if tf == 0:
                    continue
                df = self.doc_freq[term]
                idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
                norm = tf * (k1 + 1) / (tf + k1 * (1 - b + b * self.lengths[i] / self.avg_len))
                score += idf * norm
            if score > 0:
                scored.append((score, i))
        scored.sort(key=lambda s: -s[0])
        return [
            {**self.chunks[i], "score": round(score, 3)} for score, i in scored[:top_k]
        ]


@lru_cache(maxsize=4)
def _index(policies_dir: str) -> Index:
    return Index(Path(policies_dir))


def search_policies(query: str, top_k: int = 3) -> dict:
    try:
        top_k = max(1, min(int(top_k), 5))
        results = _index(str(POLICIES_DIR)).search(str(query or ""), top_k=top_k)
    except Exception as exc:
        return {"results": [], "message": f"Search failed: {exc}"}
    if not results:
        return {"results": [], "message": "No relevant passages found in the CityWheels documents."}
    return {"results": results}