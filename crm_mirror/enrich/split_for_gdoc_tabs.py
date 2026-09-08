# -*- coding: utf-8 -*-
"""Split a markdown doc at its H1s and render one paste-ready HTML per section.

Google Docs tabs cannot be produced by uploading a file — no import format (DOCX, HTML,
Markdown, ODT) has any representation for them, so every upload collapses to a single tab,
and the Docs API exposes tabs for READING only. Tabs are created in the UI.

So this produces one file per intended tab: make the tab in Docs, open the matching HTML,
Ctrl+A / Ctrl+C, paste. The combined file remains the zero-effort option — its headings
populate the Docs outline pane, which gives left-hand navigation without any manual work.

Usage: python split_for_gdoc_tabs.py <input.md> <outdir>
"""
import os, re, sys, subprocess

HERE=os.path.dirname(os.path.abspath(__file__))

def main():
    if len(sys.argv)<3:
        sys.exit("usage: python split_for_gdoc_tabs.py <input.md> <outdir>")
    src, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    text=open(src, encoding="utf-8").read()

    # split on H1 only; fenced code blocks may contain '#' so track fences
    lines=text.split("\n")
    parts=[]; cur=[]; title="Front matter"; fence=False
    for ln in lines:
        if ln.lstrip().startswith("```"): fence = not fence
        if not fence and re.match(r"^#\s+\S", ln):
            if any(l.strip() for l in cur): parts.append((title, "\n".join(cur)))
            title=ln.lstrip("# ").strip(); cur=[ln]
        else:
            cur.append(ln)
    if any(l.strip() for l in cur): parts.append((title, "\n".join(cur)))

    print(f"{len(parts)} section(s) -> one tab each\n")
    for i,(t,body) in enumerate(parts):
        slug=re.sub(r"[^a-z0-9]+","_",t.lower()).strip("_")[:44] or f"section{i}"
        mp=os.path.join(outdir, f"{i:02d}_{slug}.md")
        hp=os.path.join(outdir, f"{i:02d}_{slug}.html")
        open(mp,"w",encoding="utf-8").write(body)
        r=subprocess.run([sys.executable, os.path.join(HERE,"md_to_gdoc.py"), mp, hp],
                         capture_output=True, text=True)
        size=os.path.getsize(hp) if os.path.exists(hp) else 0
        print(f"  tab {i+1}: {t[:46]:<48} {os.path.basename(hp):<44}{size:>9,} b")
        if r.returncode!=0: print("     !", (r.stderr or r.stdout)[-160:])

    print(f"\nTab titles to create in Google Docs, in order:")
    for i,(t,_) in enumerate(parts): print(f"  {i+1}. {t}")

if __name__=="__main__":
    main()
