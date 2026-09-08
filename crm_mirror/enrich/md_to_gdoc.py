# -*- coding: utf-8 -*-
"""Markdown -> a single HTML page built for COPY-PASTE INTO GOOGLE DOCS.

Mermaid diagrams are pre-rendered to PNG (headless Chrome) and embedded as base64 <img>,
because Google Docs does not accept pasted SVG. Everything else uses paste-safe HTML
(inline styles on tables, no CSS that Docs would drop).

Usage: python md_to_gdoc.py <input.md> [output.html]
"""
import os, re, sys, html, base64, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md_to_pdf as M           # reuse the markdown->html converter

CHROME = M.CHROME

def render_mermaid_png(code, mermaid_js, width=1250):
    """render one mermaid block to a PNG (bytes) via headless Chrome"""
    init = ("<script>mermaid.initialize({startOnLoad:true,theme:'base',themeVariables:{"
            "primaryColor:'#dae8fc',primaryBorderColor:'#6c8ebf',primaryTextColor:'#000',"
            "lineColor:'#5b6b7c',fontSize:'14px'},flowchart:{useMaxWidth:false,htmlLabels:true}});</script>")
    htm = (f"<!doctype html><html><head><meta charset='utf-8'>"
           f"<style>body{{margin:0;padding:16px;background:#fff;width:{width}px;"
           f"font-family:'Segoe UI',Arial,sans-serif}}</style>"
           f"<script>{mermaid_js}</script>{init}</head>"
           f"<body><div class='mermaid'>{html.escape(code)}</div></body></html>")
    td = tempfile.mkdtemp()
    hp = os.path.join(td, "d.html"); pp = os.path.join(td, "d.png")
    open(hp, "w", encoding="utf-8").write(htm)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--virtual-time-budget=20000", f"--window-size={width+40},2400",
                    f"--screenshot={pp}", "file:///" + hp.replace("\\", "/")],
                   capture_output=True, timeout=180)
    if not os.path.exists(pp): return None
    data = open(pp, "rb").read()
    for f in (hp, pp):
        try: os.remove(f)
        except OSError: pass
    return data

# --- paste-safe inline styles (Google Docs ignores <style> blocks on paste) ---
S = {
 "h1": "font-size:22pt;color:#0b3a5d;font-family:Arial,sans-serif;margin:0 0 10px;",
 "h2": "font-size:15pt;color:#0b3a5d;font-family:Arial,sans-serif;margin:20px 0 6px;",
 "h3": "font-size:12pt;color:#14507d;font-family:Arial,sans-serif;margin:14px 0 4px;",
 "p":  "font-size:11pt;font-family:Arial,sans-serif;margin:6px 0;line-height:1.5;",
 "li": "font-size:11pt;font-family:Arial,sans-serif;margin:3px 0;line-height:1.5;",
 "th": "background-color:#0b3a5d;color:#ffffff;border:1px solid #99a;padding:6px 8px;"
       "text-align:left;font-family:Arial,sans-serif;font-size:10pt;font-weight:bold;",
 "td": "border:1px solid #99a;padding:5px 8px;font-family:Arial,sans-serif;font-size:10pt;vertical-align:top;",
 "tb": "border-collapse:collapse;width:100%;margin:10px 0;",
 "bq": "border-left:4px solid #f0a500;background-color:#fffaf0;padding:8px 12px;margin:10px 0;",
 "pre":"background-color:#f6f8fa;border:1px solid #dde3ea;padding:8px;font-family:Consolas,monospace;font-size:9.5pt;",
 "cd": "background-color:#eef2f7;font-family:Consolas,monospace;font-size:10pt;",
}
def styleize(h):
    h = h.replace("<h1>", f'<h1 style="{S["h1"]}">').replace("<h2>", f'<h2 style="{S["h2"]}">')
    h = h.replace("<h3>", f'<h3 style="{S["h3"]}">').replace("<p>", f'<p style="{S["p"]}">')
    h = h.replace("<li>", f'<li style="{S["li"]}">').replace("<th>", f'<th style="{S["th"]}">')
    h = h.replace("<td>", f'<td style="{S["td"]}">').replace("<table>", f'<table style="{S["tb"]}" border="1" cellspacing="0" cellpadding="6">')
    h = h.replace("<blockquote>", f'<blockquote style="{S["bq"]}">')
    h = h.replace("<pre>", f'<pre style="{S["pre"]}">').replace("<code>", f'<code style="{S["cd"]}">')
    h = h.replace("<hr>", '<hr style="border:none;border-top:1px solid #ccc;margin:16px 0;">')
    return h

def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + "_GoogleDocs.html"
    md = open(src, encoding="utf-8").read()
    mjs = ""
    for c in (os.path.join(HERE, "mermaid.min.js"),):
        if os.path.exists(c): mjs = open(c, encoding="utf-8").read()
    body = M.md_to_html(md)
    # swap each mermaid div for a rendered PNG
    n = 0
    def repl(m):
        nonlocal n
        code = html.unescape(m.group(1))
        png = render_mermaid_png(code, mjs) if mjs else None
        if not png: return "<p><i>[flowchart — see the PDF]</i></p>"
        n += 1
        # also drop a standalone copy next to the doc, for manual insert if needed
        out_png = os.path.splitext(dst)[0] + f"_flowchart{n}.png"
        open(out_png, "wb").write(png)
        b64 = base64.b64encode(png).decode()
        return (f'<div style="margin:14px 0;"><img src="data:image/png;base64,{b64}" '
                f'style="width:640px;max-width:100%;" alt="flowchart"></div>')
    body = re.sub(r'<div class="mermaid">(.*?)</div>', repl, body, flags=re.S)
    body = styleize(body)
    page = ("<!doctype html><html><head><meta charset='utf-8'><title>SOP</title></head>"
            "<body style='font-family:Arial,sans-serif;max-width:900px;margin:24px auto;padding:0 16px;'>"
            + body + "</body></html>")
    open(dst, "w", encoding="utf-8").write(page)
    print(f"OK  {dst}  ({os.path.getsize(dst):,} bytes, {n} diagram(s) embedded)")
    print("    -> open in Chrome, Ctrl+A, Ctrl+C, paste into the Google Doc")

if __name__ == "__main__":
    main()
