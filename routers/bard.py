from random import choice
from db import get_session
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from typing import List
from models import Headword, Lexicon, Story
from routers import lexicography
from routers.lexicography import TextIn
from utils import hash_lexicon

router = APIRouter()


class WordsIn(BaseModel):
    language: str
    required: List[Headword]
    allowed: List[Headword]


def generate_text(words_in: WordsIn, max_len=140) -> str:
    out = " ".join(w.text for w in words_in.required)
    allowed = [w.text for w in words_in.allowed]
    while len(out) < max_len:
        out = " ".join(choice(allowed))
    return out


@router.post("/generate")
async def generate(words_in: WordsIn, session: Session = Depends(get_session)):
    text = generate_text(words_in)
    vocab_used = await lexicography.analyze_text(TextIn(text, words_in.language))
    lexicon_hash = hash_lexicon(vocab_used)
    lexicon = Lexicon(hash=lexicon_hash)
    story = Story(text=text, language=words_in.language, lexicon_hash=lexicon.hash)
    session.add(story)
    session.add(lexicon)
    session.commit()
