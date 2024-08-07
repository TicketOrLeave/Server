from starlette.requests import Request
from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
from app.database import engine, init_db
from app.middleware import AuthMiddleware
from app.models import *
from app.routers.organizations import router as organizations_router
from app.routers.invitations import router as invitations_router
from app.routers.events import router as events_router
from app.routers.tickets import router as ticket_router
from app.routers.reservation import router as reservation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set up
    init_db()
    yield
    # Tear down
    # SQLModel.metadata.drop_all(bind=engine)


api = FastAPI(lifespan=lifespan)
api.add_middleware(AuthMiddleware)
api.include_router(organizations_router, prefix="/organizations")
api.include_router(invitations_router, prefix="/invitations")
api.include_router(events_router, prefix="/events")
api.include_router(ticket_router, prefix="/tickets")
api.include_router(reservation_router, prefix="/reservation")


@api.get("/")
def read_root(request: Request):
    username = request.state.user.name
    email = request.state.user.email
    return {"Hello": f"{username}, {email}"}
