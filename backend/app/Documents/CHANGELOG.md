# Changelog - Phishing Detection API

## Cập nhật Logic Database (14/10/2025)

### Thay đổi chính:

#### 1. Cấu trúc Database mới
- **Database**: `detection_phishing`
- **Collection**: `data_urls`
- **Schema**:
  ```
  {
    url: String,      // URL đầy đủ
    domain: String,   // Domain của URL
    type: String      // "legitimate" hoặc "phishing"
  }
  ```

#### 2. Logic kiểm tra URL mới

**Quy trình kiểm tra:**

1. **Bước 1**: Tìm kiếm URL trong collection `data_urls`
   - Nếu tìm thấy và `type == "legitimate"` → Trả về kết quả "legitimate" từ database
   - Nếu tìm thấy và `type == "phishing"` → Trả về kết quả "phishing" từ database

2. **Bước 2**: Nếu URL không tồn tại trong database
   - Sử dụng model ML (`model.pkl`) để phân tích và đánh giá URL
   - Extract các features từ URL
   - Dự đoán với model đã train
   - Trả về kết quả từ model

3. **Xử lý lỗi**: 
   - Nếu model không load được hoặc không thể extract features → Trả về "unknown" với source "error"

#### 3. Response Format mới

```json
{
  "url": "https://example.com",
  "domain": "example.com",
  "result": "legitimate|phishing|unknown",
  "source": "database|model|error",
  "type": "legitimate|phishing|null",
  "elapsed_ms": 123.45
}
```

**Giải thích các field:**
- `url`: URL được kiểm tra
- `domain`: Domain được extract từ URL
- `result`: Kết quả phân loại (legitimate/phishing/unknown)
- `source`: Nguồn kết quả (database/model/error)
- `type`: Loại từ database (nếu tìm thấy), null nếu dùng model
- `elapsed_ms`: Thời gian xử lý (milliseconds)

#### 4. Dependencies mới

- `pickle`: Load ML model
- `SafeFeatureExtraction`: Extract features từ URL để dùng với model

#### 5. Model Loading

- Model được load khi khởi động ứng dụng (trong `lifespan`)
- Path: `model/model.pkl`
- Có error handling nếu model không tồn tại

### Cách sử dụng:

#### API Endpoint:
```
GET /check?url=<URL_TO_CHECK>
```

#### Ví dụ:

**Request:**
```bash
curl "http://localhost:5000/check?url=https://google.com"
```

**Response (từ database):**
```json
{
  "url": "https://google.com",
  "domain": "google.com",
  "result": "legitimate",
  "source": "database",
  "type": "legitimate",
  "elapsed_ms": 12.34
}
```

**Response (từ model):**
```json
{
  "url": "https://unknown-site.com",
  "domain": "unknown-site.com",
  "result": "phishing",
  "source": "model",
  "type": null,
  "elapsed_ms": 2345.67
}
```

### Lưu ý:

1. **Database Connection**: Đảm bảo MongoDB đang chạy và collection `data_urls` đã được tạo
2. **Model File**: File `model/model.pkl` phải tồn tại để có thể dự đoán URL mới
3. **Feature Extraction**: Quá trình extract features có thể mất thời gian (timeout 5 giây)
4. **Prediction Value**: Model giả định trả về `1` cho legitimate và `-1` cho phishing 

### Cải tiến trong tương lai:

- [ ] Cache kết quả dự đoán từ model vào database
- [ ] Thêm confidence score cho predictions
- [ ] Batch processing cho nhiều URLs
- [ ] Thêm logging chi tiết hơn
