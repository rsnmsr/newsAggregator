from fastapi import FastAPI

from app.api.articles import router as articles_router
from app.api.sources import router as sources_router
from app.db.init_db import init_db

app = FastAPI(title="News Aggregator")
app.include_router(sources_router)
app.include_router(articles_router)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def home():
    return {"message": "News Aggregator API is running!"}


@app.get("/health")
def health():
    return {"status": "ok"}