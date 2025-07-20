from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, select, col
from models import Lemma, Word, Lexicon
from routers.users import hash_lexicon, hash_user_input

sample_input = {
    "text": "Ieri sembrava difficile correre rapidamente con qualcosa di verde dentro questo elegante spazio. Noi ci siamo riusciti comunque.",
    "language": "it",
}


expected_lemmas_from_sample_input = [
    {"text": "ieri", "pos": "ADV", "language": "it"},
    {"text": "sembrare", "pos": "VERB", "language": "it"},
    {"text": "difficile", "pos": "ADJ", "language": "it"},
    {"text": "correre", "pos": "VERB", "language": "it"},
    {"text": "rapidamente", "pos": "ADV", "language": "it"},
    {"text": "con", "pos": "ADP", "language": "it"},
    {"text": "qualcosa", "pos": "PRON", "language": "it"},
    {"text": "di", "pos": "ADP", "language": "it"},
    {"text": "verde", "pos": "ADJ", "language": "it"},
    {"text": "dentro", "pos": "ADP", "language": "it"},
    {"text": "questo", "pos": "DET", "language": "it"},
    {"text": "elegante", "pos": "ADJ", "language": "it"},
    {"text": "spazio", "pos": "NOUN", "language": "it"},
    {"text": "noi", "pos": "PRON", "language": "it"},
    {"text": "riuscire", "pos": "VERB", "language": "it"},
]


def test_lemmatize_authenticated_user(token: str, client: TestClient, session: Session):
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/me", headers=headers)
    assert me_res.status_code == 200
    user_id = int(me_res.json()["id"])
    res = client.post("/me/upload", json=sample_input, headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data) > 0, "response data must not be empty"
    lemmas_table = session.exec(select(Lemma.text)).all()
    assert len(lemmas_table) > 0, "lemma table must not be empty"
    words = session.exec(
        select(Lemma.text).join(Word, col(Word.lemma_id) == Lemma.id)
    ).all()
    assert words, "words table must not be empty"
    for lemma in expected_lemmas_from_sample_input:
        assert lemma["text"] in lemmas_table
        assert lemma["text"] in words
    assert data["new_lemmas_added"] > 0
    assert data["words_linked"] >= data["new_lemmas_added"]
    assert data["reused_input"] == False
    assert data["reused_lexicon"] == False


def test_lemmas_persist_for_logged_in_user(
    token: str,
    session: Session,
    client: TestClient,
):
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/me/upload", json=sample_input, headers=headers)
    assert res.status_code == 200

    for lemma in expected_lemmas_from_sample_input:
        found = session.exec(
            select(Lemma).where(
                Lemma.text == lemma["text"],
                Lemma.pos == lemma["pos"],
                Lemma.language == lemma["language"],
            )
        ).first()
        assert found is not None


def test_get_lemmas_for_logged_in_user(
    token: str, client: TestClient, session: Session
):
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/me/upload", json=sample_input, headers=headers)
    assert res.status_code == status.HTTP_200_OK
    res = client.get("/me/lemmas", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    text_only = [lemma["text"] for lemma in data]
    for lemma in expected_lemmas_from_sample_input:
        assert lemma["text"] in text_only


def test_upload_with_same_lexicon_hash(
    token: str, client: TestClient, session: Session
):
    headers = {"Authorization": f"Bearer {token}"}
    # First upload to create lexicon
    res = client.post("/me/upload", json=sample_input, headers=headers)
    assert res.status_code == status.HTTP_200_OK
    first_upload = res.json()

    # Second upload with different text but same lemmas
    modified_input = sample_input.copy()
    # Create new text with same words but minimal changes to punctuation
    modified_input["text"] = str(
        "Noi ci siamo riusciti comunque. Ieri sembrava difficile correre rapidamente con qualcosa di verde dentro questo elegante spazio."
    )
    res = client.post("/me/upload", json=modified_input, headers=headers)
    assert res.status_code == status.HTTP_200_OK
    second_upload = res.json()

    assert second_upload["reused_lexicon"] == True
    assert second_upload["lexicon_id"] == first_upload["lexicon_id"]
    assert second_upload["new_lemmas_added"] == 0


def test_upload_with_same_input_hash(token: str, client: TestClient, session: Session):
    headers = {"Authorization": f"Bearer {token}"}
    # First upload
    res = client.post("/me/upload", json=sample_input, headers=headers)
    assert res.status_code == status.HTTP_200_OK
    first_upload = res.json()

    # Second upload with identical text
    res = client.post("/me/upload", json=sample_input, headers=headers)
    assert res.status_code == status.HTTP_200_OK
    second_upload = res.json()

    assert second_upload["reused_input"] == True
    assert second_upload["lexicon_id"] == first_upload["lexicon_id"]
    assert second_upload["new_lemmas_added"] == 0
