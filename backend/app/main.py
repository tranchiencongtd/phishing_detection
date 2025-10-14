import os
import time
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from pymongo import MongoClient
from urllib.parse import urlparse

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "detection_phishing")
BLACKLIST_COLLECTION = "blacklist"
WHITELIST_COLLECTION = "whitelist"

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
    in_blacklist: bool
    in_whitelist: bool
    result: str  # "phishing", "safe", "unknown"
    source: str
    elapsed_ms: float

def extract_domain(url: str) -> str:
    """Extract domain từ URL"""
    url = url.strip()
    if not url:
        return url
    
    # Thêm protocol nếu chưa có để parse được
    if not url.lower().startswith(("http://", "https://")):
        url = "http://" + url
    
    try:
        parsed = urlparse(url)
        domain = parsed.hostname.lower() if parsed.hostname else ""
        
        # Giữ nguyên port nếu có
        if parsed.port:
            domain = f"{domain}:{parsed.port}"
            
        return domain
    except Exception:
        return url.lower()

def extract_domain_from_db_url(db_url: str) -> str:
    """Extract domain từ URL trong database"""
    db_url = db_url.strip()
    if not db_url:
        return db_url
        
    # Nếu đã có protocol, extract domain
    if db_url.lower().startswith(("http://", "https://")):
        try:
            parsed = urlparse(db_url)
            domain = parsed.hostname.lower() if parsed.hostname else ""
            if parsed.port:
                domain = f"{domain}:{parsed.port}"
            return domain
        except Exception:
            return db_url.lower()
    else:
        # Nếu không có protocol, coi như là domain luôn
        return db_url.lower()


@app.get("/health")
def health():
    return {"ok": True}

@app.get("/check", response_model=CheckResponse)
def check(url: str = Query(..., description="URL cần kiểm tra")):
    if not url:
        raise HTTPException(400, detail="Missing url")
    began = time.time()
    
    # Extract domain từ input URL
    input_domain = extract_domain(url)

    # Kiểm tra trong blacklist collection - sử dụng regex để match domain
    blacklist_col = mongo_client[DB_NAME][BLACKLIST_COLLECTION]
    blacklist_patterns = [
        # Match exact domain
        {"url": input_domain},
        # Match domain với protocol (bắt đầu với https?://domain)
        {"url": {"$regex": f"^https?://{input_domain.replace('.', r'\.')}(/.*)?$", "$options": "i"}},
    ]
    blacklist_doc = blacklist_col.find_one({"$or": blacklist_patterns}, {"_id": 1})
    in_blacklist = blacklist_doc is not None

    # Kiểm tra trong whitelist collection - sử dụng regex để match domain
    whitelist_col = mongo_client[DB_NAME][WHITELIST_COLLECTION]
    whitelist_patterns = [
        # Match exact domain  
        {"url": input_domain},
        # Match domain với protocol (bắt đầu với https?://domain)
        {"url": {"$regex": f"^https?://{input_domain.replace('.', r'\.')}(/.*)?$", "$options": "i"}},
    ]
    whitelist_doc = whitelist_col.find_one({"$or": whitelist_patterns}, {"_id": 1})
    in_whitelist = whitelist_doc is not None

    # Xác định kết quả và nguồn
    if in_blacklist:
        result = "phishing"
        source = "blacklist"
    elif in_whitelist:
        result = "safe"
        source = "whitelist"
    else:
        result = "unknown"
        source = "none"

    elapsed_ms = (time.time() - began) * 1000.0

    return CheckResponse(
        url=url,
        normalized=input_domain,  # Trả về domain đã extract
        in_blacklist=in_blacklist,
        in_whitelist=in_whitelist,
        result=result,
        source=source,
        elapsed_ms=elapsed_ms
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
