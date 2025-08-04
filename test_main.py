from fastapi.testclient import TestClient
from fastapi import status
import pytest
from routers.lexicography import TextIn
from main import app
import json


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def headwords() -> list[dict]:
    return [
        {"text": "Qué", "tag": "PRON"},
        {"text": "significa", "tag": "VERB"},
        {"text": "escalada", "tag": "ADJ"},
        {"text": "de", "tag": "ADP"},
        {"text": "privilegios", "tag": "NOUN"},
        {"text": "En", "tag": "ADP"},
        {"text": "esencia", "tag": "NOUN"},
        {"text": "la", "tag": "DET"},
        {"text": "escalada", "tag": "NOUN"},
        {"text": "de", "tag": "ADP"},
        {"text": "privilegios", "tag": "NOUN"},
        {"text": "suele", "tag": "VERB"},
        {"text": "implicar", "tag": "VERB"},
    ]


@pytest.fixture(scope="module")
def user_input():
    user_input = TextIn(
        **{
            "text": "¿Qué significa “escalada de privilegios”?, En esencia, la escalada de privilegios suele implicar pasar de una cuenta con permisos más bajos a una con permisos más altos. En términos más técnicos, consiste en explotar una vulnerabilidad, un fallo de diseño o un error de configuración en un sistema operativo o aplicación para obtener acceso no autorizado a recursos que normalmente están restringidos a los usuarios., ¿Por qué es importante?, Es raro, al realizar una prueba de penetración real, obtener un punto de apoyo (acceso inicial) que otorgue acceso administrativo directo. La escalada de privilegios es crucial porque permite obtener niveles de acceso de administrador del sistema, lo que permite realizar acciones como: Restablecer contraseñas, Evitar los controles de acceso para comprometer datos protegidos, Edición de configuraciones de software, Habilitando la persistencia, Cambiar los privilegios de usuarios existentes (o nuevos), Ejecutar cualquier comando administrativo",
            "language": "es",
        }
    )
    return user_input


@pytest.fixture(scope="module")
def short_user_input(user_input: TextIn):
    short_text = " ".join(user_input.text[:100].split(" ")[:-1]) + " (...)"
    return TextIn(**{"text": short_text, "language": user_input.language})


def test_lexicography(
    short_user_input: TextIn, headwords: list[dict], client: TestClient
):
    response = client.post("/lexicography", json=short_user_input.model_dump())
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    for headword in headwords:
        assert headword in data


def test_input_text_too_long_should_fail(user_input: TextIn, client: TestClient):
    response = client.post(
        "/lexicography",
        json=user_input.model_dump(),
    )
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


def test_unsupported_language(client: TestClient):
    # quenya, because this app should never support quenya
    quenya = "i elenion ancalima, ná calima órenyallo."
    response = client.post("/lexicography", json={"text": quenya, "language": "qya"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_specified_wrong_language(short_user_input: TextIn, client: TestClient):
    payload_with_wrong_language = short_user_input.model_dump().copy()
    payload_with_wrong_language["language"] = "en"
    response = client.post("/lexicography", json=payload_with_wrong_language)
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
    short_user_input: TextIn, headwords: list[dict], client: TestClient
):
    response = client.post("/lexicography", json=short_user_input.model_dump())
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    for item in headwords:
        assert item in data


def test_streamed_analysis(
    headwords: list[dict], user_input: TextIn, client: TestClient
):
    response = client.post(
        "/lexicography/long",
        json=user_input.model_dump(),
    )
    assert response.status_code == status.HTTP_200_OK
    data = list(json.loads(line) for line in response.iter_lines())
    for item in headwords:
        assert item in data
