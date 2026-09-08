# 2. The funnel flow

## Cold-call half

`Cold Call` forks five ways. The outcomes *are* the next stages.

- **screened out, never dialled** → `Dead/ColdCall/WrongFit`
- **number is wrong** → `Dead/ColdCall/WrongNumber`
- **picked up, said no** → `Dead/ColdCall/Not Interested`
- **picked up, keen** → `Interested`
- **rang out** → `No Pickup`

`No Pickup` is a **live** stage, not a dead end. Landing there logs the attempt and raises a
callback task at **+1 day**. It must not be configured as closed-lost, or those leads leave
the open funnel and the callback never gets worked.

The callback repeats the same four outcomes, with `Dead/ColdCall/NoPickup` as the terminal
when it rings out again. Callback and first-dial outcomes converge on the **same** stages —
they are never duplicated per branch.

`Call Attempted` is retired.

## Post-GMeet half

`GMeet Fixed` means **booked**, not attended. It forks:

- **he attended, they did not** → `Dead/GMeet/NoShow`
- **called off in advance** → `Dead/GMeet/Cancelled`
- **met, wrong fit** → `Dead/GMeet/wrong fit`
- **met, privacy concerns** → `Dead/Gmeet/Privacy Concerns`
- **met, proceed** → `Script Shared`

`Script Shared` then forks to `Dead/ScriptShared/NoShow` or `Script Results Received`.

## Diagram

```mermaid
flowchart TD
    START(["Lead created and assigned"]) --> CC{"Cold Call"}
    CC -->|"screened out, never dialled"| DWF["Dead/ColdCall/WrongFit"]
    CC -->|"number is wrong"| DWN["Dead/ColdCall/WrongNumber"]
    CC -->|"picked up, said no"| DNI["Dead/ColdCall/Not Interested"]
    CC -->|"picked up, keen"| INT["Interested"]
    CC -->|"rang out"| NP["No Pickup - NEW<br/>callback task +1 day"]

    NP --> CB{"Callback after +1 day"}
    CB -->|"number is wrong"| DWN
    CB -->|"picked up, said no"| DNI
    CB -->|"picked up, keen"| INT
    CB -->|"rang out again"| DNP["Dead/ColdCall/NoPickup - NEW"]

    INT -->|"meeting booked"| GM["GMeet Fixed<br/>BOOKED, not attended"]
    GM --> GMO{"Did the meeting happen?"}
    GMO -->|"he attended, they did not"| DGN["Dead/GMeet/NoShow - NEW"]
    GMO -->|"called off in advance"| DGC["Dead/GMeet/Cancelled - NEW"]
    GMO -->|"met, wrong fit"| DGW["Dead/GMeet/wrong fit"]
    GMO -->|"met, privacy concerns"| DGP["Dead/Gmeet/Privacy Concerns"]
    GMO -->|"met, proceed"| SS["Script Shared"]

    SS --> SSO{"Script follow-up"}
    SSO -->|"did not turn up"| DSN["Dead/ScriptShared/NoShow - NEW"]
    SSO -->|"results came back"| SRR["Script Results Received"]

    SRR --> RO{"Results reviewed"}
    RO -->|"rejected"| DRR["Dead/ResultsReceived/WrongFit-Rejected"]
    RO -->|"accepted"| CN["Commercial Negotiation"]

    CN --> NO{"Negotiation"}
    NO -->|"pricing"| DNPR["Dead/Negotiation/Pricing"]
    NO -->|"contractual"| DNC["Dead/Negotiation/Contractual"]
    NO -->|"agreed"| DCS["Deal Contract Signed"]

    DCS --> DMD["Data Migration Done"] --> MM["Metadata Matched"] --> PI["Payment Initiation"] --> WON(["Closed/Won"])

    classDef stage fill:#e8eff8,stroke:#1f4e87,color:#0e2440,stroke-width:1.5px;
    classDef decision fill:#fbf3e3,stroke:#b0730c,color:#4a3005,stroke-width:1.5px;
    classDef dead fill:#fbecea,stroke:#a3392f,color:#4d150f,stroke-width:1.5px;
    classDef newstage fill:#fdf0dd,stroke:#8a4b00,color:#4a2900,stroke-width:2.5px,stroke-dasharray:6 3;
    classDef won fill:#e8f2ec,stroke:#2f6b4f,color:#14301f,stroke-width:2px;
    classDef start fill:#eef1f5,stroke:#6b7789,color:#2a3442,stroke-width:1.5px;
    class START start;
    class INT,GM,SS,SRR,CN,DCS,DMD,MM,PI stage;
    class CC,CB,GMO,SSO,RO,NO decision;
    class DWF,DWN,DNI,DGW,DGP,DRR,DNPR,DNC dead;
    class NP,DNP,DGN,DGC,DSN newstage;
    class WON won;
```

---
