import hashlib
from routers.lexicography import HeadwordOut
from typing import List
import re


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[.,!?;:()\[\]\"']", "", text)  # light punctuation strip
    text = re.sub(r"\s+", " ", text)  # collapse whitespace
    return text


def hash_lexicon(headwords: List[HeadwordOut]) -> str:
    alphabetized = sorted(headwords, key=lambda l: (l.text, l.tag, l.language))
    serialized = "".join(f"{l.text}:{l.tag}:{l.language}" for l in alphabetized)
    return hashlib.sha256(serialized.encode()).hexdigest()


def hash_document(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()
