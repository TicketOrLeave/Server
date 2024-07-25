from unittest import mock
from cryptography.hazmat.primitives import hashes
from fastapi_nextauth_jwt.operations import derive_key
from fastapi.testclient import TestClient
from os import environ, remove
import time
from jose import jwe
import json
import pytest
from sqlmodel import SQLModel, create_engine, Session

environ["MODE"] = "TEST"

from app.main import api
from app.database import get_db_session


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


@pytest.fixture(autouse=True)
def mock_email_sender():
    print("mock_email_sender")
    with mock.patch(
        "app.utilities.mail.EmailSender.send_email"
    ) as mock_send_email, mock.patch(
        "app.utilities.mail.EmailSender.send_email_background"
    ) as mock_send_email_background:
        yield mock_send_email, mock_send_email_background
