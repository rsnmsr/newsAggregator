from fastapi import FastAPI

from app.api.feeds import router as feeds_router
from app.db.init_db import init_db

app = FastAPI(title="News Aggregator")
app.include_router(feeds_router)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def home():
    return {"message": "News Aggregator API is running!"}


@app.get("/health")
def health():
    return {"status": "ok"}