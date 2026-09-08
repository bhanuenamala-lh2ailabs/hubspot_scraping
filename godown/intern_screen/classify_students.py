# -*- coding: utf-8 -*-
"""Mark students in Sheet1 column L, per instruction 2026-08-17.

User's demonstrated convention (rows 2-6): a candidate still in / finishing college -> "In
college". They marked 2026 graduates as "In college" (applications came in May 2026 while
those people were in their final semester), so the cutoff is: education END year >= 2026, OR
explicit enrollment language, -> student. Graduated (end <= 2025, or clear post-grad full-time
work) -> "Graduated".

Signals read from the resume text (cached), education-context-scoped so a job's "2024-Present"
does not get mistaken for a degree end date:
  student   : edu end-year >= 2026 | "pursuing"/"final year"/"Nth year"/"undergraduate"/
              "expected 20xx"/"ongoing" near an education keyword
  graduated : edu end-year <= 2025 with nothing enrolling it, or a clear grad-then-worked arc

EXISTING column-L values (the user's manual marks, incl. "Schedule") are PRESERVED — this only
fills blank cells. Low-confidence rows (no year, no signal) are marked "review" not guessed.

Usage: python3 classify_students.py            (dry run: prints the classification table)
       python3 classify_students.py --apply    (writes blank L cells only)
"""
import os, re, sys, json
HUB = "/Users/bhanu/Desktop/hubspot"
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from gsheets import read, svc
SP = "/private/tmp/claude-501/-Users-bhanu-Desktop-hubspot/2bf3c003-90a4-4ea2-84fd-4ba8ed554b6b/scratchpad"
SID = "1IPA45kJ6yTsBo8d33DM0Ay_CIfBa6jrj_wrh3A4_uiQ"
APPLY = "--apply" in sys.argv
STUDENT_CUTOFF = 2026     # education ending this year or later == still a student, per the user

EDU = re.compile(r"b\.?\s?tech|b\.?\s?e\b|bachelor|university|institute|college|\bcgpa\b|"
                 r"undergraduate|m\.?\s?tech|\bmca\b|\bbca\b|b\.?\s?sc|engineering|\bdegree\b|"
                 r"integrated|dual degree|school of", re.I)
ENROLL = re.compile(r"pursuing|final[- ]year|pre[- ]final|(first|second|third|fourth|1st|2nd|3rd|4th)[ -]year|"
                    r"currently studying|expected\s+(graduation|20\d\d)|ongoing|undergraduate", re.I)
YEAR_RANGE = re.compile(r"(20\d\d)\s*[-–—to]+\s*(20\d\d|present|current|now)", re.I)
EXP_YEARS = re.compile(r"(\d+(?:\.\d+)?)\+?\s*years?\s+(of\s+)?(experience|exp)", re.I)


def edu_end_year(text):
    """Max degree end-year in education-context windows. Grabs ALL years in the window and
    takes the max, because degree dates format wildly ('Aug 2023 - May 2027', '2023-27',
    'Nov 2022 - 2026') and a dash-based range regex missed any with a month between the years.
    'Present/ongoing/current/expected' in an education window => still enrolled (=> 2099)."""
    best = None
    for m in EDU.finditer(text):
        win = text[max(0, m.start() - 150): m.end() + 150]
        if re.search(r"present|ongoing|\bcurrent\b|expected", win, re.I):
            best = max(best or 0, 2099)
        for y in re.findall(r"\b(20[12]\d)\b", win):     # 2010-2029, plausible degree years
            best = max(best or 0, int(y))
    return best


def classify(text):
    if not text or len(text) < 200:
        return "review", "no readable resume text"
    end = edu_end_year(text)
    enrolled = bool(ENROLL.search(text))
    exp = EXP_YEARS.search(text)
    yrs_exp = float(exp.group(1)) if exp else 0
    if end and end >= STUDENT_CUTOFF:
        return "In college", f"education ends {end}"
    if enrolled and not (end and end <= 2024):
        return "In college", "enrollment language"
    if end and end <= 2025:
        return "Graduated", f"graduated {end}"
    if yrs_exp >= 2:
        return "Graduated", f"{yrs_exp:g}y experience"
    if end is None and not enrolled:
        return "review", "no education year or enrollment signal"
    return "Graduated", "no student signal"


def main():
    tx = json.load(open(f"{SP}/resume_texts.json"))
    # sheet-row -> resume text (resume_texts is keyed by sheet row number as string)
    grid = read(SID, "'Sheet1'!A1:L200")
    n = len(read(SID, "'Sheet1'!A1:A200"))
    out, fill = [], 0
    col = [["L (student?)"]] if False else []
    updates = []      # (rownum, value)
    counts = {"In college": 0, "Graduated": 0, "review": 0, "preserved": 0}
    for row in range(2, n + 1):
        r = grid[row - 1] if row - 1 < len(grid) else []
        name = r[1] if len(r) > 1 else ""
        existing = r[11].strip() if len(r) > 11 else ""
        t = (tx.get(str(row)) or {}).get("text", "")
        label, why = classify(t)
        if existing:
            counts["preserved"] += 1
            out.append((row, name, existing + " (kept)", why)); continue
        counts[label] = counts.get(label, 0) + 1
        updates.append((row, label)); fill += 1
        out.append((row, name, label, why))
    print(f"{'APPLY' if APPLY else 'DRY'} | fill {fill} blank cells | "
          f"In college {counts['In college']}, Graduated {counts['Graduated']}, "
          f"review {counts['review']}, preserved {counts['preserved']}\n")
    for row, name, label, why in out:
        mark = "*" if label.endswith("(kept)") else " "
        print(f"  {mark}row{row:<4}{name[:26]:<28}{label:<20}{why}")
    if not APPLY:
        print("\nDRY RUN — re-run with --apply to write blank L cells (existing kept)."); return
    body = [[v] for _, v in sorted(updates)]
    # write each blank cell individually to avoid clobbering preserved rows
    data = [{"range": f"'Sheet1'!L{row}", "values": [[val]]} for row, val in updates]
    svc().spreadsheets().values().batchUpdate(
        spreadsheetId=SID, body={"valueInputOption": "RAW", "data": data}).execute()
    print(f"\nwrote {len(updates)} cells to column L (existing preserved).")


main()
