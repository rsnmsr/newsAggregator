from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.articles import router as articles_router
from app.api.sources import router as sources_router
from app.db.init_db import init_db

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

app = FastAPI(title="News Aggregator")
app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="frontend-static",
)
app.include_router(sources_router)
app.include_router(articles_router)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def home() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}