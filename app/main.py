from starlette.requests import Request
from fastapi import FastAPI
from app.middleware import AuthMiddleware

api = FastAPI()
api.add_middleware(AuthMiddleware)


@api.get("/")
def read_root(request: Request):
    username = request.state.username
    email = request.state.user_email
    return {"Hello": f"{username}, {email}"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(api, host='0.0.0.0', port=8000)
