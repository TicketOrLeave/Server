from typing import Generator
from sqlmodel import create_engine, Session
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
    return
    with get_db() as db:
        user1 = User(name="user1", email="email1", image_url="url1")
        user2 = User(name="user2", email="email2", image_url="url2")
        user3 = User(
            name="emad", email="emadanwer.official@gmail.com", image_url="url3"
        )
        db.add_all([user1, user2, user3])
        db.commit()

        org1 = Organization(
            id="9a0e4beb-0233-48cb-a3e5-b39852c3abf5", name="org1", owner=user1.id
        )
        org2 = Organization(name="org2", owner=user2.id)
        db.add_all([org1, org2])
        db.commit()

        user_org1 = UserOrganization(
            user_id=user1.id, organization_id=org1.id, user_role=UserRole.creator
        )
        user_org2 = UserOrganization(
            user_id=user2.id, organization_id=org2.id, user_role=UserRole.creator
        )
        user3_org1 = UserOrganization(
            user_id=user3.id, organization_id=org1.id, user_role=UserRole.creator
        )
        user3_org2 = UserOrganization(
            user_id=user3.id, organization_id=org2.id, user_role=UserRole.creator
        )
        db.add_all([user_org1, user_org2, user3_org1, user3_org2])
        db.commit()
