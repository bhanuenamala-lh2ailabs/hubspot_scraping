# -*- coding: utf-8 -*-
"""One-off: mail each caller a .vcf of EVERY lead sitting at Cold Call under their name.

This is the catch-up send. From here on `lead_vcf_notifier.py` handles new assignments
automatically, so this should only ever need running again for a new joiner.

Covers both pipelines (Scraped + Campaign) and dedups a person who appears on more than
one deal. Reuses the notifier's own vcard() so the two can never drift apart.

Usage:
  python send_coldcall_books.py --dry-run
  python send_coldcall_books.py --owners shobit,ishpreet,lamiya,yuktha
"""
import os, re, sys, json, time, datetime, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gmail_sender
from lead_vcf_notifier import hs, vcard, CONTACT_PROPS
from indian_number import to_e164

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
COLD_CALL = {"default": "3992480462", "2425754306": "4002503379"}


def main():
    dry = "--dry-run" in sys.argv
    who = "shobit,ishpreet,lamiya,yuktha"
    if "--owners" in sys.argv: who = sys.argv[sys.argv.index("--owners") + 1]
    want = [w.strip().lower() for w in who.split(",") if w.strip()]

    owners = {}
    for o in hs("/crm/v3/owners?limit=200").get("results", []):
        nm = f"{o.get('firstName','')} {o.get('lastName','')}".strip()
        if any(w in nm.lower() for w in want):
            owners[o["id"]] = {"name": nm, "email": o.get("email"), "first": nm.split(" ")[0]}
    pipes = {p["id"]: p["label"] for p in hs("/crm/v3/pipelines/deals").get("results", [])}

    after, deals = None, []
    while True:
        b = {"limit": 200, "filterGroups": [],
             "properties": ["dealname", "dealstage", "hubspot_owner_id", "pipeline"]}
        if after: b["after"] = after
        d = hs("/crm/v3/objects/deals/search", "POST", b)
        deals += d.get("results", [])
        after = d.get("paging", {}).get("next", {}).get("after")
        if not after: break

    mine = {}
    for d in deals:
        p = d["properties"]
        oid = p.get("hubspot_owner_id")
        if oid in owners and p.get("dealstage") == COLD_CALL.get(p.get("pipeline")):
            mine.setdefault(oid, []).append((d["id"], p))
    print(f"{len(deals)} deals scanned")

    for oid, rows in sorted(mine.items(), key=lambda x: -len(x[1])):
        ow = owners[oid]
        # deal -> contacts
        per_deal, want_ids = {}, set()
        for did, _ in rows:
            a = hs(f"/crm/v4/objects/deals/{did}/associations/contacts")
            ids = [str(y["toObjectId"]) for y in a.get("results", [])]
            per_deal[did] = ids; want_ids.update(ids)
        cmap = {}
        ids = list(want_ids)
        for i in range(0, len(ids), 100):
            r = hs("/crm/v3/objects/contacts/batch/read", "POST",
                   {"properties": CONTACT_PROPS, "inputs": [{"id": x} for x in ids[i:i+100]]})
            for x in r.get("results", []): cmap[x["id"]] = x["properties"]

        cards, seen, no_phone, by_pipe = [], set(), 0, {}
        for did, p in sorted(rows, key=lambda r: r[1].get("dealname") or ""):
            dn = p.get("dealname") or "(unnamed deal)"
            by_pipe[pipes.get(p.get("pipeline"), "?")] = by_pipe.get(pipes.get(p.get("pipeline"), "?"), 0) + 1
            for cid in per_deal.get(did, []):
                c = cmap.get(cid)
                if not c or cid in seen: continue
                seen.add(cid)
                cards.append(vcard(c, dn, dn, ow["name"], "Cold Call"))
                if not to_e164(c.get("mobilephone") or c.get("phone") or ""): no_phone += 1

        if not cards:
            print(f"  {ow['name']:16} {len(rows)} deals but no contacts attached — skipped"); continue

        spread = ", ".join(f"{v} in {k}" for k, v in sorted(by_pipe.items(), key=lambda x: -x[1]))
        body = (
            f"Hi {ow['first']},\n\n"
            f"Attached is your current Cold Call list from HubSpot as a contact file — "
            f"{len(cards)} contacts across {len(rows)} leads ({spread}).\n\n"
            f"HOW TO USE IT\n"
            f"Open the attachment on your phone and choose to import/save to Contacts. "
            f"All {len(cards)} save in one go — you don't have to add them one by one. "
            f"Every number is saved with the +91 prefix so you can dial or WhatsApp straight "
            f"from the contact.\n\n"
            f"Each contact is saved as NAME - COMPANY (for example \"Mustafa Imran - MIB Tech "
            f"Solutions\"), so when one of them rings you back you can see who it is before "
            f"you pick up. The contact also carries their title, email and LinkedIn where we "
            f"have it, and a note with the deal name.\n\n"
            f"FROM TODAY ONWARDS\n"
            f"Every time a new lead is assigned to you in HubSpot, you will automatically get "
            f"an email like this one with just the new contacts attached. Open it, save to "
            f"contacts, and you're ready to call — no need to copy numbers out of HubSpot "
            f"any more.\n\n"
            + (f"Note: {no_phone} of these have no usable Indian number on the record — they "
               f"will import without a phone. Reach them on email or LinkedIn instead.\n\n"
               if no_phone else "")
            + f"HubSpot stays the source of truth — please keep logging call outcomes against "
              f"the deal there.\n"
        )
        fname = (f"lh2_coldcall_{re.sub(r'[^a-z0-9]+','_',ow['name'].lower()).strip('_')}"
                 f"_{datetime.date.today().isoformat()}.vcf")
        subject = f"Your Cold Call list — {len(cards)} contacts, ready to save to your phone"
        t, detail = gmail_sender.send(ow["email"], subject, body,
                                      [(fname, ("\r\n".join(cards)).encode("utf-8"), "text/vcard")],
                                      dry=dry)
        print(f"  {ow['name']:16} {len(rows):>3} deals {len(cards):>3} contacts "
              f"({no_phone} no phone) -> {ow['email']:26} [{t}] {detail}")


if __name__ == "__main__":
    main()
