# -*- coding: utf-8 -*-
"""Aug-7 LinkedIn lead-gen forms -> dedup against HubSpot -> net new to Ishpreet.

Two exports from the same form ("Aug 5 2026" and "Bhanu Split") overlap each other as well as
HubSpot, so dedup runs twice: within the pasted files first, then against the CRM.

Dedup keys are email, LinkedIn URL and phone — NOT name. Two different people share a name far
more often than they share an inbox, and a name-only match would silently drop a real lead.
LinkedIn URLs are normalised (scheme/host/trailing slash/query) because the same profile
arrives written several ways.

Tags copied from the newest live records of this source, not from memory:
  pipeline 2425754306 (Campaign) / stage 4002503379 (Cold Call)
  lead_source "Linkedin Campaign ( IT Services )" / scraped_type left unset

Usage: python aug7_li_campaign.py [--apply]
"""
import os, sys, csv, re, json, time, glob, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); HUB = os.path.dirname(ROOT)
sys.path.insert(0, HERE)
from indian_number import to_e164, classify

env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

ISHPREET = "166322228"
PIPE     = "2425754306"          # Campaign
COLD     = "4002503379"          # Campaign / Cold Call
SOURCE   = "Linkedin Campaign ( IT Services )"
APPLY    = "--apply" in sys.argv
# default location is aug7/, but the exports land wherever they are dropped — allow both.
SRCDIR   = HUB
for _i, _a in enumerate(sys.argv):
    if _a == "--dir": SRCDIR = os.path.join(HUB, sys.argv[_i+1])
AUG7     = SRCDIR


def hs(u, m="GET", b=None):
    d = json.dumps(b).encode() if b is not None else None
    for a in range(6):
        try:
            r = urllib.request.Request("https://api.hubapi.com" + u, data=d, method=m, headers=H)
            with urllib.request.urlopen(r, timeout=60) as x:
                t = x.read().decode(); return x.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 5: time.sleep(2*(a+1)); continue
            return e.code, {"raw": e.read().decode()[:300]}
        except Exception:
            if a == 5: raise
            time.sleep(3*(a+1))


def norm_li(u):
    """linkedin.com/in/foo/ , http://…?trk=x and www. variants are all the same profile."""
    u = (u or "").strip().lower()
    if not u: return ""
    u = re.sub(r"^https?://", "", u).split("?")[0].split("#")[0]
    u = re.sub(r"^([a-z]{2,3}\.)?linkedin\.com", "linkedin.com", u)
    return u.rstrip("/")


def norm_email(e):
    return (e or "").strip().lower()


def digits10(p):
    """Last 10 digits — the comparable core of an Indian number however it was typed."""
    d = re.sub(r"[^\d]", "", str(p or ""))
    return d[-10:] if len(d) >= 10 else ""


# ------------------------------------------------------------------ read the pasted files
def read_files():
    rows = []
    for path in sorted(glob.glob(os.path.join(AUG7, "Lead generation*.csv"))):
        with open(path, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                r = { (k or "").lstrip("﻿").strip(): (v or "").strip() for k, v in r.items() }
                if str(r.get("test_lead", "")).lower() == "true":
                    continue                       # Meta's own test submissions are not people
                rows.append({
                    "file": os.path.basename(path)[:34],
                    "lead_id": r.get("lead_id", ""),
                    "created": r.get("created_date", ""),
                    "first": r.get("First name", ""), "last": r.get("Last name", ""),
                    "email": norm_email(r.get("Email address", "")),
                    "li": norm_li(r.get("LinkedIn profile URL", "")),
                    "phone_raw": r.get("Phone number", ""),
                })
    return rows


# ------------------------------------------------------------------ HubSpot side
def crm_index():
    """Every contact key already in the CRM: email, linkedin, last-10-digits of any phone."""
    em, li, ph = set(), set(), set()
    after = None; n = 0
    while True:
        b = {"limit": 200, "properties": ["email", "phone", "mobilephone", "linkedin_url", "hs_linkedin_url"],
             "filterGroups": [{"filters": [{"propertyName": "hs_object_id", "operator": "HAS_PROPERTY"}]}]}
        if after: b["after"] = after
        s, d = hs("/crm/v3/objects/contacts/search", "POST", b)
        for x in d.get("results", []):
            p = x["properties"]; n += 1
            if p.get("email"): em.add(norm_email(p["email"]))
            for k in ("linkedin_url", "hs_linkedin_url"):
                if p.get(k): li.add(norm_li(p[k]))
            for k in ("phone", "mobilephone"):
                if digits10(p.get(k)): ph.add(digits10(p[k]))
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
        time.sleep(0.1)
    li.discard(""); em.discard(""); ph.discard("")
    return em, li, ph, n


def push(rec):
    """Contact first, then deal, then associate. Deal name is the person: these are inbound
    form fills with no company field, which is how the 51 existing rows of this source read."""
    cp = {"firstname": rec["first"], "lastname": rec["last"], "email": rec["email"],
          "phone": rec["e164"], "mobilephone": rec["e164"]}
    if rec["li"]: cp["linkedin_url"] = "https://" + rec["li"]
    s, d = hs("/crm/v3/objects/contacts", "POST", {"properties": {k: v for k, v in cp.items() if v}})
    if s not in (200, 201):
        return None, f"contact {s} {str(d)[:110]}"
    ctid = d.get("id")
    name = (rec["first"] + " " + rec["last"]).strip() or rec["email"]
    dp = {"dealname": name, "pipeline": PIPE, "dealstage": COLD,
          "hubspot_owner_id": ISHPREET, "poc": ISHPREET, "lead_source": SOURCE}
    s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
    if s not in (200, 201):
        return None, f"deal {s} {str(d)[:110]}"
    did = d.get("id"); time.sleep(0.25)
    hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}", "PUT")
    return did, ""


