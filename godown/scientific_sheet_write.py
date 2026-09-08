# -*- coding: utf-8 -*-
"""Write the enriched POC data back into the master_companies sheet as a new, formatted tab."""
import json, sys
sys.path.insert(0, "/Users/bhanu/Desktop/hubspot/crm_mirror/enrich")
from gsheets import svc

SID = "1bz5sZmG_7mfRefUZld2wErxRfV9AcPNBSS6eXmyxbLE"
TAB = "POC Enrichment"

rows = json.load(open("/tmp/scientific_final.json"))

HEADER = ["Company Name", "Website", "Company LinkedIn", "POC Name", "POC Title",
          "POC LinkedIn URL", "POC Location", "Match Confidence", "POC Email",
          "Company Email", "Mobile/Phone", "Notes"]

STATUS_LABEL = {"CONFIRMED": "Confirmed", "BEST_GUESS": "Best guess", "NOT_FOUND": "Not found"}

data_rows = []
for r in rows:
    p = r.get("p") or {}
    name = f'{p.get("firstName","")} {p.get("lastName","")}'.strip() if p else ""
    loc = (p.get("location") or {}).get("linkedinText", "") if p else ""
    note = ""
    if r["status"] == "NOT_FOUND":
        note = "No LinkedIn candidate found via search"
    elif r["status"] == "BEST_GUESS":
        note = "Top search hit — company name on profile didn't strictly match; verify before outreach"
    data_rows.append([
        r.get("name", ""), r.get("website", ""), r.get("linkedin", ""),
        name, r.get("title") or "", p.get("linkedinUrl", "") if p else "",
        loc, STATUS_LABEL[r["status"]], r.get("email", ""),
        r.get("company_email", ""), r.get("phone", ""), note
    ])

values = [HEADER] + data_rows
service = svc()

# create the tab if it doesn't already exist
meta = service.spreadsheets().get(spreadsheetId=SID).execute()
existing = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
if TAB not in existing:
    r = service.spreadsheets().batchUpdate(spreadsheetId=SID, body={
        "requests": [{"addSheet": {"properties": {"title": TAB, "gridProperties":
                     {"rowCount": len(values) + 10, "columnCount": len(HEADER) + 2}}}}]
    }).execute()
    sheet_id = r["replies"][0]["addSheet"]["properties"]["sheetId"]
else:
    sheet_id = existing[TAB]

service.spreadsheets().values().update(
    spreadsheetId=SID, range=f"'{TAB}'!A1", valueInputOption="RAW",
    body={"values": values}).execute()

n_rows = len(values)
n_cols = len(HEADER)

requests = [
    # header styling
    {"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1,
                               "startColumnIndex": 0, "endColumnIndex": n_cols},
     "cell": {"userEnteredFormat": {
         "backgroundColor": {"red": 0.11, "green": 0.20, "blue": 0.34},
         "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True, "fontSize": 10},
         "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE",
         "wrapStrategy": "WRAP"}},
     "fields": "userEnteredFormat"}},
    {"updateSheetProperties": {"properties": {"sheetId": sheet_id,
        "gridProperties": {"frozenRowCount": 1}}, "fields": "gridProperties.frozenRowCount"}},
    {"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "ROWS",
        "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 34}, "fields": "pixelSize"}},
    {"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "ROWS",
        "startIndex": 1, "endIndex": n_rows}, "properties": {"pixelSize": 24}, "fields": "pixelSize"}},
    {"autoResizeDimensions": {"dimensions": {"sheetId": sheet_id, "dimension": "COLUMNS",
        "startIndex": 0, "endIndex": n_cols}}},
    {"setBasicFilter": {"filter": {"range": {"sheetId": sheet_id, "startRowIndex": 0,
        "endRowIndex": n_rows, "startColumnIndex": 0, "endColumnIndex": n_cols}}}},
    # banded rows
    {"addBanding": {"bandedRange": {"range": {"sheetId": sheet_id, "startRowIndex": 1,
        "endRowIndex": n_rows, "startColumnIndex": 0, "endColumnIndex": n_cols},
        "rowProperties": {
            "headerColor": {"red": 0.11, "green": 0.20, "blue": 0.34},
            "firstBandColor": {"red": 1, "green": 1, "blue": 1},
            "secondBandColor": {"red": 0.94, "green": 0.96, "blue": 0.99}}}}},
    # conditional formatting on Match Confidence column (col index 7 -> H)
    {"addConditionalFormatRule": {"rule": {
        "ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": n_rows,
                    "startColumnIndex": 7, "endColumnIndex": 8}],
        "booleanRule": {"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "Confirmed"}]},
                        "format": {"backgroundColor": {"red": 0.80, "green": 0.94, "blue": 0.80},
                                   "textFormat": {"foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.10}}}}},
        "index": 0}},
    {"addConditionalFormatRule": {"rule": {
        "ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": n_rows,
                    "startColumnIndex": 7, "endColumnIndex": 8}],
        "booleanRule": {"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "Best guess"}]},
                        "format": {"backgroundColor": {"red": 1.0, "green": 0.95, "blue": 0.78},
                                   "textFormat": {"foregroundColor": {"red": 0.60, "green": 0.42, "blue": 0.0}}}}},
        "index": 1}},
    {"addConditionalFormatRule": {"rule": {
        "ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": n_rows,
                    "startColumnIndex": 7, "endColumnIndex": 8}],
        "booleanRule": {"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "Not found"}]},
                        "format": {"backgroundColor": {"red": 0.98, "green": 0.85, "blue": 0.85},
                                   "textFormat": {"foregroundColor": {"red": 0.65, "green": 0.15, "blue": 0.15}}}}},
        "index": 2}},
]
service.spreadsheets().batchUpdate(spreadsheetId=SID, body={"requests": requests}).execute()
print(f"wrote {len(data_rows)} rows to tab '{TAB}'")
print(f"sheet URL: https://docs.google.com/spreadsheets/d/{SID}/edit#gid={sheet_id}")
