from fastapi.testclient import TestClient
from fastapi import status
from sqlmodel import Session, select
from models import Lemma
from routers.lemmatizer import LemmaOut
from lemmatizer.main import app
import pytest


def test_lemmatization(user_input: str, test_lemmas: list[dict], client: TestClient):
    res = client.post("/lemmatize/it", json={"text": user_input})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    for item in test_lemmas:
        assert item in data


def test_input_text_too_long_should_fail(user_input: str, client: TestClient):
    too_long = user_input * 20
    res = client.post("/lemmatize/it", json={"text": too_long})
    assert res.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


def test_unsupported_language(client: TestClient):
    spanish = "Pero no he podido yo contravenir al orden de naturaleza; que en ella cada cosa engendra su semejante."
    res = client.post("/lemmatize/it", json={"text": spanish})
    assert res.status_code == status.HTTP_400_BAD_REQUEST


sample_input = {
    "text": "Ieri sembrava difficile correre rapidamente con qualcosa di verde dentro questo elegante spazio. Noi ci siamo riusciti comunque."
}

expected_lemmas_from_sample_input = [
    {"lemma": "ieri", "pos": "ADV", "language": "it"},
    {"lemma": "sembrare", "pos": "VERB", "language": "it"},
    {"lemma": "difficile", "pos": "ADJ", "language": "it"},
    {"lemma": "correre", "pos": "VERB", "language": "it"},
    {"lemma": "rapidamente", "pos": "ADV", "language": "it"},
    {"lemma": "con", "pos": "ADP", "language": "it"},
    {"lemma": "qualcosa", "pos": "PRON", "language": "it"},
    {"lemma": "di", "pos": "ADP", "language": "it"},
    {"lemma": "verde", "pos": "ADJ", "language": "it"},
    {"lemma": "dentro", "pos": "ADP", "language": "it"},
    {"lemma": "questo", "pos": "DET", "language": "it"},
    {"lemma": "elegante", "pos": "ADJ", "language": "it"},
    {"lemma": "spazio", "pos": "NOUN", "language": "it"},
    {"lemma": "noi", "pos": "PRON", "language": "it"},
    {"lemma": "riuscire", "pos": "VERB", "language": "it"},
]


def test_lemmatize_anonymous_user(client: TestClient):
    res = client.post("/lemmatize/it", json=sample_input)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    for lemma in expected_lemmas_from_sample_input:
        assert lemma in data


def test_lemmatize_authenticated_user(token: str, client: TestClient):
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/lemmatize/it", json=sample_input, headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data) > 0
    for lemma in expected_lemmas_from_sample_input:
        assert lemma in data


def test_lemmas_persist_for_logged_in_user(
    token: str,
    test_lemmas: list[dict],
    session: Session,
    client: TestClient,
):
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/lemmatize/it", json=sample_input, headers=headers)
    assert res.status_code == 200

    for lemma in expected_lemmas_from_sample_input:
        found = session.exec(
            select(Lemma).where(
                Lemma.lemma == lemma["lemma"],
                Lemma.pos == lemma["pos"],
                Lemma.language == lemma["language"],
            )
        ).first()
        assert found is not None


def test_lemmas_not_persisted_for_anon_user(session: Session, client: TestClient):
    res = client.post("/lemmatize/it", json=sample_input)
    assert res.status_code == 200

    for lemma in expected_lemmas_from_sample_input:
        found = session.exec(
            select(Lemma).where(
                Lemma.lemma == lemma["lemma"],
                Lemma.pos == lemma["pos"],
                Lemma.language == lemma["language"],
            )
        ).first()
        assert found is None
