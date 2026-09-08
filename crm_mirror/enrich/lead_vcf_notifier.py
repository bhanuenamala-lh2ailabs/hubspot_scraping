# -*- coding: utf-8 -*-
"""When a HubSpot deal is assigned to someone, email that person a .vcf of the deal's contacts.

TRIGGER — polling, not webhooks. A HubSpot webhook needs a public HTTPS endpoint we don't
have. This diffs current deal->owner assignments against a local state file, so it only ever
reports genuinely NEW assignments (first assignment, or a hand-off to a different owner).
Run it on a schedule; see --install-task.

VCF — vCard 3.0, the format Android, iOS, Outlook and Google Contacts all import. One file
per owner per run, holding every contact on every deal newly assigned to them, so a caller
imports once and has the whole batch in their phone.

EMAIL — delegated to gmail_sender.py, which picks the first working transport
(OAuth Gmail -> service-account Gmail -> SMTP -> local outbox). Nothing is ever lost: with
no transport configured the .vcf still lands in crm_mirror/vcf_outbox/.

Usage:
  python lead_vcf_notifier.py --init          record the current state, notify nobody (run first)
  python lead_vcf_notifier.py --dry-run       show what would be sent, write files locally
  python lead_vcf_notifier.py                 send
  python lead_vcf_notifier.py --install-task  register a Windows scheduled task (every 15 min)
"""
import os, re, sys, json, time, datetime, subprocess, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gmail_sender
from indian_number import to_e164

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "vcf_notifier_state.json")
LOG = os.path.join(HERE, "vcf_notifier_log.json")
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS = env["hubspot_key"]

CONTACT_PROPS = ["firstname", "lastname", "email", "phone", "mobilephone",
                 "jobtitle", "company", "linkedin_url"]


