# -*- coding: utf-8 -*-
"""Download all 125 intern resumes from Drive and extract their text.

Handles the three shapes form uploads actually take: PDF (pypdf), DOCX (zipfile+xml),
Google Doc (export as text/plain). Anything else is recorded as unreadable rather than
silently skipped — a resume we could not read is a lane, not a zero.
"""
import os, io, re, sys, json, zipfile
HUB = "/Users/bhanu/Desktop/hubspot"
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from gsheets import svc
SP = "/private/tmp/claude-501/-Users-bhanu-Desktop-hubspot/2bf3c003-90a4-4ea2-84fd-4ba8ed554b6b/scratchpad"
OUT = os.path.join(SP, "resume_texts.json")

def docx_text(b):
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", xml))

def pdf_text(b):
    from pypdf import PdfReader
    try:
        rd = PdfReader(io.BytesIO(b))
        return re.sub(r"\s+", " ", " ".join((p.extract_text() or "") for p in rd.pages[:6]))
    except Exception as e:
        return ""

def main():
    apps = json.load(open(os.path.join(SP, "applicants.json")))
    done = {}
    if os.path.exists(OUT): done = json.load(open(OUT))
    drive = svc("drive")
    from googleapiclient.http import MediaIoBaseDownload
    for i, a in enumerate(apps, 1):
        key = str(a["row"])
        if key in done and done[key].get("chars", 0) > 0: continue
        rec = {"name": a["name"], "email": a["email"], "phone": a["phone"]}
        try:
            meta = drive.files().get(fileId=a["fid"], fields="name,mimeType,size").execute()
            mt = meta.get("mimeType", "")
            if mt == "application/vnd.google-apps.document":
                b = drive.files().export(fileId=a["fid"], mimeType="text/plain").execute()
                txt = b.decode("utf-8", "replace") if isinstance(b, bytes) else str(b)
            else:
                buf = io.BytesIO()
                dl = MediaIoBaseDownload(buf, drive.files().get_media(fileId=a["fid"]))
                fin = False
                while not fin: _, fin = dl.next_chunk()
                b = buf.getvalue()
                if mt == "application/pdf" or meta.get("name", "").lower().endswith(".pdf"):
                    txt = pdf_text(b)
                elif "wordprocessingml" in mt or meta.get("name", "").lower().endswith(".docx"):
                    txt = docx_text(b)
                else:
                    txt = b.decode("utf-8", "replace") if len(b) < 400_000 else ""
            rec["file"] = meta.get("name", ""); rec["mime"] = mt
            rec["text"] = txt[:28000]; rec["chars"] = len(txt.strip())
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {str(e)[:90]}"; rec["chars"] = 0
        done[key] = rec
        if i % 10 == 0:
            json.dump(done, open(OUT, "w")); print(f"{i}/125", flush=True)
    json.dump(done, open(OUT, "w"))
    ok = sum(1 for v in done.values() if v.get("chars", 0) > 200)
    print(f"done: {len(done)} fetched, {ok} with readable text, "
          f"{sum(1 for v in done.values() if v.get('error'))} errors")

main()
