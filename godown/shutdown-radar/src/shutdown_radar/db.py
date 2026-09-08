# -*- coding: utf-8 -*-
"""SQLite layer. Schema is exactly §3 of the build spec.

Every write is idempotent so a re-run never duplicates: candidates key on
brand_name_norm, evidence keys on a content hash of (candidate, kind, url, pattern).
"""
from __future__ import annotations
import os, json, sqlite3, hashlib, datetime
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS candidate (
  id INTEGER PRIMARY KEY,
  brand_name TEXT NOT NULL,
  brand_name_norm TEXT NOT NULL UNIQUE,
  first_seen_at TEXT NOT NULL,
  discovery_source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence (
  id INTEGER PRIMARY KEY,
  candidate_id INTEGER NOT NULL REFERENCES candidate(id),
  kind TEXT NOT NULL,
  source_url TEXT, source_name TEXT, published_at TEXT,
  as_of_date TEXT,
  snippet TEXT,
  matched_pattern TEXT, raw_json TEXT,
  fetched_at TEXT NOT NULL,
  dedupe_key TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS entity (
  cin TEXT PRIMARY KEY,
  legal_name TEXT NOT NULL, legal_name_norm TEXT NOT NULL,
  company_status TEXT, company_class TEXT, date_of_registration TEXT,
  registered_state TEXT, roc TEXT,
  source TEXT, fetched_at TEXT
);
CREATE TABLE IF NOT EXISTS candidate_entity (
  candidate_id INTEGER NOT NULL REFERENCES candidate(id),
  cin TEXT NOT NULL REFERENCES entity(cin),
  match_score REAL NOT NULL,
  match_method TEXT NOT NULL,
  is_confirmed INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY(candidate_id, cin)
);
CREATE TABLE IF NOT EXISTS liveness (
  candidate_id INTEGER PRIMARY KEY REFERENCES candidate(id),
  domain TEXT, dns_resolves INTEGER, http_status INTEGER, http_final_url TEXT,
  ssl_expired INTEGER, rdap_status TEXT, wayback_last_capture TEXT,
  liveness_score REAL, checked_at TEXT
);
CREATE TABLE IF NOT EXISTS dpiit_startup (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, name_norm TEXT NOT NULL,
  state TEXT, sector TEXT, recognition_date TEXT
);
CREATE TABLE IF NOT EXISTS backfill_progress (
  state_code TEXT PRIMARY KEY, last_offset INTEGER NOT NULL DEFAULT 0,
  total INTEGER, done INTEGER NOT NULL DEFAULT 0, updated_at TEXT
);
CREATE TABLE IF NOT EXISTS scored (
  candidate_id INTEGER PRIMARY KEY REFERENCES candidate(id),
  confidence REAL NOT NULL, tier TEXT NOT NULL,
  shutdown_date TEXT, shutdown_year INTEGER, reason TEXT,
  sector TEXT, city TEXT, funding_usd TEXT, investors TEXT,
  rationale TEXT NOT NULL, scored_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS prequal (
  candidate_id INTEGER PRIMARY KEY REFERENCES candidate(id),
  prequal_total INTEGER NOT NULL, prequal_max_possible INTEGER NOT NULL,
  prequal_pct REAL, prequal_routing TEXT, prequal_note TEXT, prequal_unscored TEXT,
  pq_funding INTEGER, pq_years INTEGER, pq_eng_headcount INTEGER, pq_sector INTEGER,
  pq_code_location INTEGER, pq_legal_status INTEGER,
  github_org TEXT, github_url TEXT, scored_at TEXT
);
CREATE TABLE IF NOT EXISTS run_stat (
  k TEXT PRIMARY KEY, v TEXT
);
CREATE INDEX IF NOT EXISTS ix_entity_norm ON entity(legal_name_norm);
CREATE INDEX IF NOT EXISTS ix_cand_norm ON candidate(brand_name_norm);
CREATE INDEX IF NOT EXISTS ix_ev_cand ON evidence(candidate_id);
CREATE INDEX IF NOT EXISTS ix_dpiit_norm ON dpiit_startup(name_norm);
"""


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def connect(path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    db = sqlite3.connect(path, timeout=60)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(SCHEMA)
    db.commit()
    return db


def upsert_candidate(db, brand_name: str, brand_norm: str, source: str) -> int:
    cur = db.execute("SELECT id FROM candidate WHERE brand_name_norm=?", (brand_norm,))
    r = cur.fetchone()
    if r: return r["id"]
    cur = db.execute(
        "INSERT INTO candidate(brand_name, brand_name_norm, first_seen_at, discovery_source) "
        "VALUES(?,?,?,?)", (brand_name, brand_norm, now(), source))
    return cur.lastrowid


def add_evidence(db, candidate_id: int, kind: str, *, source_url=None, source_name=None,
                 published_at=None, as_of_date=None, snippet=None, matched_pattern=None,
                 raw=None) -> bool:
    """-> True if newly inserted. Dedupe key makes re-runs free of duplicates."""
    key = hashlib.sha256("|".join([str(candidate_id), kind, str(source_url or ""),
                                   str(matched_pattern or ""), str(as_of_date or "")]
                                  ).encode()).hexdigest()
    try:
        db.execute(
            "INSERT INTO evidence(candidate_id,kind,source_url,source_name,published_at,"
            "as_of_date,snippet,matched_pattern,raw_json,fetched_at,dedupe_key) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (candidate_id, kind, source_url, source_name, published_at, as_of_date,
             (snippet or "")[:300], matched_pattern,
             json.dumps(raw, ensure_ascii=False) if raw is not None else None, now(), key))
        return True
    except sqlite3.IntegrityError:
        return False


def upsert_entity(db, cin: str, legal_name: str, legal_norm: str, *, status=None, cls=None,
                  dor=None, state=None, roc=None, source=None):
    db.execute(
        "INSERT INTO entity(cin,legal_name,legal_name_norm,company_status,company_class,"
        "date_of_registration,registered_state,roc,source,fetched_at) VALUES(?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(cin) DO UPDATE SET "
        "  legal_name=COALESCE(excluded.legal_name, legal_name),"
        "  legal_name_norm=COALESCE(excluded.legal_name_norm, legal_name_norm),"
        "  company_status=COALESCE(excluded.company_status, company_status),"
        "  company_class=COALESCE(excluded.company_class, company_class),"
        "  date_of_registration=COALESCE(excluded.date_of_registration, date_of_registration),"
        "  registered_state=COALESCE(excluded.registered_state, registered_state),"
        "  roc=COALESCE(excluded.roc, roc), fetched_at=excluded.fetched_at",
        (cin, legal_name, legal_norm, status, cls, dor, state, roc, source, now()))


def stat(db, k: str, v):
    db.execute("INSERT INTO run_stat(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
               (k, json.dumps(v, ensure_ascii=False, default=str)))
    db.commit()


def get_stat(db, k: str, default=None):
    r = db.execute("SELECT v FROM run_stat WHERE k=?", (k,)).fetchone()
    return json.loads(r["v"]) if r else default
