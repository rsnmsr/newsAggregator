from collections.abc import Generator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, HttpUrl
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.sessions import SessionLocal
from app.models import Feed
from app.services.rss_fetcher import get_feed


router = APIRouter(prefix="/feeds", tags=["feeds"])


class FeedCreate(BaseModel):
    url: HttpUrl


class FeedUpdate(BaseModel):
    url: HttpUrl


class FeedResponse(BaseModel):
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


@router.get("", response_model=list[FeedResponse])
def list_feeds(db: Session = Depends(get_db)):
    return db.query(Feed).order_by(Feed.id).all()


@router.get("/fetch")
def fetch_feeds(db: Session = Depends(get_db)):
    return get_feed(db)


@router.post("", response_model=FeedResponse, status_code=status.HTTP_201_CREATED)
def create_feed(payload: FeedCreate, db: Session = Depends(get_db)):
    feed = Feed(url=str(payload.url))
    db.add(feed)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A feed with this URL already exists.",
        ) from exc
    db.refresh(feed)
    return feed


@router.get("/{feed_id}", response_model=FeedResponse)
def get_feed_by_id(feed_id: int, db: Session = Depends(get_db)):
    feed = db.get(Feed, feed_id)
    if feed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found.")
    return feed


@router.put("/{feed_id}", response_model=FeedResponse)
def update_feed(feed_id: int, payload: FeedUpdate, db: Session = Depends(get_db)):
    feed = db.get(Feed, feed_id)
    if feed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found.")

    feed.url = str(payload.url)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A feed with this URL already exists.",
        ) from exc
    db.refresh(feed)
    return feed


@router.delete("/{feed_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feed(feed_id: int, db: Session = Depends(get_db)):
    feed = db.get(Feed, feed_id)
    if feed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found.")
    db.delete(feed)
    db.commit()
