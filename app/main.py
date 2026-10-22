from fastapi import FastAPI
from app.services.rss_fetcher import get_feed

app = FastAPI(title="News Aggregator")

# we need to store a list of RSS feed we might need to query
@app.get("/")
def home():
    return {"message": "News Aggregator API is running!"}


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get('/feeds')
async def feedKeys():
    return await get_feed()