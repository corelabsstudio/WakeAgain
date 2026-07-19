/* WakeAgain PWA — app shell cache (network-first for API) */
const CACHE = "wakeagain-shell-v2";
const PRECACHE = [
  "/app/",
  "/app/index.html",
  "/app/app.css",
  "/app/app.js",
  "/styles.css",
  "/js/api.js",
  "/manifest.webmanifest",
  "/assets/logo-mark.png",
  "/assets/logo-mark-256.png",
  "/favicon.svg",
  "/get-app.html",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  // Never cache API
  if (url.pathname.startsWith("/api/")) return;

  // Same-origin only
  if (url.origin !== self.location.origin) return;

  // Showcase feed/register: always network, never serve stale form layout
  if (url.pathname.indexOf("showcase") !== -1) {
    event.respondWith(fetch(req));
    return;
  }

  // Network first for HTML navigations; cache fallback
  if (req.mode === "navigate" || (req.headers.get("accept") || "").includes("text/html")) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          // Do not cache showcase pages (form split / feed-only)
          if (url.pathname.indexOf("showcase") === -1) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => caches.match(req).then((r) => r || caches.match("/app/index.html")))
    );
    return;
  }

  // Assets: cache first, then network
  event.respondWith(
    caches.match(req).then((hit) => {
      if (hit) return hit;
      return fetch(req).then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return res;
      });
    })
  );
});
