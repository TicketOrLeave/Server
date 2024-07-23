from cryptography.hazmat.primitives import hashes
from fastapi_nextauth_jwt.operations import derive_key
from fastapi.testclient import TestClient
from os import environ, remove
import time
from jose import jwe
import json
from sqlmodel import SQLModel, create_engine, Session, delete

environ["MODE"] = "TEST"

from app.main import api
from app.database import get_db_session
from app.models import User


def db_url() -> str:
    """Initialize the database for testing"""

    file_name = "database.db"
    url: str = f"sqlite:///{file_name}"
    try:
        remove(file_name)
    except:
        pass

    return url


def generate_user_token(user):
    secret = "Kbc52gWophTSylpnIUOtCiVkGwrVeBqZOO5kk3TY5cY="
    key = derive_key(
        secret=secret,
        length=32,
        salt=b"",
        algorithm=hashes.SHA256(),
        context=b"NextAuth.js Generated Encryption Key",
    )
    return jwe.encrypt(json.dumps(user), key).decode("utf-8")


user = {
    "sub": "1234567890",
    "name": "Emad Anwer",
    "email": "test@emad.com",
    "exp": time.time() + 60 * 60,
}

token = generate_user_token(user)
cookie = {"next-auth.session-token": token}


client = TestClient(api, cookies=cookie)
engine = create_engine(db_url(), echo=False)
SQLModel.metadata.create_all(bind=engine)


def get_db_override():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


api.dependency_overrides[get_db_session] = get_db_override


# def init_user():
#     user = User(name="Emad Anwer", email="test@emad.com", image_url="url1")

#     with Session(engine) as db:
#         db.add(user)
#         db.commit()
#         db.refresh(user)
#         return user


# db_user = init_user()
