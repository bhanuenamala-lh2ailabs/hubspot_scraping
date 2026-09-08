# -*- coding: utf-8 -*-
"""Mail each caller ONLY the .vcf of the LinkedIn-ad leads they were just given. No body.

Asked for explicitly: no email body. The message therefore carries a single line of plain text
naming the file and the count — an attachment-only mail with a genuinely empty body is treated
as suspicious by Gmail and by most phones, and would also leave the caller with no way to tell
which batch the file is.

Scope is the NEWLY ASSIGNED deals from aug10_campaign_split.json, not the person's whole book:
the full book already went out on Friday, and a caller opening a 200-card .vcf to find today's
150 is worse than useless.

+91 gate applies as always — a card with no dialable number is not written.

Usage: python aug10_vcf_only_mail.py [--send] [--test]
"""
import os, sys, json, time, datetime, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from lead_vcf_notifier import vcard
import gmail_sender

env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

TO = {"Lamiya": "lamiya.saleem@lh2.ai", "Yuktha": "yuktha.anand@lh2.ai",
      "Ishpreet": "ishpreet.sood@lh2.ai"}
TEST_TO = "bhanu.enamala@lh2.ai"
SEND = "--send" in sys.argv; TEST = "--test" in sys.argv
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
today = datetime.datetime.now(IST).date()


def hs(u, m="GET", b=None):
    d = json.dumps(b).encode() if b is not None else None
    for a in range(6):
        try:
            r = urllib.request.Request("https://api.hubapi.com" + u, data=d, method=m, headers=H)
            with urllib.request.urlopen(r, timeout=60) as x:
                t = x.read().decode(); return x.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 5: time.sleep(2*(a+1)); continue
            return e.code, {}
        except Exception:
            if a == 5: raise
            time.sleep(3*(a+1))


def main():
    split = json.load(open(os.path.join(HERE, "aug10_campaign_split.json"), encoding="utf-8"))
    for who, rows in split.items():
        ids = [r["id"] for r in rows]
        d2c = {}
        for i in range(0, len(ids), 100):
            _, a = hs("/crm/v4/associations/deals/contacts/batch/read", "POST",
                      {"inputs": [{"id": x} for x in ids[i:i+100]]})
            for res in (a.get("results") or []):
                d2c[str((res.get("from") or {}).get("id"))] = [str(t["toObjectId"]) for t in (res.get("to") or [])]
        cids = sorted({c for v in d2c.values() for c in v})
        cp = {}
        for i in range(0, len(cids), 100):
            _, r = hs("/crm/v3/objects/contacts/batch/read", "POST",
                      {"properties": ["firstname", "lastname", "email", "phone", "mobilephone",
                                      "company", "jobtitle"],
                       "inputs": [{"id": c} for c in cids[i:i+100]]})
            for x in (r.get("results") or []): cp[x["id"]] = x["properties"]

        cards, nophone = [], 0
        byid = {r["id"]: r for r in rows}
        for did, cl in d2c.items():
            for c in cl:
                p = cp.get(c, {})
                if not ((p.get("mobilephone") or "").strip() or (p.get("phone") or "").strip()):
                    nophone += 1; continue
                cards.append(vcard(p, p.get("company") or "", byid.get(did, {}).get("name", ""),
                                   who, "Cold Call"))
        vcf = ("\r\n".join(cards)).encode("utf-8")
        fn = f"lh2_linkedin_ads_{who.lower()}_{today.isoformat()}.vcf"
        open(os.path.join(HERE, fn), "wb").write(vcf)
        print(f"{who:<10}{len(rows):>4} leads | {len(cards):>4} vcards | "
              f"{nophone} without a number | {len(vcf)}b -> {fn}")

        if SEND:
            to = TEST_TO if TEST else TO[who]
            subj = f"LH2 — {len(cards)} LinkedIn ad leads assigned to you ({today:%d %b %Y})"
            body = (f"{len(cards)} contacts attached as {fn} — open on your phone to save them "
                    f"all at once.")
            t, detail = gmail_sender.send(to, subj, body, [(fn, vcf, "text/vcard")])
            print(f"           sent to {to} via [{t}] {detail}", flush=True)
    if not SEND:
        print("\nnot sent — pass --send (add --test to route all three to the test mailbox)")


main()
