const DEFAULT_BACKEND = 'http://localhost:5000';

async function loadSettings() {
  const { backendUrl } = await chrome.storage.local.get({ backendUrl: DEFAULT_BACKEND });
  document.getElementById('backendUrl').value = backendUrl;
}

async function saveSettings() {
  const backendUrl = document.getElementById('backendUrl').value.trim() || DEFAULT_BACKEND;
  await chrome.storage.local.set({ backendUrl });
  showStatus('connectionStatus', 'Đã lưu cài đặt.', 'success');
}

async function testConnection() {
  const backendUrl = document.getElementById('backendUrl').value.trim() || DEFAULT_BACKEND;
  const statusDiv = document.getElementById('connectionStatus');
  
  showStatus('connectionStatus', 'Đang kiểm tra kết nối...', 'neutral');
  
  try {
    const response = await fetch(`${backendUrl.replace(/\/$/, '')}/health`, {
      method: 'GET',
      cache: 'no-store'
    });
    
    if (response.ok) {
      const data = await response.json();
      showStatus('connectionStatus', `Kết nối thành công! Backend hoạt động bình thường.`, 'success');
    } else {
      showStatus('connectionStatus', `Lỗi kết nối: HTTP ${response.status}`, 'error');
    }
  } catch (error) {
    showStatus('connectionStatus', `Không thể kết nối tới backend: ${error.message}`, 'error');
  }
}

async function loadStats() {
  try {
    const response = await chrome.runtime.sendMessage({ type: 'getCache' });
    document.getElementById('statsInfo').innerHTML = `
      <div><strong>Cache URLs:</strong> ${response.cacheSize} URLs</div>
      <div><strong>Tạm thời cho phép:</strong> ${response.allowOverridesSize} hosts</div>
    `;
  } catch (error) {
    document.getElementById('statsInfo').textContent = 'Không thể tải thống kê.';
  }
}

function showStatus(elementId, message, type) {
  const element = document.getElementById(elementId);
  element.textContent = message;
  element.className = `status-info status-${type}`;
}

// Khởi tạo khi DOM ready
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  loadStats();
  
  // Event listeners
  document.getElementById('save').addEventListener('click', saveSettings);
  document.getElementById('testConnection').addEventListener('click', testConnection);
});