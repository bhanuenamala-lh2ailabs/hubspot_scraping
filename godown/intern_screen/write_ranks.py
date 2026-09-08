# -*- coding: utf-8 -*-
"""Final intern ranking -> the Google Sheet. Judgment-ordered top 30, signals below.

The top 30 were ranked by READING the resumes against what the job actually is (this
pipeline: Python on live APIs, scraping, n8n/webhook-style automation, LLM tooling, ships
that ran unattended) — not by keyword count. Where judgment overrides signals the note says
why; the starkest case is Shruti Singh: signal score 44 (keyword-light resume) but Pocket FM
GenAI-ops experience that is this job almost verbatim, plus Bengaluru.

Below rank 30: signal-score order, marked as such — reviewed only where the band reached.
Duplicates rank once (later submission noted). Unreadable resumes get no rank, never last
place: absence of extraction is not absence of skill.

Writes: Sheet1!H:K (claude_rank, claude_score, bangalore, claude_notes) aligned to each
applicant's existing row, plus a sorted tab claude_screen_ranked.
"""
import os, sys, json
HUB = "/Users/bhanu/Desktop/hubspot"
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from gsheets import svc, read
SP = "/private/tmp/claude-501/-Users-bhanu-Desktop-hubspot/2bf3c003-90a4-4ea2-84fd-4ba8ed554b6b/scratchpad"
SID = "1IPA45kJ6yTsBo8d33DM0Ay_CIfBa6jrj_wrh3A4_uiQ"

TOP = [  # (sheet_row, note) — judgment order, 1..30
 (85,  "n8n+webhooks+Claude API; SHIPPED client lead-gen automation; closest match to the role"),
 (117, "paid automation contracts (banking E2E, Oracle Flexcube); LLM eval pipelines at Turing"),
 (27,  "Pocket FM GenAI ops: Slack bots, n8n tweet->GPT->Slack, MCP+Zapier; the job verbatim; BLR"),
 (39,  "multi-agent research automation; Tavily+BeautifulSoup scraping pipeline; measurable wins"),
 (7,   "built a lead-discovery platform; LangGraph agents; production retry/eval discipline"),
 (14,  "live 3-channel AI agent; WhatsApp/SMS webhooks in Flask; n8n pipelines, zero-touch"),
 (100, "LLM workflows processing 100+ leads/day; n8n; lead-qualification +35%"),
 (45,  "OCR/BFSI automation 97% acc; scrapes when APIs are missing — right instinct"),
 (105, "GitHub REST API auditor w/ OpenRouter AI; clean modular API engineering"),
 (16,  "Claude-powered multi-agent code fixer (SORK); repo audits; full CI/CD comfort"),
 (93,  "Python backend + Selenium/BS4 + realtime data pipelines; Bengaluru"),
 (44,  "founder-minded; ships daily with Claude API; 3 live apps"),
 (5,   "Bright Data MCP scraping -> LLM -> TTS pipeline; FastAPI orchestration; old ATS #1"),
 (10,  "AI-assisted dev verified on enterprise projects; 10+ REST APIs; Bengaluru"),
 (92,  "agentic automation intern; JobPilot = Playwright + APScheduler (scrape+cron)"),
 (125, "Selenium/BS4 + SMTP/MX email-validation engine 95%+; Maps-API route optimizer"),
 (80,  "Honeywell/Nokia Python automation tools; AI agents for marketing; Bengaluru"),
 (79,  "multi-agent platforms across 2 US internships; 2 patents; research-tilted"),
 (64,  "RAG/LangChain systems + CRM RCS messaging API integration"),
 (12,  "HireBuddy prod ML 10K req/day; Docker/AWS MLOps; offline code-search ext"),
 (96,  "multi-agent research w/ live scraping; hallucination eval -80%; Bengaluru"),
 (24,  "self-correcting agentic RAG (RAGAS-judged); dockerized; pytest suite"),
 (76,  "AWS serverless automation (Lambda/CloudWatch/SNS); FastAPI inference"),
 (124, "VeriFact shipped on 3 platforms off one engine; background-task automation"),
 (59,  "full-stack ships w/ payments+deploy lifecycle; automation-light"),
 (67,  "local LLM infra (HF on GPU); offline-first design; projects still WIP"),
 (119, "unusually rigorous RAG eval (recall@5 0->0.90, faithfulness 1.0)"),
 (87,  "RAG + Azure CI/CD zero-downtime; 10k-doc ingest automation"),
 (33,  "AWS Bedrock agentic pipelines; Dockerized ML microservices"),
 (108, "solid ML pipelines + GenAI stack; more model- than ops-focused"),
]
DUP = {99: 27, 70: 68, 104: 103}

def main():
    sc = json.load(open(f"{SP}/signal_scores.json"))
    by = {r["row"]: r for r in sc}
    order = [t[0] for t in TOP]
    note = dict(TOP)
    rest = [r["row"] for r in sc
            if r["signals_score"] is not None and r["row"] not in order and r["row"] not in DUP]
    rest.sort(key=lambda x: -by[x]["signals_score"])
    ranked = order + rest
    vals = {}   # sheet_row -> [rank, score, bangalore, notes]
    for i, row in enumerate(ranked, 1):
        r = by[row]
        n = note.get(row) or ("signal-ranked; reviewed" if i <= 68 else "signal-ranked")
        vals[row] = [i, r["signals_score"], "Yes" if r.get("bangalore") else "", n]
    for drow, orig in DUP.items():
        r = by.get(drow) or {}
        vals[drow] = ["", r.get("signals_score", ""), "Yes" if r.get("bangalore") else "",
                      f"duplicate submission of row {orig} — ranked there"]
    for r in sc:
        if r["signals_score"] is None:
            vals[r["row"]] = ["", "", "", "resume unreadable (extraction failed) — review by hand"]

    n_rows = len(read(SID, "'Sheet1'!A1:A1000"))
    grid = [["claude_rank", "claude_score", "bangalore", "claude_notes"]]
    for sheet_row in range(2, n_rows + 1):
        grid.append([str(x) for x in vals.get(sheet_row, ["", "", "", ""])])
    svc().spreadsheets().values().update(
        spreadsheetId=SID, range=f"'Sheet1'!H1:K{n_rows}",
        valueInputOption="RAW", body={"values": grid}).execute()
    print(f"Sheet1 H:K written for {n_rows-1} applicant rows")

    # sorted results tab
    tab = "claude_screen_ranked"
    try:
        svc().spreadsheets().batchUpdate(spreadsheetId=SID, body={
            "requests": [{"addSheet": {"properties": {"title": tab}}}]}).execute()
    except Exception:
        pass  # exists
    hdr = [["rank", "name", "email", "phone", "signal_score", "bangalore", "note"]]
    rows = []
    for i, row in enumerate(ranked, 1):
        r = by[row]
        rows.append([i, r["name"], r["email"], r["phone"], r["signals_score"],
                     "Yes" if r.get("bangalore") else "", note.get(row, "signal-ranked")])
    svc().spreadsheets().values().update(
        spreadsheetId=SID, range=f"'{tab}'!A1:G{len(rows)+1}",
        valueInputOption="RAW", body={"values": hdr + [[str(c) for c in x] for x in rows]}).execute()
    print(f"tab '{tab}': {len(rows)} ranked rows written")
    print("\nTOP 10:")
    for i, row in enumerate(ranked[:10], 1):
        r = by[row]
        print(f'  {i:>2}. {r["name"][:28]:<30}{"BLR " if r.get("bangalore") else "    "}sig {r["signals_score"]}')

main()
