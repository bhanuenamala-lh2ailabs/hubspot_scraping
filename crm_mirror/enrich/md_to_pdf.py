# -*- coding: utf-8 -*-
"""Markdown -> styled HTML -> PDF via headless Chrome/Edge (renders Mermaid diagrams).

Usage: python md_to_pdf.py <input.md> [output.pdf]
No external Python deps: the markdown->HTML pass is a small purpose-built converter
covering what our SOPs use (headings, tables, lists, code, blockquotes, bold/italic,
links, hr, mermaid fences).
"""
import os, re, sys, html, subprocess, time, glob

CHROME = next((p for p in (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
) if os.path.exists(p)), None)

def inline(t):
    """inline markdown -> html (escape first, then re-introduce markup)"""
    t = html.escape(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href='\2'>\1</a>", t)
    return t

def md_to_html(md):
    out, i = [], 0
    lines = md.split("\n")
    while i < len(lines):
        ln = lines[i]
        # fenced code / mermaid
        if ln.strip().startswith("```"):
            lang = ln.strip().strip("`").strip()
            i += 1; buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            body = "\n".join(buf)
            if lang == "mermaid":
                out.append(f'<div class="mermaid">{html.escape(body)}</div>')
            else:
                out.append(f"<pre><code>{html.escape(body)}</code></pre>")
            continue
        # table
        if "|" in ln and i + 1 < len(lines) and re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i+1]):
            head = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2; rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in head)
            tb = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f"<table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table>")
            continue
        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            lvl = len(m.group(1)); out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>"); i += 1; continue
        # hr
        if re.match(r"^\s*---+\s*$", ln): out.append("<hr>"); i += 1; continue
        # blockquote (may contain headings/lists)
        if ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").lstrip()); i += 1
            out.append("<blockquote>" + md_to_html("\n".join(buf)) + "</blockquote>")
            continue
        # lists (ordered / unordered, one level of nesting)
        if re.match(r"^\s*([-*+]|\d+\.)\s+", ln):
            ordered = bool(re.match(r"^\s*\d+\.\s+", ln))
            tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines) and (re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i]) or
                                      (lines[i].startswith("  ") and lines[i].strip() and items)):
                l2 = lines[i]
                if re.match(r"^\s{2,}([-*+]|\d+\.)\s+", l2) and items:      # nested -> append
                    items[-1] += "<br>&nbsp;&nbsp;" + inline(re.sub(r"^\s*([-*+]|\d+\.)\s+", "• ", l2))
                elif re.match(r"^\s*([-*+]|\d+\.)\s+", l2):
                    items.append(inline(re.sub(r"^\s*([-*+]|\d+\.)\s+", "", l2)))
                else:
                    items[-1] += " " + inline(l2.strip())
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items) + f"</{tag}>")
            continue
        if not ln.strip(): i += 1; continue
        # paragraph
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^\s*(#{1,6}\s|[-*+]\s|\d+\.\s|>|```|---+\s*$)", lines[i]) and "|" not in lines[i]:
            buf.append(lines[i]); i += 1
        if buf: out.append("<p>" + inline(" ".join(buf)) + "</p>")
        elif i < len(lines) and lines[i].strip(): out.append("<p>" + inline(lines[i]) + "</p>"); i += 1
    return "\n".join(out)

CSS = """
@page { size: A4; margin: 14mm 12mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 10.5pt;
       line-height: 1.5; color: #1a1a1a; margin: 0; }
h1 { font-size: 21pt; color: #0b3a5d; border-bottom: 3px solid #0b3a5d; padding-bottom: 6px; margin: 0 0 14px; }
h2 { font-size: 14pt; color: #0b3a5d; margin: 20px 0 8px; border-bottom: 1px solid #cfd8e3; padding-bottom: 4px;
     page-break-after: avoid; }
h3 { font-size: 11.5pt; color: #14507d; margin: 14px 0 5px; page-break-after: avoid; }
p { margin: 6px 0; }
ul, ol { margin: 6px 0 6px 20px; padding-left: 6px; }
li { margin: 3px 0; }
code { background: #eef2f7; padding: 1px 4px; border-radius: 3px; font-family: Consolas, monospace; font-size: 9.5pt; }
pre { background: #f6f8fa; border: 1px solid #dde3ea; border-radius: 4px; padding: 8px; overflow: hidden; }
pre code { background: none; font-size: 9pt; }
blockquote { border-left: 4px solid #f0a500; background: #fffaf0; margin: 10px 0; padding: 8px 12px;
             border-radius: 0 4px 4px 0; page-break-inside: avoid; }
blockquote h3 { margin-top: 2px; color: #9a6700; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9.5pt; page-break-inside: avoid; }
th { background: #0b3a5d; color: #fff; text-align: left; padding: 6px 8px; font-weight: 600; }
td { border: 1px solid #dde3ea; padding: 5px 8px; vertical-align: top; }
tbody tr:nth-child(even) { background: #f7f9fc; }
hr { border: none; border-top: 1px solid #dde3ea; margin: 18px 0; }
a { color: #14507d; text-decoration: none; }
.mermaid { text-align: center; margin: 14px 0; page-break-inside: avoid; }
.mermaid svg { max-width: 100% !important; height: auto !important; }
"""

def build(md_path, pdf_path, mermaid_js):
    pdf_path = os.path.abspath(pdf_path)          # Chrome requires an absolute output path
    md = open(md_path, encoding="utf-8").read()
    body = md_to_html(md)
    mm = f"<script>{mermaid_js}</script>" if mermaid_js else ""
    init = ("<script>mermaid.initialize({startOnLoad:true,theme:'base',"
            "themeVariables:{primaryColor:'#dae8fc',primaryBorderColor:'#6c8ebf',primaryTextColor:'#000',"
            "lineColor:'#5b6b7c',fontSize:'13px'},flowchart:{useMaxWidth:true,htmlLabels:true}});</script>") if mermaid_js else ""
    htm = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style>{mm}{init}</head>
<body>{body}</body></html>"""
    tmp = os.path.splitext(pdf_path)[0] + "_tmp.html"
    open(tmp, "w", encoding="utf-8").write(htm)
    if not CHROME: sys.exit("No Chrome/Edge found for PDF rendering.")
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--run-all-compositor-stages-before-draw",
           "--virtual-time-budget=20000", f"--print-to-pdf={pdf_path}", "--no-pdf-header-footer",
           "file:///" + os.path.abspath(tmp).replace("\\", "/")]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    ok = os.path.exists(pdf_path)
    print(("OK  " if ok else "FAIL ") + pdf_path + (f"  ({os.path.getsize(pdf_path):,} bytes)" if ok else ""))
    if not ok: print(r.stdout[-800:], r.stderr[-800:])
    else: os.remove(tmp)
    return ok

if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + ".pdf"
    # local mermaid bundle if present (offline-safe), else no diagram rendering
    mjs = ""
    for c in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mermaid*.js")):
        mjs = open(c, encoding="utf-8").read(); break
    build(src, dst, mjs)
