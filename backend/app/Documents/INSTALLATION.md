# Requirements Installation Guide

## Cài đặt Dependencies

### Option 1: Cài đặt với version đúng (khuyến nghị)

Cài đặt với scikit-learn 1.6.1 để tránh warning version:

```bash
pip install -r requirements.txt
```

### Option 2: Cài đặt từng package

```bash
# Core Framework
pip install fastapi==0.111.0
pip install uvicorn==0.30.1
pip install pydantic==2.12.0

# Database
pip install pymongo==4.7.2

# Machine Learning (match với model version)
pip install scikit-learn==1.6.1
pip install numpy>=1.22.0,<2.4.0
pip install pandas==2.3.3

# Web Scraping
pip install requests==2.32.4
pip install beautifulsoup4==4.13.4
pip install lxml==5.3.0
```

### Option 3: Upgrade scikit-learn nếu đã cài version mới

Nếu bạn đã cài scikit-learn 1.7.2 và muốn downgrade về 1.6.1:

```bash
pip uninstall scikit-learn
pip install scikit-learn==1.6.1
```

## Kiểm tra cài đặt

Sau khi cài đặt, kiểm tra version:

```bash
pip list | findstr "fastapi uvicorn pymongo scikit-learn"
```

Expected output:
```
fastapi                   0.111.0
pymongo                   4.7.2
scikit-learn              1.6.1
uvicorn                   0.30.1
```

## Troubleshooting

### Warning: InconsistentVersionWarning

Nếu bạn vẫn thấy warning:
```
InconsistentVersionWarning: Trying to unpickle estimator ... from version 1.6.1 when using version 1.7.2
```

**Giải pháp:**
```bash
pip install scikit-learn==1.6.1 --force-reinstall
```

### Module not found errors

Nếu thiếu module, cài đặt từng package:
```bash
pip install <missing-package-name>
```

### Virtual Environment (Khuyến nghị)

Tạo virtual environment để tránh xung đột:

```bash
# Tạo venv
python -m venv venv

# Kích hoạt (Windows)
.\venv\Scripts\activate

# Kích hoạt (Linux/Mac)
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

## Python Version

- **Minimum**: Python 3.8+
- **Recommended**: Python 3.10 - 3.11
- **Tested**: Python 3.13

## Notes

- `scikit-learn==1.6.1` được chọn để match với version mà model đã được train
- Nếu dùng version khác có thể gây ra warning nhưng vẫn hoạt động
- Để tránh warning, nên dùng đúng version 1.6.1
