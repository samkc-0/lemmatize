from fastapi.testclient import TestClient
from fastapi import status
from sqlmodel import Session, select
from models import Lemma
from routers.lemmatizer import LemmaOut
from lemmatizer.main import app


def test_lemmatization(user_input: str, test_lemmas: list[dict], client: TestClient):
    res = client.post("/lemmatize", json={"text": user_input, "language": "it"})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    for item in test_lemmas:
        assert item in data


def test_input_text_too_long_should_fail(user_input: str, client: TestClient):
    too_long = user_input * 20
    res = client.post(
        "/lemmatize",
        json={"text": too_long, "language": "it"},
    )
    assert res.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


def test_unsupported_language(client: TestClient):
    spanish = "Pero no he podido yo contravenir al orden de naturaleza; que en ella cada cosa engendra su semejante."
    res = client.post("/lemmatize", json={"text": spanish, "language": "es"})
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_specified_wrong_language(user_input: str, client: TestClient):
    res = client.post("/lemmatize", json={"text": user_input, "language": "en"})
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_unknown_language(client: TestClient):
    res = client.post(
        "/lemmatize",
        json={
            "text": "skjdfhaiweuyroeiwr93840938y3298hfasfoiuu32fj9",
        },
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_can_guess_language(
    user_input: str, test_lemmas: list[dict], client: TestClient
):
    res = client.post("/lemmatize", json={"text": user_input})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    for item in test_lemmas:
        assert item in data
