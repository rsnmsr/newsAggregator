from collections.abc import Generator
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.sessions import SessionLocal
from app.models import Article, RSSSource
from app.services.rss_fetcher import fetch_articles


router = APIRouter(prefix="/articles", tags=["Articles"])


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    external_id: str
    title: str | None = None
    link: str | None = None
    published_at: datetime | None = None
    updated_at: datetime | None = None
    published_day: str | None = None
    processed: bool


class ArticleCreate(BaseModel):
    source_id: int
    external_id: str
    title: str | None = None
    link: str | None = None
    published_at: datetime | None = None
    updated_at: datetime | None = None
    processed: bool = False


class ArticleUpdate(BaseModel):
    title: str | None = None
    link: str | None = None
    published_at: datetime | None = None
    updated_at: datetime | None = None
    processed: bool | None = None


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[ArticleResponse])
def list_articles(
    published_on: date | None = Query(
        default=None,
        description="Filter articles by publication date (YYYY-MM-DD)",
    ),
    db: Session = Depends(get_db),
):
    query = db.query(Article).order_by(Article.published_at.desc(), Article.id.desc())
    if published_on is not None:
        query = query.filter(Article.published_day == published_on.isoformat())
    return query.limit(500).all()


@router.post("/fetch")
def fetch_new_articles(db: Session = Depends(get_db)):
    return fetch_articles(db)


@router.post("", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article(payload: ArticleCreate, db: Session = Depends(get_db)):
    if db.get(RSSSource, payload.source_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RSS source not found.")

    article = Article(
        **payload.model_dump(),
        published_day=(
            payload.published_at.date().isoformat()
            if payload.published_at is not None
            else None
        ),
    )
    db.add(article)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This article already exists for the RSS source.",
        ) from exc
    db.refresh(article)
    return article


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found.")
    return article


@router.put("/{article_id}", response_model=ArticleResponse)
def update_article(article_id: int, payload: ArticleUpdate, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(article, field, value)
    if payload.published_at is not None:
        article.published_day = payload.published_at.date().isoformat()

    db.commit()
    db.refresh(article)
    return article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(article_id: int, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found.")
    db.delete(article)
    db.commit()
