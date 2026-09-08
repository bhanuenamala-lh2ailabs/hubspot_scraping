# Task: Build a Google Maps API Scraper for Tier 2/3 Indian IT Companies

## Context

We have an existing lead-sourcing pipeline (`lh2-pipeline`) that discovers Indian IT-services companies from directory sites (GoodFirms, Clutch, etc.) and enriches them with founder contacts. Our sales data shows Tier 2/3 cities convert 2-3x better than Tier 1 (Bangalore, Pune, Hyderabad) but our directory crawlers are biased toward Tier 1 — smaller cities are under-represented because firms there don't list on GoodFirms/Clutch.

Google Maps catches these firms because every business with a Google Business Profile shows up, regardless of whether they list on directories. This script fills that gap.

## Goal

Build a standalone Python script that uses the **Google Places API (New)** Text Search endpoint to discover IT-services companies across 20+ Indian Tier 2/3 cities, deduplicate results, filter noise, and export a clean CSV that can be fed into the existing pipeline's `build` phase.

## CRITICAL: Stay Under the Free Tier

Google Places API gives **5,000 free Text Search (Pro) calls per month**. After that, it's $32/1,000 calls. We want to stay at **$0 spend** for the initial run. This means:

- **Hard budget cap: 4,500 API calls** (leave 500 buffer)
- The script MUST track call count and **stop automatically** when approaching the limit
- Log every API call with a running total
- Print a summary at the end: total calls made, remaining budget, estimated overage cost if any
- Support `--max-calls N` flag to set a custom budget cap (default: 4500)
- Support `--dry-run` to show what would be searched without making API calls

### Budget allocation strategy

With ~4,500 calls across 20 cities and 5 query variations = 100 city×query combos. Each combo gets ~45 calls max. But not all cities need the same depth:

- **Priority cities** (high potential from sales data + known IT hubs): more tiles, more queries
- **Exploratory cities** (less known, testing): fewer tiles, fewer queries

The script should allocate budget proportionally based on city priority tiers.

## Google Places API Details

### Authentication

API key in env var `GOOGLE_MAPS_API_KEY`. Add to `.env`.

### Endpoint

```
POST https://places.googleapis.com/v1/places:searchText
```

Headers:
```
Content-Type: application/json
X-Goog-Api-Key: {GOOGLE_MAPS_API_KEY}
X-Goog-FieldMask: places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.types,places.id,places.userRatingCount,places.rating,places.location
```

**IMPORTANT:** The `X-Goog-FieldMask` header controls which fields are returned AND which pricing tier you're billed at. The fields above are all **Pro tier** ($32/1,000). Do NOT request `reviews`, `editorialSummary`, or `priceLevel` — those push you to Enterprise tier ($40/1,000).

### Request body

```json
{
  "textQuery": "software development company in Mohali",
  "locationRestriction": {
    "rectangle": {
      "low": {"latitude": 30.65, "longitude": 76.68},
      "high": {"latitude": 30.75, "longitude": 76.78}
    }
  },
  "maxResultCount": 20,
  "languageCode": "en"
}
```

### Pagination

The response includes a `nextPageToken` if more results exist. To get the next page:

```json
{
  "textQuery": "...",
  "pageToken": "next_page_token_value"
}
```

Maximum 3 pages × 20 results = **60 results per query**. Each page is a separate API call. So one query = 1-3 API calls depending on result count.

### The 60-result cap problem

If a city×query combo has more than 60 matching businesses, you only see the first 60. Solution: **grid-tiling** — subdivide the city into smaller geographic tiles so each tile has <60 results.

## Implementation

### 1. City list with bounding boxes and priority

