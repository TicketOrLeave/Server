from fastapi import FastAPI
from app.middleware import AuthMiddleware

api = FastAPI()
api.add_middleware(AuthMiddleware)

@api.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host='0.0.0.0', port=8000,)