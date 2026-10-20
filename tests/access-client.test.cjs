const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const script = fs.readFileSync(path.join(__dirname, '../bull_project/bull_bot/webapp/access.js'), 'utf8');

function client(responder) {
  const calls = [], alerts = [], callbacks = {};
  class Socket { constructor(url) { this.url = url; } }
  const document = {
    documentElement: {}, querySelectorAll: () => [],
    addEventListener: (name, callback) => { callbacks[name] = callback; },
  };
  const window = {
    BULL_API_URL: 'https://api.example',
    Telegram: { WebApp: {initData: 'signed-telegram-data', showAlert: text => alerts.push(text)} },
    WebSocket: Socket,
    fetch: async (input, options) => {
      calls.push({input, options});
      return responder ? responder(input, options) : new Response('{}', {status: 200});
    },
  };
  let observe;
  const context = {window, document, location: {href: 'https://pages.example/index.html'},
    URL, Headers, Request, MutationObserver: class {constructor(cb) {observe = cb;} observe() {}}, console};
  vm.runInNewContext(script, context);
  return {window, calls, alerts, observe};
}

test('signed header is sent only to the configured API; existing request headers survive', async () => {
  const {window, calls} = client();
  await window.fetch('https://api.example/api/bookings/submit', {headers: {'Content-Type': 'application/json'}});
  assert.equal(calls[0].options.headers.get('X-Telegram-Init-Data'), 'signed-telegram-data');
  assert.equal(calls[0].options.headers.get('Content-Type'), 'application/json');
  await window.fetch('https://other.example/api/test', {headers: {Accept: 'image/png'}});
  assert.equal(calls[1].options.headers['X-Telegram-Init-Data'], undefined);
  await window.fetch(new Request('https://api.example/api/probe', {headers: {'X-Existing': 'yes'}}), {headers: {'X-New': 'yes'}});
  assert.equal(calls[2].options.headers.get('X-Existing'), 'yes');
  assert.equal(calls[2].options.headers.get('X-New'), 'yes');
});

test('expired access shows a clear message once and prevents a false success', async () => {
  const {window, alerts} = client(() => new Response(JSON.stringify({error: 'Войдите через /start'}), {status: 403}));
  await assert.rejects(() => window.fetch('https://api.example/api/probe'), /\/start/);
  await assert.rejects(() => window.fetch('https://api.example/api/probe'), /\/start/);
  assert.equal(alerts.length, 1);
});

test('images obtain a signed file URL before loading', async () => {
  const {window, calls, observe} = client(() => new Response(JSON.stringify({token: 'short-token'}), {status: 200}));
  const img = {dataset: {}, style: {}, src: '',
    getAttribute: key => key === 'data-access-src' ? 'https://api.example/api/care/passport-photo/7?t=1' : null,
    addEventListener() {}};
  observe([{type: 'attributes', target: img, addedNodes: []}]);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(new URL(img.src).searchParams.get('access_token'), 'short-token');
  assert.equal(new URL(img.src).searchParams.get('t'), '1');
  assert.equal(calls.length, 1);
  assert.equal(calls[0].options.headers.get('X-Telegram-Init-Data'), 'signed-telegram-data');
});

test('WebSocket uses signed Telegram identity only for our own host', () => {
  const {window} = client();
  assert.equal(new URL(new window.WebSocket('wss://api.example/ws/phones').url).searchParams.get('init_data'), 'signed-telegram-data');
  assert.equal(new URL(new window.WebSocket('wss://other.example/ws/phones').url).searchParams.get('init_data'), null);
});
