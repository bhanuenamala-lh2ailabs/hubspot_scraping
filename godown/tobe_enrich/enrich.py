# -*- coding: utf-8 -*-
import csv, json, urllib.request, urllib.error, time, os

HUB = "/Users/bhanu/Desktop/hubspot"
HERE = os.path.dirname(os.path.abspath(__file__))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]
IN_CSV = os.path.join(HUB, "tobe.csv")
STATE = os.path.join(HERE, "state.json")
OUT_CSV = os.path.join(HUB, "tobe_enriched.csv")

def reveal_full(li_url):
    body = {"items": [li_url], "withoutWaterfall": True}
    r = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",
                               data=json.dumps(body).encode(), method="POST",
                               headers={"apikey": SH, "Content-Type": "application/json"})
    try:
        d = json.loads(urllib.request.urlopen(r, timeout=60).read().decode())
    except urllib.error.HTTPError as e:
        return None, e.code
    except Exception as e:
        return None, str(e)[:60]
    for it in (d if isinstance(d, list) else d.get("results", [])) or []:
        if isinstance(it, dict) and it.get("status") == "success":
            return (it.get("candidate") or {}).get("contacts") or [], "success"
    return [], "no_match"

def load_state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {}

def save_state(s):
    json.dump(s, open(STATE, "w"), indent=0)

def main():
    rows = list(csv.DictReader(open(IN_CSV, encoding="utf-8-sig")))
    print(f"total rows: {len(rows)}")
    state = load_state()
    print(f"already done: {len(state)}")

    for i, r in enumerate(rows, 1):
        key = r.get("LinkedIn URL", "").strip()
        if not key or key in state:
            continue
        contacts, status = reveal_full(key)
        work = personal = phone = None
        if contacts:
            for c in contacts:
                if c.get("type") == "email":
                    if c.get("subType") == "work" and not work: work = c["value"]
                    elif c.get("subType") == "personal" and not personal: personal = c["value"]
                    elif not work and not personal and not c.get("subType"): personal = c["value"]
                if c.get("type") == "phone" and c.get("subType") == "mobile" and not phone:
                    phone = c["value"]
        final_email = work or personal or ""
        state[key] = {"email": final_email, "is_official": bool(work), "phone": phone or "",
                      "status": status}
        if i % 25 == 0 or i == len(rows):
            save_state(state)
            print(f"  [{i}/{len(rows)}] processed, {len(state)} total in state", flush=True)
        time.sleep(0.3)
    save_state(state)

    # write final enriched CSV
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["First Name","Last Name","Company","LinkedIn URL","Email","Is Official","Phone"])
        for r in rows:
            key = r.get("LinkedIn URL", "").strip()
            s = state.get(key, {})
            w.writerow([r.get("First Name",""), r.get("Last Name",""), r.get("Company",""),
                       key, s.get("email",""), "Yes" if s.get("is_official") else ("" if not s.get("email") else "No"),
                       s.get("phone","")])
    print(f"\nwrote {OUT_CSV}")

if __name__ == "__main__":
    main()
