from app.main import api as app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
