# -*- coding: utf-8 -*-
"""Mail Lamiya and Yuktha ONLY the .vcf of the NASSCOM leads just assigned to them. No body.

Same shape as the LinkedIn-ad handover: a single line of plain text naming the file and the
count, because a genuinely empty body is treated as suspicious by Gmail and by most phones, and
would leave the caller unable to tell which batch the file belongs to.

Scope is strictly today's NASSCOM push (pushed_batches.json + the first 9), not the caller's
whole book. Opening a 200-card file to find today's 63 would be worse than useless.

Every card carries the founder's name, title, company and the +91 number that passed the gate,
so the contact is dialable straight from the phone's address book.

Usage: python3 vcf_nasscom_mail.py [--send] [--to-test addr]
"""
import os, sys, json, glob, datetime

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
import gmail_sender

MAIL = {"Lamiya": "lamiya.saleem@lh2.ai", "Yuktha": "yuktha.anand@lh2.ai"}
SEND = "--send" in sys.argv
TEST = None
for i, a in enumerate(sys.argv):
    if a == "--to-test": TEST = sys.argv[i+1]


def vcard(person, title, company, phone, email, linkedin):
    """Minimal, phone-friendly vCard 3.0. N is required by Android contacts imports."""
    parts = (person or "").split()
    last = parts[-1] if len(parts) > 1 else (parts[0] if parts else "")
    first = " ".join(parts[:-1]) if len(parts) > 1 else ""
    lines = ["BEGIN:VCARD", "VERSION:3.0",
             f"N:{last};{first};;;", f"FN:{person}"]
    if company: lines.append(f"ORG:{company}")
    if title: lines.append(f"TITLE:{title}")
    if phone: lines.append(f"TEL;TYPE=CELL:{phone}")
    if email: lines.append(f"EMAIL;TYPE=INTERNET:{email}")
    if linkedin: lines.append(f"URL:{linkedin}")
    lines.append("NOTE:NASSCOM IT services - pushed " + datetime.date.today().isoformat())
    lines.append("END:VCARD")
    return "\r\n".join(lines)


def main():
    done = json.load(open(os.path.join(HERE, "pushed_batches.json"), encoding="utf-8"))
    # the second push run (Priority/Secondary from the ranked CSV) wrote its own log; without
    # this the caller's .vcf silently omits the leads they were most recently handed
    try:
        for d, v in json.load(open(os.path.join(HERE, "pushed_144.json"), encoding="utf-8")).items():
            done.setdefault(d, v)
    except Exception:
        pass
    rev = {r["domain"]: r for r in json.load(open(os.path.join(HERE, "bulk_revealed.json"), encoding="utf-8"))}
    # the first 9 went out before batching; include them so a caller's file matches their book
    try:
        for r in json.load(open(os.path.join(HERE, "above20_revealed.json"), encoding="utf-8")):
            if r.get("indian_phone") and r["domain"] not in done:
                done[r["domain"]] = {"owner": "Lamiya", "name": r["name"],
                                     "person": r["person"], "phone": r["indian_phone"]}
                rev.setdefault(r["domain"], r)
    except Exception:
        pass

    by = {}
    for dom, d in done.items():
        by.setdefault(d["owner"], []).append((dom, d))
    for who, items in by.items():
        cards, rows = [], []
        for dom, d in sorted(items, key=lambda x: x[1]["name"].lower()):
            r = rev.get(dom, {})
            cards.append(vcard(d.get("person") or r.get("person", ""), r.get("title", ""),
                               d["name"], d.get("phone") or r.get("indian_phone", ""),
                               r.get("email", ""), r.get("linkedin", "")))
            rows.append(f'{d["name"]} — {d.get("person","")} ({r.get("title","")})')
        vcf = "\r\n".join(cards).encode("utf-8")
        fn = f"nasscom_{who.lower()}_{datetime.date.today().isoformat()}.vcf"
        body = (f"{len(cards)} new NASSCOM IT-services leads assigned to you today. "
                f"Import {fn} to your phone contacts.")
        to = TEST or MAIL[who]
        print(f"\n{who}: {len(cards)} cards -> {to}   ({fn})")
        for x in rows[:5]: print(f"   {x[:88]}")
        if len(rows) > 5: print(f"   ... and {len(rows)-5} more")
        if SEND:
            t, detail = gmail_sender.send(to, f"NASSCOM leads — {len(cards)} contacts", body,
                                          attachments=[(fn, vcf, "text/vcard")])
            print(f"   sent via [{t}] {detail}")
        else:
            open(os.path.join(HERE, fn), "wb").write(vcf)
            print(f"   wrote {fn} locally (dry run)")


main()
