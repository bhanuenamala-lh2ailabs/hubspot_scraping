"""One-off: enrich only NEW gate-pass firms (skip already-enriched), then score."""
from lh2_pipeline.config import load_config
from lh2_pipeline.store import open_store
from lh2_pipeline.enrich import run_enrich
from lh2_pipeline.judge import run_score

cfg = load_config(None)
store = open_store(cfg)
try:
    stats = run_enrich(cfg, store, max_enrich=60, only_new=True)
    print("ENRICH:", {k: stats.get(k) for k in
          ("enriched", "skipped_existing", "failed", "signalhire_credits_left")})
    run_score(cfg, store)
    print("SCORE done")
finally:
    store.close()
