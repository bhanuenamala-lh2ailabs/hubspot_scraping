# -*- coding: utf-8 -*-
"""Stage net-new OutFlo RESPONDERS, ready to push. Does not touch HubSpot.

"Responded" = reply == 'Replied' — they wrote back. That is the hottest signal OutFlo gives
us, and a different thing from 'Connected' (accepted the connection request but said
nothing), which is staged separately so the two never get mixed in a push.

Net-new is judged on the DEAL, per the standing rule: a company with a HubSpot company
record but no deal still counts as new. Matched three ways because OutFlo leads arrive with
a LinkedIn URL but our older deals were not always stamped with one:
  1. deal.linkedin_url  == the lead's LinkedIn (exact, after normalising)
  2. contact.linkedin_url == the lead's LinkedIn -> that contact's deals
  3. deal name == the lead's company name (normalised)

Output: crm_mirror/enrich/outflo_replied_ready.json + .csv, ordered hottest first.

Usage: python prep_outflo_replied.py
"""
import os, re, csv, sys, json, time, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS = env["hubspot_key"]

NOT_A_COMPANY = {"self-employed", "self employed", "freelance", "freelancer", "independent",
                 "independent consultant", "none", "n/a", "-", "unemployed", "student", "retired"}


def hs(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req = urllib.request.Request("https://api.hubapi.com" + path, data=data, method=method,
                headers={"Authorization": "Bearer " + HS, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < 4: time.sleep(2 * (a + 1)); continue
            return e.code, {}
        except Exception:
            if a == 4: raise
            time.sleep(2)


def norm(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", str(s or "").lower())).strip()
def nli(u): return re.sub(r"[?#].*$", "", str(u or "").rstrip("/").lower())


def deal_name(company, person):
    c = (company or "").strip()
    return c if c and c.lower() not in NOT_A_COMPANY else (person or "").strip() or "OutFlo lead"


def main():
    leads = json.load(open(os.path.join(HUB, "crm_mirror", "outflo", "leads.json"), encoding="utf-8"))
    replied = [x for x in leads if x.get("reply") == "Replied" and x.get("linkedin")]
    conn_only = [x for x in leads if x.get("reply") != "Replied"
                 and x.get("conn") == "Connected" and x.get("linkedin")]
    print(f"OutFlo: {len(leads)} leads | REPLIED {len(replied)} | connected-not-replied {len(conn_only)}")

    # ---- everything already in HubSpot ----
    after, deals = None, []
    while True:
        b = {"limit": 200, "filterGroups": [],
             "properties": ["dealname", "linkedin_url", "hubspot_owner_id", "dealstage", "pipeline"]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        deals += d.get("results", [])
        after = d.get("paging", {}).get("next", {}).get("after")
        if not after: break
    deal_li = {nli(x["properties"].get("linkedin_url")): x for x in deals
               if x["properties"].get("linkedin_url")}
    deal_nm = {}
    for x in deals: deal_nm.setdefault(norm(x["properties"].get("dealname")), x)

    after, contacts = None, []
    while True:
        b = {"limit": 200, "filterGroups": [], "properties": ["linkedin_url", "email", "firstname", "lastname"]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/contacts/search", "POST", b)
        contacts += d.get("results", [])
        after = d.get("paging", {}).get("next", {}).get("after")
        if not after: break
    contact_li = {nli(c["properties"].get("linkedin_url")) for c in contacts
                  if c["properties"].get("linkedin_url")}
    print(f"HubSpot: {len(deals)} deals ({len(deal_li)} with a LinkedIn URL), {len(contacts)} contacts")

    def status(x):
        li = nli(x["linkedin"])
        if li in deal_li: return "in_hubspot_deal", deal_li[li]
        if norm(x.get("company")) and norm(x.get("company")) in deal_nm:
            return "company_has_deal", deal_nm[norm(x.get("company"))]
        if li in contact_li: return "contact_only", None
        return "NET_NEW", None

    out, tally = [], collections.Counter()
    for x in replied:
        st, hit = status(x); tally[st] += 1
        if st in ("in_hubspot_deal", "company_has_deal"): continue
        out.append({
            "bucket": x.get("bucket"), "name": x.get("name"),
            "first": x.get("first"), "last": x.get("last"),
            "company": x.get("company") or "", "deal_name": deal_name(x.get("company"), x.get("name")),
            "title": x.get("title") or "", "headline": (x.get("headline") or "")[:160],
            "location": x.get("location") or "", "linkedin": x["linkedin"],
            "campaign_id": x.get("campaign_id"), "sender": x.get("sender"),
            "last_action": x.get("last_action") or "", "replied_at": x.get("outflo_replied_at") or "",
            "already": st, "phone": "", "email": "", "enriched": False})
    print("\nREPLIED, checked against HubSpot:")
    for k, v in tally.most_common(): print(f"   {v:>4}  {k}")

    out.sort(key=lambda r: (r["bucket"], r["company"] or "zz"))
    jp = os.path.join(HERE, "outflo_replied_ready.json")
    json.dump(out, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cols = ["bucket", "deal_name", "company", "name", "title", "location", "linkedin",
            "headline", "sender", "last_action", "already"]
    cp = os.path.join(HERE, "outflo_replied_ready.csv")
    with open(cp, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in out: w.writerow([r.get(c, "") for c in cols])

    print(f"\nNET-NEW RESPONDERS READY: {len(out)}")
    print("   by bucket:", dict(collections.Counter(r["bucket"] for r in out)))
    nocomp = sum(1 for r in out if not r["company"])
    print(f"   without a company name (deal would fall back to person): {nocomp}")
    print(f"\n-> {jp}\n-> {cp}")
    print("\nNothing pushed. No numbers yet — none of these carry a phone until SignalHire runs.")


if __name__ == "__main__":
    main()
