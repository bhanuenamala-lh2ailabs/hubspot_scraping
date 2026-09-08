# -*- coding: utf-8 -*-
"""Stage D pre-pass — satisfy what stored evidence can, crawl only the rest.

The spec allows reusing RAW HARVESTED FACTS from earlier runs (never their scores):
  NASSCOM   domain_age.json         RDAP registration dates (1,702 domains)
            NASSCOM_RANKED.csv      jd_chars, repo/review/cicd hit counts, evidence quotes,
                                    pre2024_basis — the harvest, not the grade
  GoodFirms companies.founded_year  source-stated year (a corroborator, not archival proof)
            people table            Stage E identity (702 LinkedIn URLs)

For every Stage A-C survivor this writes what is already known, then a crawl_todo.csv naming
exactly which fetches each firm still needs (wayback / homepage / careers). A firm whose
stored evidence already yields pre2024 PROVEN-equivalent + JD signals skips those fetches.

Nothing here is a finding of absence: a survivor with no stored evidence simply gets the full
fetch list. Usage: python3 stage_d_prepass.py
"""
import os, re, csv, json, collections, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "prequal_out")
NAS = os.path.join(HUB, "godown", "nasscom")
DB = os.path.join(HUB, "lh2-pipeline", "data", "pipeline.sqlite")


def J(p):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return None


def main():
    sv = list(csv.DictReader(open(os.path.join(OUT, "survivors.csv"), encoding="utf-8-sig")))

    # ---- stored evidence maps -------------------------------------------------
    # list of {domain, registered: 'YYYY-MM-DD', ...} -> map domain -> registered date
    dage = {(r.get("domain") or "").lower(): (r.get("registered") or "")
            for r in (J(f"{NAS}/domain_age.json") or [])}
    rk = {}
    for r in csv.DictReader(open(f"{NAS}/NASSCOM_RANKED.csv", encoding="utf-8-sig")):
        d = (r.get("domain") or "").lower().strip()
        if d: rk[d] = r
    con = sqlite3.connect(DB)
    gf_founded = {}
    for dom, fy in con.execute("SELECT domain, founded_year FROM companies WHERE founded_year IS NOT NULL"):
        gf_founded[(dom or "").lower()] = int(fy)
    gf_people = collections.defaultdict(list)
    for dom, nm, role, li in con.execute("SELECT domain, name, role, linkedin_url FROM people"):
        gf_people[(dom or "").lower()].append({"name": nm, "role": role or "", "linkedin": li or ""})
    nas_id = {}
    for r in (J(f"{NAS}/founders_websearch.json") or []):
        if r.get("person"):
            nas_id[(r.get("domain") or "").lower()] = {"name": r["person"], "role": r.get("title", ""),
                                                       "linkedin": r.get("linkedin", "")}

    SENIOR = re.compile(r"founder|ceo|cto|chief|managing director|\bmd\b|director|owner|president|vp", re.I)

    rows, todo = [], []
    stats = collections.Counter()
    for s in sv:
        d = s["domain"].lower()
        e = {"domain": d, "name": s["name"], "source": s["source"]}

        # -- pre-2024 from stored facts
        created = (dage.get(d) or "")[:10]
        gfy = gf_founded.get(d)
        basis, grade = [], ""
        rr = rk.get(d)
        if rr and rr.get("pre2024_basis"): basis.append(f'nasscom:{rr["pre2024_basis"]}')
        if created and created[:4].isdigit() and int(created[:4]) <= 2023:
            basis.append(f"rdap:{created}")
        if gfy and gfy <= 2023: basis.append(f"goodfirms_founded:{gfy}")
        # RDAP registration or a prior run's archival basis = artifact-grade; source-stated
        # year alone = one corroborator -> DOMAIN_ONLY-equivalent, still needs wayback.
        strong = [b for b in basis if b.startswith(("rdap:", "nasscom:wayback", "nasscom:archive"))]
        if len(basis) >= 2 and strong: grade = "EXISTED_2CORROB"
        elif strong: grade = "DOMAIN_ONLY"
        elif basis: grade = "SOURCE_STATED_ONLY"
        e["pre2024_prepass"], e["pre2024_basis"] = grade, "; ".join(basis)

        # -- JD facts from the earlier harvest (raw counts, not the old score)
        if rr:
            e["jd_chars"] = rr.get("jd_chars", "")
            e["repo_host_hits"] = rr.get("private_repo_host_hits", "")
            e["review_gate_hits"] = rr.get("review_gate_hits", "")
            e["cicd_hits"] = rr.get("cicd_hits", "")
            e["jd_evidence"] = (rr.get("evidence") or "")[:160]
        else:
            e["jd_chars"] = e["repo_host_hits"] = e["review_gate_hits"] = e["cicd_hits"] = ""
            e["jd_evidence"] = ""

        # -- identity from stored sources
        ident = None
        for p in gf_people.get(d, []):
            if SENIOR.search(p["role"] or ""):
                ident = p; break
        ident = ident or nas_id.get(d) or (gf_people.get(d) or [None])[0]
        if ident:
            e["contact_name"], e["contact_title"] = ident["name"], ident.get("role", "")
            e["contact_linkedin"] = ident.get("linkedin", "")
            e["identity_status"] = ("identity_full" if ident.get("linkedin")
                                    else "identity_name_only")
        else:
            e["contact_name"] = e["contact_title"] = e["contact_linkedin"] = ""
            e["identity_status"] = "identity_pending"

        # -- what still needs the web
        need = []
        if grade not in ("EXISTED_2CORROB",): need.append("wayback")
        need.append("homepage")                      # D1/D3/D4 owned-IP needs a live look at all
        if not (e["jd_chars"] and str(e["jd_chars"]).isdigit() and int(e["jd_chars"]) > 0):
            need.append("careers")
        e["crawl_needs"] = "+".join(need)
        stats[e["crawl_needs"]] += 1
        stats[f"identity:{e['identity_status']}"] += 1
        if grade: stats[f"pre2024:{grade}"] += 1
        rows.append(e)
        todo.append({"domain": d, "website": s["website"], "name": s["name"], "needs": e["crawl_needs"]})

    cols = list(rows[0].keys())
    with open(os.path.join(OUT, "evidence_prepass.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    with open(os.path.join(OUT, "crawl_todo.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["domain", "website", "name", "needs"]); w.writeheader(); w.writerows(todo)

    print(f"prepass over {len(rows)} survivors:")
    for k, v in sorted(stats.items()): print(f"   {k:<38}{v}")
    wb = sum(1 for t in todo if "wayback" in t["needs"])
    cr = sum(1 for t in todo if "careers" in t["needs"])
    print(f"\ncrawl volume: wayback {wb}, homepage {len(todo)}, careers {cr}")


main()
