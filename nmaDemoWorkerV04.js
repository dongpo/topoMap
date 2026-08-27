const CACHE_NAME = "nma-agentic-v0.4-vs1";
const GLYPH_PREFIX = "https://cdn.protomaps.com/fonts/pbf/";

const PINNED_RUNTIME_ASSETS = [
  "https://unpkg.com/maplibre-gl@4.7.0/dist/maplibre-gl.css",
  "https://unpkg.com/maplibre-gl@4.7.0/dist/maplibre-gl.js",
  "https://unpkg.com/pmtiles@4.3.0/dist/pmtiles.js",
];

const LOCAL_APP_SHELL = [
  "./nmaAgentDemoV04.html",
  "./data/knowledge/portrayal-graph.json",
  "./data/demo/five-scene-demo.json",
  "./data/demo/pmtiles-capability-catalog.json",
  "./assets/symbols/nlsc112v5.4/school.svg",
  "./assets/symbols/nlsc112v5.4/fire-hydrant.svg",
  "./assets/symbols/nlsc112v5.4/police.svg",
  "./assets/symbols/nlsc112v5.4/fish-pond.svg",
  "./assets/symbols/nlsc112v5.4/post.svg",
  "./out1120902.pmtiles",
];

self.addEventListener("install", event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await cache.addAll(LOCAL_APP_SHELL);
    await Promise.allSettled(
      PINNED_RUNTIME_ASSETS.map(asset => cache.add(new Request(asset, {mode: "cors"})))
    );
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter(name => name.startsWith("nma-") && name !== CACHE_NAME).map(name => caches.delete(name)));
    await self.clients.claim();
  })());
});

function isRuntimeRequest(url) {
  return PINNED_RUNTIME_ASSETS.includes(url.href) || url.href.startsWith(GLYPH_PREFIX);
}

function isLocalShellRequest(url) {
  const canonical = new URL(url.href);
  canonical.search = "";
  return LOCAL_APP_SHELL.some(asset => new URL(asset, self.location.href).href === canonical.href);
}

function isLocalPmtiles(url) {
  return url.origin === self.location.origin && url.pathname.endsWith("/out1120902.pmtiles");
}

async function pmtilesRangeResponse(request, url, cache) {
  let full = await cache.match(url.href);
  if (!full) {
    full = await fetch(new Request(url.href));
    if (!full.ok) return full;
    await cache.put(url.href, full.clone());
  }
  const range = request.headers.get("range");
  if (!range) return full;
  const match = /^bytes=(\d+)-(\d*)$/.exec(range);
  if (!match) return new Response("Unsupported range", {status: 416});
  const bytes = await full.arrayBuffer();
  const start = Number(match[1]);
  const requestedEnd = match[2] ? Number(match[2]) : bytes.byteLength - 1;
  const end = Math.min(requestedEnd, bytes.byteLength - 1);
  if (start > end || start >= bytes.byteLength) {
    return new Response("Range not satisfiable", {
      status: 416,
      headers: {"Content-Range": `bytes */${bytes.byteLength}`},
    });
  }
  const body = bytes.slice(start, end + 1);
  return new Response(body, {
    status: 206,
    headers: {
      "Accept-Ranges": "bytes",
      "Content-Length": String(body.byteLength),
      "Content-Range": `bytes ${start}-${end}/${bytes.byteLength}`,
      "Content-Type": full.headers.get("Content-Type") || "application/octet-stream",
    },
  });
}

self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);
  if (!isRuntimeRequest(url) && !isLocalShellRequest(url)) return;

  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    if (isLocalPmtiles(url)) return pmtilesRangeResponse(event.request, url, cache);
    if (isLocalShellRequest(url)) {
      try {
        const response = await fetch(event.request);
        if (response.ok) event.waitUntil(cache.put(event.request, response.clone()));
        return response;
      } catch (error) {
        const fallback = await cache.match(event.request, {ignoreSearch: true});
        if (fallback) return fallback;
        throw error;
      }
    }
    const cached = await cache.match(event.request, {ignoreSearch: false});
    if (cached) return cached;
    const response = await fetch(event.request);
    if (response.ok || response.type === "opaque") {
      event.waitUntil(cache.put(event.request, response.clone()));
    }
    return response;
  })());
});

self.addEventListener("message", event => {
  if (event.data?.type !== "NMA_CACHE_STATUS" || !event.ports[0]) return;
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    const cached = [];
    const missing = [];
    for (const asset of PINNED_RUNTIME_ASSETS) {
      (await cache.match(asset) ? cached : missing).push(asset);
    }
    event.ports[0].postMessage({cache_name: CACHE_NAME, cached, missing});
  })());
});
