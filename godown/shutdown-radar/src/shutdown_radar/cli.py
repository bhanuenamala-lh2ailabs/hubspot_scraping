# -*- coding: utf-8 -*-
"""shutdown-radar CLI. `run-all` is the only command a human needs to type."""
from __future__ import annotations
import os, sys, json, asyncio, datetime
import typer
from rich.console import Console

from . import db as DB
from .models import norm_name
from .http import Http
from .sources import mca_stk, ibbi as IBBI, datagovin as DG, newsrss, liveness as LIVE
from . import resolve as RESOLVE, scoring, export as EXPORT, prequal as PQ

app = typer.Typer(add_completion=False, help="India startup shutdown radar")
con = Console()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "out")
DBP = os.path.join(DATA, "radar.sqlite")
LOGLINES: list[str] = []


def log(msg: str):
    LOGLINES.append(msg)
    con.print(msg)


def _db():
    return DB.connect(DBP)


@app.command()
def init():
    d = _db(); d.close()
    for p in ("manual/datagovin", "manual/ibbi", "manual/mca_stk", "manual/dpiit", "seeds", "out"):
        os.makedirs(os.path.join(DATA, p), exist_ok=True)
    log(f"initialised {DBP}")


@app.command("ingest-manual")
def ingest_manual():
    d = _db()
    log("[bold]ingest-manual[/bold]")
    log(" STK-7:")
    stk = mca_stk.ingest(d, os.path.join(DATA, "manual/mca_stk"), log)
    mca_stk.write_audit(stk["audit"], os.path.join(OUT, "stk7_parse_audit.csv"))
    log(" IBBI:")
    ib = IBBI.ingest(d, os.path.join(DATA, "manual/ibbi"), log)
    log(" data.gov.in CSVs:")
    dgc = DG.ingest_csvs(d, os.path.join(DATA, "manual/datagovin"), log)
    log(" DPIIT:")
    dp = _ingest_dpiit(d, os.path.join(DATA, "manual/dpiit"))
    DB.stat(d, "stk_audit", stk["audit"]); DB.stat(d, "ibbi", ib)
    DB.stat(d, "datagovin_csv", dgc); DB.stat(d, "dpiit", dp)
    n = d.execute("SELECT COUNT(*) c FROM entity").fetchone()["c"]
    log(f" entities in registry index: {n:,}")
    d.commit(); d.close()


def _ingest_dpiit(d, folder) -> int:
    if not os.path.isdir(folder): return 0
    import csv as _csv
    n = 0
    for fn in os.listdir(folder):
        if not fn.lower().endswith(".csv"): continue
        with open(os.path.join(folder, fn), encoding="utf-8-sig", errors="replace") as f:
            for row in _csv.DictReader(f):
                nm = (row.get("name") or row.get("Name") or
                      row.get("Startup Name") or "").strip()
                if not nm: continue
                d.execute("INSERT INTO dpiit_startup(name,name_norm,state,sector,"
                          "recognition_date) VALUES(?,?,?,?,?)",
                          (nm, norm_name(nm), row.get("state"), row.get("sector"),
                           row.get("recognition_date")))
                n += 1
    d.commit()
    log(f"  dpiit: {n} rows" if n else "  dpiit: none supplied (optional)")
    return n


@app.command()
def discover(since: str = "2024-01-01", source: str = "all"):
    d = _db()
    log("[bold]discover[/bold]")
    newsrss.load_seeds(d, os.path.join(DATA, "seeds/seed_shutdowns.csv"), log)

    async def go():
        async with Http(concurrency=10) as h:
            return await newsrss.discover(d, h, since, log, which=source)
    res = asyncio.run(go())
    DB.stat(d, "discovery", res)
    d.close()


