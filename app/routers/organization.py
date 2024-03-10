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
        user: User = request.state.get_user(request, organizations=True)
    return {"organizations": user.organizations}
