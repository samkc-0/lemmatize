from fastapi import APIRouter, status, HTTPException
from langdetect import detect, detect_langs, DetectorFactory
from pydantic import BaseModel
from typing import Optional
import spacy

DetectorFactory.seed = 0  # for consistent results


class TextIn(BaseModel):
    text: str
    language: Optional[str] = None


class HeadwordOut(BaseModel):
    text: str
    tag: str
    language: str


MAX_INPUT_LENGTH = 140

router = APIRouter()
models = {
    "it": {
        "model": spacy.load("it_core_news_sm"),
        "mapper": lambda t: HeadwordOut(text=t.lemma_, tag=t.pos_, language=t.lang_),
    }
}
IMPLEMENTED_LANGUAGES = models.keys()


@router.post("/")
async def analyze_text(
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
    if input.language not in IMPLEMENTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"language '{input.language}' not supported",
        )

    if len(input.text) > MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Input text too long. Must not exceed {MAX_INPUT_LENGTH} characters.",
        )
    nlp = models[input.language]
    try:
        doc = nlp["model"](input.text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"error analyzing text: {e}",
        )
    headwords_out = [
        nlp["mapper"](tok) for tok in doc if not tok.is_punct and not tok.is_space
    ]
    return headwords_out
