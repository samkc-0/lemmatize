from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import spacy

nlp = spacy.load("it_core_news_sm")
app = FastAPI()


class TextIn(BaseModel):
    text: str


class Lemma(BaseModel):
    lemma: str
    pos: str
    language: str


MAX_INPUT_LENGTH = 140


@app.post("/lemmatize")
def lemmatize(input: TextIn):
    if len(input.text) > MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Input text too long. Must not exceed 100 characters.",
        )
    doc = nlp(input.text)
    return [
        Lemma(lemma=tok.lemma_, pos=tok.pos_, language=tok.lang_)
        for tok in doc
        if not tok.is_punct and not tok.is_space
    ]