@app.command()
def verify(limit: int = 400):
    """Runtime probe + registry status lookup for resolved CINs."""
    d = _db()
    log("[bold]verify[/bold]")

    async def go():
        async with Http(concurrency=6) as h:
            probe = await DG.probe(h, OUT, log)
            if not probe.get("ok"):
                return probe
            cins = [r["cin"] for r in d.execute(
                "SELECT DISTINCT ce.cin FROM candidate_entity ce JOIN entity e ON e.cin=ce.cin "
                "WHERE e.company_status IS NULL OR e.company_status LIKE '%STK-7%' "
                "OR e.company_status LIKE '%IBBI%' LIMIT ?", (limit,))]
            log(f"  looking up {len(cins)} CINs against the registry")
            done = 0
            for i in range(0, len(cins), 20):
                batch = cins[i:i + 20]
                recs = await asyncio.gather(*[DG.lookup_cin(h, c) for c in batch])
                for rec in recs:
                    if rec and DG.store_record(d, rec): done += 1
                d.commit()
            log(f"  registry statuses written: {done}")
            probe["looked_up"] = len(cins); probe["updated"] = done
            return probe
    p = asyncio.run(go())
    DB.stat(d, "datagovin", p)
    d.close()


@app.command()
def resolve(min_score: int = 88, limit: int = 0):
    d = _db()
    log("[bold]resolve[/bold]")

    async def go():
        async with Http(concurrency=6) as h:
            return await RESOLVE.resolve_all(
                d, h, log, min_score=min_score, limit=limit or None,
                overrides_path=os.path.join(DATA, "seeds/brand_cin_overrides.csv"))
    r = asyncio.run(go())
    DB.stat(d, "resolve", r["stats"]); DB.stat(d, "review", r["review"])
    d.close()


@app.command()
def liveness(limit: int = 120):
    """Only for candidates with no registry confirmation — that is where it adds signal."""
    d = _db()
    log("[bold]liveness[/bold]")
    rows = d.execute(
        "SELECT c.id, c.brand_name_norm FROM candidate c "
        "LEFT JOIN candidate_entity ce ON ce.candidate_id=c.id AND ce.is_confirmed=1 "
        "LEFT JOIN liveness l ON l.candidate_id=c.id "
        "WHERE ce.cin IS NULL AND l.candidate_id IS NULL "
        "AND c.discovery_source != 'stk7' LIMIT ?", (limit,)).fetchall()
    log(f"  checking {len(rows)} unconfirmed candidates")

    async def go():
        async with Http(concurrency=8, per_domain_delay=0.2) as h:
            out = []
            for i in range(0, len(rows), 8):
                chunk = rows[i:i + 8]
                res = await asyncio.gather(*[LIVE.check(h, r["brand_name_norm"]) for r in chunk])
                for r, v in zip(chunk, res):
                    d.execute("INSERT OR REPLACE INTO liveness VALUES(?,?,?,?,?,?,?,?,?,?)",
                              (r["id"], v["domain"], v["dns_resolves"], v["http_status"],
                               v["http_final_url"], v["ssl_expired"], v["rdap_status"],
                               v["wayback_last_capture"], v["liveness_score"], DB.now()))
                    out.append(v)
                d.commit()
                if i and i % 40 == 0: log(f"    ...{i}/{len(rows)}")
            return out
    res = asyncio.run(go())
    dead = sum(1 for v in res if (v["liveness_score"] or 0) >= 0.8)
    log(f"  liveness done: {dead}/{len(res)} look dead")
    d.close()


