from collections.abc import Generator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, HttpUrl
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.sessions import SessionLocal
from app.models import RSSSource


router = APIRouter(prefix="/sources", tags=["RSS Sources"])


class SourceCreate(BaseModel):
    url: HttpUrl


class SourceUpdate(BaseModel):
    url: HttpUrl


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    etag: str | None = None
    last_modified: str | None = None
    last_fetched_at: datetime | None = None


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[SourceResponse])
def list_sources(db: Session = Depends(get_db)):
    return db.query(RSSSource).order_by(RSSSource.id).all()


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    source = RSSSource(url=str(payload.url))
    db.add(source)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An RSS source with this URL already exists.",
        ) from exc
    db.refresh(source)
    return source


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: int, db: Session = Depends(get_db)):
    source = db.get(RSSSource, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RSS source not found.")
    return source


@router.put("/{source_id}", response_model=SourceResponse)
def update_source(source_id: int, payload: SourceUpdate, db: Session = Depends(get_db)):
    source = db.get(RSSSource, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RSS source not found.")

    source.url = str(payload.url)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An RSS source with this URL already exists.",
        ) from exc
    db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.get(RSSSource, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RSS source not found.")
    db.delete(source)
    db.commit()
