from starlette.requests import Request
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, init_db
from app.middleware import AuthMiddleware
from app.models import *
from app.routers import organization


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set up
    init_db()
    yield
    # Tear down
    SQLModel.metadata.drop_all(bind=engine)


api = FastAPI(lifespan=lifespan)
api.add_middleware(AuthMiddleware)
api.include_router(organization.router)


@api.get("/")
def read_root(request: Request):
    username = request.state.user.name
    email = request.state.user.email
    return {"Hello": f"{username}, {email}"}


if __name__ == "__main__":
    import uvicorn

    SQLModel.metadata.create_all(bind=engine)
    uvicorn.run(api, host="0.0.0.0", port=8000)
