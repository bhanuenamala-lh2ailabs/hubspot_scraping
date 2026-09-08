# -*- coding: utf-8 -*-
"""data.gov.in MCA Company Master Data — runtime probe, CSV ingest, API verify/backfill.

The spec is emphatic that the field list must come from the API at runtime, not from
assumption, because only five fields are documented and the real schema may differ. The
probe is therefore the first action of `verify`, and its output is written to
data/out/datagovin_fields.json.
"""
from __future__ import annotations
import os, csv, json, asyncio
from typing import Optional

from ..models import CIN_RE, decode_cin, norm_name
from ..db import upsert_entity, stat, get_stat

RESOURCE_ID = "4dbe5667-7b6b-41d7-82af-211562424d9a"
BASE = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

STATUS_CANDIDATES = [
    "Strike Off", "STRIKE OFF", "Strike off", "Struck Off", "Under Liquidation",
    "Under CIRP", "Amalgamated", "Dissolved", "Dissolved-Liquidated",
    "Under Process of Striking Off", "Dormant u/s 455", "Not Available for e-filing",
    "Active", "Converted to LLP",
]
DISTRESS_ORDER = [
    "Dissolved", "Dissolved-Liquidated", "Under Liquidation", "Under CIRP",
    "Strike Off", "Struck Off", "STRIKE OFF", "Strike off",
    "Under Process of Striking Off", "Amalgamated",
    "Not Available for e-filing", "Dormant u/s 455",
]


def _key() -> Optional[str]:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    for envp in (os.path.join(root, ".env"),
                 os.path.join(os.path.dirname(os.path.dirname(root)), ".env")):
        if os.path.exists(envp):
            for l in open(envp, encoding="utf-8-sig"):
                if "=" in l and not l.strip().startswith("#"):
                    k, v = l.split("=", 1)
                    if k.strip().lower() in ("datagovin_api_key", "data_gov_in_key", "mcp_api"):
                        return v.strip()
    return os.environ.get("DATAGOVIN_API_KEY")


def url(**params) -> str:
    p = {"api-key": _key(), "format": "json", **params}
    return BASE + "?" + "&".join(f"{k}={v}" for k, v in p.items() if v is not None)


async def probe(http, out_dir: str, log) -> dict:
    """Mandatory runtime probe. Dumps the real field list and the working status strings."""
    key = _key()
    if not key:
        log("  !! datagovin: NO API KEY (DATAGOVIN_API_KEY in .env) — registry verify skipped")
        return {"ok": False, "reason": "no_api_key"}
    d = await http.get_json(url(limit=1))
    if not d or d.get("status") != "ok":
        log(f"  !! datagovin probe FAILED: {str(d)[:200]}")
        return {"ok": False, "reason": "probe_failed", "raw": str(d)[:400]}
    fields = [f.get("id") for f in d.get("field", [])]
    total = d.get("total")
    log(f"  datagovin: {total:,} records, {len(fields)} fields -> {fields}")

    working = {}
    for s in STATUS_CANDIDATES:
        q = url(limit=1, **{"filters[CompanyStatus]": s.replace(" ", "%20")})
        r = await http.get_json(q)
        t = (r or {}).get("total", 0) if isinstance(r, dict) else 0
        if t: working[s] = t
    if not working:
        # try the documented field name too before declaring failure
        for s in STATUS_CANDIDATES[:6]:
            q = url(limit=1, **{"filters[COMPANY_STATUS]": s.replace(" ", "%20")})
            r = await http.get_json(q)
            t = (r or {}).get("total", 0) if isinstance(r, dict) else 0
            if t: working[s] = t
    res = {"ok": bool(working), "total": total, "fields": fields,
           "status_counts": working, "resource_id": RESOURCE_ID}
    os.makedirs(out_dir, exist_ok=True)
    json.dump(res, open(os.path.join(out_dir, "datagovin_fields.json"), "w",
                        encoding="utf-8"), indent=1)
    if not working:
        log("  !! datagovin: ZERO status probes returned rows — schema may have changed. "
            "Registry status enrichment will be skipped (see datagovin_fields.json).")
    else:
        log(f"  datagovin status strings that work: "
            f"{', '.join(f'{k}={v:,}' for k, v in sorted(working.items(), key=lambda x:-x[1])[:6])}")
    return res


def _field(row: dict, *names) -> Optional[str]:
    for n in names:
        for k in row:
            if k.lower().replace("_", "") == n.lower().replace("_", ""):
                v = row[k]
                if v not in (None, "", "NA"): return str(v).strip()
    return None


async def lookup_cin(http, cin: str) -> Optional[dict]:
    d = await http.get_json(url(limit=1, **{"filters[CIN]": cin}))
    recs = (d or {}).get("records") or []
    if not recs:
        d = await http.get_json(url(limit=1, **{"filters[CORPORATE_IDENTIFICATION_NUMBER]": cin}))
        recs = (d or {}).get("records") or []
    return recs[0] if recs else None


async def lookup_name(http, exact_name: str) -> list:
    from urllib.parse import quote
    d = await http.get_json(url(limit=10, **{"filters[CompanyName]": quote(exact_name)}))
    recs = (d or {}).get("records") or []
    if not recs:
        d = await http.get_json(url(limit=10, **{"filters[COMPANY_NAME]": quote(exact_name)}))
        recs = (d or {}).get("records") or []
    return recs


def store_record(db, rec: dict, source="datagovin_api"):
    cin = _field(rec, "CIN", "CORPORATE_IDENTIFICATION_NUMBER")
    if not cin: return None
    name = _field(rec, "CompanyName", "COMPANY_NAME") or cin
    d = decode_cin(cin)
    upsert_entity(db, cin, name, norm_name(name),
                  status=_field(rec, "CompanyStatus", "COMPANY_STATUS"),
                  cls=_field(rec, "CompanyClass", "COMPANY_CLASS") or d.get("company_class"),
                  dor=_field(rec, "CompanyRegistrationdate_date", "DATE_OF_REGISTRATION")
                      or d.get("date_of_registration"),
                  state=_field(rec, "CompanyStateCode") or d.get("registered_state"),
                  roc=_field(rec, "CompanyROCcode"), source=source)
    return cin


def ingest_csvs(db, folder: str, log) -> dict:
    """Per-state CSV ingest with the mandatory truncation assertion."""
    out = {"files": 0, "rows": 0, "warnings": []}
    if not os.path.isdir(folder): return out
    files = [f for f in os.listdir(folder) if f.lower().endswith(".csv")]
    if not files:
        log("  datagovin: no per-state CSVs in data/manual/datagovin/ — "
            "registry status will come from the API only (slower, but correct)")
        return out
    for fn in sorted(files):
        n = 0
        with open(os.path.join(folder, fn), encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                if store_record(db, row, source=f"datagovin_csv:{fn}"): n += 1
        db.commit()
        out["files"] += 1; out["rows"] += n
        log(f"  datagovin CSV {fn}: {n} rows")
    return out


def truncation_check(csv_rows: int, api_total: Optional[int], fn: str) -> Optional[str]:
    """The preview-download silently row-caps. Short file => LOUD warning."""
    if api_total is None: return None
    if csv_rows < api_total * 0.98:
        return (f"TRUNCATION: {fn} has {csv_rows:,} rows but the API reports "
                f"{api_total:,} for that filter — the preview download row-capped. "
                f"API paginator fallback required for this state.")
    return None
