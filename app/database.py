from typing import Generator
from sqlmodel import create_engine, Session
from contextlib import contextmanager
from os import getenv
from app.models import *
from dotenv import load_dotenv

load_dotenv()

MODE = getenv("MODE", "DEV")


DB_USER = getenv("DB_USER")
DB_PASS = getenv("DB_PASS")
DB_HOST = getenv("DB_HOST")
DB_PORT = getenv("DB_PORT")
DB_NAME = getenv("DB_NAME")
DATA_BASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATA_BASE_URL, echo=False)


def get_db_session():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


def init_db():
    SQLModel.metadata.create_all(bind=engine)
