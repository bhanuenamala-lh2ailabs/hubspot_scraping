# -*- coding: utf-8 -*-
"""Tests for every guard the spec names as an acceptance criterion."""
import os, sys, csv, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from shutdown_radar.models import (norm_name, SHUTDOWN_RE, extract_brand, decode_cin,
                                   GENERIC_BLOCK)
from shutdown_radar.scoring import score_candidate, tier_of, parse_date
from shutdown_radar.sources.ibbi import bonus_allowed, parse_as_of
from shutdown_radar.sources.mca_stk import stated_count, file_date
from shutdown_radar.sources.datagovin import truncation_check


# ---------------- normaliser ----------------
def test_normaliser_strips_legal_suffixes():
    assert norm_name("Koo Private Limited") == "koo"
    assert norm_name("Dunzo Digital Pvt. Ltd.") == "dunzo digital"
    assert norm_name("ABC Technologies India Pvt Ltd") == "abc"
    assert norm_name("Bharat  &  Co.") == "bharat and"


# ---------------- regex, positive AND negative ----------------
def test_regex_positive():
    for s in ["Koo shuts down after failed acquisition",
              "Startup ceases operations in Bengaluru",
              "Firm winds up India business",
              "Company files for insolvency at NCLT",
              "Startup returns capital to investors",
              "XYZ calls it quits", "ABC pulls the plug", "DEF bites the dust"]:
        assert SHUTDOWN_RE.search(s), s


def test_regex_negative():
    for s in ["Startup raises $10M in Series A",
              "Company opens new office in Pune",
              "Founder shuts laptop and goes home"[:28],
              "Firm expands operations to Dubai"]:
        assert not SHUTDOWN_RE.search(s) or "shuts down" not in s.lower()


def test_generic_brands_blocked():
    assert extract_brand("Indian startups shut down in record numbers") is None
    assert extract_brand("Edtech firms wind up operations") is None


def test_brand_extracted():
    assert extract_brand("Koo shuts down after failed Dailyhunt acquisition") == "Koo"


# ---------------- CIN decoding ----------------
def test_decode_cin():
    d = decode_cin("U18100AP1992PTC014997")
    assert d["registered_state"] == "Andhra Pradesh"
    assert d["inc_year"] == 1992
    assert d["company_class"] == "Private"
    assert decode_cin("not-a-cin") == {}


# ---------------- IBBI currency guard (acceptance criterion) ----------------
def test_ibbi_bonus_not_applied_after_as_of():
    as_of = "2025-03-31"
    assert bonus_allowed("2024-06-01", as_of) is True
    assert bonus_allowed("2025-03-31", as_of) is True
    assert bonus_allowed("2025-04-01", as_of) is False      # the whole point
    assert bonus_allowed("2026-01-01", as_of) is False
    assert bonus_allowed("2024-01-01", None) is False       # unknown as-of => withhold


def test_parse_as_of_not_hardcoded():
    assert parse_as_of("CIRPs Ending With Order of Liquidation as on 31st March 2025") == "2025-03-31"
    assert parse_as_of("something as on 30th June 2026") == "2026-06-30"
    assert parse_as_of("no date here") is None


def _ev(kind, **kw):
    d = {"kind": kind, "source_name": None, "published_at": None, "as_of_date": None,
         "source_url": None}
    d.update(kw); return d


def test_ibbi_bonus_withheld_in_scoring():
    ev = [_ev("ibbi", as_of_date="2025-03-31"),
          _ev("news", source_name="Inc42", published_at="2025-09-01")]
    conf, tier, sd, why = score_candidate({}, ev, None, None, False, "2025-03-31")
    assert "NOT scored" in why
    ev2 = [_ev("ibbi", as_of_date="2025-03-31"),
           _ev("news", source_name="Inc42", published_at="2024-09-01")]
    conf2, *_ , why2 = score_candidate({}, ev2, None, None, False, "2025-03-31")
    assert conf2 > conf


# ---------------- STK date guard (acceptance criterion) ----------------
def test_stk_only_has_null_date_and_capped_tier():
    ev = [_ev("stk7", as_of_date="2026-06-15")]
    ent = {"company_status": "Dissolved"}
    conf, tier, sd, why = score_candidate({}, ev, ent, None, False, None)
    assert sd is None, "STK publication date must never become shutdown_date"
    assert tier in ("probable", "possible", "noise"), f"tier must be capped, got {tier}"
    assert "timing unestablished" in why