@app.command()
def score():
    d = _db()
    log("[bold]score[/bold]")
    ib = DB.get_stat(d, "ibbi", {}) or {}
    as_of = ib.get("as_of")
    seeds = {}
    sp = os.path.join(DATA, "seeds/seed_shutdowns.csv")
    if os.path.exists(sp):
        import csv as _csv
        for row in _csv.DictReader(open(sp, encoding="utf-8-sig")):
            seeds[norm_name(row.get("brand_name", ""))] = row

    cands = d.execute("SELECT * FROM candidate").fetchall()
    withheld = 0
    for c in cands:
        ev = d.execute("SELECT * FROM evidence WHERE candidate_id=?", (c["id"],)).fetchall()
        ent = d.execute(
            "SELECT e.* FROM candidate_entity ce JOIN entity e ON e.cin=ce.cin "
            "WHERE ce.candidate_id=? AND ce.is_confirmed=1 LIMIT 1", (c["id"],)).fetchone()
        lv = d.execute("SELECT * FROM liveness WHERE candidate_id=?", (c["id"],)).fetchone()
        dp = d.execute("SELECT 1 FROM dpiit_startup WHERE name_norm=? LIMIT 1",
                       (c["brand_name_norm"],)).fetchone()
        conf, tier, sd, why = scoring.score_candidate(c, ev, ent, lv, bool(dp), as_of)
        if "NOT scored" in why: withheld += 1
        s = seeds.get(c["brand_name_norm"], {})
        if not sd and s.get("shutdown_date"): sd = scoring.parse_date(s["shutdown_date"])
        yr = int(sd[:4]) if sd else (int(s["shutdown_year"]) if s.get("shutdown_year", "").isdigit() else None)
        d.execute(
            "INSERT OR REPLACE INTO scored(candidate_id,confidence,tier,shutdown_date,"
            "shutdown_year,reason,sector,city,funding_usd,investors,rationale,scored_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (c["id"], conf, tier, sd, yr, s.get("reason"), s.get("sector"), s.get("city"),
             s.get("funding_usd"), s.get("investors"), why, DB.now()))
    d.commit()
    DB.stat(d, "ibbi_withheld", withheld)
    import collections
    t = collections.Counter(r["tier"] for r in d.execute("SELECT tier FROM scored"))
    log(f"  tiers: {dict(t)}  | IBBI bonus withheld on {withheld} (currency guard)")
    d.close()



@app.command()
def prequal(limit: int = 400, github: bool = True):
    """LH2 pre-qualification scorecard (filterCriteria.md). 6 criteria, max 66 points.

    Peak engineering headcount is intentionally NOT automated — it needs a LinkedIn alumni
    search and spec §10 forbids LinkedIn scraping. It stays blank and is reported as
    `unscored`, which the routing text distinguishes from a genuine zero.
    """
    d = _db()
    log("[bold]prequal[/bold]  (scorecard from filterCriteria.md)")
    rows = d.execute(
        "SELECT s.candidate_id id, c.brand_name, s.shutdown_year, s.sector, s.funding_usd, "
        "       e.company_status, e.date_of_registration "
        "FROM scored s JOIN candidate c ON c.id=s.candidate_id "
        "LEFT JOIN candidate_entity ce ON ce.candidate_id=c.id AND ce.is_confirmed=1 "
        "LEFT JOIN entity e ON e.cin=ce.cin "
        "WHERE s.tier IN ('confirmed','probable') "
        "ORDER BY s.confidence DESC LIMIT ?", (limit,)).fetchall()
    log(f"  scoring {len(rows)} confirmed/probable candidates")

    async def go():
        out = []
        async with Http(concurrency=4, per_domain_delay=1.2) as h:
            for i, r in enumerate(rows, 1):
                gh = None
                if github:
                    gh = await PQ.github_lookup(h, r["brand_name"])
                inc = None
                if r["date_of_registration"]:
                    try: inc = int(str(r["date_of_registration"])[:4])
                    except Exception: inc = None
                res = PQ.score(funding_usd=r["funding_usd"], inc_year=inc,
                               shutdown_year=r["shutdown_year"], eng_headcount=None,
                               sector_text=r["sector"] or r["brand_name"],
                               github=gh, company_status=r["company_status"])
                d.execute(
                    "INSERT OR REPLACE INTO prequal(candidate_id,prequal_total,"
                    "prequal_max_possible,prequal_pct,prequal_routing,prequal_note,"
                    "prequal_unscored,pq_funding,pq_years,pq_eng_headcount,pq_sector,"
                    "pq_code_location,pq_legal_status,github_org,github_url,scored_at) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (r["id"], res["prequal_total"], res["prequal_max_possible"],
                     res["prequal_pct"], res["prequal_routing"], res["prequal_note"],
                     res["prequal_unscored"], res["pq_funding"] or None, res["pq_years"] or None,
                     res["pq_eng_headcount"] or None, res["pq_sector"] or None,
                     res["pq_code_location"] or None, res["pq_legal_status"] or None,
                     (gh or {}).get("org"), (gh or {}).get("url"), DB.now()))
                out.append(res)
                if i % 50 == 0:
                    d.commit(); log(f"    ...{i}/{len(rows)}")
        d.commit()
        return out
    res = asyncio.run(go())
    import collections as _c
    rt = _c.Counter(r["prequal_routing"] for r in res)
    log(f"  routing: {dict(rt)}")
    log(f"  fast-track (45+): {rt.get('fast_track',0)} | "
        f"cold-call (25-44): {rt.get('cold_call_first',0)} | "
        f"below 25: {rt.get('dont_pursue',0) + rt.get('dont_pursue_but_unscored',0)} "
        f"(of which {rt.get('dont_pursue_but_unscored',0)} only because criteria were UNSCORED)")
    DB.stat(d, "prequal", dict(rt))
    d.close()

