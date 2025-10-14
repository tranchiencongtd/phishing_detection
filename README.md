# Phishing Detection System

Hệ thống phát hiện phishing real-time sử dụng Machine Learning và database URL phishing.

## Cấu trúc project
```
phishing_detection/
├── backend/app/          # FastAPI backend với ML model
├── extension/           # Chrome Extension (Manifest V3)
└── README.md
```

## Thành phần chính
- **Backend FastAPI**: ML model + MongoDB lookup cho phát hiện phishing
- **Chrome Extension**: Kiểm tra real-time khi người dùng truy cập URL
- **MongoDB Database**: Lưu trữ danh sách URL phishing đã biết

## Yêu cầu hệ thống
- Python 3.13.2
- MongoDB đang chạy tại `mongodb://localhost:27017`
- Chrome/Edge browser để cài extension

## Backend API
Chạy tại http://localhost:8000 (mặc định) với các endpoint:
- GET `/health` -> Kiểm tra trạng thái server
- GET `/check?url=...` -> Kiểm tra URL phishing

### Response format
```json
{
  "url": "https://example.com",
  "result": "safe",           // "safe" | "phishing"
  "source": "db",             // "db" | "ml" | "cache"
  "type": "legitimate",       // "legitimate" | "phishing"
  "confidence": 0.95,         // 0.0 - 1.0
  "elapsed_ms": 45.2
}
```

## Cài đặt & Chạy

### 1. Setup Backend
```powershell
cd backend
pip install -r app/requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Setup MongoDB
- Cài đặt MongoDB Community Server
- Tạo database `phishing_detection` với collection `data`
- Import dữ liệu URL phishing vào collection

### 3. Cài đặt Extension (Chrome/Edge)
1. Mở `chrome://extensions` (hoặc `edge://extensions`)
2. Bật "Developer mode" 
3. Chọn "Load unpacked" và trỏ tới thư mục `extension/`
4. Backend URL mặc định là `http://localhost:8000` (có thể đổi trong Options)

## Tính năng Extension

### Phát hiện Real-time
- Kiểm tra tự động mỗi khi truy cập URL mới
- Hiển thị cảnh báo ngay lập tức nếu phát hiện phishing
- Cache kết quả để giảm độ trễ

### Popup Interface 
- Click vào icon extension để xem trạng thái trang hiện tại
- Hiển thị độ tin cậy và nguồn kiểm tra (Database/ML)
- Giao diện trực quan với màu sắc phân biệt

### Cách hoạt động
1. **Passive Detection**: Tự động kiểm tra khi người dùng điều hướng đến URL mới
2. **Active Check**: Người dùng click popup để kiểm tra thủ công 
3. **Manual Override**: Cho phép bỏ qua cảnh báo tạm thời (5 phút)

### Workflow
- Extension → gửi `GET /check?url=...` → Backend
- Backend → kiểm tra Database + ML model → trả về kết quả
- Nếu phishing → hiển thị trang cảnh báo `blocked.html`
- Popup hiển thị trạng thái với confidence score

## Machine Learning Backend

### Tính năng ML
- **GradientBoostingClassifier**: Mô hình ML chính để phân loại URL
- **Feature Extraction**: Trích xuất 20+ features từ URL (length, special chars, domain age, etc.)
- **Database Lookup**: Kiểm tra URL trong database phishing đã biết
- **Confidence Score**: Độ tin cậy dự đoán từ 0.0 đến 1.0

### Quy trình phân tích
1. Kiểm tra URL trong MongoDB (nếu có → trả về kết quả DB)
2. Nếu không có → trích xuất features và dùng ML model
3. Trả về kết quả với confidence score và elapsed time

## Testing

### Test Backend API
```powershell
# Kiểm tra health
curl "http://localhost:8000/health"

# Test URL an toàn
curl "http://localhost:8000/check?url=https://google.com"

# Test URL phishing (nếu có trong DB)
curl "http://localhost:8000/check?url=https://phishing-example.com"
```

### Test Extension
1. Load extension trong Chrome
2. Truy cập các URL test
3. Kiểm tra popup hiển thị đúng thông tin
4. Test trang cảnh báo khi phát hiện phishing

## Cấu hình MongoDB

### Database structure
```javascript
// Database: phishing_detection
// Collection: data
{
  "_id": ObjectId(...),
  "URL": "https://malicious-site.com/login",
  "label": "phishing"  // hoặc "legitimate"
}
```

### Import dữ liệu mẫu
```powershell
# Import từ CSV
mongoimport --db phishing_detection --collection data --type csv --headerline --file dataset.csv
```

## Troubleshooting

### Backend không start
- Kiểm tra MongoDB đã chạy: `mongo --eval "db.runCommand('ping')"`
- Kiểm tra port 8000 đã được sử dụng: `netstat -an | findstr :8000`
- Cài đặt dependencies: `pip install -r requirements.txt`

### Extension không hoạt động
- Kiểm tra Developer Console trong `chrome://extensions`
- Kiểm tra backend URL trong Options của extension
- Xem Network tab trong DevTools để debug API calls

### ML Model lỗi
- Scikit-learn version compatibility: `pip install scikit-learn==1.0.1`
- Retrain model nếu cần với version hiện tại