def main():
    raw = read_files()
    print(f"pasted rows (excl. test_lead): {len(raw)}")
    for f, c in collections.Counter(r["file"] for r in raw).items():
        print(f"   {c:>4}  {f}")

    # ---- dedup INSIDE the pasted set: the two exports share the same form ----
    seen_e, seen_l, seen_p, uniq, dup_in = set(), set(), set(), [], 0
    for r in raw:
        p10 = digits10(r["phone_raw"])
        if (r["email"] and r["email"] in seen_e) or (r["li"] and r["li"] in seen_l) \
           or (p10 and p10 in seen_p):
            dup_in += 1; continue
        if r["email"]: seen_e.add(r["email"])
        if r["li"]: seen_l.add(r["li"])
        if p10: seen_p.add(p10)
        uniq.append(r)
    print(f"\nafter in-file dedup: {len(uniq)}  ({dup_in} duplicates across/inside the two files)")

    # ---- +91 gate ----
    for r in uniq:
        r["e164"] = to_e164(r["phone_raw"]) or ""
        r["kind"] = classify(r["phone_raw"]) if r["e164"] else ""
    good = [r for r in uniq if r["e164"]]
    nogo = [r for r in uniq if not r["e164"]]
    print(f"+91 gate: {len(good)} dialable, {len(nogo)} rejected")
    for r in nogo:
        print(f'   REJECT  {(r["first"]+" "+r["last"]).strip()[:26]:<28}{r["phone_raw"][:22]:<24}{r["email"][:34]}')

    # ---- dedup against the CRM ----
    print("\nindexing HubSpot contacts...", flush=True)
    em, li, ph, n = crm_index()
    print(f"   {n} contacts | {len(em)} emails, {len(li)} linkedin, {len(ph)} phones")
    new, dupe = [], []
    for r in good:
        hit = ("email" if r["email"] in em else
               "linkedin" if r["li"] and r["li"] in li else
               "phone" if digits10(r["e164"]) in ph else "")
        (dupe if hit else new).append((r, hit))
    print(f"\nalready in HubSpot: {len(dupe)}")
    for r, hit in dupe:
        print(f'   dup[{hit:<8}] {(r["first"]+" "+r["last"]).strip()[:26]:<28}{r["email"][:36]}')
    print(f"\nNET NEW to push to Ishpreet: {len(new)}")
    for r, _ in new:
        print(f'   {(r["first"]+" "+r["last"]).strip()[:26]:<28}{r["e164"]:<16}{r["kind"]:<8}{r["email"][:34]}')

    out = os.path.join(HERE, "aug7_li_campaign_netnew.json")
    json.dump([r for r, _ in new], open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nwrote {os.path.basename(out)}")

    if not APPLY:
        print("\nDRY RUN — nothing written. Re-run with --apply to push.")
        return
    print("\npushing...", flush=True)
    ok = 0
    for r, _ in new:
        did, err = push(r)
        nm = (r["first"] + " " + r["last"]).strip()
        print(f'   {"OK  " if did else "FAIL"} {nm[:28]:<30}{did or err}', flush=True)
        ok += 1 if did else 0
        time.sleep(0.35)
    print(f"\npushed {ok}/{len(new)} to Ishpreet")


main()
