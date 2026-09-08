# -*- coding: utf-8 -*-
"""Normalize, dedupe, diff, and write the Bengaluru tech-event calendar.

VERIFIED_CANDIDATES below are hand-normalized from real scraped evidence (official-organizer-site
crawls via apify/website-content-crawler, cross-checked against Google search discovery) — not
generated from the noisy Tier-1 aggregator pulls, which is a deliberate call, not an oversight:

  - zen-studio/10times-events-scraper (3 runs, ~$0.22, raw_10times*.json): its category/keyword
    filters proved too loose for this account's actor version — searches for "Bengaluru" +
    category=156 (IT & Technology) surfaced jewellery shows, medical congresses, and generic
    "*Summit"-titled unrelated events, and never once surfaced the actual Bengaluru Tech Summit.
    Kept as a discovery feed for FUTURE runs (see next-run notes below), but nothing from it
    passed the target-profile filter this run.
  - parseforge/eventbrite-scraper (raw_eventbrite.json, 18 items): mostly small paid
    workshops/webinars tagged Bengaluru, not large B2B trade expos. Nothing passed the filter.
  - apify/google-search-scraper (raw_google_search.json) + apify/website-content-crawler
    (raw_bengalurutechsummit.json, raw_cypher_iew.json) is what actually found real events:
    Bengaluru Tech Summit's own site, then Cypher and India Electronics Week via Tier-3 search
    discovery, each confirmed on their own official sites.
  - Two Tier-3 discoveries (India IT Expo 2026 - Apr 6-8, and India Intl Smart City Tech Expo -
    Jul 25-27) were dropped: both already ended before this run's date (2026-08-27) - past events
    on a first run aren't part of the "upcoming" calendar. Bengaluru Space Expo (Sep 7-9, 2026)
    was dropped on target-profile grounds (aerospace/space hardware, not IT-services/software).

Next-run notes (for whoever extends this): the 10times actor's `city` field only accepts a fixed
enum of numeric IDs and Bengaluru (cityId 70532) is NOT in that enum - don't waste a run guessing
it again. `query` mode is a loose full-text search across tags, not a hard city/category filter -
treat its output as a discovery feed to manually screen, not a direct source of truth.
"""
import json, re, os, datetime, csv

HERE = os.path.dirname(os.path.abspath(__file__))
EVENTS_JSON = os.path.join(HERE, "events.json")
EVENTS_CSV = os.path.join(HERE, "events.csv")
TODAY = "2026-08-27"  # run date (Date.now()-style calls aren't available in this environment)

SCHEMA_FIELDS = ["event_name", "start_date", "end_date", "city", "venue", "state", "organizer",
                  "official_url", "category", "expected_visitors", "exhibitor_count",
                  "notable_exhibitors", "speakers_count", "registration_url", "source",
                  "source_url", "first_seen", "last_seen", "status"]

VERIFIED_CANDIDATES = [
    {
        "event_name": "Bengaluru Tech Summit 2026",
        "start_date": "2026-11-17", "end_date": "2026-11-19",
        "city": "Bengaluru", "state": "Karnataka",
        "venue": "Bangalore International Exhibition Centre (BIEC), 10th Mile, Tumkur Road, Bengaluru 562123",
        "organizer": "Dept. of Electronics, IT and BT, Government of Karnataka",
        "official_url": "https://www.bengalurutechsummit.com/",
        "category": "Technology Summit & Trade Expo",
        "expected_visitors": "60,000+ business visitors; 25,000+ delegates",
        "exhibitor_count": "1,800+",
        "notable_exhibitors": [],
        "speakers_count": "700+",
        "registration_url": "",
        "source": "official organizer site (apify/website-content-crawler)",
        "source_url": "https://bengalurutechsummit.com/",
    },
    {
        # site's own H1 says "Oct 7-9" but the venue-link banner text says "10th Edition ·
        # Oct 6-8, 2026 · KTPO, Bengaluru" - kept the more specific inline text, flagging the
        # inconsistency rather than silently picking one.
        "event_name": "Cypher 2026 (AI Conference & Expo)",
        "start_date": "2026-10-06", "end_date": "2026-10-08",
        "city": "Bengaluru", "state": "Karnataka",
        "venue": "KTPO, Bengaluru",
        "organizer": "Analytics India Magazine (AIM); presented by IBM, powered by Genpact",
        "official_url": "https://cypher.analyticsindiamag.com/",
        "category": "AI Summit & Expo",
        "expected_visitors": "5,000+ attendees",
        "exhibitor_count": "100+",
        "notable_exhibitors": [],
        "speakers_count": "150+",
        "registration_url": "https://cypher.analyticsindiamag.com/tickets",
        "source": "official organizer site (apify/website-content-crawler)",
        "source_url": "https://cypher.analyticsindiamag.com/",
    },
    {
        # 2026 edition (13-15 May 2026, per the Google snippet) already happened before this
        # run's date; the live site has moved on to the 2027 edition - that's the one recorded.
        # Its visitor/exhibitor/speaker stats block was all "0+" placeholders in the crawled
        # snapshot (JS counters that hadn't animated) - left blank rather than guessed.
        "event_name": "India Electronics Week (IEW) 2027",
        "start_date": "2027-05-05", "end_date": "2027-05-07",
        "city": "Bengaluru", "state": "Karnataka",
        "venue": "KTPO Convention Centre, Whitefield, Bengaluru",
        "organizer": "",
        "official_url": "https://www.indiaelectronicsweek.com/",
        "category": "Electronics R&D Conference & Expo",
        "expected_visitors": "",
        "exhibitor_count": "",
        "notable_exhibitors": [],
        "speakers_count": "",
        "registration_url": "",
        "source": "official organizer site (apify/website-content-crawler)",
        "source_url": "https://www.indiaelectronicsweek.com/",
    },
]


