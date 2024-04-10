"""
This file contains the tests for the middleware
"""
import unittest
from . import generate_user_token, api, get_db_override, client, engine
from fastapi.testclient import TestClient
import time
from unittest.mock import patch, AsyncMock
from app.models import User
from sqlmodel import select, SQLModel, delete


class TestMiddleWare(unittest.TestCase):
    """
    This class covers the middleware tests
     - test_middleware_new_user
     - test_middleware_existing_user
     - test_invalid_token
     - test_missing_token
     - test_expired_token
    """
    @classmethod
    def teardown_class(cls) -> None:
        """
        Delete the user created in the test
        """
        db = next(get_db_override())
        db.exec(delete(User).where(User.email == "test@test.com"))
        db.commit()

    @patch("app.middleware.EmailSender")
    def test_middleware_new_user(self, mock_email_sender):
        """ 
        Test middleware for new user it should send email to the user
        """
        user_json = {
            "sub": "1234567890",
            "name": "test",
            "email": "test@test.com",
            "exp": time.time() + 60 * 60,
        }
        self.client = TestClient(
            api, cookies={"next-auth.session-token": generate_user_token(user_json)})
        mock_send_email = AsyncMock()
        mock_email_sender.return_value.send_email = mock_send_email
        response = self.client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Hello": "test, test@test.com"}
        mock_send_email.assert_called_once_with(
            "test@test.com", "Welcome to TicketOrLeave it!", "welcome.html", username="test"
        )
        db = next(get_db_override())
        user = db.exec(select(User)
                       .where(User.email == "test@test.com")
                       .where(User.name == "test")).first()
        assert user is not None

    @patch("app.middleware.EmailSender")
    def test_middleware_existing_user(self, mock_email_sender):
        """
        Test middleware for existing user it should not send email to the user
        """
        mock_send_email = AsyncMock()
        mock_email_sender.return_value.send_email = mock_send_email
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Hello": "Emad Anwer, test@emad.com"}
        db = next(get_db_override())
        user = db.exec(select(User)
                       .where(User.email == "test@emad.com")
                       .where(User.name == "Emad Anwer")).first()
        assert user is not None
        mock_send_email.assert_not_awaited()
        mock_send_email.assert_not_called()

    def test_invalid_token(self):
        """
        Test middleware for invalid token
        """
        client = TestClient(
            api, cookies={"next-auth.session-token": "invalid"})
        response = client.get("/")
        assert response.status_code == 401
        assert response.text == "Invalid token"

    def test_missing_token(self):
        """
        Test middleware for missing token
        """
        client = TestClient(api)
        response = client.get("/")
        assert response.status_code == 401
        assert response.text == "Missing token"

    def test_expired_token(self):
        """
        Test middleware for expired token
        """
        user_json = {
            "sub": "1234567890",
            "name": "test",
            "email": "emad@gmail.com",
            "exp": time.time() - 60 * 60,
        }
        client = TestClient(
            api, cookies={"next-auth.session-token": generate_user_token(user_json)})
        response = client.get("/")
        assert response.status_code == 403
        assert response.text == "Token expired"
