/*
 * Service worker aplikacji.
 * Cache'ujemy wyłącznie powłokę aplikacji (pliki statyczne).
 * Praca offline na danych nie jest jeszcze obsługiwana — żądania /api
 * zawsze idą do sieci, żeby nie pokazywać nieaktualnych kwot.
 *
 * Wszystkie adresy liczone są od katalogu, w którym leży ten plik (BASE),
 * bo aplikacja może być zainstalowana w podkatalogu domeny.
 */
const CACHE_NAME = 'ewidencja-shell-v2';
const BASE = new URL('./', self.location).pathname;
const INDEX = `${BASE}index.html`;
const SHELL = [BASE, INDEX, `${BASE}manifest.webmanifest`, `${BASE}icons/icon.svg`];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.pathname.startsWith(`${BASE}api`) || url.pathname === `${BASE}health`) {
    return;
  }
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match(INDEX)));
    return;
  }
  event.respondWith(
    caches.match(request).then((cached) => cached || fetch(request).then((response) => {
      const copy = response.clone();
      caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
      return response;
    })),
  );
});
