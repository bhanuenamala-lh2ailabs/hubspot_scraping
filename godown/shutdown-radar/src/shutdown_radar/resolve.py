# -*- coding: utf-8 -*-
"""Brand -> CIN. Override, then exact API, then local fuzzy, then disambiguate.

Never silently takes the top fuzzy hit: auto-confirm needs score >= 92 AND a unique winner
AND a registration-date sanity check. Everything else lands in review_queue.csv.
"""
from __future__ import annotations
import os, re, csv, asyncio
from typing import Optional
from rapidfuzz import process, fuzz

from .models import norm_name, decode_cin
from .sources import datagovin

SUFFIX_FORMS = ["{b} PRIVATE LIMITED", "{b} TECHNOLOGIES PRIVATE LIMITED",
                "{b} LABS PRIVATE LIMITED", "{b} INDIA PRIVATE LIMITED",
                "{b} SOLUTIONS PRIVATE LIMITED"]


def load_overrides(path: str) -> dict:
    out = {}
    if not os.path.exists(path): return out
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            b = norm_name(row.get("brand_name", ""))
            if b and row.get("cin"):
                out[b] = (row["cin"].strip(), (row.get("legal_name") or "").strip())
    return out


def build_index(db):
    rows = db.execute("SELECT cin, legal_name, legal_name_norm, date_of_registration, "
                      "registered_state, company_class FROM entity").fetchall()
    return (rows,
            {r["legal_name_norm"]: dict(r) for r in rows},
            [r["legal_name_norm"] for r in rows])


def _year_windows(db, seeds_path: str) -> dict:
    """candidate_id -> (earliest, latest) plausible incorporation year.

    §6 says disambiguate on `DATE_OF_REGISTRATION <= founding_year + 1`. Measured against
    real hits, that rule alone is not enough and neither is a shutdown-year ceiling:

        Hike      founded 2012 -> matched a 2007 Punjab entity   (5 years too EARLY)
        Bluelearn founded 2021 -> matched a 2023 entity          (too late)
        GenWise   founded 2023 -> matched a 2025 entity          (too late)
        Muvin     shut down 2024 -> matched a 2025 entity        (incorporated after death)

    Indian company names get re-registered constantly, so a name match is not a match. The
    window is founded-3 .. founded+1 where the founding year is known (incorporation can
    precede a public launch by a year or two, not by five), otherwise anything up to the
    shutdown year. Anything outside goes to review rather than being silently attached —
    a wrong CIN stamps a dead company with a live "Active" status, which is worse than none.
    """
    import csv as _csv
    founded = {}
    if os.path.exists(seeds_path):
        for row in _csv.DictReader(open(seeds_path, encoding="utf-8-sig")):
            f = (row.get("founded") or "").strip()
            if f.isdigit():
                founded[norm_name(row.get("brand_name", ""))] = int(f)
    out = {}
    for r in db.execute("SELECT s.candidate_id, s.shutdown_year, c.brand_name_norm "
                        "FROM scored s JOIN candidate c ON c.id=s.candidate_id"):
        fy = founded.get(r["brand_name_norm"])
        if fy:
            out[r["candidate_id"]] = (fy - 3, fy + 1)
        elif r["shutdown_year"]:
            out[r["candidate_id"]] = (None, int(r["shutdown_year"]))
    return out


