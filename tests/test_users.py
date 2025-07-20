from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, select, col
from models import Lemma, UserLemma, Origin
from routers.users import hash_lemma_list, hash_user_input

sample_input = {
    "text": "Ieri sembrava difficile correre rapidamente con qualcosa di verde dentro questo elegante spazio. Noi ci siamo riusciti comunque.",
    "language": "it",
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


def test_lemmatize_authenticated_user(token: str, client: TestClient, session: Session):
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/me", headers=headers)
    assert me_res.status_code == 200
    user_id = int(me_res.json()["id"])
    res = client.post("/me/upload", json=sample_input, headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data) > 0, "response data must not be empty"
    lemmas_table = session.exec(select(Lemma.lemma)).all()
    assert len(lemmas_table) > 0, "lemma table must not be empty"
    user_lemmas = session.exec(
        select(Lemma.lemma).join(UserLemma, col(UserLemma.lemma_id) == Lemma.id)
    ).all()
    assert user_lemmas, "user lemmas table must not be empty"
    for lemma in expected_lemmas_from_sample_input:
        assert lemma["lemma"] in lemmas_table
        assert lemma["lemma"] in user_lemmas
    assert data["new_lemmas_added"] > 0
    assert data["user_lemmas_linked"] >= data["new_lemmas_added"]
    assert data["reused_input"] == False
    assert data["reused_origin"] == False


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
                Lemma.lemma == lemma["lemma"],
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
    text_only = [lemma["lemma"] for lemma in data]
    for lemma in expected_lemmas_from_sample_input:
        assert lemma["lemma"] in text_only


def test_upload_with_same_origin_hash(token: str, client: TestClient, session: Session):
    headers = {"Authorization": f"Bearer {token}"}
    # First upload to create origin
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

    assert second_upload["reused_origin"] == True
    assert second_upload["origin_id"] == first_upload["origin_id"]
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
    assert second_upload["origin_id"] == first_upload["origin_id"]
    assert second_upload["new_lemmas_added"] == 0
