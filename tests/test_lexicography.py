from fastapi.testclient import TestClient
from fastapi import status


def test_lexicography(user_input: str, test_headwords: list[dict], client: TestClient):
    response = client.post("/lexicography", json={"text": user_input, "language": "it"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    for headword in test_headwords:
        assert headword in data


def test_input_text_too_long_should_fail(user_input: str, client: TestClient):
    too_long = user_input * 20
    response = client.post(
        "/lexicography",
        json={"text": too_long, "language": "it"},
    )
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


def test_unsupported_language(client: TestClient):
    spanish = "Pero no he podido yo contravenir al orden de naturaleza; que en ella cada cosa engendra su semejante."
    response = client.post("/lexicography", json={"text": spanish, "language": "es"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_specified_wrong_language(user_input: str, client: TestClient):
    response = client.post("/lexicography", json={"text": user_input, "language": "en"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_unknown_language(client: TestClient):
    response = client.post(
        "/lexicography",
        json={
            "text": "skjdfhaiweuyroeiwr93840938y3298hfasfoiuu32fj9",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_can_guess_language(
    user_input: str, test_headwords: list[dict], client: TestClient
):
    response = client.post("/lexicography", json={"text": user_input})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    for item in test_headwords:
        assert item in data
