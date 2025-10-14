# 🛡️ Phishing Detection Extension - Luồng Hoạt động Chi tiết

## 🎯 Tổng quan
Extension hoạt động theo 3 phương thức chính:
1. **Passive Detection** - Tự động kiểm tra khi browse web
2. **Active Check** - Người dùng click icon extension
3. **Manual Override** - Cho phép truy cập tạm thời

---

## 🔄 1. LUỒNG PASSIVE DETECTION (Tự động)

### Khi người dùng navigate đến URL mới:

```
📱 USER ACTION: Navigate to website
         ↓
🔍 STEP 1: onBeforeNavigate Event Trigger
         ↓
❓ STEP 2: Should Skip URL Check?
    ├─ YES → chrome://, about:, file:// → ⏹️ SKIP
    ├─ YES → Extension pages → ⏹️ SKIP  
    └─ NO → Continue to Step 3
         ↓
🔐 STEP 3: Check Allow Override
    ├─ YES → Host in allowOverrides → ⏹️ ALLOW ACCESS
    └─ NO → Continue to Step 4
         ↓
🌐 STEP 4: Check URL with Backend
    ├─ 📊 Cache Check (Extension level)
    ├─ 🔍 Database Lookup (Backend)
    └─ 🤖 AI Model Prediction (Backend)
         ↓
⚖️ STEP 5: Decision Making
    ├─ ✅ SAFE → Allow normal browsing
    └─ ⚠️ PHISHING → Redirect to blocked.html
         ↓
🚫 STEP 6: Block & Show Warning Page
```

### Chi tiết từng bước:

#### 📍 **STEP 1: Event Listener**
```javascript
// background.js
chrome.webNavigation.onBeforeNavigate.addListener(async (details) => {
  const { tabId, url, frameId } = details;
  
  // Chỉ xử lý main frame (không phải iframe)
  if (frameId !== 0) return;
  if (tabId === -1) return;
  
  // Continue to next step...
});
```

#### 📍 **STEP 2: URL Filtering**
```javascript
function shouldSkipUrl(url) {
  const skipSchemes = ['chrome://', 'about:', 'file://'];
  const skipUrls = ['chrome://new-tab-page/', 'about:blank'];
  
  // Bỏ qua các URL hệ thống
  return skipSchemes.some(scheme => url.startsWith(scheme)) ||
         skipUrls.includes(url);
}
```

#### 📍 **STEP 3: Allow Override Check**
```javascript
// Kiểm tra xem user đã cho phép host này chưa
pruneAllow(); // Xóa expired overrides
if (allowOverrides.has(host)) return; // Cho phép truy cập
```

#### 📍 **STEP 4: Backend API Call**
```javascript
async function checkUrl(url) {
  // Cache check
  const cached = resultCache.get(url);
  if (cached && cached.exp > Date.now()) return cached;
  
  // API call to backend
  const { backendUrl } = await chrome.storage.local.get({ backendUrl: DEFAULT_BACKEND });
  const endpoint = `${backendUrl}/check?url=${encodeURIComponent(url)}`;
  
  const response = await fetch(endpoint);
  const result = await response.json();
  
  // Cache result
  resultCache.set(url, { ...result, exp: Date.now() + CACHE_TTL_MS });
  return result;
}
```

#### 📍 **STEP 5: Decision Logic**
```javascript
const checkResult = await checkUrl(url);
if (checkResult.result === 'phishing') {
  // Redirect to blocked page with details
  const params = new URLSearchParams({
    url: url,
    source: checkResult.source,
    confidence: checkResult.confidence,
    type: checkResult.type
  });
  const redirect = chrome.runtime.getURL(`blocked.html?${params.toString()}`);
  await chrome.tabs.update(tabId, { url: redirect });
}
```

---

## 🖱️ 2. LUỒNG ACTIVE CHECK (Click Extension Icon)

### Khi người dùng click vào extension icon:

```
👆 USER ACTION: Click extension icon
         ↓
📱 STEP 1: Popup Opens
         ↓
🌐 STEP 2: Get Current Tab URL
         ↓
❓ STEP 3: Check URL Type
    ├─ System Page → Show "Trang hệ thống" 
    └─ Regular URL → Continue
         ↓
🔍 STEP 4: Send Check Request to Background
         ↓
📡 STEP 5: Background Calls Backend API
         ↓
📊 STEP 6: Display Results in Popup
    ├─ Database Result → "Website an toàn/không an toàn"
    ├─ Model Result → "X% phishing/an toàn" + progress bar
    └─ Unknown → "Không thể xác định"
```

### Chi tiết Popup Flow:

#### 📍 **Popup Initialization**
```javascript
// popup.js
async function init() {
  // Get current tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  currentUrl = tab.url;
  
  // Check if special page
  if (shouldSkipUrl(currentUrl)) {
    showSpecialPage();
    return;
  }
  
  // Check URL
  await checkCurrentUrl();
}
```

#### 📍 **Display Logic**
```javascript
function displayResult(result) {
  switch(result.result) {
    case 'legitimate':
      if (result.source === 'database') {
        showStatus("✅ Website an toàn");
      } else if (result.source === 'model') {
        const percent = formatConfidence(result.confidence);
        showStatus(`🛡️ Có thể an toàn (${percent}%)`);
        showConfidenceBar(result.confidence, true);
      }
      break;
      
    case 'phishing':
      if (result.source === 'database') {
        showStatus("⚠️ Website không an toàn");
      } else if (result.source === 'model') {
        const percent = formatConfidence(result.confidence);
        showStatus(`🚨 Có thể phishing (${percent}%)`);
        showConfidenceBar(result.confidence, false);
      }
      break;
  }
}
```