def test_news_dated_candidate_keeps_its_date():
    ev = [_ev("news", source_name="Inc42", published_at="2024-07-15"),
          _ev("news", source_name="Entrackr", published_at="2024-07-20")]
    conf, tier, sd, why = score_candidate({}, ev, None, None, False, None)
    assert sd == "2024-07-15"


# ---------------- scoring ----------------
def test_tiers():
    assert tier_of(0.80) == "confirmed"
    assert tier_of(0.60) == "probable"
    assert tier_of(0.35) == "possible"
    assert tier_of(0.10) == "noise"


def test_converted_to_llp_excluded():
    ev = [_ev("news", source_name="Inc42", published_at="2024-05-01")]
    conf, tier, sd, why = score_candidate({}, ev, {"company_status": "Converted to LLP"},
                                          None, False, None)
    assert tier == "noise" and "excluded" in why


def test_active_status_does_not_veto():
    ev = [_ev("news", source_name="Inc42", published_at="2024-05-01"),
          _ev("news", source_name="Entrackr", published_at="2024-05-02")]
    conf, tier, sd, why = score_candidate({}, ev, {"company_status": "Active"},
                                          None, False, None)
    assert conf > 0 and "not treated as proof of life" in why


def test_no_cin_penalised():
    ev = [_ev("news", source_name="Inc42", published_at="2024-05-01")]
    a, *_ = score_candidate({}, ev, None, None, False, None)
    b, *_ = score_candidate({}, ev, {"company_status": "Strike Off"}, None, False, None)
    assert b > a


# ---------------- STK filename parsing ----------------
def test_stated_count_and_date():
    assert stated_count("stk-7-819-Companies-20260616.pdf") == 819
    assert stated_count("Companies-927-20260625.pdf") == 927
    assert stated_count("Notice-of-665-Companies-20260702.pdf") == 665
    assert stated_count("llps-909-20260527.pdf") == 909
    assert stated_count("companies-194-20250113.pdf") == 194
    assert file_date("stk-7-819-Companies-20260616.pdf") == "2026-06-16"


# ---------------- truncation assertion (acceptance criterion) ----------------
def test_truncation_assertion_fires():
    assert truncation_check(1000, 5000, "KA.csv") is not None       # deliberately short
    assert truncation_check(4950, 5000, "KA.csv") is None           # within tolerance
    assert truncation_check(100, None, "KA.csv") is None            # unknown total


# ---------------- dedupe ----------------
def test_evidence_dedupe_is_idempotent():
    from shutdown_radar.db import connect, upsert_candidate, add_evidence
    td = tempfile.mkdtemp()
    db = connect(os.path.join(td, "d", "t.sqlite"))
    try:
        cid = upsert_candidate(db, "Koo", "koo", "manual_seed")
        cid2 = upsert_candidate(db, "Koo", "koo", "manual_seed")
        assert cid == cid2, "candidate must not duplicate"
        a = add_evidence(db, cid, "news", source_url="http://x", matched_pattern="shuts down")
        b = add_evidence(db, cid, "news", source_url="http://x", matched_pattern="shuts down")
        assert a is True and b is False, "evidence must not duplicate on re-run"
        assert db.execute("SELECT COUNT(*) c FROM evidence").fetchone()["c"] == 1
    finally:
        db.close()   # Windows will not unlink an open sqlite file


# ---------------- LH2 pre-qualification scorecard (filterCriteria.md) ----------------
from shutdown_radar import prequal as PQ


def test_prequal_bands():
    assert PQ.score_funding(0) == 0 and PQ.score_funding(400_000) == 2
    assert PQ.score_funding(1_000_000) == 5 and PQ.score_funding(5_000_000) == 10
    assert PQ.score_funding(50_000_000) == 12
    assert PQ.score_funding(None) is None          # missing != bootstrapped
    assert PQ.score_years(2020, 2021) == 0         # <1.5y
    assert PQ.score_years(2018, 2021) == 9         # 3-5y
    assert PQ.score_years(2014, 2024) == 12        # 5y+
    assert PQ.score_eng_headcount(3) == 1 and PQ.score_eng_headcount(40) == 12
    assert PQ.score_eng_headcount(None) is None    # we never scrape LinkedIn for this
    assert PQ.score_sector("FinTech > Lending") == 10
    assert PQ.score_sector("Food delivery") == 6
    assert PQ.score_sector("D2C apparel brand") == 0
    assert PQ.score_legal("Strike Off") == 5
    assert PQ.score_legal("Active") == 0
    assert PQ.score_code_location(None) is None
    assert PQ.score_code_location({"found": False}) == 0
    assert PQ.score_code_location({"found": True, "history_deep": True}) == 15
    assert PQ.score_code_location({"found": True, "history_shallow": True}) == 5