@app.command("export")
def export_cmd(tier: str = "confirmed,probable", format: str = "csv,json"):
    d = _db()
    tiers = [t.strip() for t in tier.split(",") if t.strip()]
    fmts = [f.strip() for f in format.split(",") if f.strip()]
    res = EXPORT.write_export(d, OUT, tiers, fmts)
    rq = EXPORT.write_review(DB.get_stat(d, "review", []) or [], OUT, d)
    import collections
    tcount = collections.Counter(r["tier"] for r in d.execute("SELECT tier FROM scored"))
    ctx = {
        "stages": DB.get_stat(d, "stages", {}) or {},
        "discovery": DB.get_stat(d, "discovery", {}) or {},
        "stk_audit": DB.get_stat(d, "stk_audit", []) or [],
        "ibbi": DB.get_stat(d, "ibbi", {}) or {},
        "ibbi_withheld": DB.get_stat(d, "ibbi_withheld", 0) or 0,
        "datagovin": DB.get_stat(d, "datagovin", {}) or {},
        "truncation": DB.get_stat(d, "truncation", []) or [],
        "tiers": dict(tcount), "sample": res["rows"][:20],
        "no_url": sum(1 for r in res["rows"] if not r.get("primary_source_url")),
    }
    rp = EXPORT.write_report(OUT, ctx)
    log(f"  export: {len(res['rows'])} rows -> {res['paths']}")
    log(f"  review queue -> {rq}")
    log(f"  run report   -> {rp}")
    d.close()


@app.command()
def review():
    p = os.path.join(OUT, "review_queue.csv")
    con.print(f"review queue: {p}")


@app.command("run-all")
def run_all(since: str = "2024-01-01", liveness_limit: int = 120, verify_limit: int = 400):
    t0 = datetime.datetime.now()
    init()
    ingest_manual()
    discover(since=since, source="all")
    resolve(min_score=88, limit=0)
    verify(limit=verify_limit)
    liveness(limit=liveness_limit)
    score()
    prequal(limit=400, github=True)
    export_cmd(tier="confirmed,probable,possible", format="csv,json,xlsx")
    d = _db()
    DB.stat(d, "stages", {"elapsed": str(datetime.datetime.now() - t0)})
    d.close()
    con.print(f"[bold green]run-all complete in {datetime.datetime.now() - t0}[/bold green]")


if __name__ == "__main__":
    app()
