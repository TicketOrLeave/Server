from fastapi import APIRouter
from app.models import Organization, User
from app.database import get_db
from starlette.requests import Request
from sqlmodel import select
from sqlalchemy.orm import selectinload

router = APIRouter()


@router.get("/organization")
async def read_organization(request: Request):
    with get_db() as db:
        # add org to user
        # user1 = db.exec(
        #     select(User).where(User.email == request.state.user_email)
        # ).first()
        # user1.organizations.append(Organization(name="org1", owner=user1.id))
        # user1.organizations.append(Organization(name="org2", owner=user1.id))

        user = db.exec(
            select(User)
            .where(User.email == request.state.user_email)
            .options(selectinload(User.organizations))
        ).first()
    return {"organizations": user.organizations}