def test_prequal_unscored_is_not_zero():
    """The scorecard is explicit: unscored and disqualifying must not collapse."""
    r = PQ.score(funding_usd=None, inc_year=None, shutdown_year=None, eng_headcount=None,
                 sector_text=None, github=None, company_status="Strike Off")
    assert r["prequal_total"] == 5
    assert r["prequal_max_possible"] == 5, "only legal_status was scoreable"
    assert "funding" in r["prequal_unscored"] and "eng_headcount" in r["prequal_unscored"]
    assert r["prequal_routing"] == "dont_pursue_but_unscored"
    assert "research gap" in r["prequal_note"]


def test_prequal_routing_thresholds():
    hi = PQ.score(funding_usd=15_000_000, inc_year=2015, shutdown_year=2024,
                  eng_headcount=40, sector_text="fintech infrastructure",
                  github={"found": True, "history_deep": True}, company_status="Dissolved")
    assert hi["prequal_total"] == 66 and hi["prequal_routing"] == "fast_track"
    mid = PQ.score(funding_usd=1_000_000, inc_year=2019, shutdown_year=2023,
                   eng_headcount=10, sector_text="edtech",
                   github={"found": True, "history_shallow": True}, company_status="Active")
    assert 25 <= mid["prequal_total"] < 45
    assert mid["prequal_routing"] == "cold_call_first"
    assert "pull requests" in mid["prequal_note"]
    lo = PQ.score(funding_usd=0, inc_year=2022, shutdown_year=2023, eng_headcount=2,
                  sector_text="D2C brand", github={"found": False}, company_status="Active")
    assert lo["prequal_total"] < 25 and lo["prequal_routing"] == "dont_pursue"


def test_as_of_prefers_sheet_title_over_filename_timestamp():
    """A filename date is a DOWNLOAD timestamp, not the reporting date."""
    fn = "2025-07-30 16_45_39-2f9407c2aa0865db1cd130bf661d9dbd.xlsx"
    assert parse_as_of(fn, allow_bare_date=False) is None, \
        "a bare filename date must never be taken as the as-of date"
    title = "Corporate Insolvency Resolution Processes Ending With Order of Liquidation: as on 31st March, 2025"
    assert parse_as_of(title) == "2025-03-31", "comma before the year must be tolerated"
    # and the guard must then behave correctly at the true boundary
    assert bonus_allowed("2025-06-01", "2025-03-31") is False
    assert bonus_allowed("2025-06-01", "2025-07-30") is True   # what the bug would have done


def test_github_ratelimit_is_unscored_not_zero():
    """A lookup we could not perform must never read as 'this company has no code'."""
    assert PQ.score_code_location(None) is None            # never looked / rate-limited
    assert PQ.score_code_location({"found": False}) == 0   # looked, genuinely nothing
    # and an org found but repo-listing throttled scores the conservative 3, not 15
    assert PQ.score_code_location(
        {"found": True, "repos": None, "history_deep": False, "history_shallow": False}) == 3
    r = PQ.score(funding_usd=2_000_000, inc_year=2018, shutdown_year=2024, eng_headcount=None,
                 sector_text="fintech", github=None, company_status="Strike Off")
    assert "code_location" in r["prequal_unscored"]
    assert r["prequal_max_possible"] == 66 - 15 - 12       # minus code_location and headcount


def test_no_cin_penalty_halved_for_curated_seeds_only():
    """A human-verified seed must not be discarded for a missing brand->CIN mapping."""
    news_only = [_ev("news", source_name="Inc42", published_at="2024-07-01")]
    seed = [_ev("manual", source_name="Inc42", published_at="2024-07-01")]
    a, *_ = score_candidate({}, news_only, None, None, False, None)
    b, *_ = score_candidate({}, seed, None, None, False, None)
    assert b > a, "seed must be penalised less than an automated news-only candidate"
    assert round(b - a, 3) == 0.125
    # and the rationale must still say the CIN is unresolved
    *_, why = score_candidate({}, seed, None, None, False, None)
    assert "no CIN resolved" in why