```python
CITIES = {
    # PRIORITY TIER 1 — proven converters + large IT hubs (more budget)
    "Mohali": {
        "bbox": {"low": {"lat": 30.65, "lng": 76.65}, "high": {"lat": 30.78, "lng": 76.78}},
        "priority": 1,
        "notes": "Best converter in sales data — 27% Interested+, 1.91 avg depth"
    },
    "Surat": {
        "bbox": {"low": {"lat": 21.10, "lng": 72.75}, "high": {"lat": 21.25, "lng": 72.90}},
        "priority": 1,
        "notes": "0% WrongFit, 100% Called+ in sales data"
    },
    "Indore": {
        "bbox": {"low": {"lat": 22.65, "lng": 75.80}, "high": {"lat": 22.80, "lng": 75.95}},
        "priority": 1,
        "notes": "20% Interested+, growing startup ecosystem"
    },
    "Coimbatore": {
        "bbox": {"low": {"lat": 10.95, "lng": 76.90}, "high": {"lat": 11.10, "lng": 77.05}},
        "priority": 1,
        "notes": "Strong IT services cluster, TIDEL Park"
    },
    "Kochi": {
        "bbox": {"low": {"lat": 9.92, "lng": 76.22}, "high": {"lat": 10.07, "lng": 76.37}},
        "priority": 1,
        "notes": "Infopark + SmartCity, Kerala tech hub"
    },
    "Mysuru": {
        "bbox": {"low": {"lat": 12.25, "lng": 76.58}, "high": {"lat": 12.38, "lng": 76.72}},
        "priority": 1,
        "notes": "Infosys hometown, large IT workforce"
    },

    # PRIORITY TIER 2 — known IT presence, untested in sales
    "Nagpur": {
        "bbox": {"low": {"lat": 21.10, "lng": 79.00}, "high": {"lat": 21.20, "lng": 79.15}},
        "priority": 2,
        "notes": "MIHAN IT SEZ"
    },
    "Vizag": {
        "bbox": {"low": {"lat": 17.68, "lng": 83.18}, "high": {"lat": 17.78, "lng": 83.35}},
        "priority": 2,
        "notes": "AP IT capital, Millennium Tower"
    },
    "Thiruvananthapuram": {
        "bbox": {"low": {"lat": 8.45, "lng": 76.90}, "high": {"lat": 8.58, "lng": 77.03}},
        "priority": 2,
        "notes": "Technopark — oldest IT park in India"
    },
    "Lucknow": {
        "bbox": {"low": {"lat": 26.78, "lng": 80.88}, "high": {"lat": 26.92, "lng": 81.05}},
        "priority": 2,
        "notes": "UP IT push, multiple tech parks"
    },
    "Bhubaneswar": {
        "bbox": {"low": {"lat": 20.22, "lng": 85.78}, "high": {"lat": 20.35, "lng": 85.90}},
        "priority": 2,
        "notes": "Infocity, strong mid-size IT firms"
    },
    "Bhopal": {
        "bbox": {"low": {"lat": 23.20, "lng": 77.35}, "high": {"lat": 23.32, "lng": 77.48}},
        "priority": 2,
        "notes": "33% Interested+ in sales data (small sample)"
    },
    "Mangaluru": {
        "bbox": {"low": {"lat": 12.83, "lng": 74.82}, "high": {"lat": 12.93, "lng": 74.92}},
        "priority": 2,
        "notes": "Growing services hub"
    },
    "Vadodara": {
        "bbox": {"low": {"lat": 22.27, "lng": 73.15}, "high": {"lat": 22.37, "lng": 73.25}},
        "priority": 2,
        "notes": "IT park growing, in sales data already"
    },

    # PRIORITY TIER 3 — exploratory
    "Rajkot": {
        "bbox": {"low": {"lat": 22.27, "lng": 70.75}, "high": {"lat": 22.35, "lng": 70.85}},
        "priority": 3,
        "notes": "Small IT cluster, very under-targeted"
    },
    "Vijayawada": {
        "bbox": {"low": {"lat": 16.48, "lng": 80.58}, "high": {"lat": 16.55, "lng": 80.68}},
        "priority": 3,
        "notes": "AP startup hub"
    },
    "Hubli": {
        "bbox": {"low": {"lat": 15.33, "lng": 75.08}, "high": {"lat": 15.42, "lng": 75.18}},
        "priority": 3,
        "notes": "Emerging Karnataka Tier 3"
    },
    "Trichy": {
        "bbox": {"low": {"lat": 10.78, "lng": 78.65}, "high": {"lat": 10.87, "lng": 78.75}},
        "priority": 3,
        "notes": "IT corridor developing"
    },
    "Chandigarh": {
        "bbox": {"low": {"lat": 30.70, "lng": 76.74}, "high": {"lat": 30.78, "lng": 76.82}},
        "priority": 3,
        "notes": "Adjacent to Mohali — may overlap, dedup needed"
    },
    "Kolkata": {
        "bbox": {"low": {"lat": 22.45, "lng": 88.28}, "high": {"lat": 22.62, "lng": 88.45}},
        "priority": 3,
        "notes": "Already in sales data but 29% WrongFit — test Maps coverage"
    },
}
```

