# -*- coding: utf-8 -*-
"""Google Sheets/Drive access AS THE HUMAN ACCOUNT — the same email the mailer sends as.

Deliberately NOT the lh2-pipeline service account: the SA only sees the handful of sheets
explicitly shared with its robot address, while this token sees everything the human email
can open. Minted from the SAME OAuth client as gmail_token.json but stored SEPARATELY
(sheets_token.json) with only Sheets+Drive-metadata scopes — the send-only mail token is
never touched, so the 6:30 mailer cannot be broken from here.

First run:  python3 gsheets.py --auth     (opens the browser once; approve and done)
Then:       python3 gsheets.py --list     (sanity: 10 most recent spreadsheets)
In code:    from gsheets import svc, find, read, write

Scopes: spreadsheets (read/write cells) + drive.metadata.readonly (find files by name).
File CONTENT outside Sheets stays out of scope on purpose — widen only when a task needs it.
"""
import os, sys, glob, json

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
TOKEN = os.path.join(HUB, "sheets_token.json")
# drive.readonly added 2026-08-14: the intern-resume screen needs file CONTENT (the resumes
# are Drive uploads), which metadata-only deliberately excluded until a task needed it.
# NOTE: writing to an uploaded xlsx (not a native Sheet) needs files.update, which requires
# full "drive" scope — drive.readonly can't grant it, and that scope bump is pending a manual
# `gsheets.py --auth` re-consent (see 20 Aug band-report / company-ops-pilot thread). Left at
# drive.readonly here so native-Sheet access keeps working on the existing token in the
# meantime; bump back to full drive + re-auth only when the xlsx-write path is actually needed.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive.readonly"]


def _client():
    p = os.path.join(HUB, "gmail_oauth_client.json")
    if os.path.exists(p): return p
    hits = sorted(glob.glob(os.path.join(HUB, "client_secret_*.json")))
    if hits: return hits[0]
    sys.exit("no OAuth client json at the hubspot root")


def creds(interactive=False):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    c = None
    if os.path.exists(TOKEN):
        c = Credentials.from_authorized_user_file(TOKEN, SCOPES)
        # A token can be VALID yet under-scoped: after drive.readonly was added here, the
        # old sheets-only token still refreshed fine and --auth silently no-opped, and every
        # Drive download 403'd. Scope shortfall must force the interactive flow.
        held = set(json.load(open(TOKEN)).get("scopes") or [])
        if not set(SCOPES) <= held: c = None
    if c and c.expired and c.refresh_token:
        c.refresh(Request()); open(TOKEN, "w").write(c.to_json())
    if not c or not c.valid:
        if not interactive:
            sys.exit("sheets_token.json missing/invalid — run: python3 gsheets.py --auth")
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(_client(), SCOPES)
        c = flow.run_local_server(port=0, open_browser=True,
                                  authorization_prompt_message="")
        open(TOKEN, "w").write(c.to_json()); os.chmod(TOKEN, 0o600)
    return c


def svc(kind="sheets"):
    from googleapiclient.discovery import build
    if kind == "drive":
        return build("drive", "v3", credentials=creds(), cache_discovery=False)
    return build("sheets", "v4", credentials=creds(), cache_discovery=False)


def find(name_contains, n=10):
    """-> [(id, name, modified)] spreadsheets whose name matches, newest first."""
    q = ("mimeType='application/vnd.google-apps.spreadsheet'"
         + (f" and name contains '{name_contains}'" if name_contains else ""))
    r = svc("drive").files().list(q=q, orderBy="modifiedTime desc", pageSize=n,
                                  fields="files(id,name,modifiedTime)").execute()
    return [(f["id"], f["name"], f["modifiedTime"][:10]) for f in r.get("files", [])]


def read(sheet_id, rng):
    """-> list of rows for A1-range `rng` (include the tab name: 'Tab!A1:Z100')."""
    r = svc().spreadsheets().values().get(spreadsheetId=sheet_id, range=rng).execute()
    return r.get("values", [])


def write(sheet_id, rng, rows):
    """Overwrites `rng` with `rows` (list of lists). RAW input — no formula parsing."""
    return svc().spreadsheets().values().update(
        spreadsheetId=sheet_id, range=rng, valueInputOption="RAW",
        body={"values": rows}).execute()


if __name__ == "__main__":
    if "--auth" in sys.argv:
        c = creds(interactive=True)
        print("token saved ->", TOKEN)
    for sid, nm, mod in find("" if "--list" in sys.argv else None or "", 10):
        print(f"   {mod}  {nm[:60]:<62}{sid}")
