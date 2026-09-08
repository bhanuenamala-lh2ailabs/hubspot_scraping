# -*- coding: utf-8 -*-
"""Signal floor for the intern screen — the deterministic half of the ranking.

The job, evidenced by this project itself: drive Claude-Code-style automation against real
systems — Python on live APIs (CRM, webhooks, pagination, retries), scraping, git/CI on free
tiers, scheduled mail, data wrangling. The scorer counts VERBATIM signals per resume, with a
matched quote for each, and flags Bangalore wherever the text places the person there.

Judgment stays with the reader: this outputs signals_score + evidence, and the final rank is
assigned after actually reading the top band + edge cases. A resume whose text failed to
extract goes to a lane, never to rank-last — absence of extraction is not absence of skill.
"""
import os, re, sys, json, collections

SP = "/private/tmp/claude-501/-Users-bhanu-Desktop-hubspot/2bf3c003-90a4-4ea2-84fd-4ba8ed554b6b/scratchpad"

SIG = {
    "python":    (12, re.compile(r"\bpython\b", re.I)),
    "api_work":  (14, re.compile(r"rest(ful)? api|fastapi|flask|django|api integration|webhook|"
                                 r"\bapis?\b.{0,30}(built|integrat|consum|develop)", re.I)),
    "scraping":  (12, re.compile(r"scrap(y|ing|er)|beautifulsoup|selenium|playwright|crawl(er|ing)", re.I)),
    "git_ci":    (10, re.compile(r"github actions|gitlab ci|ci/?cd|docker|\bgit\b", re.I)),
    "data":      (8,  re.compile(r"pandas|numpy|\bsql\b|postgres|mysql|mongodb|\betl\b|data pipeline", re.I)),
    "llm_tools": (14, re.compile(r"\bllm\b|langchain|openai|gpt-?[34o]|claude|gemini|prompt engineer|"
                                 r"\brag\b|hugging ?face|fine-?tun", re.I)),
    "automation":(10, re.compile(r"automat(ed|ion|e)\b", re.I)),
    "cloud":     (6,  re.compile(r"\baws\b|\bgcp\b|google cloud|azure|vercel|railway|render|heroku|"
                                 r"cron|serverless|cloud function", re.I)),
    "shipped":   (8,  re.compile(r"deployed|in production|live at|users?\b.{0,12}\d|shipped", re.I)),
}
BLR = re.compile(r"(bengaluru|bangalore)", re.I)


def q(text, m, w=70):
    i = max(0, m.start() - 30)
    return " ".join(text[i:m.end() + 35].split())[:w]


def main():
    texts = json.load(open(os.path.join(SP, "resume_texts.json")))
    out = []
    for row, r in texts.items():
        t = r.get("text", "") or ""
        rec = {"row": int(row), "name": r["name"], "email": r["email"], "phone": r["phone"],
               "chars": r.get("chars", 0), "error": r.get("error", "")}
        if rec["chars"] < 200:
            rec["lane"] = "unreadable"; rec["signals_score"] = None
            out.append(rec); continue
        s, ev = 0, {}
        for k, (w, rx) in SIG.items():
            m = rx.search(t)
            if m: s += w; ev[k] = q(t, m)
        rec["signals_score"] = s
        rec["evidence"] = ev
        mb = BLR.search(t)
        rec["bangalore"] = bool(mb)
        rec["blr_context"] = q(t, mb) if mb else ""
        out.append(rec)
    out.sort(key=lambda r: (-(r["signals_score"] if r["signals_score"] is not None else -1), r["row"]))
    json.dump(out, open(os.path.join(SP, "signal_scores.json"), "w"), ensure_ascii=False, indent=1)
    ok = [r for r in out if r["signals_score"] is not None]
    print(f"scored {len(ok)} | unreadable lane {len(out)-len(ok)}")
    print("bangalore-flagged:", sum(1 for r in ok if r.get("bangalore")))
    print("\ntop 15 by signals:")
    for r in ok[:15]:
        print(f'   {r["signals_score"]:>3}  {r["name"][:30]:<32}{"BLR" if r.get("bangalore") else ""}')
    d = collections.Counter(r["signals_score"]//10*10 for r in ok)
    print("\nscore deciles:", dict(sorted(d.items(), reverse=True)))


main()
