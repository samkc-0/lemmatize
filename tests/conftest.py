import pytest
import random
import sys
import os
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session
from sqlmodel.pool import StaticPool
from db import get_session, create_engine
from models import Headword, User, UserCreate
from lemmatizer.main import app
import uuid

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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

headwords = [
    {"text": "avere", "tag": "AUX", "language": "it"},
    {"text": "sempre", "tag": "ADV", "language": "it"},
    {"text": "trovare", "tag": "VERB", "language": "it"},
    {"text": "il", "tag": "DET", "language": "it"},
    {"text": "racconto", "tag": "NOUN", "language": "it"},
    {"text": "di", "tag": "ADP", "language": "it"},
    {"text": "Calvino", "tag": "PROPN", "language": "it"},
    {"text": "affascinanti", "tag": "ADJ", "language": "it"},
    {"text": "ogni", "tag": "DET", "language": "it"},
    {"text": "storia", "tag": "NOUN", "language": "it"},
    {"text": "essere", "tag": "AUX", "language": "it"},
    {"text": "uno", "tag": "DET", "language": "it"},
    {"text": "piccolo", "tag": "ADJ", "language": "it"},
    {"text": "universo", "tag": "NOUN", "language": "it"},
    {"text": "di", "tag": "ADP", "language": "it"},
    {"text": "possibilità", "tag": "NOUN", "language": "it"},
]


@pytest.fixture(scope="session", name="test_headwords")
def test_headwords() -> list[dict]:
    return headwords


@pytest.fixture(scope="session", name="user")
def random_user_fixture() -> dict:
    return random.choice(test_users)


@pytest.fixture(scope="function", name="session")
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


@pytest.fixture(scope="function", name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="session", name="user_input")
def user_input() -> str:
    with open("dummy.txt") as f:
        return f.read()


@pytest.fixture(scope="function", name="token")
def token(client: TestClient) -> str:
    # make a user
    username = f"testuser-{uuid.uuid4().hex[:8]}"
    password = "pass123"
    client.post("/auth/register/", json={"username": username, "password": password})
    response = client.post(
        "/auth/token", data={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]
