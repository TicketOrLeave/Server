from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from models import *


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

import os

try:
    os.remove(sqlite_file_name)
except:
    pass

engine = create_engine(sqlite_url, echo=True)
# SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Create all tables in SQLModel.metadata
SQLModel.metadata.create_all(bind=engine)

@contextmanager
def get_db() -> Session:
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()