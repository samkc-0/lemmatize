import os
from sqlmodel import Session, create_engine
from dotenv import load_dotenv

load_dotenv()
db_name = os.getenv("DB_NAME")
if db_name is None:
    raise ValueError("must specify nonempty DB_NAME in .env")

sqlite_file_name = f"{db_name}.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)


def get_session():
    with Session(engine) as session:
        yield session
