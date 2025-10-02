import os
import time
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from pymongo import MongoClient
from urllib.parse import urlparse

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "phishing_detection")
COLLECTION = os.getenv("COLLECTION", "data")

mongo_client: Optional[MongoClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    mongo_client.admin.command('ping')
    try:
        yield
    finally:
        if mongo_client:
            mongo_client.close()

app = FastAPI(title="Phishing Detection Python API", version="1.0.0", lifespan=lifespan)

class CheckResponse(BaseModel):
    url: str
    normalized: str
    phishing_db: bool
    label: int | None
    phishing: bool
    source: str
    elapsed_ms: float

def normalize(url: str) -> str:
    url = url.strip()
    if not url:
        return url
    if not url.lower().startswith(("http://", "https://")):
        url = "http://" + url
    try:
        parsed = urlparse(url)
        host = parsed.hostname.lower() if parsed.hostname else ""
        path = (parsed.path or "/").rstrip("/")
        query = ("?" + parsed.query) if parsed.query else ""
        return f"{host}{path if path else ''}{query}"
    except Exception:
        return url.lower()


@app.get("/health")
def health():
    return {"ok": True}

@app.get("/check", response_model=CheckResponse)
def check(url: str = Query(..., description="URL cần kiểm tra")):
    if not url:
        raise HTTPException(400, detail="Missing url")
    began = time.time()
    norm = normalize(url)

    col = mongo_client[DB_NAME][COLLECTION]

    # Khớp DB: các mục được lưu có thể có tiền tố http(s)://
    patterns = [
        {"URL": {"$regex": f"^https?://{norm.rstrip('/')}/?$", "$options": "i"}},
        {"URL": {"$regex": f"^{norm.rstrip('/')}$", "$options": "i"}},
    ]
    db_doc = col.find_one({"$or": patterns}, {"_id": 1, "label": 1})
    phishing_db = db_doc is not None
    label = db_doc.get('label') if db_doc and 'label' in db_doc else None

    # Giải thích: label = 1 => hợp pháp (không phải phishing), label = 0 => phishing
    if label is not None:
        phishing = (label == 0)
        source = "db-label"
    else:
        phishing = phishing_db  
        source = "db" if phishing_db else "none"

    elapsed_ms = (time.time() - began) * 1000.0

    return CheckResponse(
        url=url,
        normalized=norm,
        phishing_db=phishing_db,
        label=label,
        phishing=phishing,
        source=source,
        elapsed_ms=elapsed_ms
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
