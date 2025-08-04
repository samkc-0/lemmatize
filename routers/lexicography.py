from fastapi import APIRouter, status, HTTPException
from fastapi.encoders import jsonable_encoder
from langdetect import detect_langs, DetectorFactory
from pydantic import BaseModel
from typing import Optional
import spacy
import json
from starlette.responses import StreamingResponse

DetectorFactory.seed = 0  # for consistent results


class TextIn(BaseModel):
    text: str
    language: Optional[str] = None


class HeadwordOut(BaseModel):
    text: str
    tag: str


MAX_INPUT_LENGTH = 140


def default_token_remap(tok) -> HeadwordOut:
    return HeadwordOut(text=tok.text, tag=tok.tag_)


router = APIRouter()
models = {
    "it": {
        "model": spacy.load("it_core_news_sm"),
        "mapper": default_token_remap,
    },
    "es": {
        "model": spacy.load("es_core_news_sm"),
        "mapper": default_token_remap,
    },
}

IMPLEMENTED_LANGUAGES = models.keys()


def stream_tokens(text: str, lang: str):
    nlp = models[lang]["model"]
    headword_mapper = models[lang]["mapper"]
    for doc in nlp.pipe(text.splitlines(), batch_size=10):
        for token in doc:
            if not token.is_punct and not token.is_space:
                yield json.dumps(
                    jsonable_encoder(headword_mapper(token)), ensure_ascii=False
                ) + "\n"


def validate_language(input: TextIn) -> str:

    try:
        detected_languages = [guess.lang for guess in detect_langs(input.text)]
        if len(detected_languages) == 0:
            raise
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
    if not isinstance(input.language, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="something went horribly wrong validating the input language",
        )
    return input.language


@router.post("/")
async def analyze_short_text(
    input: TextIn,
):
    lang: str = validate_language(input)
    if len(input.text) > MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Input text too long. Must not exceed {MAX_INPUT_LENGTH} characters.",
        )

    nlp = models[lang]
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


@router.post("/long")
async def analyze_long_text(
    input: TextIn,
):
    lang: str = validate_language(input)
    return StreamingResponse(
        stream_tokens(input.text, lang),
        media_type="application/x-ndjson",
    )