async def resolve_all(db, http, log, min_score: int = 88, limit: Optional[int] = None,
                      overrides_path: str = "") -> dict:
    ov = load_overrides(overrides_path)
    cutoffs = _year_windows(db, os.path.join(os.path.dirname(overrides_path),
                                             "seed_shutdowns.csv"))
    rows, by_norm, choices = build_index(db)
    log(f"  entity index: {len(rows):,} CINs")
    cands = db.execute(
        "SELECT c.id, c.brand_name, c.brand_name_norm, c.discovery_source FROM candidate c "
        "LEFT JOIN candidate_entity ce ON ce.candidate_id=c.id "
        "WHERE ce.candidate_id IS NULL").fetchall()
    if limit: cands = cands[:limit]
    log(f"  unresolved candidates: {len(cands):,}")

    stats = {"override": 0, "exact": 0, "fuzzy_confirmed": 0, "review": 0, "none": 0}
    review = []
    for c in cands:
        bn, norm = c["brand_name"], c["brand_name_norm"]
        win = cutoffs.get(c["id"])

        if norm in ov:
            cin, legal = ov[norm]
            db.execute("INSERT OR IGNORE INTO candidate_entity VALUES(?,?,?,?,1)",
                       (c["id"], cin, 100.0, "override"))
            stats["override"] += 1; continue

        def year_ok(dor) -> bool:
            """The incorporation-year window, applied on EVERY path.

            It has to be every path. An entity pulled in by an earlier unguarded run sits
            in the local index, and `BLUELEARN PRIVATE LIMITED` normalises to `bluelearn`,
            so the local-exact branch would re-attach the wrong CIN before the API branch
            (which did have the check) ever ran. A guard on one route only is no guard.
            """
            if not win: return True
            m = re.search(r"(19|20)\d{2}", str(dor or ""))
            if not m: return True
            y, (lo, hi) = int(m.group(0)), win
            return not ((hi and y > hi) or (lo and y < lo))

        hit = by_norm.get(norm)
        if hit:
            if year_ok(hit.get("date_of_registration")):
                db.execute("INSERT OR IGNORE INTO candidate_entity VALUES(?,?,?,?,1)",
                           (c["id"], hit["cin"], 100.0, "exact"))
                stats["exact"] += 1; continue
            stats["local_rejected_wrong_year"] = stats.get("local_rejected_wrong_year", 0) + 1
            review.append({"candidate_id": c["id"], "brand_name": bn,
                           "best_cin": hit["cin"],
                           "best_legal_name": hit.get("legal_name") or "",
                           "score": 100.0, "unique": False, "alternatives": "",
                           "reason": f"exact name match but incorporated "
                                     f"{str(hit.get('date_of_registration'))[:4]}, outside "
                                     f"plausible window {win[0] or '-'}..{win[1]}"})
            # fall through to the API lookup — a better-dated entity may exist

        # §6 step 2 — EXACT API LOOKUP. Essential, not optional: the local index is built
        # from STK-7/IBBI files, which contain obscure struck-off firms, not funded
        # startups. A seed like Koo can never match locally because its legal entity was
        # never struck off. Without this step every seed loses its CIN, takes the -0.25
        # penalty, and drops out of the export entirely.
        api_hit = None
        for form in [bn] + [f.format(b=bn) for f in SUFFIX_FORMS]:
            recs = await datagovin.lookup_name(http, form.upper())
            if not recs: continue
            for rec in recs:
                # §6 disambiguation — a name match alone is NOT a match. data.gov.in returns
                # every company that has ever held the name, and Indian company names get
                # re-registered: searching "Muvin" or "GenWise" returns entities
                # incorporated in 2025, long after the startup we care about died. Attaching
                # those would stamp a dead company with a live "Active" status, which is
                # worse than leaving the CIN blank.
                dor = datagovin._field(rec, "CompanyRegistrationdate_date",
                                       "DATE_OF_REGISTRATION") or ""
                reg_year = None
                m = re.search(r"(19|20)\d{2}", str(dor))
                if m: reg_year = int(m.group(0))
                if reg_year and win:
                    lo, hi = win
                    if (hi and reg_year > hi) or (lo and reg_year < lo):
                        stats["api_rejected_wrong_year"] =                             stats.get("api_rejected_wrong_year", 0) + 1
                        review.append({"candidate_id": c["id"], "brand_name": bn,
                                       "best_cin": datagovin._field(rec, "CIN",
                                           "CORPORATE_IDENTIFICATION_NUMBER") or "",
                                       "best_legal_name": datagovin._field(rec, "CompanyName",
                                           "COMPANY_NAME") or "", "score": 100.0,
                                       "unique": False, "alternatives": "",
                                       "reason": f"name matched but incorporated {reg_year}, "
                                                 f"outside plausible window {lo or '-'}..{hi}"})
                        continue
                cin = datagovin.store_record(db, rec, source="datagovin_api:resolve")
                if cin:
                    api_hit = cin
                    by_norm[norm_name(
                        datagovin._field(rec, "CompanyName", "COMPANY_NAME") or "")] = {"cin": cin}
                    break
            if api_hit: break
        if api_hit:
            db.execute("INSERT OR IGNORE INTO candidate_entity VALUES(?,?,?,?,1)",
                       (c["id"], api_hit, 100.0, "exact_api"))
            stats["api_exact"] = stats.get("api_exact", 0) + 1
            db.commit(); continue

        best = process.extract(norm, choices, scorer=fuzz.token_set_ratio,
                               limit=5, score_cutoff=85)
        if not best:
            stats["none"] += 1; continue
        top = best[0]
        unique = len(best) == 1 or (len(best) > 1 and top[1] - best[1][1] >= 5)
        ent = by_norm[top[0]]
        # disambiguate with what we actually have: registration year must not post-date
        # the shutdown story by much
        ok_date = year_ok(ent.get("date_of_registration"))
        if top[1] >= 92 and unique and ok_date:
            db.execute("INSERT OR IGNORE INTO candidate_entity VALUES(?,?,?,?,1)",
                       (c["id"], ent["cin"], float(top[1]), "fuzzy_token_set"))
            stats["fuzzy_confirmed"] += 1
        else:
            db.execute("INSERT OR IGNORE INTO candidate_entity VALUES(?,?,?,?,0)",
                       (c["id"], ent["cin"], float(top[1]), "fuzzy_token_set"))
            review.append({"candidate_id": c["id"], "brand_name": bn,
                           "best_cin": ent["cin"], "best_legal_name": ent["legal_name"],
                           "score": round(top[1], 1), "unique": unique,
                           "alternatives": " | ".join(f"{b[0]}({b[1]:.0f})" for b in best[1:4]),
                           "reason": ("score<92" if top[1] < 92 else
                                      "ambiguous" if not unique else "date check")})
            stats["review"] += 1
    db.commit()
    log(f"  resolve: {stats}")
    return {"stats": stats, "review": review}
