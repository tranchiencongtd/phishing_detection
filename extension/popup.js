(function() {
  let currentUrl = '';
  
  // Helper function để format confidence không làm tròn lên
  function formatConfidence(confidence) {
    return Math.floor(confidence * 100);
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

  // Khởi tạo popup
  async function init() {
    try {
      // Lấy tab hiện tại
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.url) {
        showError('Không thể lấy thông tin trang web hiện tại');
        return;
      }
      
      currentUrl = tab.url;
      document.getElementById('urlInfo').textContent = currentUrl;
      
      // Kiểm tra xem có nên bỏ qua URL này không
      if (shouldSkipUrl(currentUrl)) {
        showSpecialPage();
        return;
      }
      
      // Kiểm tra URL
      await checkCurrentUrl();
      
    } catch (error) {
      console.error('Init error:', error);
      showError('Lỗi khởi tạo: ' + error.message);
    }
  }
  
  // Kiểm tra URL hiện tại
  async function checkCurrentUrl() {
    if (!currentUrl) return;
    
    // Kiểm tra lại nếu là URL đặc biệt
    if (shouldSkipUrl(currentUrl)) {
      showSpecialPage();
      return;
    }
    
    showLoading();
    
    try {
      // Gửi yêu cầu kiểm tra đến background script
      const result = await chrome.runtime.sendMessage({
        type: 'checkUrl',
        url: currentUrl
      });
      
      if (result && result.url) {
        displayResult(result);
      } else {
        showError('Không nhận được kết quả từ backend');
      }
      
    } catch (error) {
      console.error('Check URL error:', error);
      showError('Lỗi kiểm tra: ' + error.message);
    }
  }
  
  // Hiển thị kết quả
  function displayResult(result) {
    const statusEl = document.getElementById('status');
    const detailsEl = document.getElementById('detectionDetails');
    
    // Hiển thị thông tin cơ bản
    detailsEl.style.display = 'block';
    document.getElementById('source').textContent = getSourceText(result.source);
    
    if (result.elapsed_ms) {
      document.getElementById('elapsed').textContent = Math.round(result.elapsed_ms) + 'ms';
    }
    
    // Xử lý theo kết quả
    switch (result.result) {
      case 'legitimate':
        showSafeStatus(result);
        break;
      case 'phishing':
        showDangerStatus(result);
        break;
      case 'unknown':
      default:
        showUnknownStatus(result);
        break;
    }
    
    // Hiển thị thông tin bổ sung
    if (result.type && result.type !== 'null') {
      document.getElementById('typeSection').style.display = 'block';
      document.getElementById('type').textContent = result.type;
    }
  }
  
  // Hiển thị trạng thái an toàn
  function showSafeStatus(result) {
    const statusEl = document.getElementById('status');
    statusEl.className = 'status-header status-safe';
    
    if (result.source === 'database') {
      // Từ database - hiển thị "An toàn"
      statusEl.innerHTML = `
        <div class="status-icon">✅</div>
        <div class="status-text">Website an toàn</div>
      `;
    } else if (result.source === 'model' && result.confidence !== null) {
      // Từ model - hiển thị % an toàn
      const safetyPercent = formatConfidence(result.confidence);
      statusEl.innerHTML = `
        <div class="status-icon">🛡️</div>
        <div class="status-text">Có thể an toàn (${safetyPercent}%)</div>
      `;
      showConfidenceBar(result.confidence, true);
    } else {
      statusEl.innerHTML = `
        <div class="status-icon">✅</div>
        <div class="status-text">Website hợp pháp</div>
      `;
    }
  }
  
  // Hiển thị trạng thái nguy hiểm
  function showDangerStatus(result) {
    const statusEl = document.getElementById('status');
    statusEl.className = 'status-header status-danger';
    
    if (result.source === 'database') {
      // Từ database - hiển thị "Không an toàn"
      statusEl.innerHTML = `
        <div class="status-icon">⚠️</div>
        <div class="status-text">Website không an toàn</div>
      `;
    } else if (result.source === 'model' && result.confidence !== null) {
      // Từ model - hiển thị % nguy hiểm
      const dangerPercent = formatConfidence(result.confidence);
      statusEl.innerHTML = `
        <div class="status-icon">🚨</div>
        <div class="status-text">Có thể phishing (${dangerPercent}%)</div>
      `;
      showConfidenceBar(result.confidence, false);
    } else {
      statusEl.innerHTML = `
        <div class="status-icon">⚠️</div>
        <div class="status-text">Website phishing</div>
      `;
    }
  }
  
  // Hiển thị trạng thái không xác định
  function showUnknownStatus(result) {
    const statusEl = document.getElementById('status');
    statusEl.className = 'status-header status-warning';
    statusEl.innerHTML = `
      <div class="status-icon">❓</div>
      <div class="status-text">Không thể xác định</div>
    `;
  }
  
  // Hiển thị cho trang đặc biệt (chrome://, about:, etc.)
  function showSpecialPage() {
    const statusEl = document.getElementById('status');
    statusEl.className = 'status-header status-loading';
    
    let pageType = 'Trang hệ thống';
    let icon = '🌐';
    
    if (currentUrl.includes('new-tab') || currentUrl.includes('newtab')) {
      pageType = 'Tab mới';
      icon = '📄';
    } else if (currentUrl.startsWith('chrome://')) {
      pageType = 'Trang Chrome';
      icon = '⚙️';
    } else if (currentUrl.startsWith('about:')) {
      pageType = 'Trang About';
      icon = 'ℹ️';
    } else if (currentUrl.startsWith('chrome-extension://')) {
      pageType = 'Extension';
      icon = '🧩';
    }
    
    statusEl.innerHTML = `
      <div class="status-icon">${icon}</div>
      <div class="status-text">${pageType}</div>
    `;
    
    // Ẩn nút refresh vì không cần thiết
    document.getElementById('refresh').style.display = 'none';
    
    // Hiển thị thông tin
    const detailsEl = document.getElementById('detectionDetails');
    detailsEl.style.display = 'block';
    document.getElementById('source').textContent = 'Không áp dụng';
    document.getElementById('elapsed').textContent = '-';
  }
  
  // Hiển thị thanh confidence
  function showConfidenceBar(confidence, isSafe) {
    const confidenceSection = document.getElementById('confidenceSection');
    const confidenceFill = document.getElementById('confidenceFill');
    const confidencePercent = document.getElementById('confidencePercent');
    const confidenceText = document.getElementById('confidenceText');
    const confidenceLabel = document.getElementById('confidenceLabel');
    
    confidenceSection.style.display = 'block';
    
    const percent = formatConfidence(confidence);
    confidenceFill.style.width = percent + '%';
    confidencePercent.textContent = percent + '%';
    
    if (isSafe) {
      confidenceFill.className = 'confidence-fill confidence-safe';
      confidenceLabel.textContent = 'Mức độ an toàn:';
      confidenceText.textContent = percent + '% an toàn';
    } else {
      confidenceFill.className = 'confidence-fill confidence-danger';
      confidenceLabel.textContent = 'Khả năng phishing:';
      confidenceText.textContent = percent + '% nguy hiểm';
    }
  }
  
  // Hiển thị trạng thái loading
  function showLoading() {
    const statusEl = document.getElementById('status');
    statusEl.className = 'status-header status-loading';
    statusEl.innerHTML = `
      <div class="status-icon">
        <div class="loading-spinner"></div>
      </div>
      <div class="status-text">Đang kiểm tra...</div>
    `;
    document.getElementById('detectionDetails').style.display = 'none';
  }
  
  // Hiển thị lỗi
  function showError(message) {
    const statusEl = document.getElementById('status');
    statusEl.className = 'status-header status-warning';
    statusEl.innerHTML = `
      <div class="status-icon">⚠️</div>
      <div class="status-text">${message}</div>
    `;
  }
  
  // Chuyển đổi source thành text hiển thị
  function getSourceText(source) {
    switch(source) {
      case 'database': return 'Cơ sở dữ liệu';
      case 'model': return 'Mô hình AI';
      case 'error': return 'Lỗi kiểm tra';
      default: return source || 'Không xác định';
    }
  }
  
  // Event listeners
  document.addEventListener('DOMContentLoaded', init);
  
  document.getElementById('refresh').addEventListener('click', () => {
    // Hiện lại nút refresh nếu bị ẩn
    document.getElementById('refresh').style.display = '';
    checkCurrentUrl();
  });
  
})();