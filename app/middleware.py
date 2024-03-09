from datetime import datetime
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
from app.database import get_db
from app.models import User
from os import getenv


SECRET_KEY = getenv("SECRET_KEY")


class AuthMiddleware(BaseHTTPMiddleware):
    JWT = NextAuthJWT(secret=SECRET_KEY, check_expiry=True)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
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

        with get_db() as db:
            statement = select(User).where(User.email == mail)
            user = db.exec(statement).first()

            if not user:
                user = User(email=mail, name=name, image_url=url)
                db.add(user)
                db.commit()

            request.state.username = user.name
            request.state.user_email = user.email

        response = await call_next(request)
        return response
