from fastapi import status
from fastapi.testclient import TestClient
from lemmatizer.main import app


def test_create_user(client: TestClient):
    response = client.post(
        "/auth/register/", json={"username": "testuser", "password": "password-123"}
    )
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert data["username"] == "testuser"


def test_get_token(user: dict, client: TestClient):
    response = client.post("/auth/token", data=user)
    assert response.status_code == status.HTTP_200_OK, response.json()
    data = response.json()
    assert data["token_type"] == "bearer"


def test_user_session(user: dict, client: TestClient):
    token_response = client.post("/auth/token", data=user)
    assert token_response.status_code == status.HTTP_200_OK
    token_data = token_response.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/me", headers=headers)
    assert me_response.status_code == status.HTTP_200_OK
    me_data = me_response.json()
    assert me_data["username"] == user["username"]


def test_me_invalid_token(client: TestClient):
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_me_no_token(client: TestClient):
    response = client.get("/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_me_tampered_token(user: dict, client: TestClient):
    token_response = client.post("/auth/token", data=user)
    assert token_response.status_code == status.HTTP_200_OK
    token = token_response.json()["access_token"]
    tampered_token = token + "tamper"
    headers = {"Authorization": f"Bearer {tampered_token}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