**Note:** Bounding boxes above are approximate. Verify and adjust by checking Google Maps for each city. The bbox should cover the main IT/business districts, not the entire metro area.

### 2. Query variations

```python
QUERIES = [
    "software development company in {city}",
    "IT company in {city}",
    "web development company in {city}",
    "mobile app development company in {city}",
    "custom software company in {city}",
]
```

**Budget allocation per priority:**
- Priority 1 cities: all 5 queries
- Priority 2 cities: top 3 queries ("software development", "IT company", "web development")
- Priority 3 cities: top 2 queries ("software development", "IT company")

This keeps total calls within the 4,500 budget.

### 3. Grid-tiling logic

For each city×query combo:

1. Start with the full city bounding box as a single tile
2. Run the query → if results = 60 (cap hit), subdivide into 4 tiles (split lat and lng at midpoints)
3. Re-run each sub-tile → repeat if any sub-tile hits 60
4. Max recursion depth: 2 (so max 16 tiles per city×query — prevents runaway API usage)
5. Dedup results by `place_id` across all tiles

```python
def subdivide_bbox(bbox):
    """Split a bounding box into 4 equal quadrants."""
    mid_lat = (bbox["low"]["lat"] + bbox["high"]["lat"]) / 2
    mid_lng = (bbox["low"]["lng"] + bbox["high"]["lng"]) / 2
    return [
        {"low": {"lat": bbox["low"]["lat"], "lng": bbox["low"]["lng"]}, "high": {"lat": mid_lat, "lng": mid_lng}},
        {"low": {"lat": bbox["low"]["lat"], "lng": mid_lng}, "high": {"lat": mid_lat, "lng": bbox["high"]["lng"]}},
        {"low": {"lat": mid_lat, "lng": bbox["low"]["lng"]}, "high": {"lat": mid_lat, "lng": mid_lng}},  # fix: high lat
        {"low": {"lat": mid_lat, "lng": mid_lng}, "high": {"lat": bbox["high"]["lat"], "lng": bbox["high"]["lng"]}},
    ]
```

### 4. Rate limiting and caching

