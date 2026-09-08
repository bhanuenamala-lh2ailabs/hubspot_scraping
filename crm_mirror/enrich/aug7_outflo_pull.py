# -*- coding: utf-8 -*-
"""Pull EVERY OutFlo campaign live and stage the net-new RESPONDERS.

Deliberately does not read crm_mirror/outflo/leads.json: that cache holds 13,393 leads across
campaigns the account no longer has (NITK/IITK/BITS alum lists, a legacy id block), against
1,936 actually live. Working from it would resurrect leads from campaigns that were retired.

"Replied" only — they wrote back. 'Connected' (accepted, said nothing) is a weaker signal and
is counted here but not staged, so the two never blur together in a push.

Net-new is judged on the DEAL, per the standing rule: a company or contact record without a
deal is not a worked lead. Matched on normalised LinkedIn URL first (the reliable key), then
on normalised deal name, because older deals were not always stamped with a LinkedIn URL.

Writes aug7_outflo_replied_netnew.json. Touches nothing in HubSpot.
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS, OF = env["hubspot_key"], env["outflo_api_key"]

NOT_A_COMPANY = {"self-employed", "self employed", "freelance", "freelancer", "independent",
                 "independent consultant", "none", "n/a", "-", "unemployed", "student", "retired"}


def hs(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    for a in range(6):
        try:
            req = urllib.request.Request("https://api.hubapi.com" + path, data=data, method=method,
                headers={"Authorization": "Bearer " + HS, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 5: time.sleep(2*(a+1)); continue
            return e.code, {}
        except Exception:
            if a == 5: raise
            time.sleep(3*(a+1))


def of_get(path, params=""):
    url = "https://live.outflo.in/api/public" + path + params
    for a in range(5):
        try:
            req = urllib.request.Request(url, headers={"x-api-key": OF})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 4: time.sleep(2*(a+1)); continue
            raise
        except Exception:
            if a == 4: raise
            time.sleep(3*(a+1))


def norm(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", str(s or "").lower())).strip()
def nli(u):
    u = str(u or "").strip().lower()
    if not u: return ""
    u = re.sub(r"^https?://", "", u).split("?")[0].split("#")[0]
    u = re.sub(r"^([a-z]{2,3}\.)?linkedin\.com", "linkedin.com", u)
    return u.rstrip("/")


def main():
    camps = of_get("/campaigns")
    # {status, data:{campaigns:[...]}, error} — unwrap defensively, the shape has moved before
    cl = ((camps.get("data") or {}).get("campaigns")
          if isinstance(camps.get("data"), dict) else camps.get("data")) or []
    cl = [c for c in cl if isinstance(c, dict)]
    print(f"LIVE OutFlo campaigns: {len(cl)}")
    leads = []
    for c in cl:
        cid = c.get("_id") or c.get("id"); nm_ = c.get("name") or c.get("campaignName") or cid
        got, page, total = 0, 1, None
        while True:
            d = of_get(f"/campaigns/{cid}/leads", f"?page={page}&limit=500")
            dd = d.get("data") or {}
            batch = (dd.get("leads") if isinstance(dd, dict) else dd) or []
            if total is None and isinstance(dd, dict): total = dd.get("total")
            if not batch: break
            for x in batch: x["_campaign"] = nm_; x["_cid"] = cid
            leads += batch; got += len(batch); page += 1
            if len(batch) < 500 or (total and got >= total): break
            time.sleep(0.2)
        print(f"   {got:>5}/{total}  {nm_}  [{c.get('status')}]")
    print(f"total live leads: {len(leads)}")

    rc = collections.Counter(x.get("Reply Status") or x.get("replyStatus") for x in leads)
    print("reply status:", dict(rc))

    replied = [x for x in leads
               if (x.get("Reply Status") or x.get("replyStatus")) == "Replied"
               and (x.get("LinkedIn URL") or x.get("linkedinUrl"))]
    print(f"\nREPLIED: {len(replied)}")
    print("   by campaign:", dict(collections.Counter(x["_campaign"] for x in replied)))

    # ---------- everything already in HubSpot (deal-level) ----------
    after, deals = None, []
    while True:
        b = {"limit": 200, "filterGroups": [],
             "properties": ["dealname", "linkedin_url", "hubspot_owner_id", "dealstage", "pipeline", "lead_source"]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        deals += d.get("results", [])
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    deal_li = {nli(x["properties"].get("linkedin_url")): x for x in deals if x["properties"].get("linkedin_url")}
    deal_nm = {}
    for x in deals: deal_nm.setdefault(norm(x["properties"].get("dealname")), x)
    deal_li.pop("", None); deal_nm.pop("", None)
    print(f"HubSpot: {len(deals)} deals ({len(deal_li)} carry a LinkedIn URL)")

    out, tally = [], collections.Counter()
    for x in replied:
        li = nli(x.get("LinkedIn URL") or x.get("linkedinUrl"))
        comp = (x.get("Company") or x.get("company") or "").strip()
        person = f'{(x.get("First Name") or "").strip()} {(x.get("Last Name") or "").strip()}'.strip() \
                 or (x.get("Lead") or "").strip()
        dn = comp if comp and comp.lower() not in NOT_A_COMPANY else person
        if li in deal_li: tally["in_hubspot_deal"] += 1; continue
        if norm(dn) and norm(dn) in deal_nm: tally["name_has_deal"] += 1; continue
        tally["NET_NEW"] += 1
        out.append({"campaign": x["_campaign"], "first": (x.get("First Name") or "").strip(),
                    "last": (x.get("Last Name") or "").strip(), "name": person,
                    "company": comp, "deal_name": dn or "OutFlo lead",
                    "title": (x.get("Title") or "").strip(),
                    "headline": (x.get("Headline") or "")[:160],
                    "location": (x.get("Location") or "").strip(),
                    "linkedin": "https://" + li if li else "",
                    "conn": x.get("Connection Status"), "last_action": x.get("Last Action At") or "",
                    "sender": x.get("Assigned Account") or "", "phone": "", "email": ""})
    print("\nreplied, checked against HubSpot deals:")
    for k, v in tally.most_common(): print(f"   {v:>4}  {k}")

    p = os.path.join(HERE, "aug7_outflo_replied_netnew.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nNET-NEW RESPONDERS: {len(out)}  -> {os.path.basename(p)}")
    for r in out:
        print(f'   {r["campaign"][:28]:<30}{r["deal_name"][:30]:<32}{r["name"][:22]:<24}{r["location"][:22]}')
    print("\nNo phone numbers yet — none of these carry one until SignalHire runs.")


main()
