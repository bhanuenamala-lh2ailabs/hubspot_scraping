# 5. Migration blockers and open decisions

## 243 deals are parked on `Call Attempted`

They cannot be sorted automatically — the entire reason for retiring that stage is that it
never recorded which outcome occurred.

| Owner | Scraped | Campaign | Total | Has notes | Has tasks |
|---|---:|---:|---:|---:|---:|
| Shreyas Boosnoor | 122 | 0 | 122 | 18 | 27 |
| Yuktha Anand | 38 | 5 | 43 | 42 | 14 |
| Yash Wani | 17 | 16 | 33 | 31 | 21 |
| Lamiya Saleem | 31 | 1 | 32 | 11 | 31 |
| Ishpreet Sood | 8 | 1 | 9 | 4 | 1 |
| (unassigned) | 4 | 0 | 4 | 3 | 1 |
| **Total** | **220** | **23** | **243** | **109** | **95** |

**109 have notes that do say what happened** — "number out of service", "megha busy Ashutosh
wrong number", "automated call inbox". Those can be triaged into real outcome stages.
**91 have neither note nor task**, and for those there is nothing to recover; `No Pickup` is
the honest destination. Shreyas holds 122 of the 243, so this is mostly a decision about his
queue.

These deals are **not stale** — 18 were touched today and 122 within three days. This is the
team's active working set, not an abandoned pile, so a blind bulk move would reclassify
conversations that are still live.

## Open decisions

1. **Retire `Dead/Interested/NoShow`?** It means the same thing as the new
   `Dead/GMeet/NoShow`. Keeping both splits one number across two stages.
2. **Does `Dead/ScriptShared/NoShow` count toward VCs attended?** Yes if a follow-up call is
   booked after the script goes out; no if the script is simply emailed. Currently excluded.
3. **Destination for the 243.**

## Known measurement limits

- **Calls attempted is a floor, not a dial count.** A repeat dial on a deal that does not
  change stage produces no transition and is invisible. The portal contains **2 logged call
  engagements in total** (14 July, no owner, disposition or duration) — HubSpot's call object
  is effectively unused. The only real fix is logging calls.
- **The migration will break the time series.** `Call Attempted` disappears but remains in
  history. Map historical `Call Attempted` → `No Pickup` for continuity and mark the boundary.
- **Unknown stage IDs already appear in history** (for example `3992480479`, a deleted
  stage). The metric code must skip them rather than crash or mislabel.
- **A later no-show must not retroactively decrement** the day a GMeet was booked.
- **57 of 92 open tasks are already past due.** The callback discipline the new flow depends
  on is not currently being kept, and `No Pickup` only works if the +1 day task gets worked.
