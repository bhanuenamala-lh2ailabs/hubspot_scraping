# -*- coding: utf-8 -*-
"""Render the complete funnel — cold call to closed/won — as one PNG.

Usage: python render_full_funnel.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import md_to_gdoc as G
import docx_kit as K

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT  = os.path.join(ROOT, "docs", "sop", "LH2_funnel_full.png")
MERMAID = open(os.path.join(HERE, "mermaid.min.js"), encoding="utf-8").read()

FLOW = """
flowchart TD
    START(["Lead created and assigned"]) --> CC{"COLD CALL"}

    CC -->|"screened out, never dialled"| DWF["Dead/ColdCall/WrongFit"]
    CC -->|"number is wrong"| DWN["Dead/ColdCall/WrongNumber"]
    CC -->|"picked up, said no"| DNI["Dead/ColdCall/Not Interested"]
    CC -->|"rang out"| NP["No Pickup<br/>callback task +1 day"]
    CC -->|"picked up, keen"| INT["Interested"]

    NP --> CB{"CALLBACK  +1 day"}
    CB -->|"number is wrong"| DWN
    CB -->|"said no"| DNI
    CB -->|"keen"| INT
    CB -->|"rang out again"| DNP["Dead/ColdCall/NoPickup<br/>WhatsApp + email first"]

    INT --> IO{"Did they book?"}
    IO -->|"keen, never booked"| DIN["Dead/Interested/NoShow"]
    IO -->|"booked"| GM["GMeet Fixed<br/>BOOKED, not attended"]

    GM --> GMO{"Did the meeting happen?"}
    GMO -->|"we attended, they did not"| DGN["Dead/GMeet/NoShow"]
    GMO -->|"called off in advance"| DGC["Dead/GMeet/Cancelled"]
    GMO -->|"met, wrong fit"| DGW["Dead/GMeet/wrong fit"]
    GMO -->|"met, privacy concerns"| DGP["Dead/GMeet/Privacy Concerns"]
    GMO -->|"met, proceed"| SS["Script Shared"]

    SS --> SSO{"Script follow-up"}
    SSO -->|"stopped responding"| DSN["Dead/ScriptShared/NoShow"]
    SSO -->|"output returned"| SRR["Script Results Received"]

    SRR --> RO{"Results reviewed"}
    RO -->|"rejected"| DRR["Dead/ResultsReceived/WrongFit-Rejected"]
    RO -->|"accepted"| CN["Commercial Negotiation"]

    CN --> NO{"Negotiation"}
    NO -->|"pricing"| DNPR["Dead/Negotiation/Pricing"]
    NO -->|"contractual"| DNC["Dead/Negotiation/Contractual"]
    NO -->|"agreed"| DCS["Deal Contract Signed"]

    DCS --> DMD["Data Migration Done"]
    DMD --> MM["Metadata Matched"]
    MM --> PI["Payment Initiation"]
    PI --> WON(["Closed/Won"])

    classDef stage fill:#e8eff8,stroke:#1f4e87,color:#0e2440,stroke-width:1.5px;
    classDef decision fill:#fbf3e3,stroke:#b0730c,color:#4a3005,stroke-width:1.5px;
    classDef dead fill:#fbecea,stroke:#a3392f,color:#4d150f,stroke-width:1.5px;
    classDef won fill:#e8f2ec,stroke:#2f6b4f,color:#14301f,stroke-width:2.5px;
    classDef start fill:#eef1f5,stroke:#6b7789,color:#2a3442,stroke-width:1.5px;

    class START start;
    class NP,INT,GM,SS,SRR,CN,DCS,DMD,MM,PI stage;
    class CC,CB,IO,GMO,SSO,RO,NO decision;
    class DWF,DWN,DNI,DNP,DIN,DGN,DGC,DGW,DGP,DSN,DRR,DNPR,DNC dead;
    class WON won;
"""

def render(code, width, height):
    """Same as md_to_gdoc.render_mermaid_png but with a settable viewport HEIGHT.

    The shared helper hardcodes a 2400px-tall window. The full funnel is taller than that,
    so it came back exactly 2400px high — silently CLIPPED at the bottom, losing everything
    from the negotiation stages down. A trimmed image whose height equals the viewport is
    the tell: it means the content ran past the glass, not that it happened to fit.
    """
    import html as _h, subprocess, tempfile
    init = ("<script>mermaid.initialize({startOnLoad:true,theme:'base',themeVariables:{"
            "primaryColor:'#dae8fc',primaryBorderColor:'#6c8ebf',primaryTextColor:'#000',"
            "lineColor:'#5b6b7c',fontSize:'15px'},flowchart:{useMaxWidth:false,htmlLabels:true}});</script>")
    htm = (f"<!doctype html><html><head><meta charset='utf-8'>"
           f"<style>body{{margin:0;padding:20px;background:#fff;width:{width}px;"
           f"font-family:'Segoe UI',Arial,sans-serif}}</style>"
           f"<script>{MERMAID}</script>{init}</head>"
           f"<body><div class='mermaid'>{_h.escape(code)}</div></body></html>")
    td = tempfile.mkdtemp()
    hp = os.path.join(td, "d.html"); pp = os.path.join(td, "d.png")
    open(hp, "w", encoding="utf-8").write(htm)
    subprocess.run([G.CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--hide-scrollbars", "--virtual-time-budget=30000",
                    f"--window-size={width+60},{height}",
                    f"--screenshot={pp}", "file:///" + hp.replace("\\", "/")],
                   capture_output=True, timeout=300)
    return open(pp, "rb").read() if os.path.exists(pp) else None

VIEW_H = 6000          # generous: the diagram must finish well inside this
best = None
for w in (2000, 2600):
    png = render(FLOW.strip(), w, VIEW_H)
    if not png:
        print(f"  render failed at {w}px"); continue
    data, pw, ph = K.trim_png(png, pad=24)
    clipped = ph >= VIEW_H - 30
    print(f"  {w}px wide -> {pw} x {ph}  aspect {ph/pw:.2f}"
          + ("   *** CLIPPED — raise VIEW_H" if clipped else "   complete"))
    if not clipped and (best is None or pw > best[1]):
        best = (data, pw, ph)

if best is None:
    sys.exit("every render was clipped — raise VIEW_H")
open(OUT, "wb").write(best[0])
print(f"\nwrote {OUT}  {best[1]} x {best[2]} px")
