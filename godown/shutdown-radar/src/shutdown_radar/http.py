# -*- coding: utf-8 -*-
"""Cached, rate-limited, retrying HTTP. Cache key = SHA256(url + body) per the spec."""
from __future__ import annotations
import os, json, time, hashlib, asyncio
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CACHE = os.path.join(ROOT, ".cache")
# Identifiable with contact info, per spec §10 — but deliberately WITHOUT the token
# "python-httpx". data.gov.in silently hangs (ReadTimeout, never a 4xx) on any User-Agent
# containing it, including httpx's own default. Diagnosed by A/B: curl UA -> HTTP 200 in
# 2s, python-httpx UA -> timeout at 45s against the identical URL.
UA = "shutdown-radar/1.0 (research bot; contact rahul.dhali@lh2holdings.com)"

_domain_lock: dict[str, float] = {}
_lock = asyncio.Lock()


def _key(url: str, body: Optional[str]) -> str:
    return hashlib.sha256((url + (body or "")).encode()).hexdigest()


def cache_get(url: str, body: Optional[str] = None) -> Optional[str]:
    p = os.path.join(CACHE, _key(url, body))
    if os.path.exists(p):
        try: return open(p, encoding="utf-8").read()
        except Exception: return None
    return None


def cache_put(url: str, text: str, body: Optional[str] = None):
    os.makedirs(CACHE, exist_ok=True)
    try: open(os.path.join(CACHE, _key(url, body)), "w", encoding="utf-8").write(text)
    except Exception: pass


class Http:
    """One req/sec per domain, bounded global concurrency, transparent cache."""

    def __init__(self, concurrency: int = 10, use_cache: bool = True, per_domain_delay: float = 1.0):
        self.sem = asyncio.Semaphore(concurrency)
        self.use_cache = use_cache
        self.delay = per_domain_delay
        self.client: Optional[httpx.AsyncClient] = None
        self.stats = {"hit": 0, "miss": 0, "error": 0}

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=15.0), follow_redirects=True,
            headers={"User-Agent": UA, "Accept-Language": "en-IN,en;q=0.9"})
        return self

    async def __aexit__(self, *a):
        if self.client: await self.client.aclose()

    async def _throttle(self, url: str):
        host = httpx.URL(url).host or ""
        async with _lock:
            last = _domain_lock.get(host, 0.0)
            wait = self.delay - (time.monotonic() - last)
            if wait > 0: await asyncio.sleep(wait)
            _domain_lock[host] = time.monotonic()

    @retry(stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=1.5, min=2, max=20),
           retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
           reraise=False)
    async def _raw(self, method: str, url: str, **kw) -> Optional[httpx.Response]:
        await self._throttle(url)
        r = await self.client.request(method, url, **kw)
        if r.status_code in (429, 500, 502, 503, 504):
            raise httpx.HTTPStatusError("retry", request=r.request, response=r)
        return r

    async def get_text(self, url: str) -> Optional[str]:
        if self.use_cache:
            c = cache_get(url)
            if c is not None:
                self.stats["hit"] += 1; return c
        async with self.sem:
            try:
                r = await self._raw("GET", url)
            except Exception:
                self.stats["error"] += 1; return None
        if r is None or r.status_code >= 400:
            self.stats["error"] += 1; return None
        self.stats["miss"] += 1
        cache_put(url, r.text)
        return r.text

    async def get_json(self, url: str):
        t = await self.get_text(url)
        if not t: return None
        try: return json.loads(t)
        except Exception: return None

    async def head_or_get(self, url: str):
        """Liveness probe — never cached, we want the live verdict."""
        async with self.sem:
            try:
                await self._throttle(url)
                return await self.client.get(url, timeout=10.0)
            except Exception:
                return None
