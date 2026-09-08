# -*- coding: utf-8 -*-
"""STK-7 C-PACE consolidated strike-off notices -> entities + candidates.

Structure of these PDFs, established by inspection rather than assumption:

* Each file is a run of per-state notices. Every notice repeats its table TWICE —
  once with a "Company Hindi Name" column, then again with the English "Company Name".
  Both carry the same CIN, so we key rows on CIN and prefer the English name. Page parity
  is NOT reliable, so we read the header text of each table instead.

* The stated company count appears in the notice header as a bracketed number, but there
  is one notice PER STATE per file, so the filename count is the file-level total. We take
  the stated total from the filename (e.g. "819-Companies") and assert the extracted row
  count against it — the spec's only ground-truth check.

* registered_state comes from the CIN itself (chars 7-8), not from a column. See
  models.decode_cin. That is more reliable than parsing the Hindi state name.

Streams page by page; a 94-page 900-row file never lands in memory whole.
"""
from __future__ import annotations
import os, re, csv, hashlib
from typing import Iterator, Optional
import pdfplumber

from ..models import CIN_RE, decode_cin, norm_name
from ..db import upsert_entity, upsert_candidate, add_evidence

# "819-Companies", "Companies-927", "Notice-of-665-Companies", "llps-909", "STK7-412"
_COUNT_PATTERNS = [
    re.compile(r"(\d{2,5})[-_ ]*(?:companies|compani|llps|company)", re.I),
    re.compile(r"(?:companies|compani|llps|company|stk-?7)[-_ ]*(\d{2,5})", re.I),
    re.compile(r"[-_](\d{3,5})[-_]"),
]
_DATE_RE = re.compile(r"(20\d{2})(\d{2})(\d{2})")


def stated_count(filename: str) -> Optional[int]:
    base = os.path.basename(filename)
    base = re.sub(r"\(\d+\)", "", base)
    base = _DATE_RE.sub(" ", base)          # don't read the date as a count
    for pat in _COUNT_PATTERNS:
        m = pat.search(base)
        if m:
            n = int(m.group(1))
            if 10 <= n <= 20000: return n
    return None


def file_date(filename: str) -> Optional[str]:
    m = _DATE_RE.search(os.path.basename(filename))
    if not m: return None
    y, mo, d = m.groups()
    return f"{y}-{mo}-{d}"


def _is_english(s: str) -> bool:
    if not s: return False
    letters = [c for c in s if c.isalpha()]
    if not letters: return False
    return sum(1 for c in letters if ord(c) < 128) / len(letters) > 0.7


def iter_rows(path: str) -> Iterator[dict]:
    """Yield {cin, name, name_is_english} for every table row carrying a CIN."""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            try:
                tables = page.extract_tables() or []
            except Exception:
                continue
            for tb in tables:
                for row in tb:
                    if not row: continue
                    cells = [(c or "").strip() for c in row]
                    joined = " ".join(cells)
                    m = CIN_RE.search(joined.upper())
                    if not m: continue
                    cin = m.group(0)
                    # the name is the longest non-CIN, non-workitem cell
                    name = ""
                    for c in cells:
                        cu = c.upper()
                        if not c or CIN_RE.search(cu): continue
                        if re.fullmatch(r"[A-Z]{2}\d{7}", cu): continue   # work item
                        if re.fullmatch(r"\d{1,5}", c): continue          # serial
                        if len(c) > len(name): name = c
                    yield {"cin": cin, "name": name, "name_is_english": _is_english(name)}
            page.flush_cache()
            page.get_textmap.cache_clear()


def parse_file(path: str) -> dict:
    """-> {cin: best_name} plus the audit numbers for this file."""
    best: dict[str, str] = {}
    seen_rows = 0
    for r in iter_rows(path):
        seen_rows += 1
        cin, name, eng = r["cin"], r["name"], r["name_is_english"]
        if cin not in best:
            best[cin] = name if eng else ""
        if eng and len(name) > len(best.get(cin) or ""):
            best[cin] = name
    return {"path": path, "rows_seen": seen_rows, "cins": best}


def ingest(db, folder: str, log) -> dict:
    """Parse every STK PDF in `folder`. Returns the audit rows."""
    audit, total_new = [], 0
    if not os.path.isdir(folder):
        log(f"  mca_stk: folder missing — skipped"); return {"audit": [], "entities": 0}
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(".pdf"))
    if not files:
        log("  mca_stk: no PDFs found — pipeline continues with zero STK evidence")
        return {"audit": [], "entities": 0}

    content_hashes: dict[str, str] = {}
    for fn in files:
        path = os.path.join(folder, fn)
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if h in content_hashes:
            log(f"  SKIP duplicate content: {fn} == {content_hashes[h]}")
            audit.append({"filename": fn, "stated": "", "extracted": "", "delta": "",
                          "status": f"DUPLICATE of {content_hashes[h]}"})
            continue
        content_hashes[h] = fn

        stated = stated_count(fn)
        as_of = file_date(fn)
        try:
            res = parse_file(path)
        except Exception as e:
            log(f"  PARSE FAIL {fn}: {type(e).__name__}: {e}")
            audit.append({"filename": fn, "stated": stated or "", "extracted": 0,
                          "delta": "", "status": f"PARSE FAILED: {type(e).__name__}"})
            continue

        cins = res["cins"]
        extracted = len(cins)
        if stated:
            delta = extracted - stated
            pct = abs(delta) / stated * 100
            status = "PASS" if pct <= 2 else "FAIL >2%"
            if pct > 2:
                log(f"  !! ROW-COUNT ASSERTION FAILED {fn}: stated {stated}, extracted "
                    f"{extracted} ({pct:.1f}% off)")
        else:
            delta, pct, status = "", "", "no stated count in filename"
        audit.append({"filename": fn, "stated": stated or "", "extracted": extracted,
                      "delta": delta, "status": status})

        for cin, name in cins.items():
            d = decode_cin(cin)
            legal = name or cin
            upsert_entity(db, cin, legal, norm_name(legal),
                          status="Struck Off (STK-7)", cls=d.get("company_class"),
                          dor=d.get("date_of_registration"), state=d.get("registered_state"),
                          source=f"stk7:{fn}")
            # registry-origin candidate: the bootstrapped long tail
            if name:
                cid = upsert_candidate(db, name, norm_name(name), "stk7")
                db.execute("INSERT OR IGNORE INTO candidate_entity(candidate_id,cin,match_score,"
                           "match_method,is_confirmed) VALUES(?,?,?,?,1)",
                           (cid, cin, 100.0, "exact"))
                if add_evidence(db, cid, "stk7", source_name="MCA STK-7 C-PACE",
                                as_of_date=as_of, snippet=f"STK-7 strike-off notice {fn}",
                                source_url="https://www.mca.gov.in/content/mca/global/en/"
                                           "data-and-reports/rd-roc-info/companies-struck-roc.html",
                                raw={"file": fn, "cin": cin}):
                    total_new += 1
        db.commit()
        log(f"  {fn}: stated {stated or '?'}, extracted {extracted} [{status}]")
    return {"audit": audit, "entities": total_new}


def write_audit(audit: list, out_csv: str):
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["filename", "stated_company_count", "extracted_count", "delta", "status"])
        for a in audit:
            w.writerow([a["filename"], a["stated"], a["extracted"], a["delta"], a["status"]])
