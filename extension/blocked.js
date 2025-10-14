(function(){
  // Helper function để format confidence không làm tròn lên
  function formatConfidence(confidence) {
    return Math.floor(parseFloat(confidence) * 100);
  }
  
  const params = new URLSearchParams(location.search);
  const originalUrl = params.get('url') || document.referrer || '';
  const source = params.get('source');
  const confidence = params.get('confidence');
  const type = params.get('type');
  
  // Hiển thị URL
  document.getElementById('url').textContent = originalUrl || 'URL bị chặn';
  
  // Hiển thị thông tin phát hiện
  if (source || confidence || type) {
    document.getElementById('detectionInfo').style.display = 'block';
    
    // Hiển thị nguồn phát hiện với thông tin dễ hiểu
    if (source) {
      const sourceText = getSourceText(source);
      document.getElementById('source').textContent = sourceText;
      
      // Cập nhật thông điệp chính dựa trên nguồn
      const mainMessage = getMainMessage(source);
      document.getElementById('mainMessage').textContent = mainMessage;
    }
    
    // Hiển thị độ tin cậy nếu có
    if (confidence && confidence !== '0' && confidence !== 'null') {
      document.getElementById('confidenceItem').style.display = 'block';
      const confidencePercent = formatConfidence(confidence);
      document.getElementById('confidence').textContent = confidencePercent;
    }
    
    // Hiển thị loại nếu có
    if (type && type !== 'null' && type !== 'unknown') {
      document.getElementById('typeItem').style.display = 'block';
      document.getElementById('type').textContent = type;
    }
  }

  function getSourceText(source) {
    switch(source) {
      case 'database': return 'Cơ sở dữ liệu phishing';
      case 'model': return 'Mô hình AI học máy';
      case 'error': return 'Lỗi kiểm tra';
      default: return source || 'Không xác định';
    }
  }
  
  function getMainMessage(source) {
    switch(source) {
      case 'database': return 'Trang web này đã được xác định là phishing trong cơ sở dữ liệu.';
      case 'model': return 'Trang web này được mô hình AI phát hiện có khả năng cao là phishing.';
      case 'error': return 'Không thể kiểm tra trang web này, nhưng đã được chặn để đảm bảo an toàn.';
      default: return 'Trang bạn sắp truy cập có thể là phishing.';
    }
  }

  function extractHost(u){
    try { return new URL(u).hostname; } catch(e) { return ''; }
  }

  document.getElementById('goBack').addEventListener('click', () => {
    history.length > 1 ? history.back() : (location.href = 'about:blank');
  });

  document.getElementById('proceed').addEventListener('click', async () => {
    const host = extractHost(originalUrl);
    if (!host) return;
    chrome.runtime.sendMessage({ type: 'allowHost', host, ttlMs: 10 * 1000 }, (resp) => {
      if (resp && resp.ok) {
        try { location.href = originalUrl; } catch(e) { window.open(originalUrl, '_blank'); }
      }
    });
  });
})();
