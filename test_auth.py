from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
import pytest
from db import get_session
from main import app
from models import User, UserCreate
import random
import os

os.environ["TESTING"] = "1"

test_users = [
    {"username": "alice", "password": "lemon2025"},
    {"username": "bob", "password": "rocket88"},
    {"username": "carol", "password": "panda321"},
    {"username": "dave", "password": "stone444"},
    {"username": "erin", "password": "maple999"},
    {"username": "frank", "password": "cloud721"},
    {"username": "grace", "password": "echo550"},
    {"username": "heidi", "password": "sunset131"},
    {"username": "ivan", "password": "pixel707"},
    {"username": "judy", "password": "river303"},
]


@pytest.fixture(name="user")
def random_user_fixture() -> dict:
    return random.choice(test_users)


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for payload in test_users:
            user_in = UserCreate(**payload)
            user = User.from_create(user_in)
            session.add(user)
            session.commit()
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


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
    me_response = client.get("/auth/me", headers=headers)
    assert me_response.status_code == status.HTTP_200_OK
    me_data = me_response.json()
    assert me_data["message"] == f"Hello {user['username']}"


def test_me_invalid_token(client: TestClient):
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_me_tampered_token(user: dict, client: TestClient):
    token_response = client.post("/auth/token", data=user)
    assert token_response.status_code == status.HTTP_200_OK
    token = token_response.json()["access_token"]
    tampered_token = token + "tamper"
    headers = {"Authorization": f"Bearer {tampered_token}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_me_no_token(client: TestClient):
    response = client.get("/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
