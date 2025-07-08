from fastapi.testclient import TestClient
from fastapi import status
from main import app
import pytest

client = TestClient(app)


@pytest.fixture(name="user_input")
def user_input() -> str:
    with open("dummy.txt") as f:
        return f.read()


def test_lemmatization(user_input: str):
    res = client.post("/italian", json={"text": user_input})
    assert res.status_code == status.HTTP_200_OK
    lemmas = [
        {"lemma": "avere", "pos": "AUX", "language": "it"},
        {"lemma": "sempre", "pos": "ADV", "language": "it"},
        {"lemma": "trovare", "pos": "VERB", "language": "it"},
        {"lemma": "il", "pos": "DET", "language": "it"},
        {"lemma": "racconto", "pos": "NOUN", "language": "it"},
        {"lemma": "di", "pos": "ADP", "language": "it"},
        {"lemma": "Calvino", "pos": "PROPN", "language": "it"},
        {"lemma": "affascinanti", "pos": "ADJ", "language": "it"},
        {"lemma": "ogni", "pos": "DET", "language": "it"},
        {"lemma": "storia", "pos": "NOUN", "language": "it"},
        {"lemma": "essere", "pos": "AUX", "language": "it"},
        {"lemma": "uno", "pos": "DET", "language": "it"},
        {"lemma": "piccolo", "pos": "ADJ", "language": "it"},
        {"lemma": "universo", "pos": "NOUN", "language": "it"},
        {"lemma": "di", "pos": "ADP", "language": "it"},
        {"lemma": "possibilità", "pos": "NOUN", "language": "it"},
    ]
    data = res.json()
    for item in lemmas:
        assert item in data


def test_input_text_too_long_should_fail(user_input: str):
    too_long = user_input * 20
    res = client.post("/italian", json={"text": too_long})
    assert res.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


def test_unsupported_language():
    spanish = "Pero no he podido yo contravenir al orden de naturaleza; que en ella cada cosa engendra su semejante."
    res = client.post("/italian", json={"text": spanish})
    assert res.status_code == status.HTTP_400_BAD_REQUEST
