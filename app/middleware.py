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
from app.database import get_db, get_db_session
from app.models import User, Organization, UserOrganization, UserRole
from os import getenv
from sqlalchemy.orm import joinedload


SECRET_KEY = getenv("SECRET_KEY")


class AuthMiddleware(BaseHTTPMiddleware):
    # TODO: edit this line
    JWT = NextAuthJWT(secret=SECRET_KEY, check_expiry=True, csrf_methods=["X"])

    def get_user(self, request: Request, organizations=False):
        with get_db() as db:
            # We Make eager loading to load the organizations of the user
            if organizations:
                statement = (
                    select(User)
                    .options(joinedload(User.organizations))
                    .where(User.email == request.state.user_email)
                )
            else:
                statement = select(User).where(User.email == request.state.user_email)

            user = db.exec(statement).first()
            return user

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
        db = next(get_db_session())

        statement = select(User).where(User.email == mail)
        user = db.exec(statement).first()

        if not user:
            user = User(email=mail, name=name, image_url=url)
            organization = Organization(name=f"{name} Organization", owner=user.id)

            db.add_all([user, organization])
            user_organization = UserOrganization(
                user_id=user.id,
                organization_id=organization.id,
                user_role=UserRole.creator,
            )
            db.add(user_organization)
            db.commit()

        request.state.user = user
        request.state.db = db
        response = await call_next(request)
        db.close()
        return response
