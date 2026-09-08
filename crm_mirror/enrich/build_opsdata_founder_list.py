# -*- coding: utf-8 -*-
"""Turn the ops-data 307 into a COMPANY / FOUNDER / EMAIL list for the campaign.

Tracxn packs people into one blob: "Name; Title; email; bio" per person, people separated
by newlines. We unpack it and pick the person most likely to be able to sell the operating
playbook — founder/CEO first, then MD/director, then whoever has an email.

Never invents an address. A row with no email says so.
"""
import os, re, csv, sys, json, collections
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(HUB, "exports", "opsdata", "opsdata_healthy_500.json")
FILL = os.path.join(HERE, "opsdata_email_fill.json")
OUT = os.path.join(HUB, "exports", "opsdata")

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
GENERIC = ("info@", "contact@", "support@", "hello@", "sales@", "admin@", "enquiry@",
           "inquiry@", "care@", "help@", "office@", "team@", "mail@", "connect@")
# rank of seniority — who can actually decide to sell company data
RANK = [
    (re.compile(r"(?i)\b(co[- ]?founder|founder)\b"), 1),
    (re.compile(r"(?i)\b(ceo|chief executive)\b"), 1),
    (re.compile(r"(?i)\b(managing director|\bmd\b|owner|proprietor|chairman)\b"), 2),
    (re.compile(r"(?i)\b(coo|chief operating|cto|chief technology|cpo|cfo)\b"), 3),
    (re.compile(r"(?i)\b(president|partner|vice president|\bvp\b)\b"), 4),
    (re.compile(r"(?i)\bdirector\b"), 5),
    (re.compile(r"(?i)\bhead\b"), 6),
]


def seniority(title: str) -> int:
    for pat, r in RANK:
        if pat.search(title or ""): return r
    return 9


def parse_people(blob: str):
    """-> [{name, title, email}] from Tracxn's Key People Info blob."""
    out = []
    if not blob: return out
    for chunk in re.split(r"[\r\n]+", blob):
        chunk = chunk.strip()
        if len(chunk) < 3: continue
        parts = [p.strip() for p in chunk.split(";")]
        name = parts[0] if parts else ""
        # a name is 1-5 words, letters only, no @ and no digits
        if not name or "@" in name or len(name) > 60: continue
        if not re.fullmatch(r"[A-Za-z][A-Za-z .'\-]{2,58}", name): continue
        title = parts[1] if len(parts) > 1 else ""
        em = ""
        for p in parts[1:]:
            m = EMAIL.search(p)
            if m: em = m.group(0); break
        if not em:
            m = EMAIL.search(chunk)
            if m: em = m.group(0)
        out.append({"name": name.strip(), "title": title.strip(), "email": em.lower()})
    return out


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    strict = [r for r in rows if (r["distress"] if r["distress"] != "" else 0) <= 10]
    fill = json.load(open(FILL, encoding="utf-8")) if os.path.exists(FILL) else {}

    out, stats = [], collections.Counter()
    for r in strict:
        people = parse_people(r.get("key_people") or "")
        # attach any personal emails Tracxn listed separately
        spare = [e for e in EMAIL.findall(r.get("key_people_emails") or "")
                 if not any(e.lower().startswith(g) for g in GENERIC)]
        for p in people:
            if not p["email"] and spare:
                # only if the local-part plausibly matches the person
                first = p["name"].split()[0].lower()
                m = next((e for e in spare if first[:4] in e.split("@")[0].lower()), "")
                if m: p["email"] = m
        people.sort(key=lambda p: (seniority(p["title"]), 0 if p["email"] else 1))

        founder = people[0] if people else None
        src = "Tracxn key people"
        enr = fill.get(r["company"]) or {}
        # SignalHire fills the gap where Tracxn named nobody, or named nobody with an email
        if (not founder or not founder["email"]) and enr.get("person") and enr.get("emails"):
            founder = {"name": enr["person"], "title": enr.get("title") or "",
                       "email": enr["emails"][0]}
            src = "SignalHire"
        elif not founder and enr.get("person"):
            founder = {"name": enr["person"], "title": enr.get("title") or "", "email": ""}
            src = "SignalHire"

        company_email = next((e for e in EMAIL.findall(r.get("company_emails") or "")), "")
        name = founder["name"] if founder else ""
        title = founder["title"] if founder else ""
        email = founder["email"] if founder else ""
        if name and email: stats["founder + personal email"] += 1
        elif name and company_email: stats["founder named, only company email"] += 1
        elif name: stats["founder named, NO email"] += 1
        elif company_email: stats["no founder, only company email"] += 1
        else: stats["nothing"] += 1

        out.append({
            "company": r["company"], "founder_name": name, "founder_title": title,
            "founder_email": email, "company_email": company_email,
            "email_source": src if email else ("company email" if company_email else ""),
            "other_people": "; ".join(f"{p['name']} ({p['title'][:28]})"
                                      for p in people[1:4]),
            "employees": r["employees"], "founded": r["founded"], "age_years": r["age_years"],
            "city": r["city"], "state": r["state"], "sector": r["sector"],
            "stage": r["stage"], "revenue_usd": r["revenue_usd"],
            "funding_usd": r["funding_usd"], "distress": r["distress"],
            "engage_score": r["engage_score"], "domain": r["domain"],
            "linkedin": r["linkedin"], "website": r["website"], "tracxn_url": r["tracxn_url"],
        })

    out.sort(key=lambda x: (0 if x["founder_email"] else 1 if x["company_email"] else 2,
                            -x["engage_score"]))
    cols = list(out[0].keys())
    p = os.path.join(OUT, "LH2_OpsData_Founders_2026-08-04.csv")
    with open(p, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
    json.dump(out, open(os.path.join(OUT, "opsdata_founders.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"COMPANY / FOUNDER / EMAIL — {len(out)} companies\n")
    for k, v in stats.most_common(): print(f"   {v:>4}  {k}")
    reach = sum(1 for r in out if r["founder_email"] or r["company_email"])
    named = sum(1 for r in out if r["founder_name"])
    print(f"\n   founder NAMED           : {named}/{len(out)} ({100*named//len(out)}%)")
    print(f"   founder PERSONAL email  : {sum(1 for r in out if r['founder_email'])}")
    print(f"   reachable at all        : {reach}/{len(out)} ({100*reach//len(out)}%)")
    print(f"\n-> {p}")
    return out


if __name__ == "__main__":
    main()
