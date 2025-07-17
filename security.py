import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
from passlib.context import CryptContext


if os.getenv("TESTING"):
    password_context = CryptContext(schemes=["plaintext"])
else:
    password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hash: str) -> bool:
    return password_context.verify(password, hash)
