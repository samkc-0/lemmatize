from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, select, col
from models import Headword, Word, Lexicon
from routers.users import hash_lexicon, hash_document

sample_input = {
    "text": "Ieri sembrava difficile correre rapidamente con qualcosa di verde dentro questo elegante spazio. Noi ci siamo riusciti comunque.",
    "language": "it",
}


expected_headwords_from_sample_input = [
    {"text": "ieri", "tag": "ADV", "language": "it"},
    {"text": "sembrare", "tag": "VERB", "language": "it"},
    {"text": "difficile", "tag": "ADJ", "language": "it"},
    {"text": "correre", "tag": "VERB", "language": "it"},
    {"text": "rapidamente", "tag": "ADV", "language": "it"},
    {"text": "con", "tag": "ADP", "language": "it"},
    {"text": "qualcosa", "tag": "PRON", "language": "it"},
    {"text": "di", "tag": "ADP", "language": "it"},
    {"text": "verde", "tag": "ADJ", "language": "it"},
    {"text": "dentro", "tag": "ADP", "language": "it"},
    {"text": "questo", "tag": "DET", "language": "it"},
    {"text": "elegante", "tag": "ADJ", "language": "it"},
    {"text": "spazio", "tag": "NOUN", "language": "it"},
    {"text": "noi", "tag": "PRON", "language": "it"},
    {"text": "riuscire", "tag": "VERB", "language": "it"},
]


def test_analyze_text_for_authenticated_user(
    token: str, client: TestClient, session: Session
):
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/auth/me", headers=headers)
    assert me_response.status_code == 200
    user_id = int(me_response.json()["id"])
    response = client.post("/users/upload", json=sample_input, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0, "response data must not be empty"
    headwords_table = session.exec(select(Headword.text)).all()
    assert len(headwords_table) > 0, "headwords table must not be empty"
    words = session.exec(
        select(Headword.text).join(Word, col(Word.headword_id) == Headword.id)
    ).all()
    assert words, "words table must not be empty"
    for headword in expected_headwords_from_sample_input:
        assert headword["text"] in headwords_table
        assert headword["text"] in words
    assert data["new_headwords_added"] > 0
    assert data["words_linked"] >= data["new_headwords_added"]
    assert data["reused_input"] == False
    assert data["reused_lexicon"] == False


def test_headwords_persist_for_logged_in_user(
    token: str,
    session: Session,
    client: TestClient,
):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/users/upload", json=sample_input, headers=headers)
    assert response.status_code == 200

    for headword in expected_headwords_from_sample_input:
        found = session.exec(
            select(Headword).where(
                Headword.text == headword["text"],
                Headword.tag == headword["tag"],
                Headword.language == headword["language"],
            )
        ).first()
        assert found is not None


def test_get_headwords_for_logged_in_user(
    token: str, client: TestClient, session: Session
):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/users/upload", json=sample_input, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    response = client.get("/users/words", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    text_only = [headword["text"] for headword in data]
    for headword in expected_headwords_from_sample_input:
        assert headword["text"] in text_only


def test_upload_with_same_lexicon_hash(
    token: str, client: TestClient, session: Session
):
    headers = {"Authorization": f"Bearer {token}"}
    # First upload to create lexicon
    response = client.post("/users/upload", json=sample_input, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    first_upload = response.json()

    # Second upload with different text but same words
    modified_input = sample_input.copy()
    modified_input["text"] = str(
        "Noi ci siamo riusciti comunque. Ieri sembrava difficile correre rapidamente con qualcosa di verde dentro questo elegante spazio."
    )

    response = client.post("/users/upload", json=modified_input, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    second_upload = response.json()

    assert second_upload["reused_lexicon"] == True
    assert second_upload["lexicon_id"] == first_upload["lexicon_id"]
    assert second_upload["new_headwords_added"] == 0


def test_upload_with_same_input_hash(token: str, client: TestClient, session: Session):
    headers = {"Authorization": f"Bearer {token}"}
    # First upload
    response = client.post("/users/upload", json=sample_input, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    first_upload = response.json()

    # Second upload with identical text
    response = client.post("/users/upload", json=sample_input, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    second_upload = response.json()

    assert second_upload["reused_input"] == True
    assert second_upload["lexicon_id"] == first_upload["lexicon_id"]
    assert second_upload["new_headwords_added"] == 0
