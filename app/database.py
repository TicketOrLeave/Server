from typing import Generator
from sqlmodel import create_engine, SQLModel, Session
from contextlib import contextmanager
from os import remove, getenv
from app.models import *


MODE = getenv("MODE", "dev")

if MODE == "dev":
    sqlite_file_name = "database.db"
    DATA_BASE_URL = f"sqlite:///{sqlite_file_name}"

    try:
        remove(sqlite_file_name)
    except:
        pass
else:
    DB_USER = getenv("DB_USER")
    DB_PASS = getenv("DB_PASS")
    DB_HOST = getenv("DB_HOST")
    DB_PORT = getenv("DB_PORT")
    DB_NAME = getenv("DB_NAME")
    DATA_BASE_URL: str = (
        f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )


engine = create_engine(DATA_BASE_URL, echo=True)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
