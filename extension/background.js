// Background service worker: realtime phishing check via backend /check (webNavigation based)
const DEFAULT_BACKEND = 'http://localhost:5000';
const allowOverrides = new Map(); // host -> expiry timestamp
const resultCache = new Map(); // url -> { phishing:boolean, exp:number }
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

async function isPhishing(url) {
  // Cache per full URL to reduce backend calls during rapid reloads
  pruneCache();
  const cached = resultCache.get(url);
  if (cached && cached.exp > Date.now()) return cached.phishing;
  const { backendUrl } = await chrome.storage.local.get({ backendUrl: DEFAULT_BACKEND });
  const query = new URLSearchParams({ url });
  const endpoint = `${backendUrl.replace(/\/$/, '')}/check?${query.toString()}`;
  let phishing = false;
  try {
    const res = await fetch(endpoint, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      phishing = !!data.phishing;
    }
  } catch (e) {
    // fail open
  }
  resultCache.set(url, { phishing, exp: Date.now() + CACHE_TTL_MS });
  return phishing;
}

function pruneCache() {
  const now = Date.now();
  for (const [u, v] of resultCache.entries()) if (v.exp <= now) resultCache.delete(u);
}

chrome.webNavigation.onBeforeNavigate.addListener(async (details) => {
  const { tabId, url, frameId } = details;
  if (frameId !== 0) return; // only main frame
  if (tabId === -1) return;
  const host = normalizeForHost(url);
  pruneAllow();
  if (allowOverrides.has(host)) return;
  const phishing = await isPhishing(url);
  if (phishing) {
    const redirect = chrome.runtime.getURL(`blocked.html?url=${encodeURIComponent(url)}`);
    try { await chrome.tabs.update(tabId, { url: redirect }); } catch (e) {}
  }
});

// Message handlers
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg?.type === 'allowHost' && msg.host) {
    const ttlMs = typeof msg.ttlMs === 'number' ? msg.ttlMs : 5 * 60 * 1000;
    allowOverrides.set(msg.host, Date.now() + ttlMs);
    sendResponse({ ok: true });
    return true;
  }
});
