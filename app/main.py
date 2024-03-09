from starlette.requests import Request
from fastapi import FastAPI

from app.database import engine
from app.middleware import AuthMiddleware
from dotenv import load_dotenv
from app.models import *

load_dotenv()



api = FastAPI()
api.add_middleware(AuthMiddleware)


@api.get("/")
def read_root(request: Request):
    username = request.state.username
    email = request.state.user_email
    return {"Hello": f"{username}, {email}"}


@api.get("/organization")
def get_user_organization(request: Request):
    user: User = request.state.get_user(request)
    user_organizations = "".join([org.name for org in user.organizations])
    return {"User Organization": f"{user_organizations} "}


if __name__ == "__main__":
    import uvicorn
    SQLModel.metadata.create_all(bind=engine)
    uvicorn.run(api, host="0.0.0.0", port=8000)
