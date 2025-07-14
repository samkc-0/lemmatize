from fastapi import APIRouter, status, HTTPException
from langdetect import detect, DetectorFactory
from pydantic import BaseModel
import spacy

DetectorFactory.seed = 0  # for consistent results


class TextIn(BaseModel):
    text: str


class Lemma(BaseModel):
    lemma: str
    pos: str
    language: str


MAX_INPUT_LENGTH = 140

router = APIRouter()
nlp = spacy.load("it_core_news_sm")


@router.post("/{language}")
def lemmatize(language: str, input: TextIn):
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
    doc = nlp(input.text)
    return [
        Lemma(lemma=tok.lemma_, pos=tok.pos_, language=tok.lang_)
        for tok in doc
        if not tok.is_punct and not tok.is_space
    ]
