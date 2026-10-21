from fastapi import FastAPI

app = FastAPI(title="News Aggregator")


@app.get("/")
def home():
    return {"message": "News Aggregator API is running!"}


@app.get("/health")
def health():
    return {"status": "ok"}