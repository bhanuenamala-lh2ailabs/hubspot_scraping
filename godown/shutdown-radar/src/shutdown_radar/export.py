# -*- coding: utf-8 -*-
"""CSV/JSON/XLSX export, review queue, and run_report.md."""
from __future__ import annotations
import os, csv, json, datetime, collections

COLS = ["brand_name", "legal_name", "cin", "company_status", "company_class",
        "date_of_registration", "registered_state", "tier", "confidence",
        "shutdown_date", "shutdown_year", "sector", "city", "funding_usd", "investors",
        "reason", "domain", "dns_resolves", "wayback_last_capture", "dpiit_recognised",
        "evidence_count", "primary_source_url", "primary_source_name",
        "all_source_urls", "rationale",
        "prequal_total", "prequal_max_possible", "prequal_pct", "prequal_routing",
        "prequal_unscored", "pq_funding", "pq_years", "pq_eng_headcount", "pq_sector",
        "pq_code_location", "pq_legal_status", "github_url", "prequal_note"]


def rows_for_export(db, tiers):
    q = """
    SELECT c.id, c.brand_name, s.confidence, s.tier, s.shutdown_date, s.shutdown_year,
           s.reason, s.sector, s.city, s.funding_usd, s.investors, s.rationale,
           e.cin, e.legal_name, e.company_status, e.company_class, e.date_of_registration,
           e.registered_state,
           l.domain, l.dns_resolves, l.wayback_last_capture,
           q.prequal_total, q.prequal_max_possible, q.prequal_pct, q.prequal_routing,
           q.prequal_unscored, q.prequal_note, q.pq_funding, q.pq_years,
           q.pq_eng_headcount, q.pq_sector, q.pq_code_location, q.pq_legal_status,
           q.github_url
    FROM scored s
    JOIN candidate c ON c.id = s.candidate_id
    LEFT JOIN candidate_entity ce ON ce.candidate_id = c.id AND ce.is_confirmed = 1
    LEFT JOIN entity e ON e.cin = ce.cin
    LEFT JOIN liveness l ON l.candidate_id = c.id
    LEFT JOIN prequal q ON q.candidate_id = c.id
    """
    seed_ids = {r["id"] for r in db.execute(
        "SELECT id FROM candidate WHERE discovery_source='manual_seed'")}
    out = []
    for r in db.execute(q):
        # Hand-curated seeds ALWAYS export, whatever they score. They are ground truth we
        # put in — a human verified the shutdown and cited a source — not candidates the
        # pipeline discovered and must justify. Most sit at 0.255 only because their brand
        # cannot be mapped to a legal entity and their domain is still parked, neither of
        # which is evidence they are alive. Their true tier and confidence are printed
        # unchanged, so nothing is overstated; they are simply not silently dropped.
        if tiers and r["tier"] not in tiers and r["id"] not in seed_ids: continue
        ev = db.execute("SELECT source_url, source_name FROM evidence WHERE candidate_id=? "
                        "AND source_url IS NOT NULL", (r["id"],)).fetchall()
        urls = [e["source_url"] for e in ev if e["source_url"]]
        # Provenance is mandatory (§0) but a URL is not always obtainable: seed_shutdowns.csv
        # carries a source NAME ("Inc42") and no link. Recording the name keeps every row
        # sourced without inventing a URL, which would be the worse failure.
        names = [n["source_name"] for n in db.execute(
            "SELECT DISTINCT source_name FROM evidence WHERE candidate_id=? "
            "AND source_name IS NOT NULL", (r["id"],))]
        n_ev = db.execute("SELECT COUNT(*) n FROM evidence WHERE candidate_id=?",
                          (r["id"],)).fetchone()["n"]
        dp = db.execute("SELECT 1 FROM dpiit_startup d JOIN candidate c2 ON c2.id=? "
                        "AND d.name_norm=c2.brand_name_norm LIMIT 1", (r["id"],)).fetchone()
        out.append({
            "brand_name": r["brand_name"], "legal_name": r["legal_name"], "cin": r["cin"],
            "company_status": r["company_status"], "company_class": r["company_class"],
            "date_of_registration": r["date_of_registration"],
            "registered_state": r["registered_state"], "tier": r["tier"],
            "confidence": round(r["confidence"], 3), "shutdown_date": r["shutdown_date"],
            "shutdown_year": r["shutdown_year"], "sector": r["sector"], "city": r["city"],
            "funding_usd": r["funding_usd"], "investors": r["investors"],
            "reason": r["reason"], "domain": r["domain"], "dns_resolves": r["dns_resolves"],
            "wayback_last_capture": r["wayback_last_capture"],
            "dpiit_recognised": 1 if dp else 0, "evidence_count": n_ev,
            "prequal_total": r["prequal_total"], "prequal_max_possible": r["prequal_max_possible"],
            "prequal_pct": r["prequal_pct"], "prequal_routing": r["prequal_routing"],
            "prequal_unscored": r["prequal_unscored"], "prequal_note": r["prequal_note"],
            "pq_funding": r["pq_funding"], "pq_years": r["pq_years"],
            "pq_eng_headcount": r["pq_eng_headcount"], "pq_sector": r["pq_sector"],
            "pq_code_location": r["pq_code_location"], "pq_legal_status": r["pq_legal_status"],
            "github_url": r["github_url"],
            "primary_source_url": urls[0] if urls else "",
            "primary_source_name": (names[0] if names else ""),
            "all_source_urls": " | ".join(dict.fromkeys(urls))[:1000],
            "rationale": r["rationale"]})
    out.sort(key=lambda x: (-x["confidence"], x["brand_name"] or ""))
    return out


