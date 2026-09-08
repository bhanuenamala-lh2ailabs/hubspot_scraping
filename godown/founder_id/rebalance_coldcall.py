# -*- coding: utf-8 -*-
"""Level Yuktha and Lamiya's Cold Call stock — 2026-08-17 instruction "both have same".

29 deals at Cold Call, split Lamiya 22 / Yuktha 7. 29 is odd so exact-equal is impossible;
target is 15/14. Move 7 of Lamiya's OLDEST Cold Call deals to Yuktha.

Deliberately NOT moved: today's fresh prequal_q1 pushes (source_tab='prequal_q1') — that
cohort was already split 4/4 and moving it would just re-imbalance the newest work. Oldest
deals go first because they are the most likely to be stale re-verification stock, not live
conversations. Both hubspot_owner_id and poc are updated (poc drives report routing).

Usage: python3 rebalance_coldcall.py [--apply]
"""
import os, sys, json, time, urllib.request, urllib.error

HUB = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
LAMIYA, YUKTHA = "96574824", "96573782"
NAME = {LAMIYA: "Lamiya", YUKTHA: "Yuktha"}
COLD = ["3992480462", "4002503379"]
APPLY = "--apply" in sys.argv


def hs(u, m="GET", b=None):
    d = json.dumps(b).encode() if b is not None else None
    for a in range(6):
        try:
            r = urllib.request.Request("https://api.hubapi.com" + u, data=d, method=m, headers=H)
            with urllib.request.urlopen(r, timeout=60) as x:
                t = x.read().decode(); return x.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 5: time.sleep(2 * (a + 1)); continue
            return e.code, {"raw": e.read().decode()[:200]}
        except Exception:
            if a == 5: raise
            time.sleep(3 * (a + 1))


def cold_deals(owner):
    out, after = [], None
    while True:
        b = {"limit": 200, "properties": ["dealname", "createdate", "source_tab", "lead_source", "dealstage"],
             "filterGroups": [{"filters": [
                 {"propertyName": "hubspot_owner_id", "operator": "EQ", "value": owner},
                 {"propertyName": "dealstage", "operator": "IN", "values": COLD}]}]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        out += d.get("results", [])
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    return out


def main():
    lam = cold_deals(LAMIYA); yuk = cold_deals(YUKTHA)
    total = len(lam) + len(yuk)
    tgt_lam = total // 2 + (total % 2)          # the larger half stays with the busier owner
    move_n = len(lam) - tgt_lam
    print(f"Cold Call now — Lamiya {len(lam)}, Yuktha {len(yuk)} (total {total})")
    print(f"target Lamiya {tgt_lam}, Yuktha {total - tgt_lam}  ->  move {move_n} Lamiya->Yuktha\n")
    if move_n <= 0:
        print("already level within 1 — nothing to do"); return

    # oldest first, but never today's fresh prequal cohort
    movable = [d for d in lam if d["properties"].get("source_tab") != "prequal_q1"]
    movable.sort(key=lambda d: d["properties"].get("createdate", ""))
    pick = movable[:move_n]
    if len(pick) < move_n:                       # not enough non-prequal; fall back to oldest overall
        rest = [d for d in sorted(lam, key=lambda d: d["properties"].get("createdate", ""))
                if d["id"] not in {p["id"] for p in pick}]
        pick += rest[:move_n - len(pick)]
    for d in pick:
        p = d["properties"]
        print(f'   move {d["id"]:<14}{p.get("dealname","")[:34]:<36}{p.get("createdate","")[:10]}  {p.get("lead_source","")[:24]}')
    if not APPLY:
        print("\nDRY RUN — nothing changed. Re-run with --apply."); return

    ok = 0
    for d in pick:
        s, _ = hs(f"/crm/v3/objects/deals/{d['id']}", "PATCH",
                  {"properties": {"hubspot_owner_id": YUKTHA, "poc": YUKTHA}})
        ok += s == 200
        time.sleep(0.2)
    la, yu = cold_deals(LAMIYA), cold_deals(YUKTHA)
    print(f"\nmoved {ok}/{len(pick)} | VERIFY live — Lamiya {len(la)}, Yuktha {len(yu)}")


main()
