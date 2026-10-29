/* All-time sales downloads use the same API and authentication as analytics. */
(() => {
  const menu = document.getElementById('sales-export-menu');
  const status = document.getElementById('sales-export-status');
  if (!menu || !status) return;
  const buttons = [...menu.querySelectorAll('[data-sales-export]')];
  let busy = false;

  async function download(format) {
    if (busy) return;
    busy = true;
    buttons.forEach(button => { button.disabled = true; });
    status.textContent = 'Подготавливаем все данные…';
    menu.setAttribute('aria-busy', 'true');
    try {
      const api = window.BULL_API_URL.replace(/\/$/, '');
      const response = await window.fetch(`${api}/api/admin/export?format=${format}`, {
        headers: {'ngrok-skip-browser-warning': '1'},
        cache: 'no-store'
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(typeof error.detail === 'string' ? error.detail :
          'Не удалось выгрузить данные. Повторите попытку.');
      }
      const type = response.headers.get('content-type') || '';
      const expected = format === 'csv' ? 'text/csv' :
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
      if (!type.includes(expected)) throw new Error('Сервер не вернул файл выгрузки.');
      const blob = await response.blob();
      if (!blob.size) throw new Error('Сервер вернул пустой файл.');
      const href = URL.createObjectURL(blob);
      const link = document.createElement('a');
      const stamp = new Date().toISOString().replace(/[:.]/g, '-');
      link.href = href;
      link.download = `bull_sales_all_${stamp}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      // Give the browser / Telegram webview time to consume the blob.
      setTimeout(() => URL.revokeObjectURL(href), 60000);
      status.textContent = 'Файл подготовлен. Скачивание началось.';
    } catch (error) {
      status.textContent = error.message || 'Ошибка соединения. Повторите попытку.';
    } finally {
      busy = false;
      buttons.forEach(button => { button.disabled = false; });
      menu.removeAttribute('aria-busy');
    }
  }

  buttons.forEach(button => button.addEventListener('click', () => download(button.dataset.salesExport)));
  document.addEventListener('click', event => {
    // The generated download link must not close its own progress message.
    if (event.isTrusted && !menu.contains(event.target)) menu.open = false;
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menu.open) {
      menu.open = false;
      menu.querySelector('summary').focus();
    }
  });
})();
