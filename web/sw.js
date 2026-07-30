const CACHE = "musix-v3";
const ASSETS = ["./manifest.json"];

self.addEventListener("install", e => {
  // Only cache static assets, NOT index.html — always fetch fresh HTML
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  // Delete all old caches on activate
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener("fetch", e => {
  const url = e.request.url;

  // Never cache API calls
  if (url.includes("onrender.com")) return;

  // Network-first for HTML — ensures updates always propagate
  if (url.endsWith("/") || url.includes("index.html")) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match("./"))
    );
    return;
  }

  // Cache-first for other static assets
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request))
  );
});
