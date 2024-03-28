from datetime import datetime
from typing import Optional
from fastapi_nextauth_jwt import NextAuthJWT
from fastapi_nextauth_jwt.exceptions import (
    InvalidTokenError,
    MissingTokenError,
    TokenExpiredException,
)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from sqlmodel import select
from app.database import get_db, get_db_session
from app.models import User, Organization
from os import getenv
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv
from app.utilities.mail import EmailSender
import asyncio

load_dotenv()

SECRET_KEY = getenv("SECRET_KEY")


class AuthMiddleware(BaseHTTPMiddleware):
    # TODO: edit this line
    JWT = NextAuthJWT(secret=SECRET_KEY, check_expiry=True, csrf_methods=["X"])
    allowed_paths = [
        "/docs",
        "/openapi.json",
        "/redoc",
        "/events/event",
        "/reservation/*",
    ]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in self.allowed_paths:
            return await call_next(request)
        for path in self.allowed_paths:
            if path.endswith("*") and (
                request.url.path.startswith(path[:-1])
                or request.url.path.startswith(path[:-2])
            ):
                return await call_next(request)

        try:
            decoded_token = self.JWT(request)
        except InvalidTokenError:
            return Response(status_code=401, content="Invalid token")
        except MissingTokenError:
            return Response(status_code=401, content="Missing token")
        except TokenExpiredException:
            return Response(status_code=403, content="Token expired")

        sub_id = decoded_token.get("sub")
        mail = decoded_token.get("email")
        name = decoded_token.get("name")
        exp = decoded_token.get("exp")
        exp_datetime = datetime.utcfromtimestamp(exp)
        url = decoded_token.get("picture")
        db = next(get_db_session())

        statement = select(User).where(User.email == mail)
        user = db.exec(statement).first()

        if not user:
            user = User(email=mail, name=name, image_url=url)
            db.add(user)
            db.commit()
            db.refresh(user)
            # send welcome email
            main = EmailSender()
            asyncio.create_task(
                main.send_email(
                    mail,
                    "Welcome to TicketOrLeave it!",
                    "welcome.html",
                    username=name,
                )
            )
        # get user current organization
        # organization: Optional[Organization] = next(
        #     (
        #         org
        #         for org in user.organizations
        #         if org.id == user.current_organization_id
        #     ),
        #     None,
        # )

        request.state.user = user
        # request.state.current_organization = organization
        request.state.db = db
        response = await call_next(request)
        db.close()
        return response
