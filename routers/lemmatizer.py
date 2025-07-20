from fastapi import APIRouter, status, HTTPException
from langdetect import detect, detect_langs, DetectorFactory
from pydantic import BaseModel
from typing import Optional
import spacy

DetectorFactory.seed = 0  # for consistent results

IMPLEMETED_LANGUAGES = ["it"]


class TextIn(BaseModel):
    text: str
    language: Optional[str] = None


class LemmaOut(BaseModel):
    lemma: str
    pos: str
    language: str


MAX_INPUT_LENGTH = 140

router = APIRouter()
models = {"it": spacy.load("it_core_news_sm")}


@router.post("/")
async def lemmatize(
    input: TextIn,
):
    try:
        detected_languages = [l.lang for l in detect_langs(input.text)]
        most_likely_language = detected_languages[0]
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="unable to confirm input language",
        )
    if input.language is None:
        input.language = most_likely_language
    elif input.language not in detected_languages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"specified input language is {input.language}, but only detected '[{','.join(detected_languages)}]'",
        )
    if input.language not in models.keys():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"language '{input.language}' not supported",
        )

    if len(input.text) > MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Input text too long. Must not exceed {MAX_INPUT_LENGTH} characters.",
        )
    doc = models[input.language](input.text)
    lemmas_out = [
        LemmaOut(lemma=tok.lemma_, pos=tok.pos_, language=tok.lang_)
        for tok in doc
        if not tok.is_punct and not tok.is_space
    ]
    return lemmas_out
