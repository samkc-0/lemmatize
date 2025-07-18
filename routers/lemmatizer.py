from fastapi import APIRouter, status, HTTPException, Depends
from sqlmodel import Session, select
from langdetect import detect, DetectorFactory
from pydantic import BaseModel
from typing import Annotated
from db import get_session
from models import User, Lemma
from .auth import get_optional_user
import spacy

DetectorFactory.seed = 0  # for consistent results

IMPLEMETED_LANGUAGES = ["it"]


class TextIn(BaseModel):
    text: str


class LemmaOut(BaseModel):
    lemma: str
    pos: str
    language: str


MAX_INPUT_LENGTH = 140

router = APIRouter()
models = {"it": spacy.load("it_core_news_sm")}


@router.post("/{language}")
def lemmatize(
    language: str,
    input: TextIn,
    session: Session = Depends(get_session),
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
):
    if language not in IMPLEMETED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"language {language} not supported",
        )

    if len(input.text) > MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Input text too long. Must not exceed 100 characters.",
        )
    try:
        lang = detect(input.text)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="unable to detect language"
        )

    if lang != language:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"input must be in {language} (detected: {lang})",
        )
    doc = models[language](input.text)
    lemmas_out = [
        LemmaOut(lemma=tok.lemma_, pos=tok.pos_, language=tok.lang_)
        for tok in doc
        if not tok.is_punct and not tok.is_space
    ]

    if current_user:
        for lemma in lemmas_out:
            existing = session.exec(
                select(Lemma).where(
                    Lemma.lemma == lemma.lemma,
                    Lemma.pos == lemma.pos,
                    Lemma.language == lemma.language,
                )
            ).first()
            if not existing:
                session.add(Lemma(**lemma.model_dump()))
        session.commit()

    return lemmas_out