def write_export(db, out_dir: str, tiers, formats=("csv",)) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.date.today().strftime("%Y%m%d")
    rows = rows_for_export(db, tiers)
    paths = {}
    base = os.path.join(out_dir, f"india_startup_shutdowns_{stamp}")
    if "csv" in formats:
        p = base + ".csv"
        with open(p, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
            w.writeheader(); w.writerows(rows)
        paths["csv"] = p
    if "json" in formats:
        p = base + ".json"
        json.dump(rows, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        paths["json"] = p
    if "xlsx" in formats:
        try:
            from openpyxl import Workbook
            wb = Workbook(); ws = wb.active; ws.title = "shutdowns"
            ws.append(COLS)
            for r in rows: ws.append([r.get(c, "") for c in COLS])
            ws.freeze_panes = "A2"
            p = base + ".xlsx"; wb.save(p); paths["xlsx"] = p
        except Exception:
            pass
    return {"rows": rows, "paths": paths}


def write_review(review, out_dir: str, db) -> str:
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "review_queue.csv")
    poss = db.execute(
        "SELECT c.brand_name, s.confidence, s.tier, s.rationale FROM scored s "
        "JOIN candidate c ON c.id=s.candidate_id WHERE s.tier='possible' "
        "ORDER BY s.confidence DESC").fetchall()
    with open(p, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["type", "brand_name", "best_cin", "best_legal_name", "score",
                    "alternatives", "reason", "confidence", "tier", "rationale"])
        for r in sorted(review, key=lambda x: -x["score"]):
            w.writerow(["unconfirmed_match", r["brand_name"], r["best_cin"],
                        r["best_legal_name"], r["score"], r["alternatives"], r["reason"],
                        "", "", ""])
        for r in poss:
            w.writerow(["possible_tier", r["brand_name"], "", "", "", "", "",
                        round(r["confidence"], 3), r["tier"], r["rationale"]])
    return p


def write_report(out_dir: str, ctx: dict) -> str:
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "run_report.md")
    L = []
    A = L.append
    A(f"# shutdown-radar — run report\n")
    A(f"Generated {datetime.datetime.now().isoformat(timespec='seconds')}\n")

    A("## Stage counts\n")
    A("| Stage | Result |\n|---|---|")
    for k, v in ctx.get("stages", {}).items(): A(f"| {k} | {v} |")

    A("\n## Discovery by source\n")
    A("| Source | Candidates |\n|---|---:|")
    for k, v in (ctx.get("discovery", {}).get("counts") or {}).items(): A(f"| {k} | {v} |")

    zero = ctx.get("discovery", {}).get("zero_sources") or []
    A("\n## ⚠ Sources returning ZERO\n")
    if zero:
        for z in zero: A(f"- **{z}** returned nothing this run")
    else:
        A("None — every source returned at least one row.")

    A("\n## STK-7 row-count assertion\n")
    A("| File | Stated | Extracted | Delta | Status |\n|---|---:|---:|---:|---|")
    for a in ctx.get("stk_audit", []):
        A(f"| {a['filename']} | {a['stated']} | {a['extracted']} | {a['delta']} | {a['status']} |")

    A("\n## IBBI coverage gap\n")
    ib = ctx.get("ibbi", {})
    A(f"- List as-of date: **{ib.get('as_of') or 'UNKNOWN'}**")
    A(f"- Rows ingested: {ib.get('rows', 0)} ({ib.get('with_cin', 0)} with a CIN)")
    A(f"- Any candidate whose shutdown_date is later than the as-of date gets **no IBBI "
      f"bonus** — absence from a point-in-time list is not evidence. "
      f"{ctx.get('ibbi_withheld', 0)} candidates were affected.")

    A("\n## data.gov.in probe\n")
    dg = ctx.get("datagovin", {})
    if dg.get("ok"):
        A(f"- Records: {dg.get('total'):,}")
        A(f"- Fields reported by the API: `{', '.join(dg.get('fields') or [])}`")
        A("- Working status strings:")
        for k, v in sorted((dg.get("status_counts") or {}).items(), key=lambda x: -x[1]):
            A(f"  - `{k}` → {v:,}")
    else:
        A(f"- **PROBE FAILED / SKIPPED**: {dg.get('reason')}")

    tr = ctx.get("truncation") or []
    A("\n## CSV truncation assertion\n")
    if tr:
        for t in tr: A(f"- ⚠ {t}")
    else:
        A("No per-state CSVs supplied, so no truncation check was needed "
          "(registry status came from the API).")

    A("\n## Tier distribution\n")
    A("| Tier | Rows |\n|---|---:|")
    for k, v in (ctx.get("tiers") or {}).items(): A(f"| {k} | {v} |")

    A("\n## Sample — top 20 by confidence\n")
    A("| Brand | Tier | Conf | CIN | Status | Shutdown | Rationale |\n|---|---|---:|---|---|---|---|")
    for r in (ctx.get("sample") or [])[:20]:
        A(f"| {r['brand_name']} | {r['tier']} | {r['confidence']} | {r['cin'] or ''} | "
          f"{r['company_status'] or ''} | {r['shutdown_date'] or ''} | {(r['rationale'] or '')[:110]} |")

    open(p, "w", encoding="utf-8").write("\n".join(L))
    return p
