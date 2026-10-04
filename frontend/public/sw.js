/* Service worker: the whole tool must open and work with no signal.
   - App shell: cache-first.
   - /shared/** (models + templates, ~2 MB): cache-first, fetched once; this is the "side-load" the brief talks about.
   - /api/** : never cached; the app queues records (src/lib/offlineQueue.ts) and runs the models locally instead. */
const CACHE = "karibu-v1";
const SHELL = ["/", "/index.html", "/manifest.webmanifest"];
const SHARED = [
  "/shared/models/intent.json",
  "/shared/models/langid.json",
  "/shared/models/aspect.json",
  "/shared/models/sentiment.json",
  "/shared/templates/replies.json",
  "/shared/templates/labels.json",
  "/shared/templates/listing.json",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((c) => c.addAll(SHELL).then(() => c.addAll(SHARED).catch(() => {})))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.pathname.startsWith("/api") || url.origin !== self.location.origin) return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(event.request, copy));
          }
          return res;
        })
        .catch(() => (event.request.mode === "navigate" ? caches.match("/index.html") : Response.error()));
    })
  );
});