def slug(name):
    s = re.sub(r"[^\w\s-]", "", name.lower())
    return re.sub(r"[\s_]+", "-", s).strip("-")


def normalized_id(rec):
    year = rec["start_date"][:4]
    return f'{slug(rec["event_name"])}|{year}|{slug(rec["city"])}'


def main():
    known = {}
    if os.path.exists(EVENTS_JSON):
        for rec in json.load(open(EVENTS_JSON)):
            known[rec["normalized_id"]] = rec

    new_count = changed_count = unchanged_count = 0
    changelog = []
    final = dict(known)  # start from known, overlay this run's results

    for cand in VERIFIED_CANDIDATES:
        nid = normalized_id(cand)
        status = "upcoming" if cand["end_date"] >= TODAY else "past"
        rec = {**cand, "notable_exhibitors": ";".join(cand["notable_exhibitors"]),
               "normalized_id": nid, "status": status}

        if nid not in known:
            rec["first_seen"] = TODAY
            rec["last_seen"] = TODAY
            final[nid] = rec
            new_count += 1
            changelog.append(("NEW", rec))
        else:
            prev = known[nid]
            diff_fields = [f for f in ("start_date", "end_date", "venue", "official_url")
                           if prev.get(f) != rec.get(f)]
            merged = dict(prev)
            merged.update({k: v for k, v in rec.items() if v not in (None, "", [])})
            merged["last_seen"] = TODAY
            final[nid] = merged
            if diff_fields:
                changed_count += 1
                changelog.append(("CHANGED", merged, diff_fields))
            else:
                unchanged_count += 1

    # mark anything known-but-not-seen-this-run as past if its end_date has lapsed
    for nid, rec in final.items():
        if rec.get("end_date", "9999") < TODAY and rec.get("status") != "past":
            rec["status"] = "past"

    ordered = sorted(final.values(), key=lambda r: r["start_date"])
    json.dump(ordered, open(EVENTS_JSON, "w"), indent=1, ensure_ascii=False)

    with open(EVENTS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["normalized_id"] + SCHEMA_FIELDS)
        w.writeheader()
        for r in ordered:
            row = {k: r.get(k, "") for k in ["normalized_id"] + SCHEMA_FIELDS}
            w.writerow(row)

    print(f"=== Bengaluru tech-event calendar run ({TODAY}) ===")
    print(f"total events tracked: {len(ordered)}")
    print(f"new: {new_count} | changed: {changed_count} | unchanged: {unchanged_count}")
    print("sources scraped: 5 (10times x1 relevant run + eventbrite x1 + google-search x1 + "
          "website-content-crawler x2) | actor errors: 0 (all runs succeeded; low signal-to-noise "
          "on 10times/eventbrite was a relevance issue, not a failure)")
    print(f"\nwrote {EVENTS_JSON}")
    print(f"wrote {EVENTS_CSV}")

    if changelog:
        print("\n-- NEW / CHANGED events --")
        for entry in changelog:
            kind = entry[0]
            rec = entry[1]
            print(f"  [{kind}] {rec['event_name']} | {rec['start_date']} to {rec['end_date']} | "
                  f"{rec['city']} | {rec['official_url']}")


if __name__ == "__main__":
    main()
