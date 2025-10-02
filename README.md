# Phishing Detection (Local DB - Realtime)

Giải pháp gồm 2 phần:
- Backend Node.js đọc MongoDB (localhost:27017, db `phishing_detection`, collection `data` cột `URL`).
- Extension trình duyệt (MV3) kiểm tra **realtime** mỗi lần người dùng truy cập URL bằng cách gọi API `/check`, nếu kết quả `phishing: true` thì chặn và hiển thị trang cảnh báo.

## Yêu cầu
- Node.js 18+
- MongoDB đang chạy tại `mongodb://localhost:27017`

## Cài đặt và chạy Backend

```powershell
# đi đến thư mục backend
cd "c:\Users\admin\OneDrive\Documents\thạc sỹ\HKIII\an_toan_bao_mat_thong_tin\phishing_detection\backend"

# cài dependencies
npm install

# (tuỳ chọn) seed dữ liệu mẫu
npm run seed

# chạy server
npm start
```

Mặc định backend chạy ở http://localhost:4000 với các endpoint:
- GET `/health`
- GET `/list` -> trả về `{ count, urls: string[] }`
- GET `/check?url=...` -> `{ url, normalized, phishing: boolean }`

Biến môi trường:
- `MONGO_URI` (mặc định `mongodb://localhost:27017`)
- `DB_NAME` (mặc định `phishing_detection`)
- `COLLECTION` (mặc định `data`)

## Cài đặt Extension (Chrome/Edge)
1. Mở trình duyệt -> `chrome://extensions` (hoặc `edge://extensions`).
2. Bật Developer mode.
3. Chọn "Load unpacked" và trỏ tới thư mục:
   `c:\Users\admin\OneDrive\Documents\thạc sỹ\HKIII\an_toan_bao_mat_thong_tin\phishing_detection\extension`
4. Backend URL mặc định là `http://localhost:4000`. Có thể vào Options của extension để đổi.

## Cách hoạt động (Realtime)
- Mỗi request điều hướng (main_frame) trình duyệt → extension chặn tạm và gửi HTTP `GET /check?url=<đầy đủ>` đến backend.
- Backend chuẩn hoá và kiểm tra URL có tồn tại trong collection (theo pattern chuẩn) → trả về `phishing: true/false`.
- Nếu `true` → extension redirect trang sang `blocked.html?url=<original>`.
- Người dùng có thể chọn “Tiếp tục tạm thời” (allow host 5 phút) → các lần truy cập kế tiếp host đó không bị gọi `/check` (giảm độ trễ).

## Ghi chú
- Cột trong MongoDB nên thống nhất tên `URL` và lưu dạng đầy đủ: `https://domain/path`.
- Backend chuẩn hoá để so khớp bỏ protocol nhưng pattern tìm kiếm vẫn hỗ trợ cả http/https và dấu `/` cuối.
- Nếu muốn mở rộng chặn toàn bộ sub-path của một domain chỉ cần thay regex ở backend hoặc chuyển sang lưu domain gốc.

## Bảo mật & Quyền riêng tư
- Mỗi lần điều hướng chỉ gửi đúng URL đích tới backend nội bộ để kiểm tra (không gửi lịch sử khác).
- Không ghi log ngoài trừ khi bạn bật pino logger backend.
- Không lưu trữ danh sách cục bộ nhiều → dữ liệu trung tâm cập nhật lập tức.

## Python Backend (FastAPI + ML) bổ sung

Thư mục: `python_backend/`

Chức năng:
- Endpoint `GET /health`
- Endpoint `GET /check?url=...` trả về:
   - `phishing_db`: true nếu URL tồn tại trong Mongo (collection `data`, field `URL`).
   - `phishing_ml`: kết quả mô hình ML (RandomForest hoặc heuristic fallback nếu chưa train).
   - `phishing`: `phishing_db OR phishing_ml`.
   - `source`: "db" | "ml" | "none".

### Cài đặt (PowerShell)
```powershell
cd "c:\Users\admin\OneDrive\Documents\thạc sỹ\HKIII\an_toan_bao_mat_thong_tin\phishing_detection\python_backend"
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

### Chạy server
```powershell
uvicorn app.main:app --reload --port 5000
```
Server: http://localhost:5000

### Gọi thử
```powershell
curl "http://localhost:5000/health"
curl "http://localhost:5000/check?url=https://www.southbankmosaics.com"
```

### Train mô hình (đơn giản)
```powershell
cd python_backend
./.venv/Scripts/Activate.ps1
python -m app.train
```
Sinh file model: `python_backend/app/model.joblib`.

### Tích hợp với extension
- Có thể đổi backend URL của extension sang FastAPI (ví dụ http://localhost:5000) nếu muốn dùng quyết định ML.
- Endpoint `/check` của Python trả cùng trường `phishing` nên extension không cần đổi logic.

### Ghi chú kỹ thuật
- Nếu dataset ít, fallback heuristic sẽ quyết định dựa trên độ dài, số ký tự đặc biệt.
- Có thể mở rộng thêm đặc trưng: entropy, suspicious TLD, từ khoá thương hiệu.
- Nên thêm scheduler train lại định kỳ khi dữ liệu tăng.

---
### So sánh chế độ cũ (cache /list) vs realtime /check
| Tiêu chí | Cache danh sách | Realtime /check |
|----------|-----------------|-----------------|
| Độ trễ cập nhật DB | Chậm (tối đa = chu kỳ refresh) | Ngay lập tức |
| Số request backend | Ít (định kỳ) | Nhiều (mỗi điều hướng) |
| Phụ thuộc dynamic rules | Có | Không |
| Độ chính xác tức thời | Trung bình | Cao |

Nếu backend chịu tải tốt và danh sách thay đổi thường xuyên → dùng realtime. Nếu bạn muốn giảm truy vấn, có thể thêm cache ngắn hạn (memory 30–60s) trong `background.js`.