def hs(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req = urllib.request.Request("https://api.hubapi.com" + path, data=data, method=method,
                headers={"Authorization": "Bearer " + HS, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                t = r.read().decode(); return json.loads(t) if t else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < 4: time.sleep(2 * (a + 1)); continue
            return {}
        except Exception:
            if a == 4: return {}
            time.sleep(2)
    return {}


# ---------------------------------------------------------------- vCard
def _esc(s):
    return (str(s or "").replace("\\", "\\\\").replace(";", r"\;")
            .replace(",", r"\,").replace("\n", r"\n"))


def vcard(c, company, deal, owner, stage=""):
    """One vCard 3.0 record.

    The saved contact name carries a COMPANY SUFFIX — "Mustafa Imran - MIB Tech Solutions".
    A caller's phone fills up with names they've never met; the company is what they
    actually recognise when it rings back. The suffix goes on BOTH `FN` and the surname
    field of `N` because iOS renders FN while some Android apps rebuild the display name
    from N — putting it in one place only makes it vanish on half the handsets.
    """
    fn = (c.get("firstname") or "").strip(); ln = (c.get("lastname") or "").strip()
    org = (c.get("company") or company or "").strip()
    person = (fn + " " + ln).strip()
    full = f"{person} - {org}" if person and org else (person or org or "Unknown")
    ln_disp = f"{ln} - {org}" if org else ln
    if not ln and org: ln_disp = f"- {org}" if fn else org
    L = ["BEGIN:VCARD", "VERSION:3.0", f"N:{_esc(ln_disp)};{_esc(fn)};;;", f"FN:{_esc(full)}"]
    if org: L.append(f"ORG:{_esc(org)}")
    if c.get("jobtitle"): L.append(f"TITLE:{_esc(c['jobtitle'])}")
    # Always dial-ready: force +91<10 digits>. Older records hold bare 10-digit numbers,
    # which a phone saves verbatim and then fails to dial from abroad or match on WhatsApp.
    seen = set()
    for k, typ in (("mobilephone", "CELL"), ("phone", "WORK")):
        v = (c.get(k) or "").strip()
        if not v: continue
        v = to_e164(v) or v                      # keep a genuine foreign number as-is
        if v not in seen:
            seen.add(v); L.append(f"TEL;TYPE={typ},VOICE:{v}")
    if c.get("email"): L.append(f"EMAIL;TYPE=WORK:{c['email']}")
    if c.get("linkedin_url"): L.append(f"URL:{c['linkedin_url']}")
    note = f"LH2 lead — deal: {deal}"
    if stage: note += f" ({stage})"
    note += f". Owner: {owner}. Assigned {datetime.date.today().isoformat()}."
    L += [f"NOTE:{_esc(note)}", "END:VCARD"]
    return "\r\n".join(L)


# ---------------------------------------------------------------- scheduling
def install_task(minutes=15):
    py = sys.executable.replace("python.exe", "pythonw.exe")
    if not os.path.exists(py): py = sys.executable
    cmd = ["schtasks", "/Create", "/TN", "LH2 VCF lead notifier", "/SC", "MINUTE",
           "/MO", str(minutes), "/F", "/TR", f'"{py}" "{os.path.abspath(__file__)}"']
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    print(f"\nRuns every {minutes} min. Remove with:  schtasks /Delete /TN \"LH2 VCF lead notifier\" /F")


# ---------------------------------------------------------------- main
def main():
    if "--install-task" in sys.argv:
        n = int(sys.argv[sys.argv.index("--install-task") + 1]) if len(sys.argv) > sys.argv.index("--install-task") + 1 and sys.argv[sys.argv.index("--install-task") + 1].isdigit() else 15
        install_task(n); return
    dry = "--dry-run" in sys.argv; init = "--init" in sys.argv

    owners = {o["id"]: {"name": f"{o.get('firstName','')} {o.get('lastName','')}".strip(),
                        "email": o.get("email")}
              for o in hs("/crm/v3/owners?limit=200").get("results", [])}
    pipes = {p["id"]: p["label"] for p in hs("/crm/v3/pipelines/deals").get("results", [])}
    stages = {s["id"]: s["label"] for pid in pipes
              for s in hs(f"/crm/v3/pipelines/deals/{pid}").get("stages", [])}

    after, deals = None, []
    while True:
        b = {"limit": 200, "filterGroups": [],
             "properties": ["dealname", "dealstage", "hubspot_owner_id", "pipeline"]}
        if after: b["after"] = after
        d = hs("/crm/v3/objects/deals/search", "POST", b)
        deals += d.get("results", [])
        after = d.get("paging", {}).get("next", {}).get("after")
        if not after: break

    current = {x["id"]: (x["properties"].get("hubspot_owner_id") or "") for x in deals}
    prev = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else None

    if init or prev is None:
        json.dump(current, open(STATE, "w"), indent=0)
        print(f"state initialised with {len(current)} deals — nothing sent.\n"
              f"Future assignments will be picked up from here.")
        return

    new = {did: oid for did, oid in current.items() if oid and prev.get(did) != oid}
    print(f"{len(deals)} deals scanned | newly assigned since last run: {len(new)}")
    if not new:
        if not dry: json.dump(current, open(STATE, "w"), indent=0)
        return

    by_owner = {}
    for did, oid in new.items(): by_owner.setdefault(oid, []).append(did)
    dmap = {x["id"]: x["properties"] for x in deals}
    sent_log = json.load(open(LOG, encoding="utf-8")) if os.path.exists(LOG) else []

    for oid, dids in by_owner.items():
        ow = owners.get(oid, {}); to = ow.get("email")
        if not to:
            print(f"  !! owner {oid} has no email in HubSpot — skipped"); continue

        # deal -> contact ids (one association call per deal, then ONE batch read)
        want, per_deal = set(), {}
        for did in dids:
            a = hs(f"/crm/v4/objects/deals/{did}/associations/contacts")
            ids = [str(y["toObjectId"]) for y in a.get("results", [])]
            per_deal[did] = ids; want.update(ids)
        cmap = {}
        ids = list(want)
        for i in range(0, len(ids), 100):
            r = hs("/crm/v3/objects/contacts/batch/read", "POST",
                   {"properties": CONTACT_PROPS, "inputs": [{"id": x} for x in ids[i:i+100]]})
            for x in r.get("results", []): cmap[x["id"]] = x["properties"]

        cards, lines, n_nophone = [], [], 0
        for did in sorted(dids, key=lambda d: dmap.get(d, {}).get("dealname") or ""):
            p = dmap.get(did, {})
            dn = p.get("dealname") or "(unnamed deal)"
            st = stages.get(p.get("dealstage"), "")
            pipe = pipes.get(p.get("pipeline"), "")
            for cid in per_deal[did]:
                c = cmap.get(cid)
                if not c: continue
                cards.append(vcard(c, dn, dn, ow.get("name"), st))
                ph = (c.get("mobilephone") or c.get("phone") or "").strip()
                if not ph: n_nophone += 1
                nm = ((c.get("firstname") or "") + " " + (c.get("lastname") or "")).strip()
                lines.append(f"  • {nm or '(no name)':28} {dn[:26]:28} {ph or 'no phone':16} "
                             f"{c.get('jobtitle') or ''}")
            if not per_deal[did]:
                lines.append(f"  • {'(no contact attached)':28} {dn[:26]:28}")

        if not cards:
            print(f"  {ow.get('name','?'):18} {len(dids)} deal(s) but no contacts attached — nothing to send")
            continue

        first = (ow.get("name") or "").split(" ")[0]
        pipe_note = f" in the {pipe} pipeline" if pipe else ""
        body = (f"Hi {first},\n\n"
                f"{len(dids)} new lead{'s' if len(dids) != 1 else ''} "
                f"{'have' if len(dids) != 1 else 'has'} been assigned to you in HubSpot{pipe_note}.\n"
                f"The attached .vcf holds {len(cards)} contact{'s' if len(cards) != 1 else ''} — "
                f"open it on your phone to add them all at once.\n\n"
                + "\n".join(lines) + "\n\n"
                + (f"({n_nophone} of these have no phone on the record.)\n\n" if n_nophone else "")
                + "Please log the outcome against the deal in HubSpot after you call.\n")
        fname = (f"lh2_leads_{re.sub(r'[^a-z0-9]+', '_', (ow.get('name') or 'owner').lower()).strip('_')}"
                 f"_{datetime.date.today().isoformat()}.vcf")
        subject = f"{len(dids)} new LH2 lead{'s' if len(dids) != 1 else ''} assigned to you"
        t, detail = gmail_sender.send(to, subject, body,
                                      [(fname, ("\r\n".join(cards)).encode("utf-8"), "text/vcard")],
                                      dry=dry)
        print(f"  {ow.get('name','?'):18} {len(dids):>3} deal(s) {len(cards):>3} contact(s) "
              f"-> {to:32} [{t}] {detail}")
        if not dry:
            sent_log.append({"at": datetime.datetime.now().isoformat(timespec="seconds"),
                             "owner": ow.get("name"), "to": to, "deals": len(dids),
                             "contacts": len(cards), "transport": t, "detail": str(detail)})

    if not dry:
        json.dump(current, open(STATE, "w"), indent=0)
        json.dump(sent_log[-500:], open(LOG, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