---

## 🔓 3. LUỒNG MANUAL OVERRIDE (Cho phép tạm thời)

### Khi người dùng ở trang blocked.html:

```
🚫 USER ON: blocked.html page
         ↓
👆 USER ACTION: Click "Tiếp tục tạm thời"
         ↓
📨 STEP 1: Send allowHost Message to Background
         ↓
⏰ STEP 2: Background Adds Host to allowOverrides
    └─ TTL: 10 seconds (configurable)
         ↓
✅ STEP 3: Redirect to Original URL
         ↓
🔄 STEP 4: onBeforeNavigate Fires Again
         ↓
✅ STEP 5: Allow Override Check Passes
         ↓
🌐 STEP 6: Normal Website Loading
```

---

## 🖥️ 4. BACKEND API WORKFLOW

### Khi nhận request từ extension:

```
📡 API REQUEST: GET /check?url=...
         ↓
📊 STEP 1: Database Lookup
    ├─ Found → Return database result
    └─ Not Found → Continue to Step 2
         ↓
🤖 STEP 2: Feature Extraction
    └─ SafeFeatureExtraction(url) → 22 features
         ↓
🧠 STEP 3: ML Model Prediction
    ├─ prediction = model.predict(features)
    └─ confidence = model.predict_proba(features)
         ↓
📄 STEP 4: Response Format
{
  "url": "https://example.com",
  "result": "phishing|legitimate|unknown",
  "source": "database|model|error",
  "type": "phishing|legitimate|null",
  "confidence": 0.85,
  "elapsed_ms": 123.45
}
```

### Backend Logic Detail:

#### 📍 **Database Check**
```python
# Check trong MongoDB collection data_urls
db_doc = data_urls_col.find_one({"url": url}, {"type": 1})
if db_doc:
    url_type = db_doc.get("type", "").lower()
    if url_type in ["legitimate", "phishing"]:
        return CheckResponse(result=url_type, source="database")
```

#### 📍 **ML Model Processing**
```python
# Feature extraction
feature_extractor = SafeFeatureExtraction(url, timeout=5)
features = feature_extractor.features

# Prediction
features_array = np.array([features], dtype=np.float64)
prediction = ml_model.predict(features_array)[0]

# Confidence
probabilities = ml_model.predict_proba(features_array)[0]
confidence = float(probabilities[prediction])
```

---

## 📊 5. DATA FLOW DIAGRAM

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   🌐 Website    │────│  📱 Extension   │────│  🖥️ Backend    │
│                 │    │                 │    │                 │
│ User navigates  │    │ 1. Intercept    │    │ 4. Check DB     │
│ to URL          │    │ 2. Cache check  │    │ 5. Extract feat │
│                 │    │ 3. API call     │    │ 6. ML predict   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ↑                       ↓                       ↓
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │ 📊 Local Cache  │    │ 🗄️ MongoDB     │
         │              │                 │    │                 │
         └──────────────│ - Results       │    │ - Known URLs    │
          Allow/Block   │ - Overrides     │    │ - User data     │
                        └─────────────────┘    └─────────────────┘
```

---

## ⚡ 6. PERFORMANCE OPTIMIZATIONS

### 🎯 **Extension Level:**
- **Local Cache**: 30s TTL cho mỗi URL
- **Allow Override**: Tránh check lặp lại host đã cho phép
- **Skip System URLs**: Không check chrome://, about:

### 🎯 **Backend Level:**
- **Database First**: Check MongoDB trước (nhanh nhất)
- **Feature Caching**: Cache extracted features
- **Model Loading**: Load model một lần khi startup

### 🎯 **Network Level:**
- **Parallel Processing**: Không block UI
- **Timeout Handling**: 5s timeout cho feature extraction
- **Error Fallback**: Fail open khi backend down

---

## 🛡️ 7. SECURITY MEASURES

### 🔒 **Extension Security:**
- **CSP Compliance**: Không inline scripts
- **Permission Minimal**: Chỉ cần thiết permissions
- **URL Validation**: Validate input URLs

### 🔒 **Backend Security:**
- **Input Sanitization**: Clean URLs before processing
- **Rate Limiting**: Prevent API abuse
- **Error Handling**: Không expose internal errors

---

## 📈 8. MONITORING & DEBUGGING

### 📊 **Metrics Tracked:**
- Cache hit rate
- API response time
- Detection accuracy
- Override frequency

### 🔍 **Debug Information:**
- Console logging cho development
- Performance timing
- Error stack traces
- API call details

---

## 🚀 9. DEPLOYMENT WORKFLOW

```
👨‍💻 DEVELOPMENT → 📦 BUILD → 🧪 TEST → 🚀 DEPLOY
     ↓              ↓         ↓        ↓
   Local test    Extension   Manual   Chrome Store
   Backend dev   packaging   testing  Extension
   Model train   Manifest    E2E      Backend prod
                 validation  flows    MongoDB
```

Đây là luồng hoạt động đầy đủ của extension phishing detection! 🎯