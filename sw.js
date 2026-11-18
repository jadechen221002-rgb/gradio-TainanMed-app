/* Service Worker:離線備援頁 + 靜態資源快取
 * 注意:Gradio 的資料互動需要連線伺服器,因此 API 請求一律走網路,不做快取。 */
const VERSION = "v1";
const CORE_CACHE = `tainan-core-${VERSION}`;
const ASSET_CACHE = `tainan-assets-${VERSION}`;
const PRECACHE = [
  "/offline",
  "/manifest.webmanifest",
  "/pwa/icons/icon-192.png",
  "/pwa/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CORE_CACHE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => ![CORE_CACHE, ASSET_CACHE].includes(k))
            .map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Gradio API / 事件串流 / 上傳下載:永遠走網路
  if (url.pathname.startsWith("/gradio_api") || url.pathname.startsWith("/queue")) return;

  // 頁面導覽:網路優先,斷線時顯示離線頁
  if (req.mode === "navigate") {
    event.respondWith(fetch(req).catch(() => caches.match("/offline")));
    return;
  }

  // PWA 圖示:快取優先
  if (url.pathname.startsWith("/pwa/")) {
    event.respondWith(caches.match(req).then((hit) => hit || fetch(req)));
    return;
  }

  // Gradio 前端靜態檔(檔名含 hash):先用快取、背景更新
  if (url.pathname.startsWith("/assets/")) {
    event.respondWith(
      caches.open(ASSET_CACHE).then(async (cache) => {
        const hit = await cache.match(req);
        const network = fetch(req)
          .then((res) => {
            if (res.ok) cache.put(req, res.clone());
            return res;
          })
          .catch(() => hit);
        return hit || network;
      })
    );
  }
});