- **Rate limit:** max 10 requests/second (Google's QPS limit for Places API)
- **Cache:** write every API response to a local SQLite database or JSON cache (keyed by query + bbox hash). Re-runs never re-call the API for the same query+bbox.
- **Budget tracker:** a simple counter that increments with every API call. Check before each call — if at limit, stop gracefully.

```python
class BudgetTracker:
    def __init__(self, max_calls: int = 4500):
        self.max_calls = max_calls
        self.calls_made = 0

    def can_call(self) -> bool:
        return self.calls_made < self.max_calls

    def record_call(self):
        self.calls_made += 1
        if self.calls_made % 100 == 0:
            print(f"  API calls: {self.calls_made}/{self.max_calls} ({self.remaining} remaining)")

    @property
    def remaining(self) -> int:
        return self.max_calls - self.calls_made

    @property
    def estimated_cost(self) -> float:
        overage = max(0, self.calls_made - 5000)
        return overage * 0.032  # $32/1000
```

### 5. Noise filtering

After collecting all results, filter out non-IT-services businesses:

**Reject if `types` includes any of:**
```python
REJECT_TYPES = {
    "electronics_store", "hardware_store", "computer_repair_service",
    "computer_store", "electrical_repair_service", "locksmith",
    "education", "school", "university", "training_center",
    "telecommunications_service_provider", "cell_phone_store",
    "print_shop", "accounting", "insurance_agency",
    "real_estate_agency", "shopping_mall", "convenience_store",
}
```

**Reject if company name contains (case-insensitive):**
```python
REJECT_NAME_PATTERNS = [
    "computer repair", "laptop service", "cctv", "surveillance",
    "coaching", "training institute", "academy", "classes",
    "tcs", "infosys", "wipro", "hcl tech", "tech mahindra",
    "cognizant", "accenture", "capgemini",  # big cos, not our ICP
    "xerox", "printer", "toner", "cartridge",
]
```

**Require:**
- `websiteUri` is present (no website = can't dedup or enrich)
- `userRatingCount` >= 3 (filters ghost listings)
- `userRatingCount` <= 200 (filters very large companies)

### 6. Output schema

Export a CSV matching the pipeline's expected input format:

```csv
company_name,domain,office_phone,address,city,rating,review_count,place_id,source,discovered_at
```

| Column | Source | Notes |
|---|---|---|
| `company_name` | `displayName.text` | Strip "Pvt Ltd", "LLP", etc. for cleaner matching |
| `domain` | Extract from `websiteUri` (canonical domain using tldextract) | **This is the dedup key** |
| `office_phone` | `nationalPhoneNumber` | NOT founder mobile — office phone |
| `address` | `formattedAddress` | Full address string |
| `city` | The city we searched (from our city list, not parsed from address) | Consistent city name |
| `rating` | `rating` | Google rating |
| `review_count` | `userRatingCount` | Proxy for company size/activity |
| `place_id` | `id` | Google's dedup key |
| `source` | `"google_maps"` | Constant |
| `discovered_at` | ISO timestamp | When this run happened |

### 7. Deduplication

Three levels:
1. **Within the run:** dedup by `place_id` (across tiles and queries for the same city)
2. **Within the output:** dedup by canonical `domain` (one company may have multiple locations)
3. **Against existing pipeline data:** if `data/delivered_domains.txt` or the pipeline SQLite exists, exclude domains already known. Support `--exclude-file PATH` flag.

### 8. CLI interface

```bash
# Full run (all cities, within free tier)
python gmaps_scraper.py

# Dry run — show what would be searched, estimated API calls, no actual calls
python gmaps_scraper.py --dry-run

# Limit to specific cities
python gmaps_scraper.py --cities Mohali,Surat,Indore

# Limit to priority tier
python gmaps_scraper.py --priority 1

# Custom budget cap
python gmaps_scraper.py --max-calls 2000

# Exclude domains already in pipeline
python gmaps_scraper.py --exclude-file data/delivered_domains.txt

# Output file (default: data/exports/gmaps_tier2_leads.csv)
python gmaps_scraper.py --output data/exports/gmaps_tier2_leads.csv
```

### 9. Summary output

After the run, print a clear summary:

```
=== Google Maps Tier 2/3 IT Company Discovery ===

API calls made:      1,847 / 4,500 budget
Estimated cost:      $0.00 (within free tier of 5,000)
Cities searched:     20
Queries executed:    68
Raw results:         2,341
After noise filter:  1,456
After dedup:         1,102
After domain dedup:  934
After exclude file:  891 net-new

Output: data/exports/gmaps_tier2_leads.csv (891 rows)

Top cities by yield:
  Mohali:        87 firms
  Coimbatore:    72 firms
  Surat:         68 firms
  Indore:        64 firms
  Kochi:         61 firms
  ...
```

### 10. File structure

```
gmaps_scraper/
    __init__.py
    scraper.py        # main scraper logic
    cities.py         # city definitions with bounding boxes
    filters.py        # noise filtering logic
    cache.py          # API response caching
    budget.py         # budget tracking
    export.py         # CSV export
    __main__.py       # CLI entry point
```

Or if simpler: a single `gmaps_scraper.py` file is fine. Don't over-engineer — this is a discovery tool, not a production service.

## Dependencies

```
httpx
tldextract
python-dotenv
```

All likely already in the project. No new dependencies needed.

## Important constraints

- **Stay under 4,500 API calls.** This is the hard constraint. The script must track and enforce this.
- **Cache everything.** Every API response cached locally so re-runs cost zero.
- **Never fabricate.** If a field is missing from the API response, leave it blank.
- **Polite and compliant.** This uses the official Google API, not scraping — so we're ToS-compliant. Respect rate limits (10 QPS).
- **The output feeds into the existing pipeline.** The CSV format must be ingestable by the pipeline's `build` phase (canonical domain is the dedup key).
- **Bounding boxes are approximate.** Verify against Google Maps before the first real run. If a bbox is wrong, results will be wrong or empty.

## Testing plan

1. `python gmaps_scraper.py --dry-run` → shows estimated calls, no API usage
2. `python gmaps_scraper.py --cities Mohali --max-calls 50` → test one city, tiny budget
3. Check output CSV — verify company names look like real IT firms, domains resolve, phones are present
4. `python gmaps_scraper.py --cities Mohali --max-calls 50` again → verify cache works (0 new API calls)
5. `python gmaps_scraper.py --priority 1 --max-calls 1000` → run all Priority 1 cities
6. Full run: `python gmaps_scraper.py` → all cities within 4,500 budget


the json key we have in this project, i just enabled the google maps API new so please go ahead and implement the above. 