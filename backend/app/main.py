import os
import time
import pickle
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from pymongo import MongoClient
from safe_feature_extraction import SafeFeatureExtraction
import numpy as np
import warnings
from dotenv import load_dotenv


# Kiểm tra xem có đang chạy trên Railway không
IS_PRODUCTION = os.getenv("RAILWAY_ENVIRONMENT_NAME") is not None or os.getenv("MONGO_URI") is not None

if not IS_PRODUCTION:
    # Chỉ load .env cho local development
    try:
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
        print("Development mode: Loading .env file")
    except ImportError:
        pass
else:
    print("Production mode: Using Railway environment variables")


# MongoDB config - sử dụng Atlas cho production
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "detection_phishing") 
DATA_URLS_COLLECTION = os.getenv("DATA_URLS_COLLECTION", "data_urls")
PORT = int(os.getenv("PORT", 8000))
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "model_5.pkl")

mongo_client: Optional[MongoClient] = None
ml_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client, ml_model
    # Kết nối MongoDB
    try:
        print(MONGO_URI)
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        mongo_client.admin.command('ping')
        print("MongoDB connected successfully")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        mongo_client = None
    
    # Load ML model
    try:
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                ml_model = pickle.load(f)
            print(f"Model loaded successfully from {MODEL_PATH}")
        else:
            print(f"Warning: Model file not found at {MODEL_PATH}")
    except Exception as e:
        print(f"Error loading model: {e}")
    
    try:
        yield
    finally:
        if mongo_client:
            mongo_client.close()

app = FastAPI(title="Phishing Detection Python API", version="1.0.0", lifespan=lifespan)

# CORS để extension có thể gọi API
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên giới hạn origins cụ thể
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class CheckResponse(BaseModel):
    url: str
    result: str  # "phishing", "legitimate", "unknown"
    source: str  # "database", "model", "error"
    type: Optional[str] = None  # Type from database if found
    confidence: Optional[float] = None  # Confidence score from model (0-1)
    elapsed_ms: float


@app.get("/health")
def health():
    return {"ok": True}

@app.get("/check", response_model=CheckResponse)
def check(url: str = Query(..., description="URL cần kiểm tra")):
    if not url:
        raise HTTPException(400, detail="Missing url")
    began = time.time()

    # Kiểm tra trong data_urls collection
    data_urls_col = mongo_client[DB_NAME][DATA_URLS_COLLECTION]
    
    # Tìm kiếm URL trong database (exact match)
    db_doc = data_urls_col.find_one({"url": url}, {"type": 1})
    
    if db_doc:
        # URL tồn tại trong database
        url_type = db_doc.get("type", "").lower()
        
        if url_type == "legitimate":
            result = "legitimate"
            source = "database"
            elapsed_ms = (time.time() - began) * 1000.0
            return CheckResponse(
                url=url,
                result=result,
                source=source,
                type=url_type,
                confidence=None,
                elapsed_ms=elapsed_ms
            )
        elif url_type == "phishing":
            result = "phishing"
            source = "database"
            elapsed_ms = (time.time() - began) * 1000.0
            return CheckResponse(
                url=url,
                result=result,
                source=source,
                type=url_type,
                confidence=None,
                elapsed_ms=elapsed_ms
            )
    
    # URL không tồn tại trong database, sử dụng model để đánh giá
    if ml_model is None:
        elapsed_ms = (time.time() - began) * 1000.0
        return CheckResponse(
            url=url,
            result="unknown",
            source="error",
            type=None,
            confidence=None,
            elapsed_ms=elapsed_ms
        )
    
    try:
        # Extract features từ URL
        feature_extractor = SafeFeatureExtraction(url, timeout=5)
        features = feature_extractor.features
        
        if len(features) == 0:
            # Không thể extract features
            elapsed_ms = (time.time() - began) * 1000.0
            return CheckResponse(
                url=url,
                result="unknown",
                source="error",
                type=None,
                confidence=None,
                elapsed_ms=elapsed_ms
            )
        

        features_array = np.array([features], dtype=np.float64)
        prediction = ml_model.predict(features_array)[0]  # Lấy phần tử đầu tiên

        # Lấy xác suất dự đoán nếu model hỗ trợ predict_proba
        confidence = None
        try:
            if hasattr(ml_model, 'predict_proba'):
                probabilities = ml_model.predict_proba(features_array)[0]
                # Lấy xác suất của class được dự đoán
                if prediction == 1:
                    # legitimate - lấy xác suất của class 1
                    confidence = float(probabilities[1]) if len(probabilities) > 1 else float(probabilities[0])
                else:
                    # phishing - lấy xác suất của class 0
                    confidence = float(probabilities[0])
        except Exception as e:
            print(f"Warning: Cannot get confidence score: {e}")
        
        # Convert prediction to result ( 1 = legitimate, -1 = phishing)
        if prediction == 1:
            result = "legitimate"
        else:
            result = "phishing"
        
        source = "model"
        
    except Exception as e:
        print(f"Error predicting URL {url}: {e}")
        print(f"Features length: {len(features) if 'features' in locals() else 'N/A'}")
        print(f"Error type: {type(e).__name__}")
        result = "unknown"
        source = "error" 
        confidence = None
    
    elapsed_ms = (time.time() - began) * 1000.0
    
    return CheckResponse(
        url=url,
        result=result,
        source=source,
        type=None,
        confidence=confidence,
        elapsed_ms=elapsed_ms
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
