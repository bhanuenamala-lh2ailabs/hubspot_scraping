# -*- coding: utf-8 -*-
"""Domain liveness — only for candidates with no registry confirmation."""
from __future__ import annotations
import re, ssl, socket, asyncio, datetime
from typing import Optional
import dns.resolver

PARKED = ("sedoparking", "afternic", "buy this domain", "domain for sale",
          "hugedomains", "godaddy.com/forsale", "parkingcrew", "bodis.com")
TLDS = (".com", ".in", ".co", ".ai", ".co.in", ".io")


def guess_domains(brand_norm: str) -> list[str]:
    s = brand_norm.replace(" ", "")
    if len(s) < 3: return []
    return [s + t for t in TLDS]


def dns_ok(domain: str) -> Optional[bool]:
    try:
        dns.resolver.resolve(domain, "A", lifetime=5)
        return True
    except dns.resolver.NXDOMAIN:
        return False
    except Exception:
        return None


def ssl_expired(domain: str) -> Optional[bool]:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=6) as s:
            with ctx.wrap_socket(s, server_hostname=domain) as ss:
                na = ss.getpeercert().get("notAfter")
        exp = datetime.datetime.strptime(na, "%b %d %H:%M:%S %Y %Z")
        return exp < datetime.datetime.now()
    except Exception:
        return None


async def check(http, brand_norm: str) -> dict:
    out = {"domain": None, "dns_resolves": None, "http_status": None, "http_final_url": None,
           "ssl_expired": None, "rdap_status": None, "wayback_last_capture": None,
           "liveness_score": 0.0}
    for d in guess_domains(brand_norm):
        ok = dns_ok(d)
        if ok is None: continue
        out["domain"] = d
        out["dns_resolves"] = 1 if ok else 0
        if not ok:
            out["liveness_score"] = 0.9        # NXDOMAIN is the strongest single signal
            break
        r = await http.head_or_get("https://" + d)
        if r is None:
            r = await http.head_or_get("http://" + d)
        if r is not None:
            out["http_status"] = r.status_code
            out["http_final_url"] = str(r.url)
            body = (r.text or "")[:4000].lower()
            if any(p in body for p in PARKED): out["liveness_score"] += 0.6
            if r.status_code >= 500: out["liveness_score"] += 0.4
            elif r.status_code == 200: out["liveness_score"] -= 0.2
        else:
            out["liveness_score"] += 0.5       # refused
        out["ssl_expired"] = 1 if ssl_expired(d) else 0
        if out["ssl_expired"]: out["liveness_score"] += 0.25
        rd = await http.get_json(f"https://rdap.org/domain/{d}")
        if rd:
            statuses = " ".join(rd.get("status") or []).lower()
            out["rdap_status"] = statuses[:80]
            if any(k in statuses for k in ("client hold", "redemption", "pending delete")):
                out["liveness_score"] += 0.5
        cdx = await http.get_json(
            f"http://web.archive.org/cdx/search/cdx?url={d}&output=json&limit=-1")
        if cdx and len(cdx) > 1:
            out["wayback_last_capture"] = cdx[-1][1] if len(cdx[-1]) > 1 else None
        break
    out["liveness_score"] = max(0.0, min(1.0, out["liveness_score"]))
    return out
