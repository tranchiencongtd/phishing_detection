const DEFAULT_BACKEND = 'http://localhost:8000';
const allowOverrides = new Map(); 
const resultCache = new Map(); 
const CACHE_TTL_MS = 30 * 1000; // 30s per exact URL

function normalizeForHost(input) {
  try {
    const u = new URL(input);
    return u.hostname.toLowerCase();
  } catch (e) {
    return '';
  }
}

function pruneAllow() {
  const now = Date.now();
  for (const [h, exp] of allowOverrides.entries()) if (exp <= now) allowOverrides.delete(h);
}

async function checkUrl(url) {
  // Cache per full URL to reduce backend calls during rapid reloads
  pruneCache();
  const cached = resultCache.get(url);
  if (cached && cached.exp > Date.now()) return cached;
  
  const { backendUrl } = await chrome.storage.local.get({ backendUrl: DEFAULT_BACKEND });
  const query = new URLSearchParams({ url });
  const endpoint = `${backendUrl.replace(/\/$/, '')}/check?${query.toString()}`;
  
  let result = {
    url: url,
    result: 'unknown',
    source: 'error',
    type: null,
    confidence: null,
    elapsed_ms: 0,
    isPhishing: false
  };
  
  try {
    const res = await fetch(endpoint, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      
      // Xử lý confidence để đảm bảo logic đúng
      let processedConfidence = data.confidence;
      if (data.source === 'model' && processedConfidence !== null) {
        // Đảm bảo confidence luôn thể hiện mức độ chắc chắn của kết quả dự đoán
        // Nếu result là legitimate, confidence đã là xác suất legitimate
        // Nếu result là phishing, confidence đã là xác suất phishing
        processedConfidence = Math.abs(processedConfidence);
      }
      
      result = {
        ...data,
        confidence: processedConfidence,
        isPhishing: data.result === 'phishing'
      };
    }
  } catch (e) {
    console.warn('Backend check failed:', e);
    // fail open - treat as legitimate when backend is unavailable
  }
  
  resultCache.set(url, { ...result, exp: Date.now() + CACHE_TTL_MS });
  return result;
}

function pruneCache() {
  const now = Date.now();
  for (const [u, v] of resultCache.entries()) if (v.exp <= now) resultCache.delete(u);
}

function shouldSkipUrl(url) {
  if (!url) return true;
  
  // Bỏ qua các URL nội bộ của Chrome
  const skipSchemes = [
    'chrome://',
    'chrome-extension://',
    'edge://',
    'moz-extension://',
    'about:',
    'data:',
    'javascript:',
    'file://'
  ];
  
  // Bỏ qua các trang đặc biệt
  const skipUrls = [
    'chrome://new-tab-page/',
    'chrome://newtab/',
    'chrome://startpageshared/',
    'about:blank',
    'about:newtab'
  ];
  
  const urlLower = url.toLowerCase();
  
  // Kiểm tra scheme
  if (skipSchemes.some(scheme => urlLower.startsWith(scheme))) {
    return true;
  }
  
  // Kiểm tra URL cụ thể
  if (skipUrls.some(skipUrl => urlLower === skipUrl || urlLower.startsWith(skipUrl))) {
    return true;
  }
  
  return false;
}

chrome.webNavigation.onBeforeNavigate.addListener(async (details) => {
  const { tabId, url, frameId } = details;
  if (frameId !== 0) return; 
  if (tabId === -1) return;
  
  // Bỏ qua các URL không cần kiểm tra
  if (shouldSkipUrl(url)) {
    return;
  }
  
  const host = normalizeForHost(url);
  pruneAllow();
  if (allowOverrides.has(host)) return;
  
  const checkResult = await checkUrl(url);
  if (checkResult.isPhishing) {
    const params = new URLSearchParams({
      url: url,
      source: checkResult.source || 'unknown',
      confidence: checkResult.confidence || 0,
      type: checkResult.type || 'unknown'
    });
    const redirect = chrome.runtime.getURL(`blocked.html?${params.toString()}`);
    try { 
      await chrome.tabs.update(tabId, { url: redirect }); 
    } catch (e) {
      console.error('Failed to redirect to blocked page:', e);
    }
  }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg?.type === 'allowHost' && msg.host) {
    const ttlMs = typeof msg.ttlMs === 'number' ? msg.ttlMs : 5 * 60 * 1000;
    allowOverrides.set(msg.host, Date.now() + ttlMs);
    sendResponse({ ok: true });
    return true;
  }
  
  if (msg?.type === 'checkUrl' && msg.url) {
    // Kiểm tra URL được yêu cầu từ popup hoặc content script
    checkUrl(msg.url).then(result => {
      sendResponse(result);
    }).catch(error => {
      sendResponse({
        url: msg.url,
        result: 'unknown',
        source: 'error',
        type: null,
        confidence: null,
        elapsed_ms: 0,
        isPhishing: false,
        error: error.message
      });
    });
    return true; // Will respond asynchronously
  }
  
  if (msg?.type === 'getCache') {
    // Trả về thông tin cache hiện tại
    sendResponse({
      cacheSize: resultCache.size,
      allowOverridesSize: allowOverrides.size
    });
    return true;
  }
});
