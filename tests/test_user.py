from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

another_sample_input = {
    "text": "Il gatto nero attraversò silenziosamente il giardino illuminato dalla luna, mentre il cane abbaiava in lontananza."
}

expected_lemmas_from_another_sample = [
    {"lemma": "il", "pos": "DET", "language": "it"},
    {"lemma": "gatto", "pos": "NOUN", "language": "it"},
    {"lemma": "nero", "pos": "ADJ", "language": "it"},
    {"lemma": "attraversare", "pos": "VERB", "language": "it"},
    {"lemma": "silenziosamente", "pos": "ADV", "language": "it"},
    {"lemma": "il", "pos": "DET", "language": "it"},
    {"lemma": "giardino", "pos": "NOUN", "language": "it"},
    {"lemma": "illuminare", "pos": "VERB", "language": "it"},
    {"lemma": "dalla", "pos": "ADP", "language": "it"},
    {"lemma": "luna", "pos": "NOUN", "language": "it"},
    {"lemma": "mentre", "pos": "SCONJ", "language": "it"},
    {"lemma": "il", "pos": "DET", "language": "it"},
    {"lemma": "cane", "pos": "NOUN", "language": "it"},
    {"lemma": "abbaiare", "pos": "VERB", "language": "it"},
    {"lemma": "in", "pos": "ADP", "language": "it"},
    {"lemma": "lontananza", "pos": "NOUN", "language": "it"},
]


def test_get_lemmas_for_logged_in_user(
    token: str, client: TestClient, session: Session
):
    client.post("/lemmatize/it", json=another_sample_input)
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/me/lemmas", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    for lemma in expected_lemmas_from_another_sample:
        assert lemma in data
