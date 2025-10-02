(function(){
  const params = new URLSearchParams(location.search);
  const originalUrl = params.get('url') || document.referrer || '';
  document.getElementById('url').textContent = originalUrl || 'URL bị chặn';

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
