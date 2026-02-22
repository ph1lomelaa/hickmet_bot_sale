(function() {
  const urlParams = new URLSearchParams(window.location.search);
  const apiUrlParam = urlParams.get('api_url');
  const defaultApiUrl = apiUrlParam || 'https://hickmet.duckdns.org';

  if (!window.BULL_API_URL) {
    window.BULL_API_URL = defaultApiUrl;
  }

  // Для отладки
  console.log('🌐 BULL_API_URL:', window.BULL_API_URL);
})();
