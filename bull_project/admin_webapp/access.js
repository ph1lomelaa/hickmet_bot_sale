/* Shared Mini App access client. Keep the three deployed copies identical. */
(() => {
  if (window.BullAccess) return;
  const nativeFetch = window.fetch.bind(window);
  const api = new URL(window.BULL_API_URL, location.href);
  const initData = () => window.Telegram?.WebApp?.initData || '';
  const isApi = url => url.origin === api.origin && url.pathname.startsWith('/api/');
  const isMedia = url => isApi(url) && /^\/api\/care\/passport-(photo|original|pdf)\/\d+$/.test(url.pathname);
  let notified = false;
  function notify(message) {
    if (notified) return;
    notified = true;
    if (window.Telegram?.WebApp?.showAlert) window.Telegram.WebApp.showAlert(message);
    else window.alert(message);
  }
  window.fetch = async (input, options = {}) => {
    const url = new URL(input instanceof Request ? input.url : input, location.href);
    if (!isApi(url)) return nativeFetch(input, options);
    const headers = new Headers(input instanceof Request ? input.headers : undefined);
    new Headers(options.headers).forEach((value, key) => headers.set(key, value));
    headers.set('X-Telegram-Init-Data', initData());
    const response = await nativeFetch(input, {...options, headers});
    if (response.status === 401 || response.status === 403) {
      const error = await response.clone().json().catch(() => ({}));
      const message = error.error || 'Откройте бота и введите новый пароль через /start. Ваши брони и история сохранены.';
      notify(message);
      throw new Error(message);
    }
    return response;
  };
  async function mediaUrl(raw) {
    const url = new URL(raw, location.href);
    if (!isMedia(url)) return raw;
    const response = await window.fetch(`${api.origin}/api/access/media-token?path=${encodeURIComponent(url.pathname)}`);
    if (!response.ok) throw new Error('Не удалось получить доступ к файлу');
    const data = await response.json();
    url.searchParams.set('access_token', data.token);
    return url.href;
  }
  // Native images and downloads cannot send headers. Use short, path-bound links.
  async function protectImage(img) {
    const raw = img.getAttribute('data-access-src') || img.getAttribute('src');
    if (!raw || img.dataset.accessSource === raw) return;
    const url = new URL(raw, location.href);
    if (!isMedia(url) || url.searchParams.has('access_token')) return;
    img.dataset.accessSource = raw;
    try {
      img.addEventListener('load', () => { img.style.display = ''; }, {once: true});
      const href = await mediaUrl(raw);
      if (img.dataset.accessSource === raw) img.src = href;
    } catch (_) { /* The access message is shown by fetch. */ }
  }
  const observer = new MutationObserver(records => {
    for (const record of records) {
      if (record.type === 'attributes') protectImage(record.target);
      for (const node of record.addedNodes) {
        if (node.nodeType !== 1) continue;
        if (node.matches('img')) protectImage(node);
        node.querySelectorAll('img').forEach(protectImage);
      }
    }
  });
  observer.observe(document.documentElement, {childList: true, subtree: true, attributes: true, attributeFilter: ['src', 'data-access-src']});
  document.querySelectorAll('img').forEach(protectImage);
  document.addEventListener('click', async event => {
    const link = event.target.closest?.('a[href]');
    if (!link || !isMedia(new URL(link.href, location.href))) return;
    event.preventDefault();
    const target = link.target === '_blank' ? window.open('about:blank', '_blank') : null;
    try {
      const href = await mediaUrl(link.href);
      if (target) target.location.href = href;
      else {
        const download = document.createElement('a');
        download.href = href;
        download.download = link.download;
        // The detached anchor does not bubble back into this handler.
        download.click();
      }
    } catch (_) { if (target) target.close(); }
  }, true);
  const NativeWebSocket = window.WebSocket;
  window.WebSocket = class extends NativeWebSocket {
    constructor(raw, protocols) {
      const url = new URL(raw, location.href);
      if (url.host === api.host && url.pathname.startsWith('/ws/')) url.searchParams.set('init_data', initData());
      if (protocols === undefined) super(url.href);
      else super(url.href, protocols);
    }
  };
  window.BullAccess = {mediaUrl};
})();
