LH2 AI LABS — EXHAUSTIVE NUMERIC DUMP
==============================================================================================================
generated              : 2026-08-17 23:51 IST
source                 : HubSpot portal 246754894 (live extract)
deals                  : 2,141
stage transitions      : 4,921
notes                  : 1,981
tasks                  : 288
engagements            : 29
contacts               : 3,186
companies              : 2,635
date range (createdate): 2026-07-15 -> 2026-08-17  (34 days)

NO CONCLUSIONS ARE DRAWN IN THIS DOCUMENT. It is a complete numeric record for independent analysis.

CONTENTS
   1. Definitions & data dictionary
   2. Deal inventory — every dimension
   3. Stage distribution — current and ever-reached
   4. The funnel — overall and sliced
   5. Depth analysis — how far leads travel
   6. Daily time series
   7. Weekly time series
   8. Per-person activity
   9. Lead-source deep dive
  10. Pipeline deep dive
  11. Timelines — time to each stage
  12. Dwell time per stage
  13. Stage transition matrix
  14. Death analysis
  15. Cohort analysis by creation week
  16. Cumulative pipeline over time
  17. LoC / PR economics
  18. Live pipeline inventory
  19. Notes analysis
  20. Tasks analysis
  21. Contacts & companies
  22. Per-deal appendix (deals past Cold Call)

##############################################################################################################
## 1. DEFINITIONS & DATA DICTIONARY
##############################################################################################################
depth / max stage reached : highest funnel rank a deal EVER touched, rebuilt from the full
                            transition history (from_stage and to_stage), plus a floor implied
                            by its Dead/* label (e.g. Dead/GMeet/* implies it reached GMeet Fixed).
                            Rank order: Cold Call < No Pickup < Interested < GMeet Fixed < Script Shared < Script Results Received < Commercial Negotiation < Deal Contract Signed < Data Migration Done < Metadata Matched < Payment Initiation < Closed/Won
is_human                  : stage move made in the HubSpot UI (sourceType=CRM_UI) vs INTEGRATION/API.
tier-1                    : LoC/PR ratio between 300 and 2000 inclusive.
live                      : not Closed/Won and not Dead/*.
resolved                  : Closed/Won + all Dead/* (i.e. outcome settled).
age_days                  : days from createdate to 2026-08-17.
idle_days                 : days since the deal's last stage move.
t_<stage>                 : days from createdate to the first RECORDED ENTRY transition into that
                            stage. NOTE this differs slightly from depth: depth also credits a stage
                            if it appears only as a from_stage (i.e. the entry predates the history
                            window) or is implied by a Dead/* floor. So 'ever reached' counts in
                            section 3.2/5 are >= the t_<stage> counts in section 11. Both are given.
deleted stages            : some historical transitions reference pipeline stages that have since
                            been deleted; they appear as '(deleted stage <id>)'. See section 1.1.


--------------------------------------------------------------------------------------------------------------
1.1 DELETED STAGES still referenced by history
--------------------------------------------------------------------------------------------------------------
  10 distinct deleted stage ids appear in 199 transition endpoints.
  These are from an earlier pipeline design. They carry no rank and are excluded from funnel/depth maths.
    (deleted stage 3992480463)            86
    (deleted stage 3992480479)            48
    (deleted stage 3992480476)            22
    (deleted stage 3992480477)            15
    (deleted stage 3992480466)            15
    (deleted stage 3992480472)             5
    (deleted stage 3992480478)             3
    (deleted stage 3992480474)             2
    (deleted stage 3992480468)             2
    (deleted stage 3992480470)             1

STAGE RANK TABLE
  rank  0  Cold Call
  rank  1  No Pickup
  rank  2  Interested
  rank  3  GMeet Fixed
  rank  4  Script Shared
  rank  5  Script Results Received
  rank  6  Commercial Negotiation
  rank  7  Deal Contract Signed
  rank  8  Data Migration Done
  rank  9  Metadata Matched
  rank 10  Payment Initiation
  rank 11  Closed/Won
  dead-stage floors:
    Dead/ColdCall/WrongFit                       implies reached rank 0 (Cold Call)
    Dead/ColdCall/WrongNumber                    implies reached rank 0 (Cold Call)
    Dead/ColdCall/NoPickup                       implies reached rank 1 (No Pickup)
    Dead/ColdCall/Not Interested                 implies reached rank 2 (Interested)
    Dead/Interested/NoShow                       implies reached rank 2 (Interested)
    Dead/GMeet/NoShow                            implies reached rank 3 (GMeet Fixed)
    Dead/GMeet/Cancelled                         implies reached rank 3 (GMeet Fixed)
    Dead/GMeet/wrong fit                         implies reached rank 3 (GMeet Fixed)
    Dead/GMeet/Privacy Concerns                  implies reached rank 3 (GMeet Fixed)
    Dead/ScriptShared/NoShow                     implies reached rank 4 (Script Shared)
    Dead/ResultsReceived/WrongFit-Rejected       implies reached rank 5 (Script Results Received)
    Dead/Negotiation/Pricing                     implies reached rank 6 (Commercial Negotiation)
    Dead/Negotiation/Contractual                 implies reached rank 6 (Commercial Negotiation)

##############################################################################################################
## 2. DEAL INVENTORY — EVERY DIMENSION
##############################################################################################################

--------------------------------------------------------------------------------------------------------------
2.1 by PIPELINE
--------------------------------------------------------------------------------------------------------------
value                                                  deals       % 
Scraped                                                 1605   74.96%
Campaign                                                 536   25.04%
TOTAL                                                   2141  100.00%

--------------------------------------------------------------------------------------------------------------
2.2 by LEAD SOURCE
--------------------------------------------------------------------------------------------------------------
value                                                  deals       % 
Scraping Algo ( IT services )                            920   42.97%
Linkedin Campaign ( IT Services )                        355   16.58%
NASSCOM ( IT Services )                                  224   10.46%
Outflo Outreach ( Startups )                             177    8.27%
Tracxn Sheet ( Startups )                                175    8.17%
Founder Search ( IT Services )                           173    8.08%
Scraping Algo ( Startups )                                50    2.34%
Romania ( IT Services )                                   29    1.35%
Private Codebase Tracker sheet ( IT services )            22    1.03%
Scraped ( IT Services )                                    9    0.42%
(none)                                                     7    0.33%
TOTAL                                                   2141  100.00%

--------------------------------------------------------------------------------------------------------------
2.3 by OWNER
--------------------------------------------------------------------------------------------------------------
value                                                  deals       % 
Lamiya Saleem                                            728   34.00%
Yuktha Anand                                             714   33.35%
(unassigned)                                             502   23.45%
Ishpreet Sood                                            141    6.59%
Shobit Gupta                                              53    2.48%
Ashish Ranjan                                              3    0.14%
TOTAL                                                   2141  100.00%

--------------------------------------------------------------------------------------------------------------
2.4 by CURRENT STAGE
--------------------------------------------------------------------------------------------------------------
value                                                  deals       % 
Dead/ColdCall/WrongFit                                   727   33.96%
No Pickup                                                533   24.89%
Dead/ColdCall/WrongNumber                                239   11.16%
Dead/ColdCall/Not Interested                             199    9.29%
Cold Call                                                192    8.97%
Interested                                               119    5.56%
Dead/GMeet/wrong fit                                      25    1.17%
Script Shared                                             24    1.12%
Dead/ResultsReceived/WrongFit-Rejected                    21    0.98%
Dead/Interested/NoShow                                    18    0.84%
GMeet Fixed                                               13    0.61%
Closed/Won                                                11    0.51%
Dead/Negotiation/Pricing                                   6    0.28%
Commercial Negotiation                                     5    0.23%
Dead/ScriptShared/NoShow                                   3    0.14%
Deal Contract Signed                                       2    0.09%
Script Results Received                                    2    0.09%
Dead/Negotiation/Contractual                               1    0.05%
Dead/GMeet/Privacy Concerns                                1    0.05%
TOTAL                                                   2141  100.00%

--------------------------------------------------------------------------------------------------------------
2.5 by DEPTH REACHED
--------------------------------------------------------------------------------------------------------------
value                                                  deals       % 
0 Cold Call                                             1084   50.63%
1 No Pickup                                              543   25.36%
2 Interested                                             364   17.00%
4 Script Shared                                           54    2.52%
3 GMeet Fixed                                             40    1.87%
5 Script Results Received                                 25    1.17%
6 Commercial Negotiation                                  15    0.70%
11 Closed/Won                                             12    0.56%
7 Deal Contract Signed                                     2    0.09%
9 Metadata Matched                                         1    0.05%
10 Payment Initiation                                      1    0.05%
TOTAL                                                   2141  100.00%

--------------------------------------------------------------------------------------------------------------
2.6 by OUTCOME
--------------------------------------------------------------------------------------------------------------
value                                                  deals       % 
Dead                                                    1240   57.92%
Live                                                     890   41.57%
Closed/Won                                                11    0.51%
TOTAL                                                   2141  100.00%

--------------------------------------------------------------------------------------------------------------
2.7 by CREATE WEEK
--------------------------------------------------------------------------------------------------------------
value                                                  deals       % 
2026-08-10                                               721   33.68%
2026-08-03                                               497   23.21%
2026-07-27                                               409   19.10%
2026-08-17                                               241   11.26%
2026-07-20                                               162    7.57%
2026-07-13                                               111    5.18%
TOTAL                                                   2141  100.00%

--------------------------------------------------------------------------------------------------------------
2.8 by SCRAPED TYPE
--------------------------------------------------------------------------------------------------------------
value                                                  deals       % 
ITservices                                              1126   52.59%
(none)                                                   793   37.04%
Distressed startups                                      222   10.37%
TOTAL                                                   2141  100.00%

--------------------------------------------------------------------------------------------------------------
2.9 by DISTRESS TIER
--------------------------------------------------------------------------------------------------------------
value                                                  deals       % 
(none)                                                  2131   99.53%
Medium                                                     6    0.28%
Low                                                        4    0.19%
TOTAL                                                   2141  100.00%

--------------------------------------------------------------------------------------------------------------
2.10 by SOURCE TAB
--------------------------------------------------------------------------------------------------------------
value                                                  deals       % 
(none)                                                  1336   62.40%
nasscom                                                  228   10.65%
goodfirms                                                207    9.67%
founder_hunt                                             100    4.67%
OutFlo API                                                82    3.83%
searchq                                                   73    3.41%
prequal_q1                                                68    3.18%
romania                                                   29    1.35%
funded                                                    10    0.47%
linkedin                                                   8    0.37%
TOTAL                                                   2141  100.00%

--------------------------------------------------------------------------------------------------------------
2.11 CROSS-TAB: lead source x pipeline
--------------------------------------------------------------------------------------------------------------
source                                                    Campaign         Scraped     TOTAL
Scraping Algo ( IT services )                                    0             920       920
Linkedin Campaign ( IT Services )                              355               0       355
NASSCOM ( IT Services )                                          0             224       224
Outflo Outreach ( Startups )                                   177               0       177
Tracxn Sheet ( Startups )                                        0             175       175
Founder Search ( IT Services )                                   0             173       173
Scraping Algo ( Startups )                                       0              50        50
Romania ( IT Services )                                          0              29        29
Private Codebase Tracker sheet ( IT services )                   0              22        22
Scraped ( IT Services )                                          0               9         9
(none)                                                           4               3         7

--------------------------------------------------------------------------------------------------------------
2.12 CROSS-TAB: lead source x owner
--------------------------------------------------------------------------------------------------------------
source                                             Lamiya       Yuktha       (none)     Ishpreet       Shobit       Ashish    TOTAL
Scraping Algo ( IT services )                         236          234          422           16           12            0      920
Linkedin Campaign ( IT Services )                     153          155            0           47            0            0      355
NASSCOM ( IT Services )                               121          103            0            0            0            0      224
Outflo Outreach ( Startups )                           47           46           61           23            0            0      177
Tracxn Sheet ( Startups )                              57           57            7           46            6            2      175
Founder Search ( IT Services )                         83           90            0            0            0            0      173
Scraping Algo ( Startups )                             22           28            0            0            0            0       50
Romania ( IT Services )                                 0            0            0            0           29            0       29
Private Codebase Tracker sheet ( IT service             1            0           12            4            5            0       22
Scraped ( IT Services )                                 8            1            0            0            0            0        9
(none)                                                  0            0            0            5            1            1        7

--------------------------------------------------------------------------------------------------------------
2.13 CROSS-TAB: owner x current stage
--------------------------------------------------------------------------------------------------------------
stage                                            Lamiya       Yuktha       (none)     Ishpreet       Shobit       Ashish    TOTAL
Dead/ColdCall/WrongFit                              243          216          193           72            3            0      727
No Pickup                                           169          201          155            8            0            0      533
Dead/ColdCall/WrongNumber                           106          123            3            7            0            0      239
Dead/ColdCall/Not Interested                         54           28          113            4            0            0      199
Cold Call                                            81           82            0            1           28            0      192
Interested                                           49           40           19            8            2            1      119
Dead/GMeet/wrong fit                                  9            2            1            8            3            2       25
Script Shared                                         2           12            0           10            0            0       24
Dead/ResultsReceived/WrongFit-Rejected                1            2            1           13            4            0       21
Dead/Interested/NoShow                                1            2           13            0            2            0       18
GMeet Fixed                                           8            3            2            0            0            0       13
Closed/Won                                            0            0            1            6            4            0       11
Dead/Negotiation/Pricing                              1            1            0            0            4            0        6
Commercial Negotiation                                2            1            0            2            0            0        5
Dead/ScriptShared/NoShow                              1            0            0            1            1            0        3
Deal Contract Signed                                  0            1            0            0            1            0        2
Script Results Received                               1            0            0            1            0            0        2
Dead/Negotiation/Contractual                          0            0            0            0            1            0        1
Dead/GMeet/Privacy Concerns                           0            0            1            0            0            0        1

--------------------------------------------------------------------------------------------------------------
2.14 CROSS-TAB: depth x lead source
--------------------------------------------------------------------------------------------------------------
source                                           d0     d1     d2     d3     d4     d5     d6     d7     d8     d9    d10    d11    TOT
Scraping Algo ( IT services )                   345    311    219     13     11      6      6      1      0      0      1      7    920
Linkedin Campaign ( IT Services )               320     11      5      7      8      2      1      0      0      0      0      1    355
NASSCOM ( IT Services )                          90     90     37      6      0      0      1      0      0      0      0      0    224
Outflo Outreach ( Startups )                     51     24     68      7     21      4      2      0      0      0      0      0    177
Tracxn Sheet ( Startups )                        71     59     20      6      3     10      2      1      0      0      0      3    175
Founder Search ( IT Services )                  162      7      3      1      0      0      0      0      0      0      0      0    173
Scraping Algo ( Startups )                        9     28     10      0      3      0      0      0      0      0      0      0     50
Romania ( IT Services )                          29      0      0      0      0      0      0      0      0      0      0      0     29
Private Codebase Tracker sheet ( IT service       2      9      2      0      6      1      2      0      0      0      0      0     22
Scraped ( IT Services )                           5      4      0      0      0      0      0      0      0      0      0      0      9
(none)                                            0      0      0      0      2      2      1      0      0      1      0      1      7

##############################################################################################################
## 3. STAGE DISTRIBUTION — CURRENT AND EVER-REACHED
##############################################################################################################

--------------------------------------------------------------------------------------------------------------
3.1 CURRENT stage
--------------------------------------------------------------------------------------------------------------
stage                                            deals        %     cum%
Dead/ColdCall/WrongFit                             727   33.96%   33.96%
No Pickup                                          533   24.89%   58.85%
Dead/ColdCall/WrongNumber                          239   11.16%   70.01%
Dead/ColdCall/Not Interested                       199    9.29%   79.31%
Cold Call                                          192    8.97%   88.28%
Interested                                         119    5.56%   93.83%
Dead/GMeet/wrong fit                                25    1.17%   95.00%
Script Shared                                       24    1.12%   96.12%
Dead/ResultsReceived/WrongFit-Rejected              21    0.98%   97.10%
Dead/Interested/NoShow                              18    0.84%   97.94%
GMeet Fixed                                         13    0.61%   98.55%
Closed/Won                                          11    0.51%   99.07%
Dead/Negotiation/Pricing                             6    0.28%   99.35%
Commercial Negotiation                               5    0.23%   99.58%
Dead/ScriptShared/NoShow                             3    0.14%   99.72%
Deal Contract Signed                                 2    0.09%   99.81%
Script Results Received                              2    0.09%   99.91%
Dead/Negotiation/Contractual                         1    0.05%   99.95%
Dead/GMeet/Privacy Concerns                          1    0.05%  100.00%

--------------------------------------------------------------------------------------------------------------
3.2 EVER-REACHED (from full transition history)
--------------------------------------------------------------------------------------------------------------
stage                                           ever reached  % of all
Cold Call                                               2141   100.00%
No Pickup                                               1057    49.37%
Interested                                               514    24.01%
GMeet Fixed                                              150     7.01%
Script Shared                                            110     5.14%
Script Results Received                                   56     2.62%
Commercial Negotiation                                    31     1.45%
Deal Contract Signed                                      16     0.75%
Data Migration Done                                       14     0.65%
Metadata Matched                                          14     0.65%
Payment Initiation                                        13     0.61%
Closed/Won                                                12     0.56%

--------------------------------------------------------------------------------------------------------------
3.3 ENTRIES into each stage (transition count, may exceed deal count)
--------------------------------------------------------------------------------------------------------------
stage                                           entries   human  system
Cold Call                                          2065      16    2049
Dead/ColdCall/WrongFit                              760     418     342
No Pickup                                           563     329     234
Call Attempted (retired)                            289     278      11
Interested                                          269     231      38
Dead/ColdCall/WrongNumber                           240     235       5
Dead/ColdCall/Not Interested                        213     150      63
Script Shared                                        87      60      27
(deleted stage 3992480463)                           86      86       0
GMeet Fixed                                          53      50       3
(deleted stage 3992480479)                           48      48       0
Dead/GMeet/wrong fit                                 39      39       0
Script Results Received                              29      21       8
Dead/Interested/NoShow                               27      27       0
(deleted stage 3992480476)                           22      22       0
Dead/ResultsReceived/WrongFit-Rejected               22      20       2
Commercial Negotiation                               21      16       5
(deleted stage 3992480477)                           15      15       0
(deleted stage 3992480466)                           15      15       0
Deal Contract Signed                                 12      10       2
Closed/Won                                           12      10       2
Dead/Negotiation/Pricing                              6       6       0
(deleted stage 3992480472)                            5       5       0
Data Migration Done                                   5       5       0
(deleted stage 3992480478)                            3       3       0
Dead/GMeet/Privacy Concerns                           3       3       0
Dead/ScriptShared/NoShow                              3       3       0
(deleted stage 3992480474)                            2       2       0
(deleted stage 3992480468)                            2       2       0
Payment Initiation                                    2       2       0
(deleted stage 3992480470)                            1       1       0
Metadata Matched                                      1       1       0
Dead/Negotiation/Contractual                          1       0       1

##############################################################################################################
## 4. THE FUNNEL — OVERALL AND SLICED
##############################################################################################################

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — ALL DEALS  (n=2141)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                              2141   100.00%          -       0
No Pickup                              1057    49.37%     49.37%    1084
Interested                              514    24.01%     48.63%     543
GMeet Fixed                             150     7.01%     29.18%     364
Script Shared                           110     5.14%     73.33%      40
Script Results Received                  56     2.62%     50.91%      54
Commercial Negotiation                   31     1.45%     55.36%      25
Deal Contract Signed                     16     0.75%     51.61%      15
Data Migration Done                      14     0.65%     87.50%       2
Metadata Matched                         14     0.65%    100.00%       0
Payment Initiation                       13     0.61%     92.86%       1
Closed/Won                               12     0.56%     92.31%       1
  outcome: won 11  dead 1240  live 890   raw win 0.514%   resolved win 0.879%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — PIPELINE = Campaign  (n=536)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                               536   100.00%          -       0
No Pickup                               165    30.78%     30.78%     371
Interested                              130    24.25%     78.79%      35
GMeet Fixed                              57    10.63%     43.85%      73
Script Shared                            43     8.02%     75.44%      14
Script Results Received                  13     2.43%     30.23%      30
Commercial Negotiation                    6     1.12%     46.15%       7
Deal Contract Signed                      2     0.37%     33.33%       4
Data Migration Done                       2     0.37%    100.00%       0
Metadata Matched                          2     0.37%    100.00%       0
Payment Initiation                        1     0.19%     50.00%       1
Closed/Won                                1     0.19%    100.00%       0
  outcome: won 1  dead 459  live 76   raw win 0.187%   resolved win 0.217%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — PIPELINE = Scraped  (n=1605)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                              1605   100.00%          -       0
No Pickup                               892    55.58%     55.58%     713
Interested                              384    23.93%     43.05%     508
GMeet Fixed                              93     5.79%     24.22%     291
Script Shared                            67     4.17%     72.04%      26
Script Results Received                  43     2.68%     64.18%      24
Commercial Negotiation                   25     1.56%     58.14%      18
Deal Contract Signed                     14     0.87%     56.00%      11
Data Migration Done                      12     0.75%     85.71%       2
Metadata Matched                         12     0.75%    100.00%       0
Payment Initiation                       12     0.75%    100.00%       0
Closed/Won                               11     0.69%     91.67%       1
  outcome: won 10  dead 781  live 814   raw win 0.623%   resolved win 1.264%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — SOURCE = Scraping Algo ( IT services )  (n=920)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                               920   100.00%          -       0
No Pickup                               575    62.50%     62.50%     345
Interested                              264    28.70%     45.91%     311
GMeet Fixed                              45     4.89%     17.05%     219
Script Shared                            32     3.48%     71.11%      13
Script Results Received                  21     2.28%     65.62%      11
Commercial Negotiation                   15     1.63%     71.43%       6
Deal Contract Signed                      9     0.98%     60.00%       6
Data Migration Done                       8     0.87%     88.89%       1
Metadata Matched                          8     0.87%    100.00%       0
Payment Initiation                        8     0.87%    100.00%       0
Closed/Won                                7     0.76%     87.50%       1
  outcome: won 7  dead 532  live 381   raw win 0.761%   resolved win 1.299%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — SOURCE = Linkedin Campaign ( IT Services )  (n=355)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                               355   100.00%          -       0
No Pickup                                35     9.86%      9.86%     320
Interested                               24     6.76%     68.57%      11
GMeet Fixed                              19     5.35%     79.17%       5
Script Shared                            12     3.38%     63.16%       7
Script Results Received                   4     1.13%     33.33%       8
Commercial Negotiation                    2     0.56%     50.00%       2
Deal Contract Signed                      1     0.28%     50.00%       1
Data Migration Done                       1     0.28%    100.00%       0
Metadata Matched                          1     0.28%    100.00%       0
Payment Initiation                        1     0.28%    100.00%       0
Closed/Won                                1     0.28%    100.00%       0
  outcome: won 1  dead 335  live 19   raw win 0.282%   resolved win 0.298%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — SOURCE = NASSCOM ( IT Services )  (n=224)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                               224   100.00%          -       0
No Pickup                               134    59.82%     59.82%      90
Interested                               44    19.64%     32.84%      90
GMeet Fixed                               7     3.12%     15.91%      37
Script Shared                             1     0.45%     14.29%       6
Script Results Received                   1     0.45%    100.00%       0
Commercial Negotiation                    1     0.45%    100.00%       0
Deal Contract Signed                      0     0.00%      0.00%       1
Data Migration Done                       0     0.00%          -       0
Metadata Matched                          0     0.00%          -       0
Payment Initiation                        0     0.00%          -       0
Closed/Won                                0     0.00%          -       0
  outcome: won 0  dead 103  live 121   raw win 0.000%   resolved win 0.000%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — SOURCE = Outflo Outreach ( Startups )  (n=177)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                               177   100.00%          -       0
No Pickup                               126    71.19%     71.19%      51
Interested                              102    57.63%     80.95%      24
GMeet Fixed                              34    19.21%     33.33%      68
Script Shared                            27    15.25%     79.41%       7
Script Results Received                   6     3.39%     22.22%      21
Commercial Negotiation                    2     1.13%     33.33%       4
Deal Contract Signed                      0     0.00%      0.00%       2
Data Migration Done                       0     0.00%          -       0
Metadata Matched                          0     0.00%          -       0
Payment Initiation                        0     0.00%          -       0
Closed/Won                                0     0.00%          -       0
  outcome: won 0  dead 122  live 55   raw win 0.000%   resolved win 0.000%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — SOURCE = Tracxn Sheet ( Startups )  (n=175)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                               175   100.00%          -       0
No Pickup                               104    59.43%     59.43%      71
Interested                               45    25.71%     43.27%      59
GMeet Fixed                              25    14.29%     55.56%      20
Script Shared                            19    10.86%     76.00%       6
Script Results Received                  16     9.14%     84.21%       3
Commercial Negotiation                    6     3.43%     37.50%      10
Deal Contract Signed                      4     2.29%     66.67%       2
Data Migration Done                       3     1.71%     75.00%       1
Metadata Matched                          3     1.71%    100.00%       0
Payment Initiation                        3     1.71%    100.00%       0
Closed/Won                                3     1.71%    100.00%       0
  outcome: won 2  dead 105  live 68   raw win 1.143%   resolved win 1.869%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — SOURCE = Founder Search ( IT Services )  (n=173)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                               173   100.00%          -       0
No Pickup                                11     6.36%      6.36%     162
Interested                                4     2.31%     36.36%       7
GMeet Fixed                               1     0.58%     25.00%       3
Script Shared                             0     0.00%      0.00%       1
Script Results Received                   0     0.00%          -       0
Commercial Negotiation                    0     0.00%          -       0
Deal Contract Signed                      0     0.00%          -       0
Data Migration Done                       0     0.00%          -       0
Metadata Matched                          0     0.00%          -       0
Payment Initiation                        0     0.00%          -       0
Closed/Won                                0     0.00%          -       0
  outcome: won 0  dead 1  live 172   raw win 0.000%   resolved win 0.000%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — SOURCE = Scraping Algo ( Startups )  (n=50)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                                50   100.00%          -       0
No Pickup                                41    82.00%     82.00%       9
Interested                               13    26.00%     31.71%      28
GMeet Fixed                               3     6.00%     23.08%      10
Script Shared                             3     6.00%    100.00%       0
Script Results Received                   0     0.00%      0.00%       3
Commercial Negotiation                    0     0.00%          -       0
Deal Contract Signed                      0     0.00%          -       0
Data Migration Done                       0     0.00%          -       0
Metadata Matched                          0     0.00%          -       0
Payment Initiation                        0     0.00%          -       0
Closed/Won                                0     0.00%          -       0
  outcome: won 0  dead 21  live 29   raw win 0.000%   resolved win 0.000%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — SOURCE = Romania ( IT Services )  (n=29)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                                29   100.00%          -       0
No Pickup                                 0     0.00%      0.00%      29
Interested                                0     0.00%          -       0
GMeet Fixed                               0     0.00%          -       0
Script Shared                             0     0.00%          -       0
Script Results Received                   0     0.00%          -       0
Commercial Negotiation                    0     0.00%          -       0
Deal Contract Signed                      0     0.00%          -       0
Data Migration Done                       0     0.00%          -       0
Metadata Matched                          0     0.00%          -       0
Payment Initiation                        0     0.00%          -       0
Closed/Won                                0     0.00%          -       0
  outcome: won 0  dead 1  live 28   raw win 0.000%   resolved win 0.000%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — SOURCE = Private Codebase Tracker sheet ( IT services )  (n=22)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                                22   100.00%          -       0
No Pickup                                20    90.91%     90.91%       2
Interested                               11    50.00%     55.00%       9
GMeet Fixed                               9    40.91%     81.82%       2
Script Shared                             9    40.91%    100.00%       0
Script Results Received                   3    13.64%     33.33%       6
Commercial Negotiation                    2     9.09%     66.67%       1
Deal Contract Signed                      0     0.00%      0.00%       2
Data Migration Done                       0     0.00%          -       0
Metadata Matched                          0     0.00%          -       0
Payment Initiation                        0     0.00%          -       0
Closed/Won                                0     0.00%          -       0
  outcome: won 0  dead 12  live 10   raw win 0.000%   resolved win 0.000%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — OWNER = Lamiya Saleem  (n=728)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                               728   100.00%          -       0
No Pickup                               314    43.13%     43.13%     414
Interested                              144    19.78%     45.86%     170
GMeet Fixed                              27     3.71%     18.75%     117
Script Shared                            12     1.65%     44.44%      15
Script Results Received                   5     0.69%     41.67%       7
Commercial Negotiation                    3     0.41%     60.00%       2
Deal Contract Signed                      0     0.00%      0.00%       3
Data Migration Done                       0     0.00%          -       0
Metadata Matched                          0     0.00%          -       0
Payment Initiation                        0     0.00%          -       0
Closed/Won                                0     0.00%          -       0
  outcome: won 0  dead 416  live 312   raw win 0.000%   resolved win 0.000%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — OWNER = Yuktha Anand  (n=714)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                               714   100.00%          -       0
No Pickup                               317    44.40%     44.40%     397
Interested                              113    15.83%     35.65%     204
GMeet Fixed                              27     3.78%     23.89%      86
Script Shared                            19     2.66%     70.37%       8
Script Results Received                   5     0.70%     26.32%      14
Commercial Negotiation                    3     0.42%     60.00%       2
Deal Contract Signed                      1     0.14%     33.33%       2
Data Migration Done                       0     0.00%      0.00%       1
Metadata Matched                          0     0.00%          -       0
Payment Initiation                        0     0.00%          -       0
Closed/Won                                0     0.00%          -       0
  outcome: won 0  dead 374  live 340   raw win 0.000%   resolved win 0.000%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — OWNER = (none)  (n=502)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                               502   100.00%          -       0
No Pickup                               325    64.74%     64.74%     177
Interested                              164    32.67%     50.46%     161
GMeet Fixed                              14     2.79%      8.54%     150
Script Shared                             9     1.79%     64.29%       5
Script Results Received                   3     0.60%     33.33%       6
Commercial Negotiation                    2     0.40%     66.67%       1
Deal Contract Signed                      2     0.40%    100.00%       0
Data Migration Done                       2     0.40%    100.00%       0
Metadata Matched                          2     0.40%    100.00%       0
Payment Initiation                        2     0.40%    100.00%       0
Closed/Won                                1     0.20%     50.00%       1
  outcome: won 1  dead 325  live 176   raw win 0.199%   resolved win 0.307%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — OWNER = Ishpreet Sood  (n=141)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                               141   100.00%          -       0
No Pickup                                76    53.90%     53.90%      65
Interested                               68    48.23%     89.47%       8
GMeet Fixed                              59    41.84%     86.76%       9
Script Shared                            48    34.04%     81.36%      11
Script Results Received                  25    17.73%     52.08%      23
Commercial Negotiation                   11     7.80%     44.00%      14
Deal Contract Signed                      7     4.96%     63.64%       4
Data Migration Done                       7     4.96%    100.00%       0
Metadata Matched                          7     4.96%    100.00%       0
Payment Initiation                        6     4.26%     85.71%       1
Closed/Won                                6     4.26%    100.00%       0
  outcome: won 6  dead 105  live 30   raw win 4.255%   resolved win 5.405%

--------------------------------------------------------------------------------------------------------------
4.x FUNNEL — OWNER = Shobit Gupta  (n=53)
--------------------------------------------------------------------------------------------------------------
stage                               reached  % of top  step conv    lost
Cold Call                                53   100.00%          -       0
No Pickup                                22    41.51%     41.51%      31
Interested                               22    41.51%    100.00%       0
GMeet Fixed                              20    37.74%     90.91%       2
Script Shared                            19    35.85%     95.00%       1
Script Results Received                  15    28.30%     78.95%       4
Commercial Negotiation                   11    20.75%     73.33%       4
Deal Contract Signed                      6    11.32%     54.55%       5
Data Migration Done                       5     9.43%     83.33%       1
Metadata Matched                          5     9.43%    100.00%       0
Payment Initiation                        5     9.43%    100.00%       0
Closed/Won                                5     9.43%    100.00%       0
  outcome: won 4  dead 18  live 31   raw win 7.547%   resolved win 18.182%

##############################################################################################################
## 5. DEPTH ANALYSIS — HOW FAR LEADS TRAVEL
##############################################################################################################

--------------------------------------------------------------------------------------------------------------
5.1 depth distribution
--------------------------------------------------------------------------------------------------------------
depth   stage                            deals        %  cum% (>= this depth)
0       Cold Call                         1084   50.63%               100.00%
1       No Pickup                          543   25.36%                49.37%
2       Interested                         364   17.00%                24.01%
3       GMeet Fixed                         40    1.87%                 7.01%
4       Script Shared                       54    2.52%                 5.14%
5       Script Results Received             25    1.17%                 2.62%
6       Commercial Negotiation              15    0.70%                 1.45%
7       Deal Contract Signed                 2    0.09%                 0.75%
8       Data Migration Done                  0    0.00%                 0.65%
9       Metadata Matched                     1    0.05%                 0.65%
10      Payment Initiation                   1    0.05%                 0.61%
11      Closed/Won                          12    0.56%                 0.56%

--------------------------------------------------------------------------------------------------------------
5.2 depth stats by lead source
--------------------------------------------------------------------------------------------------------------
source                                               n  mean depth  median   max    %>=2    %>=4
Scraping Algo ( IT services )                      920        1.08     1.0    11   28.7%    3.5%
Linkedin Campaign ( IT Services )                  355        0.28     0.0    11    6.8%    3.4%
NASSCOM ( IT Services )                            224        0.84     1.0     6   19.6%    0.4%
Outflo Outreach ( Startups )                       177        1.68     2.0     6   57.6%   15.3%
Tracxn Sheet ( Startups )                          175        1.32     1.0    11   25.7%   10.9%
Founder Search ( IT Services )                     173        0.09     0.0     3    2.3%    0.0%
Scraping Algo ( Startups )                          50        1.20     1.0     4   26.0%    6.0%
Romania ( IT Services )                             29        0.00     0.0     0    0.0%    0.0%
Private Codebase Tracker sheet ( IT services )      22        2.45     1.5     6   50.0%   40.9%
Scraped ( IT Services )                              9        0.44     0.0     1    0.0%    0.0%
(none)                                               7        6.29     5.0    11  100.0%  100.0%

--------------------------------------------------------------------------------------------------------------
5.3 depth stats by owner
--------------------------------------------------------------------------------------------------------------
owner                            n  mean depth  median   max    %>=2    %>=4
Lamiya Saleem                  728        0.69     0.0     6   19.8%    1.6%
Yuktha Anand                   714        0.68     0.0     7   15.8%    2.7%
(none)                         502        1.05     1.0    11   32.7%    1.8%
Ishpreet Sood                  141        2.27     1.0    11   48.2%   34.0%
Shobit Gupta                    53        2.55     0.0    11   41.5%   35.8%
Ashish Ranjan                    3        5.33     5.0     6  100.0%  100.0%

--------------------------------------------------------------------------------------------------------------
5.4 number of stage moves per deal
--------------------------------------------------------------------------------------------------------------
  all deals      : n=2141 sum=4,921 mean=2.3 median=2.0 p25=2.0 p75=3.0 p90=3.0 min=1.0 max=8.0 sd=0.9
  human moves    : n=2141 sum=2,129 mean=1.0 median=1.0 p25=0.0 p75=1.0 p90=2.0 min=0.0 max=7.0 sd=0.9
  deals past CC  : n=514 sum=1,482 mean=2.9 median=3.0 p25=2.0 p75=3.0 p90=5.0 min=1.0 max=8.0 sd=1.3
  won deals      : n=11 sum=58 mean=5.3 median=5.0 p25=4.0 p75=7.0 p90=7.0 min=3.0 max=8.0 sd=1.7

##############################################################################################################
## 6. DAILY TIME SERIES
##############################################################################################################
date           new  moves  human  notes  tasks  conn  gmeet script  won          LoC
2026-07-15     106    106      0      0      0     0      0      0    0            0
2026-07-16       0      5      4      2      0     1      0      0    0            0
2026-07-17       5      5      0      0      0     0      0      0    0            0
2026-07-20       5     80     75     21      4    11      0      0    0            0
2026-07-21      24    154    146     43      6     9      5      1    0            0
2026-07-22      74    176     78     47     22     3      0      0    0            0
2026-07-23      59    213     68     39     31    14      2      0    0            0
2026-07-27       3     49     49     29      1     5      1      2    0            0
2026-07-28     109    222     89    365     43    25      1      1    1    3,408,665
2026-07-29      70    105     35     41     21    10      1      4    0            0
2026-07-30     226    303     78     33      3     8      0      3    2   11,335,221
2026-07-31       0     55     55     14      0     7      0      1    0            0
2026-08-01       1      5      5      0      0     0      0      0    0            0
2026-08-02       0      2      2      0      0     0      0      0    0            0
2026-08-03     114    231    119     49     19    16      2      4    1    4,773,185
2026-08-04      71    244    173    146     37    36      1      4    0            0
2026-08-05      42    406    119    107     20    40     12      7    5   30,701,516
2026-08-06      28    122     94     85      8    15      6      7    0            0
2026-08-07     242    327     86     84      5    11      3      5    0            0
2026-08-10     262    417    156    146      6    20      1      6    2   19,893,747
2026-08-11     200    361    161    149     23    45      5      1    0            0
2026-08-12       0    359    122    136      5    29      2      4    0            0
2026-08-13     179    383    145    153     14    23      1      5    0            0
2026-08-14      80    214    134    145     11    24      2      0    0            0
2026-08-17     241    377    136    147      7    29      5      5    0            0
TOTAL         2141   4921   2129   1981    288           50     60   11   70,112,334

##############################################################################################################
## 7. WEEKLY TIME SERIES
##############################################################################################################
week           new  moves  human  notes  tasks  inter  gmeet script results  neg  won      raw LoC    tier1 LoC
2026-07-13     111    116      4      2      2      1      0      0       0    0    0            0            0
2026-07-20     162    623    367    150     63     26      7      1       1    1    0            0            0
2026-07-27     409    741    313    482     68     18      3     11      11    8    3   14,743,886    6,588,669
2026-08-03     497   1330    591    471     89     70     24     27       4    2    6   35,474,701   15,380,759
2026-08-10     721   1734    718    729     59    101     11     16       3    2    2   19,893,747   19,893,747
2026-08-17     241    377    136    147      7     15      5      5       2    3    0            0            0

--------------------------------------------------------------------------------------------------------------
7.1 weekly new leads BY SOURCE
--------------------------------------------------------------------------------------------------------------
week          Scraping Algo  Linkedin Camp  NASSCOM ( IT   Outflo Outrea  Tracxn Sheet   Founder Searc  Scraping Algo  Romania ( IT 
2026-07-13              106              0              0              0              5              0              0              0
2026-07-20              142              0              0              8              7              0              0              0
2026-07-27              153              0              0            129            110              0              0              0
2026-08-03              256             92              0             40             53              0             50              0
2026-08-10              200            263            219              0              0              0              0             29
2026-08-17               63              0              5              0              0            173              0              0

--------------------------------------------------------------------------------------------------------------
7.2 weekly HUMAN stage moves BY OWNER
--------------------------------------------------------------------------------------------------------------
week                Lamiya        Yuktha        (none)      Ishpreet        Shobit        Ashish
2026-07-13               0             0             0             0             0             0
2026-07-20               0             0           334            22            10             0
2026-07-27               0             0           272             7            34             0
2026-08-03             204           175            92            79            38             0
2026-08-10             335           337             0            29            17             0
2026-08-17              66            63             0             1             6             0

--------------------------------------------------------------------------------------------------------------
7.3 weekly NOTES BY OWNER
--------------------------------------------------------------------------------------------------------------
week                Lamiya        Yuktha        (none)      Ishpreet        Shobit        Ashish
2026-07-13               0             0             0             0             0             0
2026-07-20               0             0           140            10             0             0
2026-07-27               0             0           467             6             9             0
2026-08-03             130           173           154             5             6             2
2026-08-10             372           343             0             2            12             0
2026-08-17              80            67             0             0             0             0

##############################################################################################################
## 8. PER-PERSON ACTIVITY
##############################################################################################################

--------------------------------------------------------------------------------------------------------------
8.x Lamiya Saleem
--------------------------------------------------------------------------------------------------------------
  deals owned            : 728
  human stage moves made : 605
  notes written          : 582
  tasks created          : 115
  active days            : 11
  distinct deals/day     : n=11 sum=563 mean=51.2 median=54.0 p25=41.0 p75=66.5 p90=70.0 min=12.0 max=71.0 sd=18.4
  moves/day              : n=11 sum=605 mean=55.0 median=58.0 p25=46.0 p75=69.5 p90=73.0 min=14.0 max=75.0 sd=18.1
  notes/day              : n=10 sum=582 mean=58.2 median=68.5 p25=43.0 p75=76.8 p90=80.2 min=8.0 max=82.0 sd=24.7
  owned-deal outcomes    : won 0  dead 416  live 312
  owned-deal depth       : n=728 sum=505 mean=0.7 median=0.0 p25=0.0 p75=1.0 p90=2.0 min=0.0 max=6.0 sd=1.0
  moves BY TARGET STAGE:
      No Pickup                                      147
      Dead/ColdCall/WrongFit                         126
      Dead/ColdCall/WrongNumber                      106
      Interested                                      91
      Dead/ColdCall/Not Interested                    57
      Call Attempted (retired)                        34
      GMeet Fixed                                     16
      Script Shared                                   12
      Dead/GMeet/wrong fit                             8
      Cold Call                                        3
      Script Results Received                          3
      Dead/ResultsReceived/WrongFit-Rejected           1
      Dead/ScriptShared/NoShow                         1
  daily detail:
      date          deals  moves  notes
      2026-08-03       12     14      0
      2026-08-04       43     50      8
      2026-08-05       32     40     34
      2026-08-06       52     58     46
      2026-08-07       39     42     42
      2026-08-10       70     73     82
      2026-08-11       69     75     74
      2026-08-12       54     56     76
      2026-08-13       71     73     77
      2026-08-14       57     58     63
      2026-08-17       64     66     80

--------------------------------------------------------------------------------------------------------------
8.x Yuktha Anand
--------------------------------------------------------------------------------------------------------------
  deals owned            : 714
  human stage moves made : 575
  notes written          : 583
  tasks created          : 27
  active days            : 11
  distinct deals/day     : n=11 sum=523 mean=47.5 median=51.0 p25=32.5 p75=64.0 p90=71.0 min=11.0 max=72.0 sd=19.9
  moves/day              : n=11 sum=575 mean=52.3 median=57.0 p25=42.0 p75=66.5 p90=75.0 min=12.0 max=77.0 sd=19.8
  notes/day              : n=11 sum=583 mean=53.0 median=60.0 p25=40.0 p75=70.0 p90=73.0 min=12.0 max=76.0 sd=19.9
  owned-deal outcomes    : won 0  dead 374  live 340
  owned-deal depth       : n=714 sum=485 mean=0.7 median=0.0 p25=0.0 p75=1.0 p90=2.0 min=0.0 max=7.0 sd=1.0
  moves BY TARGET STAGE:
      No Pickup                                      182
      Dead/ColdCall/WrongNumber                      122
      Interested                                      79
      Dead/ColdCall/WrongFit                          76
      Call Attempted (retired)                        44
      Dead/ColdCall/Not Interested                    28
      GMeet Fixed                                     21
      Script Shared                                   16
      Dead/ResultsReceived/WrongFit-Rejected           2
      Commercial Negotiation                           2
      Script Results Received                          1
      Deal Contract Signed                             1
      Dead/GMeet/wrong fit                             1
  daily detail:
      date          deals  moves  notes
      2026-08-03       11     12     12
      2026-08-04       42     48     41
      2026-08-05       29     43     39
      2026-08-06       29     31     39
      2026-08-07       36     41     42
      2026-08-10       51     57     61
      2026-08-11       71     77     73
      2026-08-12       54     58     60
      2026-08-13       67     70     76
      2026-08-14       72     75     73
      2026-08-17       61     63     67

--------------------------------------------------------------------------------------------------------------
8.x Ishpreet Sood
--------------------------------------------------------------------------------------------------------------
  deals owned            : 141
  human stage moves made : 138
  notes written          : 23
  tasks created          : 26
  active days            : 13
  distinct deals/day     : n=13 sum=125 mean=9.6 median=5.0 p25=2.0 p75=15.0 p90=18.4 min=1.0 max=38.0 sd=10.6
  moves/day              : n=13 sum=138 mean=10.6 median=8.0 p25=2.0 p75=18.0 p90=19.6 min=1.0 max=39.0 sd=10.9
  notes/day              : n=7 sum=23 mean=3.3 median=3.0 p25=2.0 p75=4.0 p90=4.8 min=2.0 max=6.0 sd=1.5
  owned-deal outcomes    : won 6  dead 105  live 30
  owned-deal depth       : n=141 sum=320 mean=2.3 median=1.0 p25=0.0 p75=4.0 p90=5.0 min=0.0 max=11.0 sd=2.8
  moves BY TARGET STAGE:
      Dead/ColdCall/WrongFit                          36
      Script Shared                                   18
      Call Attempted (retired)                        12
      Interested                                      11
      Dead/ColdCall/Not Interested                     8
      Dead/ResultsReceived/WrongFit-Rejected           8
      Dead/GMeet/wrong fit                             7
      Dead/ColdCall/WrongNumber                        7
      GMeet Fixed                                      5
      Script Results Received                          4
      (deleted stage 3992480479)                       3
      (deleted stage 3992480472)                       3
      Dead/Interested/NoShow                           3
      Commercial Negotiation                           3
      (deleted stage 3992480468)                       2
      Dead/ScriptShared/NoShow                         2
      (deleted stage 3992480466)                       1
      (deleted stage 3992480470)                       1
      (deleted stage 3992480474)                       1
      Metadata Matched                                 1
      Deal Contract Signed                             1
      Dead/Negotiation/Pricing                         1
  daily detail:
      date          deals  moves  notes
      2026-07-20        4      4      4
      2026-07-21       15     18      6
      2026-07-27        3      3      2
      2026-07-29        2      2      4
      2026-07-30        1      2      0
      2026-08-03       16     18      3
      2026-08-04       38     39      2
      2026-08-05       19     20      0
      2026-08-06        2      2      0
      2026-08-10       12     12      0
      2026-08-11        7      9      2
      2026-08-12        5      8      0
      2026-08-17        1      1      0

--------------------------------------------------------------------------------------------------------------
8.x Shobit Gupta
--------------------------------------------------------------------------------------------------------------
  deals owned            : 53
  human stage moves made : 105
  notes written          : 27
  tasks created          : 27
  active days            : 17
  distinct deals/day     : n=17 sum=95 mean=5.6 median=5.0 p25=2.0 p75=7.0 p90=11.6 min=1.0 max=16.0 sd=4.4
  moves/day              : n=17 sum=105 mean=6.2 median=6.0 p25=2.0 p75=8.0 p90=11.6 min=1.0 max=16.0 sd=4.5
  notes/day              : n=9 sum=27 mean=3.0 median=3.0 p25=1.0 p75=3.0 p90=5.0 min=1.0 max=9.0 sd=2.5
  owned-deal outcomes    : won 4  dead 18  live 31
  owned-deal depth       : n=53 sum=135 mean=2.5 median=0.0 p25=0.0 p75=5.0 p90=6.8 min=0.0 max=11.0 sd=3.6
  moves BY TARGET STAGE:
      Dead/ColdCall/WrongFit                          13
      Script Results Received                         12
      Commercial Negotiation                          10
      Closed/Won                                      10
      Dead/GMeet/wrong fit                             9
      Dead/ResultsReceived/WrongFit-Rejected           9
      Deal Contract Signed                             8
      Script Shared                                    7
      Dead/Negotiation/Pricing                         5
      Data Migration Done                              5
      Cold Call                                        4
      Dead/Interested/NoShow                           4
      (deleted stage 3992480472)                       2
      Interested                                       2
      (deleted stage 3992480474)                       1
      Dead/ColdCall/Not Interested                     1
      Payment Initiation                               1
      Call Attempted (retired)                         1
      GMeet Fixed                                      1
  daily detail:
      date          deals  moves  notes
      2026-07-21        6     10      0
      2026-07-27        1      1      1
      2026-07-28        7      7      2
      2026-07-29        5      6      1
      2026-07-30        6      6      4
      2026-07-31        6      8      1
      2026-08-01        4      4      0
      2026-08-02        2      2      0
      2026-08-03        7      8      0
      2026-08-04       10     10      3
      2026-08-05       16     16      3
      2026-08-06        1      1      0
      2026-08-07        2      3      0
      2026-08-10       14     14      3
      2026-08-13        2      2      0
      2026-08-14        1      1      9
      2026-08-17        5      6      0

--------------------------------------------------------------------------------------------------------------
8.x Ashish Ranjan
--------------------------------------------------------------------------------------------------------------
  deals owned            : 3
  human stage moves made : 0
  notes written          : 2
  tasks created          : 4
  notes/day              : n=1 sum=2 mean=2.0 median=2.0 p25=2.0 p75=2.0 p90=2.0 min=2.0 max=2.0 sd=0.0
  owned-deal outcomes    : won 0  dead 2  live 1
  owned-deal depth       : n=3 sum=16 mean=5.3 median=5.0 p25=5.0 p75=5.5 p90=5.8 min=5.0 max=6.0 sd=0.6
  moves BY TARGET STAGE:
  daily detail:
      date          deals  moves  notes
      2026-08-05        0      0      2

##############################################################################################################
## 9. LEAD-SOURCE DEEP DIVE
##############################################################################################################
source                                            deals  >=Int  >=GM  >=SS  won t1won  dead  live      rawLoC       t1LoC   win%   res%
Scraping Algo ( IT services )                       920    264    45    32    7     6   532   381  40,739,710  20,645,768  0.76%  1.30%
Linkedin Campaign ( IT Services )                   355     24    19    12    1     1   335    19  17,525,955  17,525,955  0.28%  0.30%
NASSCOM ( IT Services )                             224     44     7     1    0     0   103   121           0           0  0.00%  0.00%
Outflo Outreach ( Startups )                        177    102    34    27    0     0   122    55           0           0  0.00%  0.00%
Tracxn Sheet ( Startups )                           175     45    25    19    2     1   105    68   9,478,877   1,323,660  1.14%  1.87%
Founder Search ( IT Services )                      173      4     1     0    0     0     1   172           0           0  0.00%  0.00%
Scraping Algo ( Startups )                           50     13     3     3    0     0    21    29           0           0  0.00%  0.00%
Romania ( IT Services )                              29      0     0     0    0     0     1    28           0           0  0.00%  0.00%
Private Codebase Tracker sheet ( IT services )       22     11     9     9    0     0    12    10           0           0  0.00%  0.00%
Scraped ( IT Services )                               9      0     0     0    0     0     4     5           0           0  0.00%  0.00%
(none)                                                7      7     7     7    1     1     4     2   2,367,792   2,367,792 14.29% 20.00%

--------------------------------------------------------------------------------------------------------------
9.1 per-source: age, idle, notes
--------------------------------------------------------------------------------------------------------------
source                                            mean age  mean idle  notes/deal  moves/deal
Scraping Algo ( IT services )                         15.3       11.3        0.96        2.63
Linkedin Campaign ( IT Services )                      8.0        5.0        0.18        2.04
NASSCOM ( IT Services )                                3.7        3.2        1.08        2.06
Outflo Outreach ( Startups )                          17.7       12.5        1.63        2.31
Tracxn Sheet ( Startups )                             17.6       11.4        0.62        2.56
Founder Search ( IT Services )                         0.0        0.0        0.08        1.08
Scraping Algo ( Startups )                            13.0       10.6        1.66        2.88
Romania ( IT Services )                                3.0        3.0        0.31        1.03
Private Codebase Tracker sheet ( IT services )        20.0       13.1        0.64        3.00
Scraped ( IT Services )                                4.0        2.4        0.89        1.89
(none)                                                14.7       11.1        0.29        2.14

--------------------------------------------------------------------------------------------------------------
9.2 per-source: death-reason breakdown
--------------------------------------------------------------------------------------------------------------
source                                    ColdCall/Wron  ColdCall/Wron  ColdCall/Not   GMeet/wrong f  ResultsReceiv  Interested/No  Negotiation/P
Scraping Algo ( IT services )                       245            132            123              7              6             14              3
Linkedin Campaign ( IT Services )                   323              1              0              7              2              1              1
NASSCOM ( IT Services )                              18             76              7              2              0              0              0
Outflo Outreach ( Startups )                         64              5             45              2              3              2              0
Tracxn Sheet ( Startups )                            62             16             14              4              8              0              1
Founder Search ( IT Services )                        0              1              0              0              0              0              0
Scraping Algo ( Startups )                            7              4              8              1              0              0              0
Romania ( IT Services )                               1              0              0              0              0              0              0
Private Codebase Tracker sheet ( IT ser               4              0              2              2              1              1              1
Scraped ( IT Services )                               0              4              0              0              0              0              0
(none)                                                3              0              0              0              1              0              0

##############################################################################################################
## 10. PIPELINE DEEP DIVE
##############################################################################################################

--------------------------------------------------------------------------------------------------------------
10.x Campaign  (n=536)
--------------------------------------------------------------------------------------------------------------
  stage distribution:
      Dead/ColdCall/WrongFit                           388   72.39%
      Dead/ColdCall/Not Interested                      45    8.40%
      No Pickup                                         40    7.46%
      Script Shared                                     15    2.80%
      Interested                                        13    2.43%
      Dead/GMeet/wrong fit                               9    1.68%
      Dead/ResultsReceived/WrongFit-Rejected             6    1.12%
      Dead/ColdCall/WrongNumber                          6    1.12%
      GMeet Fixed                                        4    0.75%
      Dead/Interested/NoShow                             3    0.56%
      Commercial Negotiation                             2    0.37%
      Dead/GMeet/Privacy Concerns                        1    0.19%
      Cold Call                                          1    0.19%
      Closed/Won                                         1    0.19%
      Dead/Negotiation/Pricing                           1    0.19%
      Script Results Received                            1    0.19%
  sources:
      Linkedin Campaign ( IT Services )                355
      Outflo Outreach ( Startups )                     177
      (none)                                             4
  owners:
      Yuktha Anand                                     201
      Lamiya Saleem                                    200
      Ishpreet Sood                                     73
      (none)                                            61
      Ashish Ranjan                                      1
  won 1  LoC 17,525,955   depth mean 0.79

--------------------------------------------------------------------------------------------------------------
10.x Scraped  (n=1605)
--------------------------------------------------------------------------------------------------------------
  stage distribution:
      No Pickup                                        493   30.72%
      Dead/ColdCall/WrongFit                           339   21.12%
      Dead/ColdCall/WrongNumber                        233   14.52%
      Cold Call                                        191   11.90%
      Dead/ColdCall/Not Interested                     154    9.60%
      Interested                                       106    6.60%
      Dead/GMeet/wrong fit                              16    1.00%
      Dead/Interested/NoShow                            15    0.93%
      Dead/ResultsReceived/WrongFit-Rejected            15    0.93%
      Closed/Won                                        10    0.62%
      Script Shared                                      9    0.56%
      GMeet Fixed                                        9    0.56%
      Dead/Negotiation/Pricing                           5    0.31%
      Dead/ScriptShared/NoShow                           3    0.19%
      Commercial Negotiation                             3    0.19%
      Deal Contract Signed                               2    0.12%
      Dead/Negotiation/Contractual                       1    0.06%
      Script Results Received                            1    0.06%
  sources:
      Scraping Algo ( IT services )                    920
      NASSCOM ( IT Services )                          224
      Tracxn Sheet ( Startups )                        175
      Founder Search ( IT Services )                   173
      Scraping Algo ( Startups )                        50
      Romania ( IT Services )                           29
      Private Codebase Tracker sheet ( IT services )    22
      Scraped ( IT Services )                            9
      (none)                                             3
  owners:
      Lamiya Saleem                                    528
      Yuktha Anand                                     513
      (none)                                           441
      Ishpreet Sood                                     68
      Shobit Gupta                                      53
      Ashish Ranjan                                      2
  won 10  LoC 52,586,379   depth mean 0.98

##############################################################################################################
## 11. TIMELINES — DAYS FROM CREATE TO EACH STAGE
##############################################################################################################

--------------------------------------------------------------------------------------------------------------
11.1 all deals that reached the stage
--------------------------------------------------------------------------------------------------------------
stage                              n  days from createdate (stats)
Cold Call                       2045  n=2045 sum=0 mean=0.0 median=0.0 p25=0.0 p75=0.0 p90=0.0 min=0.0 max=0.0 sd=0.0
No Pickup                        563  n=563 sum=2,495 mean=4.4 median=2.0 p25=0.0 p75=6.0 p90=14.0 min=0.0 max=21.0 sd=5.9
Interested                       248  n=248 sum=583 mean=2.4 median=1.0 p25=0.0 p75=5.0 p90=7.0 min=0.0 max=21.0 sd=3.3
GMeet Fixed                       52  n=52 sum=131 mean=2.5 median=1.0 p25=0.0 p75=4.0 p90=7.0 min=0.0 max=14.0 sd=3.3
Script Shared                     82  n=82 sum=253 mean=3.1 median=1.0 p25=0.0 p75=5.0 p90=9.8 min=0.0 max=15.0 sd=4.3
Script Results Received           27  n=27 sum=114 mean=4.2 median=2.0 p25=0.5 p75=7.5 p90=10.6 min=0.0 max=15.0 sd=4.6
Commercial Negotiation            21  n=21 sum=108 mean=5.1 median=5.0 p25=0.0 p75=7.0 p90=13.0 min=0.0 max=18.0 sd=5.4
Deal Contract Signed              10  n=10 sum=57 mean=5.7 median=5.5 p25=0.8 p75=8.0 p90=9.9 min=0.0 max=18.0 sd=5.6
Data Migration Done                5  n=5 sum=35 mean=7.0 median=6.0 p25=6.0 p75=9.0 p90=11.4 min=1.0 max=13.0 sd=4.4
Metadata Matched                   1  n=1 sum=0 mean=0.0 median=0.0 p25=0.0 p75=0.0 p90=0.0 min=0.0 max=0.0 sd=0.0
Payment Initiation                 2  n=2 sum=12 mean=6.0 median=6.0 p25=3.0 p75=9.0 p90=10.8 min=0.0 max=12.0 sd=8.5
Closed/Won                        12  n=12 sum=89 mean=7.4 median=7.5 p25=5.2 p75=8.5 p90=11.8 min=2.0 max=15.0 sd=3.8

--------------------------------------------------------------------------------------------------------------
11.2 same, WON deals only
--------------------------------------------------------------------------------------------------------------
Cold Call                          4  n=4 sum=0 mean=0.0 median=0.0 p25=0.0 p75=0.0 p90=0.0 min=0.0 max=0.0 sd=0.0
GMeet Fixed                        1  n=1 sum=1 mean=1.0 median=1.0 p25=1.0 p75=1.0 p90=1.0 min=1.0 max=1.0 sd=0.0
Script Shared                      8  n=8 sum=5 mean=0.6 median=0.0 p25=0.0 p75=0.0 p90=1.5 min=0.0 max=5.0 sd=1.8
Script Results Received            7  n=7 sum=23 mean=3.3 median=2.0 p25=1.0 p75=5.5 p90=7.4 min=0.0 max=8.0 sd=3.1
Commercial Negotiation             7  n=7 sum=32 mean=4.6 median=5.0 p25=1.5 p75=7.5 p90=8.4 min=0.0 max=9.0 sd=3.7
Deal Contract Signed               8  n=8 sum=39 mean=4.9 median=5.5 p25=2.2 p75=8.0 p90=8.3 min=0.0 max=9.0 sd=3.6
Data Migration Done                5  n=5 sum=35 mean=7.0 median=6.0 p25=6.0 p75=9.0 p90=11.4 min=1.0 max=13.0 sd=4.4
Payment Initiation                 1  n=1 sum=12 mean=12.0 median=12.0 p25=12.0 p75=12.0 p90=12.0 min=12.0 max=12.0 sd=0.0
Closed/Won                        11  n=11 sum=82 mean=7.5 median=8.0 p25=4.5 p75=9.0 p90=12.0 min=2.0 max=15.0 sd=4.0

--------------------------------------------------------------------------------------------------------------
11.3 create -> close for won deals
--------------------------------------------------------------------------------------------------------------
  days_to_close (property) : n=11 sum=82 mean=7.5 median=8.0 p25=4.5 p75=9.0 p90=12.0 min=2.0 max=15.0 sd=4.0
  age of live deals        : n=890 sum=8,735 mean=9.8 median=6.0 p25=3.0 p75=17.0 p90=25.0 min=0.0 max=33.0 sd=9.1
  age of dead deals        : n=1240 sum=16,277 mean=13.1 median=10.0 p25=7.0 p75=18.0 p90=26.0 min=0.0 max=33.0 sd=8.3
  idle days, live deals    : n=890 sum=5,723 mean=6.4 median=6.0 p25=0.0 p75=12.0 p90=12.0 min=0.0 max=28.0 sd=5.4
  idle days by depth (live):
      depth 0 Cold Call                    n=192 sum=104 mean=0.5 median=0.0 p25=0.0 p75=0.0 p90=3.0 min=0.0 max=13.0 sd=1.4
      depth 1 No Pickup                    n=518 sum=4,186 mean=8.1 median=10.0 p25=4.0 p75=12.0 p90=12.0 min=0.0 max=12.0 sd=4.1
      depth 2 Interested                   n=126 sum=971 mean=7.7 median=6.0 p25=3.0 p75=11.0 p90=19.0 min=0.0 max=28.0 sd=6.6
      depth 3 GMeet Fixed                  n=17 sum=179 mean=10.5 median=10.0 p25=3.0 p75=19.0 p90=25.0 min=0.0 max=25.0 sd=9.2
      depth 4 Script Shared                n=27 sum=235 mean=8.7 median=7.0 p25=4.5 p75=12.0 p90=18.4 min=0.0 max=20.0 sd=6.1
      depth 5 Script Results Received      n=2 sum=7 mean=3.5 median=3.5 p25=1.8 p75=5.2 p90=6.3 min=0.0 max=7.0 sd=4.9
      depth 6 Commercial Negotiation       n=6 sum=30 mean=5.0 median=2.5 p25=0.0 p75=5.0 p90=12.5 min=0.0 max=20.0 sd=7.7
      depth 7 Deal Contract Signed         n=2 sum=11 mean=5.5 median=5.5 p25=2.8 p75=8.2 p90=9.9 min=0.0 max=11.0 sd=7.8

##############################################################################################################
## 12. DWELL TIME PER STAGE (days between consecutive moves)
##############################################################################################################
stage                                            n  stats (days)
Cold Call                                     1873  n=1873 sum=4,177 mean=2.2 median=0.9 p25=0.1 p75=3.3 p90=6.0 min=0.0 max=18.1 sd=2.9
No Pickup                                       30  n=30 sum=7 mean=0.2 median=0.0 p25=0.0 p75=0.0 p90=0.8 min=0.0 max=2.9 sd=0.6
Interested                                     150  n=150 sum=593 mean=4.0 median=1.2 p25=0.1 p75=7.0 p90=12.0 min=0.0 max=21.1 sd=4.8
GMeet Fixed                                     40  n=40 sum=117 mean=2.9 median=2.2 p25=0.3 p75=4.5 p90=6.1 min=0.0 max=14.0 sd=3.2
Script Shared                                   63  n=63 sum=399 mean=6.3 median=5.1 p25=1.9 p75=9.5 p90=13.7 min=0.0 max=20.1 sd=5.2
Script Results Received                         27  n=27 sum=71 mean=2.6 median=1.3 p25=0.1 p75=4.0 p90=7.2 min=0.0 max=10.2 sd=3.0
Commercial Negotiation                          16  n=16 sum=48 mean=3.0 median=1.3 p25=0.9 p75=3.8 p90=7.9 min=0.0 max=12.7 sd=3.7
Deal Contract Signed                            10  n=10 sum=17 mean=1.7 median=2.1 p25=0.2 p75=2.6 p90=3.2 min=0.0 max=4.0 sd=1.4
Data Migration Done                              5  n=5 sum=7 mean=1.5 median=2.0 p25=0.7 p75=2.0 p90=2.0 min=0.7 max=2.0 sd=0.7
Metadata Matched                                 1  n=1 sum=1 mean=1.3 median=1.3 p25=1.3 p75=1.3 p90=1.3 min=1.3 max=1.3 sd=0.0
Payment Initiation                               2  n=2 sum=0 mean=0.0 median=0.0 p25=0.0 p75=0.0 p90=0.0 min=0.0 max=0.0 sd=0.0
Closed/Won                                       1  n=1 sum=0 mean=0.1 median=0.1 p25=0.1 p75=0.1 p90=0.1 min=0.1 max=0.1 sd=0.0
(deleted stage 3992480463)                      86  n=86 sum=5 mean=0.1 median=0.0 p25=0.0 p75=0.0 p90=0.1 min=0.0 max=0.8 sd=0.2
(deleted stage 3992480476)                      22  n=22 sum=28 mean=1.3 median=0.9 p25=0.3 p75=2.0 p90=2.8 min=0.0 max=2.9 sd=1.1
(deleted stage 3992480478)                       3  n=3 sum=0 mean=0.0 median=0.0 p25=0.0 p75=0.0 p90=0.0 min=0.0 max=0.0 sd=0.0
(deleted stage 3992480477)                      15  n=15 sum=21 mean=1.4 median=1.9 p25=0.8 p75=2.1 p90=2.1 min=0.0 max=2.1 sd=0.8
(deleted stage 3992480479)                      48  n=48 sum=61 mean=1.3 median=1.0 p25=0.8 p75=1.9 p90=2.0 min=0.0 max=3.0 sd=0.7
(deleted stage 3992480466)                      15  n=15 sum=16 mean=1.1 median=0.9 p25=0.8 p75=1.0 p90=1.6 min=0.8 max=2.0 sd=0.4
Call Attempted (retired)                       289  n=289 sum=1,665 mean=5.8 median=2.3 p25=1.2 p75=9.4 p90=15.1 min=0.0 max=16.3 sd=5.6
Dead/Interested/NoShow                           9  n=9 sum=5 mean=0.6 median=0.0 p25=0.0 p75=0.1 p90=2.3 min=0.0 max=3.2 sd=1.2
Dead/ColdCall/Not Interested                    14  n=14 sum=8 mean=0.6 median=0.0 p25=0.0 p75=0.0 p90=0.6 min=0.0 max=7.2 sd=1.9
Dead/ColdCall/WrongFit                          33  n=33 sum=7 mean=0.2 median=0.0 p25=0.0 p75=0.1 p90=0.3 min=0.0 max=5.0 sd=0.9
Dead/GMeet/Privacy Concerns                      2  n=2 sum=0 mean=0.0 median=0.0 p25=0.0 p75=0.0 p90=0.0 min=0.0 max=0.0 sd=0.0
(deleted stage 3992480472)                       5  n=5 sum=5 mean=1.0 median=0.8 p25=0.8 p75=1.1 p90=1.1 min=0.8 max=1.1 sd=0.2
(deleted stage 3992480474)                       2  n=2 sum=2 mean=1.0 median=1.0 p25=0.9 p75=1.1 p90=1.1 min=0.8 max=1.1 sd=0.2
(deleted stage 3992480468)                       2  n=2 sum=1 mean=0.4 median=0.4 p25=0.2 p75=0.6 p90=0.7 min=0.0 max=0.8 sd=0.6
(deleted stage 3992480470)                       1  n=1 sum=1 mean=0.8 median=0.8 p25=0.8 p75=0.8 p90=0.8 min=0.8 max=0.8 sd=0.0
Dead/GMeet/wrong fit                            14  n=14 sum=43 mean=3.0 median=4.7 p25=0.0 p75=4.7 p90=4.8 min=0.0 max=4.8 sd=2.4
Dead/ResultsReceived/WrongFit-Rejected           1  n=1 sum=0 mean=0.0 median=0.0 p25=0.0 p75=0.0 p90=0.0 min=0.0 max=0.0 sd=0.0
Dead/ColdCall/WrongNumber                        1  n=1 sum=0 mean=0.0 median=0.0 p25=0.0 p75=0.0 p90=0.0 min=0.0 max=0.0 sd=0.0

##############################################################################################################
## 13. STAGE TRANSITION MATRIX (from -> to, human moves)
##############################################################################################################
from                                    to                                            count
Cold Call                               Dead/ColdCall/WrongFit                          338
Cold Call                               No Pickup                                       317
Cold Call                               Call Attempted (retired)                        233
Cold Call                               Dead/ColdCall/WrongNumber                       219
Cold Call                               Interested                                      183
Cold Call                               (deleted stage 3992480463)                       85
Cold Call                               Dead/ColdCall/Not Interested                     79
Interested                              Dead/ColdCall/Not Interested                     32
(create)                                Call Attempted (retired)                         27
Cold Call                               Dead/GMeet/wrong fit                             27
(create)                                (deleted stage 3992480479)                       26
Interested                              Dead/ColdCall/WrongFit                           25
Interested                              GMeet Fixed                                      24
Cold Call                               (deleted stage 3992480479)                       22
GMeet Fixed                             Script Shared                                    21
Cold Call                               GMeet Fixed                                      19
Script Shared                           Dead/ColdCall/WrongFit                           17
Cold Call                               Script Shared                                    17
Call Attempted (retired)                Interested                                       16
Script Shared                           Script Results Received                          16
Dead/ColdCall/WrongFit                  Dead/ColdCall/Not Interested                     15
Interested                              Dead/Interested/NoShow                           14
Interested                              Call Attempted (retired)                         13
Dead/GMeet/wrong fit                    Dead/ColdCall/WrongFit                           13
(create)                                Interested                                       12
Cold Call                               (deleted stage 3992480476)                       12
Call Attempted (retired)                Dead/ColdCall/Not Interested                     12
Interested                              Script Shared                                    11
Interested                              No Pickup                                        11
(create)                                Cold Call                                        10
(create)                                (deleted stage 3992480466)                       10
No Pickup                               Interested                                        9
(create)                                (deleted stage 3992480476)                        8
Cold Call                               (deleted stage 3992480477)                        8
(create)                                (deleted stage 3992480477)                        7
Script Shared                           Dead/ResultsReceived/WrongFit-Rejected            7
Script Results Received                 Commercial Negotiation                            7
Commercial Negotiation                  Deal Contract Signed                              6
No Pickup                               Dead/ColdCall/WrongFit                            6
No Pickup                               Dead/ColdCall/WrongNumber                         6
Dead/ColdCall/Not Interested            Interested                                        5
Data Migration Done                     Closed/Won                                        5
Dead/Interested/NoShow                  Dead/ColdCall/WrongFit                            5
Script Results Received                 Dead/ResultsReceived/WrongFit-Rejected            5
Dead/ColdCall/Not Interested            Dead/ColdCall/WrongFit                            5
No Pickup                               Dead/ColdCall/Not Interested                      5
Call Attempted (retired)                Dead/ColdCall/WrongFit                            4
(create)                                (deleted stage 3992480472)                        4
Script Shared                           Dead/GMeet/wrong fit                              4
GMeet Fixed                             Dead/GMeet/wrong fit                              4
Dead/ColdCall/WrongFit                  Cold Call                                         4
Script Results Received                 Script Shared                                     4
Interested                              Dead/ColdCall/WrongNumber                         4
Dead/ColdCall/WrongFit                  Dead/ColdCall/WrongNumber                         4
(create)                                (deleted stage 3992480478)                        3
Dead/Interested/NoShow                  Dead/ColdCall/Not Interested                      3
Interested                              (deleted stage 3992480466)                        3
Script Shared                           Interested                                        3
Commercial Negotiation                  Dead/Negotiation/Pricing                          3
Script Shared                           Dead/ScriptShared/NoShow                          3
Cold Call                               Script Results Received                           3
Interested                              Dead/ResultsReceived/WrongFit-Rejected            3
Deal Contract Signed                    Data Migration Done                               3
GMeet Fixed                             Dead/Interested/NoShow                            3
Script Shared                           Dead/Interested/NoShow                            3
Deal Contract Signed                    Closed/Won                                        3
Script Shared                           Commercial Negotiation                            3
Cold Call                               Dead/ResultsReceived/WrongFit-Rejected            3
Dead/ColdCall/WrongFit                  Call Attempted (retired)                          3
(create)                                Script Shared                                     3
No Pickup                               GMeet Fixed                                       3
Call Attempted (retired)                (deleted stage 3992480466)                        2
Dead/ColdCall/Not Interested            Call Attempted (retired)                          2
(create)                                (deleted stage 3992480468)                        2
(create)                                GMeet Fixed                                       2
Call Attempted (retired)                (deleted stage 3992480476)                        2
Deal Contract Signed                    Commercial Negotiation                            2
(create)                                Commercial Negotiation                            2
Commercial Negotiation                  Dead/ResultsReceived/WrongFit-Rejected            2
Call Attempted (retired)                GMeet Fixed                                       2
Script Results Received                 Deal Contract Signed                              2
Dead/ColdCall/WrongFit                  Dead/Interested/NoShow                            2
Script Results Received                 Dead/GMeet/wrong fit                              2
Commercial Negotiation                  Data Migration Done                               2
Call Attempted (retired)                Dead/Interested/NoShow                            2
Cold Call                               Dead/Interested/NoShow                            2
(create)                                Script Results Received                           2
Script Shared                           Dead/ColdCall/Not Interested                      2
Call Attempted (retired)                Dead/ColdCall/WrongNumber                         2
GMeet Fixed                             Interested                                        2
(create)                                (deleted stage 3992480463)                        1
Call Attempted (retired)                Dead/GMeet/Privacy Concerns                       1
Dead/GMeet/Privacy Concerns             Dead/ColdCall/WrongFit                            1
Cold Call                               (deleted stage 3992480474)                        1
Cold Call                               (deleted stage 3992480472)                        1
Script Shared                           Dead/Negotiation/Pricing                          1
Call Attempted (retired)                Cold Call                                         1
(create)                                (deleted stage 3992480470)                        1
(create)                                (deleted stage 3992480474)                        1
(create)                                Dead/ColdCall/Not Interested                      1
Deal Contract Signed                    Payment Initiation                                1
Payment Initiation                      Closed/Won                                        1
Dead/GMeet/wrong fit                    Dead/Interested/NoShow                            1
(create)                                Metadata Matched                                  1
Cold Call                               Dead/GMeet/Privacy Concerns                       1
Dead/GMeet/Privacy Concerns             Dead/GMeet/wrong fit                              1
Dead/ColdCall/WrongFit                  Interested                                        1
GMeet Fixed                             Commercial Negotiation                            1
Commercial Negotiation                  Payment Initiation                                1
Payment Initiation                      Dead/ColdCall/WrongFit                            1
Interested                              Dead/GMeet/wrong fit                              1
Script Results Received                 Dead/Negotiation/Pricing                          1
Script Shared                           Dead/GMeet/Privacy Concerns                       1
Dead/ResultsReceived/WrongFit-Rejected  Script Shared                                     1
Dead/ColdCall/WrongNumber               Dead/ColdCall/WrongFit                            1
GMeet Fixed                             Dead/ColdCall/WrongFit                            1
No Pickup                               Script Shared                                     1
Script Results Received                 Dead/ColdCall/WrongFit                            1
Interested                              Cold Call                                         1
GMeet Fixed                             Dead/ColdCall/Not Interested                      1
Dead/ColdCall/Not Interested            Commercial Negotiation                            1
Dead/ColdCall/WrongFit                  Script Shared                                     1
Script Shared                           Deal Contract Signed                              1
Dead/ColdCall/WrongFit                  No Pickup                                         1
(create)                                Deal Contract Signed                              1
Deal Contract Signed                    Script Shared                                     1
Script Shared                           Closed/Won                                        1
GMeet Fixed                             Dead/Negotiation/Pricing                          1

--------------------------------------------------------------------------------------------------------------
13.1 SYSTEM (INTEGRATION/API) transitions
--------------------------------------------------------------------------------------------------------------
from                                    to                                            count
(create)                                Cold Call                                      2041
Cold Call                               Dead/ColdCall/WrongFit                          296
Call Attempted (retired)                No Pickup                                       234
(create)                                Dead/ColdCall/Not Interested                     61
(create)                                Dead/ColdCall/WrongFit                           45
(create)                                Interested                                       26
(create)                                Script Shared                                    20
(create)                                Call Attempted (retired)                         10
(create)                                Script Results Received                           6
Call Attempted (retired)                Dead/ColdCall/WrongNumber                         5
GMeet Fixed                             Interested                                        5
Cold Call                               Cold Call                                         5
Interested                              Script Shared                                     5
Call Attempted (retired)                Interested                                        5
Script Results Received                 Commercial Negotiation                            4
(create)                                GMeet Fixed                                       3
Interested                              Cold Call                                         2
Dead/ColdCall/WrongFit                  Dead/ResultsReceived/WrongFit-Rejected            1
GMeet Fixed                             Script Shared                                     1
Cold Call                               Script Results Received                           1
Script Results Received                 Closed/Won                                        1
Interested                              Call Attempted (retired)                          1
Cold Call                               Interested                                        1
Dead/Interested/NoShow                  Dead/ColdCall/Not Interested                      1
Script Shared                           Deal Contract Signed                              1
Commercial Negotiation                  Dead/ColdCall/WrongFit                            1
Dead/ColdCall/Not Interested            Closed/Won                                        1
Closed/Won                              Script Results Received                           1
Commercial Negotiation                  Interested                                        1
Metadata Matched                        Script Shared                                     1

--------------------------------------------------------------------------------------------------------------
13.2 backward / regressive moves (to a LOWER rank)
--------------------------------------------------------------------------------------------------------------
  count: 49
    Interested                             -> Call Attempted (retired)                14
    Interested                             -> No Pickup                               11
    GMeet Fixed                            -> Interested                               7
    Script Results Received                -> Script Shared                            4
    Script Shared                          -> Interested                               3
    Interested                             -> Cold Call                                3
    Deal Contract Signed                   -> Commercial Negotiation                   2
    Call Attempted (retired)               -> Cold Call                                1
    Closed/Won                             -> Script Results Received                  1
    Commercial Negotiation                 -> Interested                               1
    Metadata Matched                       -> Script Shared                            1
    Deal Contract Signed                   -> Script Shared                            1

##############################################################################################################
## 14. DEATH ANALYSIS
##############################################################################################################
total dead: 1240  (57.92% of all)

--------------------------------------------------------------------------------------------------------------
14.1 by death stage
--------------------------------------------------------------------------------------------------------------
death stage                                      deals  % of dead  % of all  mean depth
Dead/ColdCall/WrongFit                             727     58.63%    33.96%        0.19
Dead/ColdCall/WrongNumber                          239     19.27%    11.16%        0.10
Dead/ColdCall/Not Interested                       199     16.05%     9.29%        2.06
Dead/GMeet/wrong fit                                25      2.02%     1.17%        3.32
Dead/ResultsReceived/WrongFit-Rejected              21      1.69%     0.98%        5.52
Dead/Interested/NoShow                              18      1.45%     0.84%        2.44
Dead/Negotiation/Pricing                             6      0.48%     0.28%        6.00
Dead/ScriptShared/NoShow                             3      0.24%     0.14%        4.33
Dead/Negotiation/Contractual                         1      0.08%     0.05%        6.00
Dead/GMeet/Privacy Concerns                          1      0.08%     0.05%        4.00

--------------------------------------------------------------------------------------------------------------
14.2 deaths grouped by funnel position of the death LABEL
--------------------------------------------------------------------------------------------------------------
  ColdCall               1165    93.95%
  Interested               18     1.45%
  GMeet                    26     2.10%
  ScriptShared              3     0.24%
  ResultsReceived          21     1.69%
  Negotiation               7     0.56%
  other                     0     0.00%

--------------------------------------------------------------------------------------------------------------
14.3 deaths where the deal had actually reached deeper than the death label implies
--------------------------------------------------------------------------------------------------------------
  count: 58 of 1240 (4.7%)
    Dead/ColdCall/WrongFit (actually reached Interested)                                         23
    Dead/ColdCall/WrongFit (actually reached Script Shared)                                      16
    Dead/ColdCall/WrongNumber (actually reached Interested)                                       6
    Dead/Interested/NoShow (actually reached Script Shared)                                       3
    Dead/GMeet/wrong fit (actually reached Script Results Received)                               2
    Dead/ColdCall/WrongFit (actually reached Script Results Received)                             2
    Dead/ColdCall/WrongFit (actually reached Commercial Negotiation)                              1
    Dead/ResultsReceived/WrongFit-Rejected (actually reached Closed/Won)                          1
    Dead/ResultsReceived/WrongFit-Rejected (actually reached Metadata Matched)                    1
    Dead/ColdCall/Not Interested (actually reached Payment Initiation)                            1
    Dead/ColdCall/WrongFit (actually reached GMeet Fixed)                                         1
    Dead/ColdCall/Not Interested (actually reached Script Shared)                                 1

##############################################################################################################
## 15. COHORT ANALYSIS BY CREATION WEEK
##############################################################################################################
cohort           n  >=Int  >=GM  >=SS  won  dead  live  %>=Int   %>=SS   win%  mean depth  mean age
2026-07-13     111     53     6     2    0    70    41  47.75%   1.80%  0.00%        1.34      32.9
2026-07-20     162     55    19    18    4   108    50  33.95%  11.11%  2.47%        1.44      25.8
2026-07-27     409    164    63    54    5   272   132  40.10%  13.20%  1.22%        1.51      18.7
2026-08-03     497    116    40    30    2   282   213  23.34%   6.04%  0.40%        1.03      11.6
2026-08-10     721    106    19     5    0   472   249  14.70%   0.69%  0.00%        0.56       5.5
2026-08-17     241     20     3     1    0    36   205   8.30%   0.41%  0.00%        0.30       0.0

##############################################################################################################
## 16. CUMULATIVE PIPELINE OVER TIME
##############################################################################################################
week          cum leads  cum moves  cum notes  cum won    cum raw LoC    cum t1 LoC  open deals EOW
2026-07-13          111        116          2        0              0             0              41
2026-07-20          273        739        152        0              0             0              91
2026-07-27          682       1480        634        3     14,743,886     6,588,669             216
2026-08-03         1179       2810       1105        9     50,218,587    21,969,428             423
2026-08-10         1900       4544       1834       11     70,112,334    41,863,175             667
2026-08-17         2141       4921       1981       11     70,112,334    41,863,175             872

##############################################################################################################
## 17. LoC / PR ECONOMICS
##############################################################################################################
deal                                    LoC     PRs   LoC/PR  tier1stage                                   source                          created     closed      
FabLead                          20,093,942   7,495    2,681  FalseClosed/Won                              Scraping Algo ( IT services )   2026-07-28  2026-08-05  
Deliqt                           17,525,955  13,793    1,271   TrueClosed/Won                              Linkedin Campaign ( IT Services 2026-08-07  2026-08-10  
IT- Antino                       12,828,951  36,300      353   TrueDead/Negotiation/Pricing                Scraping Algo ( IT services )   2026-07-21  2026-07-28  
WebCodeGenie                     12,064,704  14,486      833   TrueDeal Contract Signed                    Scraping Algo ( IT services )   2026-07-28              
Investmint                        8,155,217   3,529    2,311  FalseClosed/Won                              Tracxn Sheet ( Startups )       2026-07-20  2026-07-30  
Serpent Consulting 2              5,386,248   7,988      674   TrueClosed/Won                              Scraping Algo ( IT services )   2026-07-28  2026-08-05  
Gloify                            4,773,185   6,642      719   TrueClosed/Won                              Scraping Algo ( IT services )   2026-07-22  2026-08-03  
Backspacce Technologies           3,408,665   6,209      549   TrueClosed/Won                              Scraping Algo ( IT services )   2026-07-21  2026-07-28  
Backspace Technologies 2          3,180,004   4,797      663   TrueClosed/Won                              Scraping Algo ( IT services )   2026-07-28  2026-07-30  
Backspace Technologies 3          2,367,792   4,757      498   TrueClosed/Won                              -                               2026-08-07  2026-08-10  
Serpent Consulting 1              2,358,399   3,387      696   TrueClosed/Won                              Scraping Algo ( IT services )   2026-07-21  2026-08-05  
Scaletech                         1,539,267   2,288      673   TrueClosed/Won                              Scraping Algo ( IT services )   2026-07-28  2026-08-05  
Baaz                              1,323,660   1,911      693   TrueClosed/Won                              Tracxn Sheet ( Startups )       2026-07-30  2026-08-05  
Nickelfox                           788,990   2,449      322   TrueDead/Negotiation/Pricing                Private Codebase Tracker sheet  2026-07-21  2026-08-10  
S - Riyalto - 2                     265,857      13   20,451  FalseDead/ResultsReceived/WrongFit-Rejected  Tracxn Sheet ( Startups )       2026-07-21  2026-07-28  
Humalect                            200,000       -        -   NoneDeal Contract Signed                    Tracxn Sheet ( Startups )       2026-07-30              

  all LoC deals   : n=16 sum=96,260,836 mean=6,016,302.2 median=3,294,334.5 p25=1,485,365.2 p75=9,132,588.8 p90=15,177,453.0 min=200,000.0 max=20,093,942.0 sd=6,313,939.2
  all PR counts   : n=15 sum=116,044 mean=7,736.3 median=4,797.0 p25=2,918.0 p75=7,741.5 p90=14,208.8 min=13.0 max=36,300.0 sd=8,892.8
  all ratios      : n=15 sum=33,386 mean=2,225.7 median=692.7 p25=606.0 p75=1,051.7 p90=2,533.0 min=322.2 max=20,450.5 sd=5,087.5
  WON LoC         : n=11 sum=70,112,334 mean=6,373,848.5 median=3,408,665.0 p25=2,363,095.5 p75=6,770,732.5 p90=17,525,955.0 min=1,323,660.0 max=20,093,942.0 sd=6,475,832.4
  WON tier-1 LoC  : n=9 sum=41,863,175 mean=4,651,463.9 median=3,180,004.0 p25=2,358,399.0 p75=4,773,185.0 p90=7,814,189.4 min=1,323,660.0 max=17,525,955.0 sd=5,015,604.9
  totals: all=96,260,836  won=70,112,334  won-tier1=41,863,175

--------------------------------------------------------------------------------------------------------------
17.1 per DISTINCT COMPANY (deals de-duplicated by name root)
--------------------------------------------------------------------------------------------------------------
company                        deals     total LoC     tier1 LoC  deal names
fablead                            1    20,093,942             0  FabLead
deliqt                             1    17,525,955    17,525,955  Deliqt
backspace technologies             3     8,956,461     8,956,461  Backspacce Technologies, Backspace Technologies 2, Backspace Technologies 3
investmint                         1     8,155,217             0  Investmint
serpent consulting                 2     7,744,647     7,744,647  Serpent Consulting 1, Serpent Consulting 2
gloify                             1     4,773,185     4,773,185  Gloify
scaletech                          1     1,539,267     1,539,267  Scaletech
baaz                               1     1,323,660     1,323,660  Baaz

  11 won deals -> 8 distinct companies
  per-company LoC  : n=8 sum=70,112,334 mean=8,764,041.8 median=7,949,932.0 p25=3,964,705.5 p75=11,098,834.5 p90=18,296,351.1 min=1,323,660.0 max=20,093,942.0 sd=6,866,775.2
  per-company t1   : n=6 sum=41,863,175 mean=6,977,195.8 median=6,258,916.0 p25=2,347,746.5 p75=8,653,507.5 p90=13,241,208.0 min=1,323,660.0 max=17,525,955.0 sd=6,036,124.5

--------------------------------------------------------------------------------------------------------------
17.2 LoC by lead source / pipeline / owner
--------------------------------------------------------------------------------------------------------------
  by lead source:
      Scraping Algo ( IT services )                    7 wins    40,739,710    20,645,768 tier1
      Linkedin Campaign ( IT Services )                1 wins    17,525,955    17,525,955 tier1
      Tracxn Sheet ( Startups )                        2 wins     9,478,877     1,323,660 tier1
      (none)                                           1 wins     2,367,792     2,367,792 tier1
  by pipeline:
      Scraped                                         10 wins    52,586,379    24,337,220 tier1
      Campaign                                         1 wins    17,525,955    17,525,955 tier1
  by owner:
      Ishpreet Sood                                    6 wins    50,521,018    30,427,076 tier1
      Shobit Gupta                                     4 wins    18,267,656    10,112,439 tier1
      (none)                                           1 wins     1,323,660     1,323,660 tier1

##############################################################################################################
## 18. LIVE PIPELINE INVENTORY
##############################################################################################################
live deals: 890
stage                             deals   prob    known LoC  mean age  mean idle
Cold Call                           192   0.10            0       0.5        0.5
No Pickup                           533   0.12            0      12.7        8.1
Interested                          119   0.20            0      10.5        8.0
GMeet Fixed                          13   0.40            0      10.3        7.9
Script Shared                        24   0.55            0      15.1        9.1
Script Results Received               2   0.60            0      10.5        3.5
Commercial Negotiation                5   0.60            0      13.0        2.0
Deal Contract Signed                  2   0.85   12,264,704      19.0        5.5

--------------------------------------------------------------------------------------------------------------
18.1 live deals at depth >= GMeet Fixed (the deep pipeline), full list
--------------------------------------------------------------------------------------------------------------
deal                              stage                        depth  age  idle  notes         LoCowner             source
Humalect                          Deal Contract Signed             7   18     0      1     200,000Yuktha Anand      Tracxn Sheet ( Startups )
WebCodeGenie                      Deal Contract Signed             7   20    11      1  12,064,704Shobit Gupta      Scraping Algo ( IT services 
3SC                               Commercial Negotiation           6   18     0      1           0Lamiya Saleem     Outflo Outreach ( Startups )
Phyt.Health                       Commercial Negotiation           6   13     0      2           0Ishpreet Sood     Outflo Outreach ( Startups )
Travanleo Info Solutions India Pr Commercial Negotiation           6    4     0      1           0Yuktha Anand      NASSCOM ( IT Services )
Logicloom                         Commercial Negotiation           6   20     5      2           0Ishpreet Sood     Scraping Algo ( IT services 
Vision Infotech                   Commercial Negotiation           6   10     5      2           0Lamiya Saleem     Scraping Algo ( IT services 
Make Me A Sticker (Alan)          Interested                       6   21    20      1           0Ashish Ranjan     -
Propreturns                       Script Results Received          5   14     0      2           0Lamiya Saleem     Tracxn Sheet ( Startups )
Lakhan Jain                       Script Results Received          5    7     7      0           0Ishpreet Sood     -
Learninga                         Script Shared                    4   12     0      4           0Yuktha Anand      Outflo Outreach ( Startups )
C4Scale                           Script Shared                    4   12     0      2           0Yuktha Anand      Linkedin Campaign ( IT Servi
Uday Tanwar                       Script Shared                    4   10     0      2           0Yuktha Anand      Linkedin Campaign ( IT Servi
Queppelin                         Script Shared                    4    0     0      1           0Yuktha Anand      Scraping Algo ( IT services 
Vah Vah                           Script Shared                    4   18     4      1           0Yuktha Anand      Tracxn Sheet ( Startups )
Credence Digital Health           Script Shared                    4   12     4      1           0Lamiya Saleem     Linkedin Campaign ( IT Servi
Shaligram Infotech                Script Shared                    4   10     4      2           0Yuktha Anand      Scraping Algo ( IT services 
Mayur Patki                       Script Shared                    4   18     5      4           0Yuktha Anand      Outflo Outreach ( Startups )
Orane Consulting Private Limited  Interested                       4   10     5      3           0Lamiya Saleem     Scraping Algo ( IT services 
Techify Solutions Pvt Ltd         Script Shared                    4    6     5      3           0Yuktha Anand      Scraping Algo ( IT services 
Unicode Systems                   Interested                       4   27     6      1           0Ishpreet Sood     Private Codebase Tracker she
Naoki International Technologies  Interested                       4   18     6      2           0Ishpreet Sood     Outflo Outreach ( Startups )
Zimo Technologies Pvt. Ltd. (ZimO Script Shared                    4   12     7      4           0Yuktha Anand      Outflo Outreach ( Startups )
Minaions                          Script Shared                    4   12     7      0           0Ishpreet Sood     Linkedin Campaign ( IT Servi
Nishant Vispute                   Script Shared                    4   12    10      6           0Yuktha Anand      Outflo Outreach ( Startups )
Flashpoint AI                     Script Shared                    4   13    10      5           0Yuktha Anand      Outflo Outreach ( Startups )
Encureit                          Script Shared                    4   20    11      3           0Lamiya Saleem     Private Codebase Tracker she
Vikas Chauhan                     Script Shared                    4   19    11      6           0Yuktha Anand      Outflo Outreach ( Startups )
Zensar                            Script Shared                    4   27    12      1           0Ishpreet Sood     Scraping Algo ( IT services 
Zepto                             Script Shared                    4   18    12      0           0Ishpreet Sood     Outflo Outreach ( Startups )
Brandsmashers Tech                Script Shared                    4   12    12      1           0Ishpreet Sood     Linkedin Campaign ( IT Servi
OpeninApp                         Script Shared                    4   18    14      1           0Ishpreet Sood     Tracxn Sheet ( Startups )
AltWorld                          Script Shared                    4   18    14      0           0Ishpreet Sood     Tracxn Sheet ( Startups )
Vaibhav Tayal                     Script Shared                    4   19    18      3           0Ishpreet Sood     Outflo Outreach ( Startups )
Mayank Chawla                     Script Shared                    4   19    19      2           0Ishpreet Sood     Outflo Outreach ( Startups )
Mehar Kaila                       Script Shared                    4   19    19      2           0Ishpreet Sood     Outflo Outreach ( Startups )
iPixxel Tech Private Limited      Script Shared                    4   27    20      1           0Ishpreet Sood     Scraping Algo ( IT services 
Tart Labs                         GMeet Fixed                      3    4     0      1           0Lamiya Saleem     NASSCOM ( IT Services )
Techno Tackle Software Solutions  GMeet Fixed                      3    3     0      2           0Lamiya Saleem     NASSCOM ( IT Services )
Ayasya Digital Solutions LLP      GMeet Fixed                      3    0     0      2           0Yuktha Anand      NASSCOM ( IT Services )
Infynno Solutions                 GMeet Fixed                      3    0     0      2           0Lamiya Saleem     Founder Search ( IT Services
Perigeon Software Private Limited GMeet Fixed                      3    4     3      2           0Lamiya Saleem     NASSCOM ( IT Services )
WebGuruz Technologies Pvt Ltd     GMeet Fixed                      3    6     5      4           0Lamiya Saleem     Scraping Algo ( IT services 
TekWissen India                   Interested                       3    6     6      2           0Yuktha Anand      Scraping Algo ( IT services 
valantic India                    GMeet Fixed                      3    6     6      2           0Yuktha Anand      Scraping Algo ( IT services 
Northcorp Software                GMeet Fixed                      3   10    10      3           0Yuktha Anand      Scraping Algo ( IT services 
TE Connectivity                   GMeet Fixed                      3   18    11      2           0Lamiya Saleem     Outflo Outreach ( Startups )
Akshay  Waghmare                  GMeet Fixed                      3   20    12      4           0Lamiya Saleem     Outflo Outreach ( Startups )
Aarshay Jain                      GMeet Fixed                      3   19    12      2           0Lamiya Saleem     Outflo Outreach ( Startups )
Somesh Chaturvedi                 GMeet Fixed                      3   19    19      1           0-                 Outflo Outreach ( Startups )
Mobibeans Solution Pvt Ltd.       Interested                       3   21    20      2           0-                 Tracxn Sheet ( Startups )
Kaarva                            Interested                       3   31    25      0           0Ishpreet Sood     Tracxn Sheet ( Startups )
Resha Mandi                       Interested                       3   31    25      0           0Ishpreet Sood     Tracxn Sheet ( Startups )
Samniya Digital Pvt. Ltd.         GMeet Fixed                      3   25    25      0           0-                 Scraping Algo ( IT services 

##############################################################################################################
## 19. NOTES ANALYSIS
##############################################################################################################
total notes: 1981  |  deals with >=1 note: 1355
  notes per deal (all deals)  : n=2141 sum=1,713 mean=0.8 median=1.0 p25=0.0 p75=1.0 p90=2.0 min=0.0 max=6.0 sd=0.8
  notes per deal (>=1 note)   : n=1355 sum=1,713 mean=1.3 median=1.0 p25=1.0 p75=1.0 p90=2.0 min=1.0 max=6.0 sd=0.6

--------------------------------------------------------------------------------------------------------------
19.1 notes by owner
--------------------------------------------------------------------------------------------------------------
  (none)                            761
  Yuktha Anand                      583
  Lamiya Saleem                     582
  Shobit Gupta                       27
  Ishpreet Sood                      23
  Bhanu Enamala                       3
  Ashish Ranjan                       2

--------------------------------------------------------------------------------------------------------------
19.2 notes by week
--------------------------------------------------------------------------------------------------------------
  2026-07-13          2
  2026-07-20        150
  2026-07-27        482
  2026-08-03        471
  2026-08-10        729
  2026-08-17        147

--------------------------------------------------------------------------------------------------------------
19.3 keyword frequency in note bodies
--------------------------------------------------------------------------------------------------------------
  wrong number                138    6.97%
  wrong fit                    55    2.78%
  not interested               58    2.93%
  did not pick                152    7.67%
  call back                    45    2.27%
  callback                      1    0.05%
  follow up                    11    0.56%
  follow-up                    64    3.23%
  whatsapp                     26    1.31%
  wa                           45    2.27%
  mail                        148    7.47%
  meeting                      30    1.51%
  gmeet                        29    1.46%
  script                       83    4.19%
  shared                       71    3.58%
  interested                  115    5.81%
  busy                         32    1.62%
  switched off                 14    0.71%
  out of service               13    0.66%
  wrong poc                    27    1.36%
  proposal                      4    0.20%
  codebase                    167    8.43%
  repo                          9    0.45%
  pr                          278   14.03%
  demo                          1    0.05%
  legal                         2    0.10%
  agreement                     3    0.15%
  migration                    58    2.93%
  deadpool                     50    2.52%

--------------------------------------------------------------------------------------------------------------
19.4 note length
--------------------------------------------------------------------------------------------------------------
  chars: n=1981 sum=199,012 mean=100.5 median=25.0 p25=12.0 p75=98.0 p90=210.0 min=1.0 max=1,232.0 sd=206.6

##############################################################################################################
## 20. TASKS ANALYSIS
##############################################################################################################
total tasks: 288
  by owner:
      Lamiya Saleem                                115
      (none)                                        88
      Shobit Gupta                                  27
      Yuktha Anand                                  27
      Ishpreet Sood                                 26
      Ashish Ranjan                                  4
      Bhanu Enamala                                  1
  by status:
      NOT_STARTED                                  224
      COMPLETED                                     63
      WAITING                                        1
  by type:
      TODO                                         141
      CALL                                         140
      EMAIL                                          7
  by week created:
      2026-08-03                                    89
      2026-07-27                                    68
      2026-07-20                                    63
      2026-08-10                                    59
      2026-08-17                                     7
      2026-07-13                                     2

##############################################################################################################
## 21. CONTACTS & COMPANIES
##############################################################################################################
contacts: 3186   companies: 2635
  with phone    : 2849
  with mobile   : 1846
  with email    : 2556
  with linkedin : 3009
  by create week:
      2026-07-13        203
      2026-07-20        776
      2026-07-27        745
      2026-08-03        566
      2026-08-10        720
      2026-08-17        176
  companies by country:
      (none)                             1983
      India                               636
      United States,
 India                 9
      India,
 India                         2
      United States                         1
      United Kingdom,
 United States        1
      Canada,
 India                        1
      United Kingdom,
 India                1
      Singapore,
 India                     1

##############################################################################################################
## 22. PER-DEAL APPENDIX — every deal that got past Cold Call (depth >= 1)
##############################################################################################################
columns: deal | source | owner | pipeline | depth | current stage | created | age | idle | moves | notes | LoC | full stage path with dates
total: 1057 deals

[11] Baaz
     src=Tracxn Sheet ( Startups ) | owner=- | pipe=Scraped | stage=Closed/Won
     created=2026-07-30 age=18d idle=12d moves=5(h5) notes=0 tasks=0 LoC=1323660.0 PR=1911.0 ratio=693
     path: Script Shared(07-30H) > Script Results Received(07-31H) > Commercial Negotiation(08-02H) > Deal Contract Signed(08-03H) > Closed/Won(08-05H)

[11] Backspacce Technologies
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Closed/Won
     created=2026-07-21 age=27d idle=20d moves=3(h1) notes=1 tasks=1 LoC=3408665.0 PR=6209.0 ratio=549
     path: (deleted stage 3992480474)(07-21H) > Script Results Received(07-22S) > Closed/Won(07-28S)

[11] Backspace Technologies 2
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Closed/Won
     created=2026-07-28 age=20d idle=18d moves=4(h3) notes=1 tasks=1 LoC=3180004.0 PR=4797.0 ratio=663
     path: Script Shared(07-28S) > Commercial Negotiation(07-28H) > Data Migration Done(07-29H) > Closed/Won(07-30H)

[11] Backspace Technologies 3
     src=- | owner=Shobit Gupta | pipe=Scraped | stage=Closed/Won
     created=2026-08-07 age=10d idle=7d moves=3(h3) notes=0 tasks=0 LoC=2367792.0 PR=4757.0 ratio=498
     path: Deal Contract Signed(08-07H) > Script Shared(08-07H) > Closed/Won(08-10H)

[11] Deliqt
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Closed/Won
     created=2026-08-07 age=10d idle=7d moves=4(h3) notes=1 tasks=0 LoC=17525955.0 PR=13793.0 ratio=1271
     path: Cold Call(08-07S) > Script Shared(08-07H) > Deal Contract Signed(08-07H) > Closed/Won(08-10H)

[11] FabLead
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Closed/Won
     created=2026-07-28 age=20d idle=12d moves=5(h4) notes=1 tasks=0 LoC=20093942.0 PR=7495.0 ratio=2681
     path: Script Shared(07-28S) > Script Results Received(08-01H) > Commercial Negotiation(08-04H) > Deal Contract Signed(08-05H) > Closed/Won(08-05H)

[11] Gloify
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Closed/Won
     created=2026-07-22 age=26d idle=14d moves=8(h7) notes=2 tasks=3 LoC=4773185.0 PR=6642.0 ratio=719
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > GMeet Fixed(07-23H) > Script Shared(07-27H) > Script Results Received(07-29H) > Deal Contract Signed(07-30H) > Payment Initiation(08-03H) > Closed/Won(08-03H)

[11] Investmint
     src=Tracxn Sheet ( Startups ) | owner=Shobit Gupta | pipe=Scraped | stage=Closed/Won
     created=2026-07-20 age=28d idle=18d moves=7(h3) notes=2 tasks=2 LoC=8155217.0 PR=3529.0 ratio=2311
     path: Cold Call(07-20S) > Cold Call(07-23S) > Script Results Received(07-28S) > Commercial Negotiation(07-28S) > Deal Contract Signed(07-29H) > Data Migration Done(07-29H) > Closed/Won(07-30H)

[11] S - Riyalto - 2
     src=Tracxn Sheet ( Startups ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-21 age=27d idle=20d moves=5(h2) notes=1 tasks=1 LoC=265857.0 PR=13.0 ratio=20451
     path: Dead/ColdCall/Not Interested(07-21H) > Closed/Won(07-28S) > Script Results Received(07-28S) > Commercial Negotiation(07-28S) > Dead/ResultsReceived/WrongFit-Rejected(07-28H)

[11] Scaletech
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Closed/Won
     created=2026-07-28 age=20d idle=12d moves=7(h6) notes=2 tasks=0 LoC=1539267.0 PR=2288.0 ratio=673
     path: Script Shared(07-28S) > Script Results Received(07-30H) > Script Shared(07-31H) > Script Results Received(07-31H) > Commercial Negotiation(08-02H) > Data Migration Done(08-03H) > Closed/Won(08-05H)

[11] Serpent Consulting 1
     src=Scraping Algo ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Closed/Won
     created=2026-07-21 age=27d idle=12d moves=7(h6) notes=2 tasks=2 LoC=2358399.0 PR=3387.0 ratio=696
     path: Cold Call(07-21H) > Script Shared(07-21H) > Deal Contract Signed(07-28S) > Commercial Negotiation(07-30H) > Deal Contract Signed(08-01H) > Data Migration Done(08-03H) > Closed/Won(08-05H)

[11] Serpent Consulting 2
     src=Scraping Algo ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Closed/Won
     created=2026-07-28 age=20d idle=12d moves=5(h3) notes=2 tasks=1 LoC=5386248.0 PR=7988.0 ratio=674
     path: Script Results Received(07-28S) > Commercial Negotiation(07-28S) > Deal Contract Signed(07-31H) > Data Migration Done(08-03H) > Closed/Won(08-05H)

[10] DataCrops Software Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=6(h5) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > GMeet Fixed(07-28H) > Commercial Negotiation(07-28H) > Payment Initiation(07-28H) > Dead/ColdCall/WrongFit(07-28H) > Dead/ColdCall/Not Interested(07-28H)

[9] TechWeb Solutions
     src=- | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-27 age=21d idle=19d moves=3(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Metadata Matched(07-27H) > Script Shared(07-28S) > Dead/ResultsReceived/WrongFit-Rejected(07-29H)

[7] Humalect
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Deal Contract Signed
     created=2026-07-30 age=18d idle=0d moves=4(h3) notes=1 tasks=0 LoC=200000.0 PR=- ratio=-
     path: Cold Call(07-30S) > Script Shared(08-13H) > Script Results Received(08-14H) > Deal Contract Signed(08-17H)

[7] WebCodeGenie
     src=Scraping Algo ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Deal Contract Signed
     created=2026-07-28 age=20d idle=11d moves=3(h2) notes=1 tasks=1 LoC=12064704.0 PR=14486.0 ratio=833
     path: Deal Contract Signed(07-28S) > Commercial Negotiation(07-28H) > Deal Contract Signed(08-06H)

[6] 3SC 
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Commercial Negotiation
     created=2026-07-30 age=18d idle=0d moves=5(h4) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-06H) > Script Shared(08-06H) > Script Results Received(08-07H) > Commercial Negotiation(08-17H)

[6] 9stacks
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/Negotiation/Pricing
     created=2026-08-03 age=14d idle=13d moves=6(h5) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > GMeet Fixed(08-03H) > Dead/ColdCall/Not Interested(08-03H) > Commercial Negotiation(08-03H) > Dead/Negotiation/Pricing(08-04H)

[6] Brilworks Software
     src=Private Codebase Tracker sheet ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/Negotiation/Contractual
     created=2026-07-28 age=20d idle=20d moves=1(h0) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Dead/Negotiation/Contractual(07-28S)

[6] IT - Reckonsys
     src=Scraping Algo ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/Negotiation/Pricing
     created=2026-07-21 age=27d idle=19d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: (deleted stage 3992480472)(07-21H) > Script Shared(07-22S) > Dead/Negotiation/Pricing(07-29H)

[6] IT- Antino
     src=Scraping Algo ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/Negotiation/Pricing
     created=2026-07-21 age=27d idle=20d moves=5(h3) notes=1 tasks=1 LoC=12828951.0 PR=36300.0 ratio=353
     path: Cold Call(07-21H) > (deleted stage 3992480474)(07-21H) > Script Results Received(07-22S) > Commercial Negotiation(07-28S) > Dead/Negotiation/Pricing(07-28H)

[6] Logicloom
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Commercial Negotiation
     created=2026-07-28 age=20d idle=5d moves=7(h6) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Script Shared(07-28S) > Script Results Received(07-29H) > Dead/ResultsReceived/WrongFit-Rejected(07-30H) > Script Shared(07-30H) > Script Results Received(07-31H) > Script Shared(08-04H) > Commercial Negotiation(08-12H)

[6] Make Me A Sticker (Alan)
     src=- | owner=Ashish Ranjan | pipe=Campaign | stage=Interested
     created=2026-07-27 age=21d idle=20d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Commercial Negotiation(07-27H) > Interested(07-28S)

[6] Nickelfox
     src=Private Codebase Tracker sheet ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/Negotiation/Pricing
     created=2026-07-21 age=27d idle=7d moves=4(h4) notes=2 tasks=2 LoC=788990.0 PR=2449.0 ratio=322
     path: Cold Call(07-21H) > Script Results Received(07-21H) > Commercial Negotiation(07-28H) > Dead/Negotiation/Pricing(08-10H)

[6] Phyt.Health
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Commercial Negotiation
     created=2026-08-04 age=13d idle=0d moves=6(h5) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-04H) > GMeet Fixed(08-06H) > Script Shared(08-10H) > Script Results Received(08-17H) > Commercial Negotiation(08-17H)

[6] QualeInfoTech
     src=Scraping Algo ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/Negotiation/Pricing
     created=2026-07-28 age=20d idle=17d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Script Shared(07-28S) > Script Results Received(07-31H) > Dead/Negotiation/Pricing(07-31H)

[6] Schrout Software
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-28 age=20d idle=14d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Commercial Negotiation(07-28S) > Dead/ResultsReceived/WrongFit-Rejected(08-03H)

[6] Tarun Anand
     src=Linkedin Campaign ( IT Services ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/Negotiation/Pricing
     created=2026-08-10 age=7d idle=0d moves=4(h3) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-10S) > No Pickup(08-13H) > GMeet Fixed(08-13H) > Dead/Negotiation/Pricing(08-17H)

[6] TechMonkey
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-07-21 age=27d idle=20d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Commercial Negotiation(07-21H) > Dead/ColdCall/WrongFit(07-28S)

[6] Travanleo Info Solutions India Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Commercial Negotiation
     created=2026-08-13 age=4d idle=0d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Script Shared(08-13H) > Commercial Negotiation(08-17H)

[6] Vision Infotech
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Commercial Negotiation
     created=2026-08-07 age=10d idle=5d moves=6(h5) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-10H) > GMeet Fixed(08-11H) > Script Shared(08-11H) > Script Results Received(08-12H) > Commercial Negotiation(08-12H)

[5]  A360PL
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-21 age=27d idle=0d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: GMeet Fixed(07-21H) > Script Shared(07-28S) > Dead/ResultsReceived/WrongFit-Rejected(08-17H)

[5] Aditya Ganguli
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-28 age=20d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Script Shared(07-28S) > Dead/ResultsReceived/WrongFit-Rejected(08-10H)

[5] Baja
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-17 age=31d idle=14d moves=5(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-17S) > Interested(07-21H) > GMeet Fixed(07-21H) > Interested(07-23S) > Dead/ResultsReceived/WrongFit-Rejected(08-03H)

[5] ClanConnect
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-30 age=18d idle=14d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ResultsReceived/WrongFit-Rejected(08-03H)

[5] Codeground
     src=Tracxn Sheet ( Startups ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-28 age=20d idle=12d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Script Shared(07-28S) > Dead/ResultsReceived/WrongFit-Rejected(08-05H)

[5] Crio.Do
     src=Tracxn Sheet ( Startups ) | owner=Ashish Ranjan | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-07-28 age=20d idle=13d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Script Results Received(07-28S) > Dead/GMeet/wrong fit(08-04H)

[5] Cruzata
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-21 age=27d idle=20d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: (deleted stage 3992480479)(07-21H) > Dead/ColdCall/WrongFit(07-23S) > Dead/ResultsReceived/WrongFit-Rejected(07-28S)

[5] Enaviya
     src=Scraping Algo ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-28 age=20d idle=20d moves=1(h0) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Dead/ResultsReceived/WrongFit-Rejected(07-28S)

[5] Geekster
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-30 age=18d idle=14d moves=3(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Script Results Received(08-03H) > Dead/ResultsReceived/WrongFit-Rejected(08-03H)

[5] H3 Mart
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-30 age=18d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ResultsReceived/WrongFit-Rejected(08-14H)

[5] Kylient Software Solutions
     src=Private Codebase Tracker sheet ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-21 age=27d idle=13d moves=4(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: (deleted stage 3992480470)(07-21H) > GMeet Fixed(07-22S) > Interested(07-28S) > Dead/ResultsReceived/WrongFit-Rejected(08-04H)

[5] Lakhan Jain
     src=- | owner=Ishpreet Sood | pipe=Campaign | stage=Script Results Received
     created=2026-08-10 age=7d idle=7d moves=1(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Script Results Received(08-10H)

[5] Mayank Sheoran
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-29 age=19d idle=10d moves=5(h4) notes=4 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Interested(08-05H) > Script Shared(08-05H) > Script Results Received(08-07H) > Dead/ResultsReceived/WrongFit-Rejected(08-07H)

[5] OpenCubicles Technologies Pvt Ltd
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-08-06 age=11d idle=7d moves=4(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-06S) > Dead/ColdCall/WrongFit(08-06H) > Script Shared(08-06H) > Dead/ResultsReceived/WrongFit-Rejected(08-10H)

[5] Procuzy - New Deal
     src=- | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-01 age=16d idle=12d moves=2(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Script Results Received(08-01H) > Dead/ColdCall/WrongFit(08-05H)

[5] Propreturns
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Script Results Received
     created=2026-08-03 age=14d idle=0d moves=5(h4) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Interested(08-03H) > GMeet Fixed(08-03H) > Script Shared(08-17H) > Script Results Received(08-17H)

[5] QuadB Tech
     src=Scraping Algo ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/ScriptShared/NoShow
     created=2026-07-28 age=20d idle=6d moves=3(h2) notes=1 tasks=2 LoC=- PR=- ratio=-
     path: Script Results Received(07-28S) > Script Shared(07-28H) > Dead/ScriptShared/NoShow(08-11H)

[5] Signimus Technologies: Hiring PHP, MERN, Java, DotNet and other Dev
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-08-11 age=6d idle=0d moves=4(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > GMeet Fixed(08-11H) > Script Shared(08-12H) > Dead/ResultsReceived/WrongFit-Rejected(08-17H)

[5] Skill Lync
     src=Tracxn Sheet ( Startups ) | owner=Ashish Ranjan | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-07-28 age=20d idle=13d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Script Results Received(07-28S) > Dead/GMeet/wrong fit(08-04H)

[5] Stoa
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-30 age=18d idle=14d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-03H) > Dead/ResultsReceived/WrongFit-Rejected(08-03H)

[5] Tech Web
     src=Scraping Algo ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-28 age=20d idle=18d moves=3(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Script Shared(07-28S) > Script Results Received(07-29H) > Dead/ResultsReceived/WrongFit-Rejected(07-30H)

[5] Two Circles
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-30 age=18d idle=12d moves=3(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Script Results Received(08-01H) > Dead/ResultsReceived/WrongFit-Rejected(08-05H)

[5] Vave Microtech
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-07-29 age=19d idle=7d moves=5(h4) notes=3 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Script Shared(07-29H) > Script Results Received(08-06H) > Script Shared(08-06H) > Dead/ColdCall/WrongFit(08-10H)

[5] Velumani Selvaraj
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-08-06 age=11d idle=5d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-06S) > Script Shared(08-10H) > Dead/ResultsReceived/WrongFit-Rejected(08-12H)

[5] Zeda
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ResultsReceived/WrongFit-Rejected
     created=2026-07-30 age=18d idle=14d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ResultsReceived/WrongFit-Rejected(08-03H)

[4] Aadarsh Gupta
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-07-29 age=19d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Script Shared(07-29S) > Dead/ColdCall/WrongFit(08-10H)

[4] Affinity Assurance
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-08-05 age=12d idle=6d moves=4(h3) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > GMeet Fixed(08-05H) > Script Shared(08-10H) > Dead/ColdCall/WrongFit(08-11H)

[4] AltWorld
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Script Shared
     created=2026-07-30 age=18d idle=14d moves=3(h2) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-03H) > Script Shared(08-03H)

[4] Anoop N
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-07-29 age=19d idle=7d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Script Shared(07-29H) > Dead/ColdCall/WrongFit(08-10H)

[4] Athmin Technologies
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ScriptShared/NoShow
     created=2026-07-15 age=33d idle=6d moves=8(h6) notes=2 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Interested(07-20H) > Call Attempted (retired)(07-20H) > (deleted stage 3992480466)(07-20H) > Interested(07-22S) > Script Shared(07-27H) > Dead/ScriptShared/NoShow(08-11H)

[4] Bloom CS
     src=Scraping Algo ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Interested(07-28S) > Script Shared(07-28S) > Dead/Interested/NoShow(08-05H)

[4] Brandsmashers Tech
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Script Shared
     created=2026-08-05 age=12d idle=12d moves=3(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > GMeet Fixed(08-05H) > Script Shared(08-05H)

[4] C4Scale
     src=Linkedin Campaign ( IT Services ) | owner=Yuktha Anand | pipe=Campaign | stage=Script Shared
     created=2026-08-05 age=12d idle=0d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > GMeet Fixed(08-17H) > Script Shared(08-17H)

[4] Cloudberry
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-07-21 age=27d idle=12d moves=3(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: (deleted stage 3992480472)(07-21H) > Script Shared(07-22S) > Dead/ColdCall/WrongFit(08-05H)

[4] Cognizant
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-08-05 age=12d idle=7d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > Script Shared(08-05H) > Dead/ColdCall/WrongFit(08-10H)

[4] Compose
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-08-04 age=13d idle=7d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Script Shared(08-05H) > Dead/ColdCall/WrongFit(08-10H)

[4] Credence Digital Health
     src=Linkedin Campaign ( IT Services ) | owner=Lamiya Saleem | pipe=Campaign | stage=Script Shared
     created=2026-08-05 age=12d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > Script Shared(08-13H)

[4] Doomshell
     src=Private Codebase Tracker sheet ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Interested(07-28S) > Script Shared(07-28S) > Dead/Interested/NoShow(08-05H)

[4] EasyReplenish
     src=- | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-03 age=14d idle=6d moves=2(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Script Shared(08-03H) > Dead/ColdCall/WrongFit(08-11H)

[4] Encureit
     src=Private Codebase Tracker sheet ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Script Shared
     created=2026-07-28 age=20d idle=11d moves=4(h2) notes=3 tasks=3 LoC=- PR=- ratio=-
     path: Interested(07-28S) > Script Shared(07-28S) > Interested(08-05H) > Script Shared(08-06H)

[4] Finantic AI
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-07-29 age=19d idle=6d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Script Shared(07-29S) > Dead/ColdCall/WrongFit(08-11H)

[4] Flashpoint AI
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Script Shared
     created=2026-08-04 age=13d idle=10d moves=4(h3) notes=5 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-05H) > GMeet Fixed(08-06H) > Script Shared(08-07H)

[4] Fraazo
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ScriptShared/NoShow
     created=2026-08-04 age=13d idle=0d moves=4(h3) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-04H) > Script Shared(08-04H) > Dead/ScriptShared/NoShow(08-17H)

[4] Koinex
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-04 age=13d idle=6d moves=4(h3) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-04H) > Script Shared(08-04H) > Dead/ColdCall/Not Interested(08-11H)

[4] Learninga
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Script Shared
     created=2026-08-05 age=12d idle=0d moves=4(h3) notes=4 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > Interested(08-05H) > GMeet Fixed(08-05H) > Script Shared(08-17H)

[4] Makemysticker
     src=- | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-08-03 age=14d idle=7d moves=2(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Script Shared(08-03H) > Dead/ColdCall/WrongFit(08-10H)

[4] MatchLog Solutions Pvt. Ltd.
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/GMeet/wrong fit
     created=2026-08-04 age=13d idle=6d moves=5(h4) notes=3 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-04H) > GMeet Fixed(08-05H) > Script Shared(08-06H) > Dead/GMeet/wrong fit(08-11H)

[4] Mayank Chawla
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Script Shared
     created=2026-07-29 age=19d idle=19d moves=2(h1) notes=2 tasks=2 LoC=- PR=- ratio=-
     path: Interested(07-29S) > Script Shared(07-29H)

[4] Mayur Patki
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Script Shared
     created=2026-07-30 age=18d idle=5d moves=7(h5) notes=4 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-05H) > Call Attempted (retired)(08-05H) > No Pickup(08-05S) > Interested(08-06H) > GMeet Fixed(08-06H) > Script Shared(08-12H)

[4] Mebelkart
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-08-04 age=13d idle=4d moves=4(h3) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-04H) > Script Shared(08-04H) > Dead/GMeet/wrong fit(08-13H)

[4] Mehar Kaila
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Script Shared
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Script Shared(07-29S)

[4] Minaions
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Script Shared
     created=2026-08-05 age=12d idle=7d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > Script Shared(08-10H)

[4] NMG
     src=Private Codebase Tracker sheet ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-07-21 age=27d idle=12d moves=4(h3) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-21H) > (deleted stage 3992480472)(07-21H) > Script Shared(07-22S) > Dead/GMeet/wrong fit(08-05H)

[4] Naoki International Technologies (P) Limited
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Interested
     created=2026-07-30 age=18d idle=6d moves=5(h4) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-05H) > GMeet Fixed(08-05H) > Script Shared(08-05H) > Interested(08-11H)

[4] Nishant Vispute
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Script Shared
     created=2026-08-05 age=12d idle=10d moves=4(h3) notes=6 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > Interested(08-05H) > GMeet Fixed(08-05H) > Script Shared(08-07H)

[4] OpeninApp
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Script Shared
     created=2026-07-30 age=18d idle=14d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Script Shared(08-03H)

[4] Orane Consulting Private Limited
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-07 age=10d idle=5d moves=6(h5) notes=3 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-10H) > GMeet Fixed(08-11H) > Script Shared(08-12H) > Dead/ColdCall/Not Interested(08-12H) > Interested(08-12H)

[4] Parag Sinha
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/GMeet/Privacy Concerns
     created=2026-07-29 age=19d idle=16d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Script Shared(07-29S) > Dead/GMeet/Privacy Concerns(08-01H)

[4] Paras Nigam
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-07-29 age=19d idle=7d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Script Shared(07-29H) > Dead/ColdCall/WrongFit(08-10H)

[4] Queppelin
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Script Shared
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Script Shared(08-17H)

[4] Religent Systems
     src=Private Codebase Tracker sheet ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-07-28 age=20d idle=20d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Interested(07-28S) > Script Shared(07-28S) > Dead/GMeet/wrong fit(07-28H)

[4] SRV Technology
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-08-06 age=11d idle=0d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-06S) > Script Shared(08-07H) > Dead/ColdCall/WrongFit(08-17H)

[4] SS Enterprises
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Dead/Interested/NoShow
     created=2026-07-30 age=18d idle=4d moves=3(h2) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Script Shared(08-06H) > Dead/Interested/NoShow(08-13H)

[4] Shaligram Infotech
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Script Shared
     created=2026-08-07 age=10d idle=4d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > GMeet Fixed(08-10H) > Script Shared(08-13H)

[4] Techify Solutions Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Script Shared
     created=2026-08-11 age=6d idle=5d moves=4(h3) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H) > GMeet Fixed(08-12H) > Script Shared(08-12H)

[4] Tejas Kadam
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-07-29 age=19d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Script Shared(07-29S) > Dead/ColdCall/WrongFit(08-10H)

[4] Tensor Thoughts
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-07-28 age=20d idle=17d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Script Shared(07-28S) > Dead/ColdCall/WrongFit(07-31H)

[4] ThoughtWin
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-07 age=10d idle=5d moves=4(h3) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-10H) > Script Shared(08-10H) > Dead/ColdCall/WrongFit(08-12H)

[4] Uday Tanwar
     src=Linkedin Campaign ( IT Services ) | owner=Yuktha Anand | pipe=Campaign | stage=Script Shared
     created=2026-08-07 age=10d idle=0d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > GMeet Fixed(08-14H) > Script Shared(08-17H)

[4] Ultrafly Solutions
     src=Private Codebase Tracker sheet ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-07-21 age=27d idle=12d moves=3(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: (deleted stage 3992480472)(07-21H) > Script Shared(07-22S) > Dead/ColdCall/WrongFit(08-05H)

[4] Unicode Systems
     src=Private Codebase Tracker sheet ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Interested
     created=2026-07-21 age=27d idle=6d moves=5(h4) notes=1 tasks=2 LoC=- PR=- ratio=-
     path: (deleted stage 3992480472)(07-21H) > Script Shared(07-22S) > Interested(08-11H) > Dead/ColdCall/Not Interested(08-11H) > Interested(08-11H)

[4] Vah Vah
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Script Shared
     created=2026-07-30 age=18d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Script Shared(08-13H)

[4] Vaibhav Tayal
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Script Shared
     created=2026-07-29 age=19d idle=18d moves=2(h1) notes=3 tasks=2 LoC=- PR=- ratio=-
     path: GMeet Fixed(07-29S) > Script Shared(07-30H)

[4] Varun Nagda
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-07-29 age=19d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Script Shared(07-29S) > Dead/ColdCall/WrongFit(08-10H)

[4] Vikas Chauhan
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Script Shared
     created=2026-07-29 age=19d idle=11d moves=4(h3) notes=6 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Interested(08-05H) > GMeet Fixed(08-05H) > Script Shared(08-06H)

[4] Zensar
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Script Shared
     created=2026-07-21 age=27d idle=12d moves=3(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: (deleted stage 3992480468)(07-21H) > Interested(07-22S) > Script Shared(08-05H)

[4] Zepto
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Script Shared
     created=2026-07-30 age=18d idle=12d moves=3(h2) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-05H) > Script Shared(08-05H)

[4] Zimo Technologies Pvt. Ltd. (ZimO.One)
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Script Shared
     created=2026-08-05 age=12d idle=7d moves=4(h3) notes=4 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > Interested(08-05H) > GMeet Fixed(08-05H) > Script Shared(08-10H)

[4] iPixxel Tech Private Limited
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=Script Shared
     created=2026-07-21 age=27d idle=20d moves=4(h2) notes=1 tasks=3 LoC=- PR=- ratio=-
     path: (deleted stage 3992480468)(07-21H) > (deleted stage 3992480466)(07-21H) > Interested(07-22S) > Script Shared(07-28S)

[3] Aarshay Jain
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=GMeet Fixed
     created=2026-07-29 age=19d idle=12d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Interested(08-05H) > GMeet Fixed(08-05H)

[3] Adv. Parikshet Kadian
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/GMeet/wrong fit
     created=2026-08-10 age=7d idle=7d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-10S) > Dead/GMeet/wrong fit(08-10H)

[3] Akshay  Waghmare
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=GMeet Fixed
     created=2026-07-28 age=20d idle=12d moves=3(h2) notes=4 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Interested(08-05H) > GMeet Fixed(08-05H)

[3] Alan (YC US connect)
     src=Scraping Algo ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-07-28 age=20d idle=13d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Interested(07-28S) > Dead/GMeet/wrong fit(08-04H)

[3] Assystant
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-07-15 age=33d idle=13d moves=5(h4) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Call Attempted (retired)(07-20H) > Interested(07-20H) > GMeet Fixed(07-29H) > Dead/GMeet/wrong fit(08-04H)

[3] Ayasya Digital Solutions LLP
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=GMeet Fixed
     created=2026-08-17 age=0d idle=0d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Interested(08-17H) > GMeet Fixed(08-17H)

[3] Charles D'cunha
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/GMeet/wrong fit
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/GMeet/wrong fit(08-10H)

[3] Crib
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-07-30 age=18d idle=13d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/GMeet/wrong fit(08-04H)

[3] Gitesh Kund
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/GMeet/wrong fit
     created=2026-08-04 age=13d idle=13d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Dead/GMeet/wrong fit(08-04H)

[3] Infintus
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-07-30 age=18d idle=13d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/GMeet/wrong fit(08-04H)

[3] Infynno Solutions
     src=Founder Search ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=GMeet Fixed
     created=2026-08-17 age=0d idle=0d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Interested(08-17H) > GMeet Fixed(08-17H)

[3] Ishita Gangwar
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/GMeet/wrong fit
     created=2026-08-10 age=7d idle=7d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-10S) > Dead/GMeet/wrong fit(08-10H)

[3] Kaarva
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Interested
     created=2026-07-17 age=31d idle=25d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-17S) > GMeet Fixed(07-21H) > Interested(07-23S)

[3] KeyValue Software Systems
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-08-03 age=14d idle=13d moves=4(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Interested(08-03H) > GMeet Fixed(08-04H) > Dead/Interested/NoShow(08-04H)

[3] Khushbu Dhiman
     src=Linkedin Campaign ( IT Services ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/GMeet/wrong fit
     created=2026-08-07 age=10d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/GMeet/wrong fit(08-13H)

[3] KlyONIX Tech
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-07-30 age=18d idle=7d moves=3(h2) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > GMeet Fixed(08-06H) > Dead/ColdCall/WrongFit(08-10H)

[3] Kudzu Infotech
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-08-07 age=10d idle=7d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > GMeet Fixed(08-07H) > Dead/GMeet/wrong fit(08-10H)

[3] LiveRamp
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Dead/Interested/NoShow
     created=2026-08-05 age=12d idle=7d moves=6(h5) notes=4 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > Interested(08-05H) > GMeet Fixed(08-05H) > Interested(08-05H) > GMeet Fixed(08-05H) > Dead/Interested/NoShow(08-10H)

[3] MIB Tech Solutions
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/GMeet/wrong fit
     created=2026-08-04 age=13d idle=13d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Dead/GMeet/wrong fit(08-04H)

[3] Manoj Mathur
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Dead/GMeet/wrong fit
     created=2026-08-05 age=12d idle=5d moves=6(h4) notes=4 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > Interested(08-05H) > Call Attempted (retired)(08-05H) > No Pickup(08-05S) > GMeet Fixed(08-06H) > Dead/GMeet/wrong fit(08-12H)

[3] Mobibeans Solution Pvt Ltd.
     src=Tracxn Sheet ( Startups ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-27 age=21d idle=20d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: GMeet Fixed(07-27H) > Interested(07-28S)

[3] Northcorp Software
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=GMeet Fixed
     created=2026-08-07 age=10d idle=10d moves=4(h3) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/ColdCall/WrongFit(08-07H) > No Pickup(08-07H) > GMeet Fixed(08-07H)

[3] Perigeon Software Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=GMeet Fixed
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > GMeet Fixed(08-14H)

[3] Resha Mandi
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Interested
     created=2026-07-17 age=31d idle=25d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-17S) > GMeet Fixed(07-21H) > Interested(07-23S)

[3] SSOSEC
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-17 age=31d idle=25d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-17S) > GMeet Fixed(07-21H) > Dead/Interested/NoShow(07-21H) > Dead/ColdCall/Not Interested(07-23S)

[3] Samniya Digital Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=GMeet Fixed
     created=2026-07-23 age=25d idle=25d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > GMeet Fixed(07-23H)

[3] Shivam Patel
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/GMeet/wrong fit
     created=2026-08-10 age=7d idle=7d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-10S) > Dead/GMeet/wrong fit(08-10H)

[3] Somesh Chaturvedi
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=GMeet Fixed
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: GMeet Fixed(07-29S)

[3] TE Connectivity
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=GMeet Fixed
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > GMeet Fixed(08-06H)

[3] TM Systems
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-08-07 age=10d idle=7d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > GMeet Fixed(08-07H) > Dead/GMeet/wrong fit(08-10H)

[3] TagSkills® EdTech Private Limited
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Dead/GMeet/wrong fit(08-12H)

[3] Tart Labs
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=GMeet Fixed
     created=2026-08-13 age=4d idle=0d moves=3(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-14H) > GMeet Fixed(08-17H)

[3] Techno Tackle Software Solutions
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=GMeet Fixed
     created=2026-08-14 age=3d idle=0d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > Interested(08-14H) > GMeet Fixed(08-17H)

[3] TekWissen India
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > GMeet Fixed(08-11H) > Interested(08-11H)

[3] Terralogic Software Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Dead/GMeet/wrong fit(08-13H)

[3] WebGuruz Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=GMeet Fixed
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=4 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > GMeet Fixed(08-12H)

[3] Zscaler Softech India Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Dead/GMeet/wrong fit(08-13H)

[3] iB Hubs
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Dead/GMeet/wrong fit(08-12H)

[3] null - The Open Security Community
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/GMeet/wrong fit
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Dead/GMeet/wrong fit(08-12H)

[3] valantic India
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=GMeet Fixed
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > GMeet Fixed(08-11H)

[2] 4w Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480477)(07-21H) > Dead/ColdCall/Not Interested(07-23S)

[2] 88gravity
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=17d moves=3(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-31H) > Dead/ColdCall/Not Interested(07-31H)

[2] 91social
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=4(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > (deleted stage 3992480476)(07-23H) > Dead/ColdCall/Not Interested(07-23S)

[2] 9series Inc
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-15 age=33d idle=26d moves=5(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480476)(07-21H) > (deleted stage 3992480466)(07-21H) > Interested(07-22S)

[2] A3Logics
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=4(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480476)(07-21H) > Dead/ColdCall/Not Interested(07-23S)

[2] AAPNA Infotheek Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=0d moves=3(h2) notes=3 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-07H) > No Pickup(08-17H)

[2] ADVMEDIA
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=13d moves=4(h3) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Interested(07-20H) > Dead/ColdCall/WrongFit(08-04H) > Dead/ColdCall/Not Interested(08-04H)

[2] AGENCY09
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-07-15 age=33d idle=13d moves=5(h3) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480466)(07-21H) > Interested(07-22S) > Dead/Interested/NoShow(08-04H)

[2] AIS Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=5d moves=4(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/WrongFit(08-06H) > Cold Call(08-06H) > Dead/ColdCall/Not Interested(08-12H)

[2] AISCOR Private Limited
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Dead/ColdCall/Not Interested(07-23H)

[2] ANGLER Technologies India Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Interested(08-17H)

[2] APPiLY Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-07-15 age=33d idle=13d moves=4(h3) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Interested(07-20H) > Dead/Interested/NoShow(08-04H)

[2] ARKA Softwares
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=4(h3) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Call Attempted (retired)(07-20H) > Dead/ColdCall/Not Interested(07-23H)

[2] Aapna Infotech
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=19d moves=4(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > Interested(07-21H) > Dead/ColdCall/Not Interested(07-29H)

[2] Aartek Software Solutions Pvt. Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=4(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480477)(07-21H) > Dead/ColdCall/Not Interested(07-23S)

[2] Aaryavarta Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=4(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480477)(07-21H) > Dead/ColdCall/Not Interested(07-23S)

[2] Aavatto
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=5(h3) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > Interested(07-21H) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[2] Abhiwan Technology
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=19d moves=6(h4) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > Interested(07-21H) > (deleted stage 3992480466)(07-21H) > Interested(07-22S) > Dead/ColdCall/Not Interested(07-29H)

[2] Absolin Software Solutions LLP
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-14H)

[2] Accucia
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=19d moves=5(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480466)(07-21H) > Interested(07-22S) > Dead/ColdCall/Not Interested(07-29H)

[2] Ace Infoway
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-07-15 age=33d idle=13d moves=5(h3) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480466)(07-21H) > Interested(07-22S) > Dead/Interested/NoShow(08-04H)

[2] Acesoft Labs
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] Act T Connect
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-07-15 age=33d idle=13d moves=4(h3) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > Interested(07-21H) > Dead/Interested/NoShow(08-04H)

[2] Adequate Infosoft Pvt. Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480477)(07-22H) > Dead/ColdCall/Not Interested(07-23S)

[2] Adhoc Softwares INC
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=5(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480479)(07-21H) > (deleted stage 3992480476)(07-21H) > Dead/ColdCall/Not Interested(07-23S)

[2] Aditya Dwivedi
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=0d moves=6(h4) notes=6 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Interested(08-05H) > Call Attempted (retired)(08-05H) > No Pickup(08-05S) > Interested(08-06H) > Dead/ColdCall/Not Interested(08-17H)

[2] Adsum Originator LLP
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-15 age=33d idle=26d moves=5(h3) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480479)(07-21H) > (deleted stage 3992480466)(07-21H) > Interested(07-22S)

[2] Advanced Millennium Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > (deleted stage 3992480477)(07-23H) > Dead/ColdCall/Not Interested(07-23S)

[2] AdventSys Technologies Private Limited
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-15 age=33d idle=28d moves=2(h1) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Interested(07-20H)

[2] Aeonix Research and Innovations LLP
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > Dead/ColdCall/Not Interested(08-14H)

[2] Agile Robots SE
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-07-30 age=18d idle=11d moves=3(h2) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-06H) > No Pickup(08-06H)

[2] Aglowid It Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-07-15 age=33d idle=13d moves=5(h3) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Call Attempted (retired)(07-21H) > (deleted stage 3992480466)(07-21H) > Interested(07-22S) > Dead/Interested/NoShow(08-04H)

[2] Aican Private Limited
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480476)(07-21H) > Dead/ColdCall/Not Interested(07-23S)

[2] AiderPro Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=4(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-22H) > (deleted stage 3992480476)(07-22H) > Dead/ColdCall/Not Interested(07-23S)

[2] Ailoitte
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=13d moves=5(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480466)(07-21H) > Interested(07-22S) > Dead/ColdCall/Not Interested(08-04H)

[2] Aimbeat Technology Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480476)(07-21H) > Dead/ColdCall/Not Interested(07-23S)

[2] Akhil Varyani
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Albertsons Companies India
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=12d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/Not Interested(08-05H)

[2] Ali Moizuddin
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-28S)

[2] Allo Health
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-03 age=14d idle=13d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Dead/ColdCall/Not Interested(08-04H)

[2] Alphawizz Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/ColdCall/Not Interested(08-07H)

[2] Alphre
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=5(h3) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480478)(07-21H) > (deleted stage 3992480477)(07-21H) > Dead/ColdCall/Not Interested(07-23S)

[2] AlterSquare
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Interested(07-21H) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[2] Altysys
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Interested
     created=2026-07-21 age=27d idle=12d moves=2(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-21S) > Interested(08-05H)

[2] Alumnus Software Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-14H)

[2] Analogue IT Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=13d moves=6(h4) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480466)(07-21H) > Interested(07-22S) > Dead/Interested/NoShow(08-04H) > Dead/ColdCall/Not Interested(08-04H)

[2] Anil Kanthi
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Ankit Singhal
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Ankur Sharma
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Annova Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Dead/ColdCall/Not Interested(08-13H)

[2] Antsglobe Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=13d moves=8(h6) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480479)(07-21H) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480466)(07-21H) > Interested(07-22S) > Dead/Interested/NoShow(08-04H) > Dead/ColdCall/Not Interested(08-04H)

[2] Anubhav Kulshrestha
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Anurag Kabra
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Anviam Solutions
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-07-15 age=33d idle=5d moves=6(h4) notes=2 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480466)(07-21H) > Interested(07-22S) > Dead/ColdCall/Not Interested(08-12H) > Interested(08-12H)

[2] Apoorv Garg
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Apparrant Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-07-15 age=33d idle=19d moves=6(h4) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Interested(07-21H) > (deleted stage 3992480466)(07-21H) > Interested(07-22S) > Dead/ColdCall/WrongFit(07-29H)

[2] Appcrunk Technologies Private Limited
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=19d moves=4(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Interested(07-20H) > Dead/ColdCall/Not Interested(07-29H)

[2] Appsimity Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=6(h4) notes=3 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Call Attempted (retired)(07-20H) > Interested(07-20H) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[2] Appsinvo Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > (deleted stage 3992480476)(07-20H) > Dead/ColdCall/Not Interested(07-23S)

[2] Appsvolt
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480476)(07-20H) > Dead/ColdCall/Not Interested(07-23S)

[2] Appusamy Subbian
     src=Linkedin Campaign ( IT Services ) | owner=Lamiya Saleem | pipe=Campaign | stage=Interested
     created=2026-08-07 age=10d idle=4d moves=2(h1) notes=2 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-13H)

[2] Aquaconnect
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-03 age=14d idle=6d moves=3(h2) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Interested(08-04H) > Dead/ColdCall/Not Interested(08-11H)

[2] Areteans
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/ColdCall/Not Interested(08-10H)

[2] Argenius
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > (deleted stage 3992480477)(07-21H) > Dead/ColdCall/Not Interested(07-23S)

[2] Arham Web Works
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=19d moves=4(h3) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Interested(07-20H) > Dead/ColdCall/Not Interested(07-29H)

[2] Arieotech
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=4(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > (deleted stage 3992480476)(07-22H) > Dead/ColdCall/Not Interested(07-23S)

[2] Aripra Infotech
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=13d moves=6(h4) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Interested(07-20H) > (deleted stage 3992480466)(07-20H) > Interested(07-22S) > Dead/ColdCall/Not Interested(08-04H)

[2] Ark Newtech
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=11d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/Not Interested(08-06H)

[2] Arminus
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Dead/ColdCall/Not Interested(08-11H)

[2] Arokee Online Solutions Pvt. Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480476)(07-20H) > Dead/ColdCall/Not Interested(07-23S)

[2] Arth Technology
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480476)(07-20H) > Dead/ColdCall/Not Interested(07-23S)

[2] Artoon Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=5(h3) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Cold Call(07-20H) > (deleted stage 3992480476)(07-20H) > Dead/ColdCall/Not Interested(07-23S)

[2] Aryavrat Infotech Inc.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=7(h5) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Cold Call(07-20H) > (deleted stage 3992480463)(07-20H) > Cold Call(07-20H) > (deleted stage 3992480477)(07-21H) > Dead/ColdCall/Not Interested(07-23S)

[2] Askme Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=7(h5) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-16H) > Interested(07-16H) > Cold Call(07-16S) > (deleted stage 3992480463)(07-20H) > Interested(07-20H) > Dead/ColdCall/Not Interested(07-23H)

[2] Asparrow Tech
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=19d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Interested(07-20H) > Dead/ColdCall/Not Interested(07-29H)

[2] Atharva System
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=5d moves=3(h2) notes=3 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Interested(08-06H) > No Pickup(08-12H)

[2] Atidan Technologies
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/ColdCall/Not Interested(08-07H)

[2] Atomic North
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=6(h4) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-16H) > Call Attempted (retired)(07-16H) > Cold Call(07-20H) > (deleted stage 3992480477)(07-21H) > Dead/ColdCall/Not Interested(07-23S)

[2] Atreya Thapliyal
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Automatrix Innovation
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-07-28 age=20d idle=13d moves=4(h3) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/WrongFit(07-28H) > Interested(07-28H) > Dead/Interested/NoShow(08-04H)

[2] Averta Strategy Pvt LTd.
     src=Founder Search ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Interested(08-17H)

[2] Ayush Agarwal
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-28S)

[2] Azympto
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > (deleted stage 3992480476)(07-23H) > Dead/ColdCall/Not Interested(07-23S)

[2] Bandhan Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=5d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H) > Interested(08-12H)

[2] Baxi
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=0d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-04H) > No Pickup(08-17H)

[2] Belinnov Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=3 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-14H)

[2] Best of Breed Software Solutions India Pvt Ltd
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > Interested(08-14H)

[2] BharatAgri
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-03 age=14d idle=14d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Dead/ColdCall/Not Interested(08-03H)

[2] Bhavyansh Infotech India Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] Big Oh Tech
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] BigStep Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=18d moves=4(h3) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/Not Interested(07-30H) > Call Attempted (retired)(07-30H) > Dead/ColdCall/Not Interested(07-30H)

[2] BlazeDream Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=18d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/Not Interested(07-30H)

[2] Brainstorm Force
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-08-04 age=13d idle=11d moves=3(h2) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-05H) > Dead/ColdCall/WrongFit(08-06H)

[2] Briskstar Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/Not Interested(07-28H)

[2] BugendaiTech
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Dead/ColdCall/Not Interested(07-23H)

[2] CADOpt Technologies Private Limited
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-10H)

[2] CEDURA Testsol Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-13H)

[2] CLOUDSUFI
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Interested
     created=2026-07-30 age=18d idle=12d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-05H)

[2] CYBROSYS Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-10H)

[2] Canarys
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-07-22 age=26d idle=13d moves=5(h4) notes=3 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > (deleted stage 3992480476)(07-22H) > Call Attempted (retired)(07-22H) > Interested(07-23H) > Dead/ColdCall/WrongFit(08-04H)

[2] Canopus Infosystems
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=3(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > Dead/ColdCall/Not Interested(07-28H)

[2] Careator Technologies
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Dead/ColdCall/Not Interested(08-12H)

[2] Celestiq Datatech Pvt. Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > Dead/ColdCall/Not Interested(07-23H)

[2] Celexsa Technologies Private Limited
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-30 age=18d idle=18d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > Interested(07-30H)

[2] Chandrachood Raveendran
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-28S)

[2] Choice TechLab
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=17d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/Not Interested(07-31H)

[2] Clarion Technologies
     src=Private Codebase Tracker sheet ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-03 age=14d idle=14d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Dead/ColdCall/Not Interested(08-03H)

[2] ClaySys Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/Not Interested(07-28H)

[2] Clerisy Solutions Private Limited
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=18d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/Not Interested(07-30H)

[2] Cloud.in
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Dead/ColdCall/Not Interested(08-12H)

[2] CodeGama
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-22 age=26d idle=25d moves=3(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > Interested(07-23H)

[2] Codeflies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] Codelynks Software Solutions
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Interested(08-17H)

[2] Codetentacles Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > (deleted stage 3992480477)(07-22H) > Dead/ColdCall/Not Interested(07-23S)

[2] Codzgarage Infotech
     src=Private Codebase Tracker sheet ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=18d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/Not Interested(07-30H)

[2] CognitiveClouds
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=17d moves=4(h3) notes=3 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > Interested(07-22H) > Dead/ColdCall/Not Interested(07-31H)

[2] CoinDCX
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Interested(07-29S)

[2] Colan Infotech Private Limited
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-03 age=14d idle=13d moves=4(h3) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > Interested(08-03H) > Dead/ColdCall/Not Interested(08-04H)

[2] Conacent Consulting
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/Not Interested(07-28H)

[2] Contata Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=3d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H) > Interested(08-14H)

[2] Cosette Network Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Dead/ColdCall/Not Interested(08-11H)

[2] Covalense Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-14H)

[2] CraftedQ
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=17d moves=3(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-31H) > Dead/ColdCall/Not Interested(07-31H)

[2] Creant Technologies Private Limited
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-22 age=26d idle=19d moves=4(h3) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Interested(07-22H) > Dead/ColdCall/Not Interested(07-29H) > Interested(07-29H)

[2] Crypso
     src=Tracxn Sheet ( Startups ) | owner=Shobit Gupta | pipe=Scraped | stage=Interested
     created=2026-07-17 age=31d idle=20d moves=3(h0) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-17S) > Cold Call(07-23S) > Interested(07-28S)

[2] CyRAACS™
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Dead/ColdCall/Not Interested(08-12H)

[2] Cybersapient
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > Interested(08-05S)

[2] Cygnet Infotech Pvt Ltd
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-13H)

[2] DATAMATO
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > (deleted stage 3992480477)(07-22H) > Dead/ColdCall/Not Interested(07-23S)

[2] DI Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=3(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/WrongFit(07-28H) > Dead/ColdCall/Not Interested(07-28H)

[2] DIATOZ: Digital A to Z Solutions
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=3 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] DTC Infotech
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=3(h2) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > Dead/ColdCall/Not Interested(07-23H)

[2] Decipher Zone Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-07-30 age=18d idle=13d moves=3(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(07-31H) > Dead/ColdCall/WrongFit(08-04H)

[2] Deepmindz Innovations
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=3(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/WrongFit(07-28H) > Dead/ColdCall/Not Interested(07-28H)

[2] DeoTech Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/WrongFit(07-28H) > Dead/ColdCall/Not Interested(07-28H)

[2] Deorwine Infotech
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-30 age=18d idle=17d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(07-31H)

[2] Depex Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=17d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/Not Interested(07-31H)

[2] Deqode
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > (deleted stage 3992480476)(07-22H) > Dead/ColdCall/Not Interested(07-23S)

[2] Dev Technosys LLC
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Interested(08-17H)

[2] Devolyt
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/WrongFit(07-28H) > Dead/ColdCall/Not Interested(07-28H)

[2] DevsLane
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=4d moves=3(h2) notes=3 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H) > Dead/ColdCall/Not Interested(08-13H)

[2] Divergent Software Labs Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-13H)

[2] Dotcom IoT
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=4(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/WrongFit(07-28H) > Dead/Interested/NoShow(07-28H) > Dead/ColdCall/Not Interested(07-28H)

[2] Dreams Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=5(h4) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/WrongFit(07-28H) > Cold Call(07-28H) > Dead/ColdCall/WrongFit(07-28H) > Dead/ColdCall/Not Interested(07-28H)

[2] DreamzTech Solutions Inc.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/WrongFit(07-28H) > Dead/ColdCall/Not Interested(07-28H)

[2] Easyrewardz Software Services
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-07 age=10d idle=7d moves=3(h2) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H) > Interested(08-10H)

[2] Eatlo
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-04 age=13d idle=6d moves=3(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-04H) > Dead/ColdCall/Not Interested(08-11H)

[2] Ecleva Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/Not Interested(07-28H)

[2] EdgeVerve
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=3(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > Dead/ColdCall/Not Interested(07-23H)

[2] EmbedSense Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > Interested(08-14H)

[2] Emorphis Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-28 age=20d idle=20d moves=3(h2) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > Interested(07-28H)

[2] Emsphere Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > (deleted stage 3992480479)(07-22H) > (deleted stage 3992480476)(07-22H) > Dead/ColdCall/Not Interested(07-23S)

[2] Ennovations Techserv
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-07-28 age=20d idle=13d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Interested(07-28H) > Dead/Interested/NoShow(08-04H)

[2] Enterprise System Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-13H)

[2] Ethical Intelligent Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-07-30 age=18d idle=13d moves=4(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > Interested(07-30H) > Dead/ColdCall/WrongFit(08-04H)

[2] Evenion Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=4(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Interested(07-22H) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[2] FSS
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/ColdCall/WrongNumber
     created=2026-07-30 age=18d idle=11d moves=4(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-06H) > Cold Call(08-06H) > Dead/ColdCall/WrongNumber(08-06H)

[2] Finacus Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/WrongFit(07-28H) > Dead/ColdCall/Not Interested(07-28H)

[2] Finnoto
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-03 age=14d idle=11d moves=3(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Interested(08-04H) > Dead/ColdCall/WrongFit(08-06H)

[2] Flyers Soft Private Limited
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-07-28 age=20d idle=13d moves=4(h3) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > Interested(07-28H) > Dead/Interested/NoShow(08-04H)

[2] Fractal
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Interested(07-29S)

[2] FrontPage
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=11d moves=4(h3) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-06H) > Dead/ColdCall/WrongFit(08-06H) > Dead/ColdCall/Not Interested(08-06H)

[2] Futiq Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/WrongFit(07-28H) > Dead/ColdCall/Not Interested(07-28H)

[2] Gaurav Dube
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Geek Informatic & Technologies Private Limited
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=6d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H) > Dead/ColdCall/Not Interested(08-11H)

[2] GenxAI SoftGrid
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=3(h2) notes=3 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H) > Interested(08-11H)

[2] Goodpick Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=5(h3) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Dead/ColdCall/WrongFit(07-28H) > Cold Call(07-28S) > Dead/ColdCall/WrongFit(07-28H) > Dead/ColdCall/Not Interested(07-28H)

[2] GramFactory
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/Not Interested(08-06H)

[2] GrocShop
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=5(h3) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > Interested(08-04H) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[2] Hacking Articles
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-12H)

[2] HashedIn
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > (deleted stage 3992480476)(07-22H) > Dead/ColdCall/Not Interested(07-23S)

[2] HeapTrace Technology
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-07H)

[2] Henceforth Solutions Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Interested(08-17H)

[2] HighLevel
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-21 age=27d idle=12d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-21S) > Dead/ColdCall/Not Interested(08-05H)

[2] Hiranmoy B.
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] HirePro
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/ColdCall/Not Interested(08-12H)

[2] Hitech Infotech Services Pvt. Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-11 age=6d idle=6d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H) > Dead/ColdCall/WrongFit(08-11H)

[2] Hutech Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > (deleted stage 3992480476)(07-22H) > Dead/ColdCall/Not Interested(07-23S)

[2] Hypto
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=13d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/Not Interested(08-04H)

[2] INFOCRATS
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] Immersive Infotech Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=4 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] Incentius
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > (deleted stage 3992480476)(07-22H) > Dead/ColdCall/Not Interested(07-23S)

[2] Indigrators Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-17H)

[2] IntelliaTech Solutions Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=0d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H) > Dead/ColdCall/Not Interested(08-17H)

[2] Intense Technologies Ltd
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-14H)

[2] Jabit Soft
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Interested(08-17H)

[2] Jagdeep Singh
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Jerwin P.
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-28S)

[2] Jeyanthinath M.
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=0d moves=3(h2) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Interested(08-05H) > Dead/ColdCall/Not Interested(08-17H)

[2] Judge India Solutions
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=4d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H) > Dead/ColdCall/Not Interested(08-13H)

[2] Kovaion Consulting India Pvt Ltd
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Dead/ColdCall/Not Interested(08-14H)

[2] Kran Consulting Pvt. Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-07H)

[2] Kredily
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-03 age=14d idle=13d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Dead/ColdCall/Not Interested(08-04H)

[2] Kripesh Adwani
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Krishnendu Nandi
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Kyt
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=14d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/Not Interested(08-03H)

[2] LN Webworks Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=4d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H) > Interested(08-13H)

[2] Laxmikant Agarwal
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Dead/ColdCall/Not Interested(07-29H)

[2] Leegality
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=7d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/ColdCall/WrongFit(08-10H) > Dead/ColdCall/Not Interested(08-10H)

[2] LiveSalesman
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=6d moves=4(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H) > No Pickup(08-11H) > Dead/ColdCall/Not Interested(08-11H)

[2] Lorhan IT
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/ColdCall/Not Interested(08-07H)

[2] Luqa Technologies
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-08-05 age=12d idle=12d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > Interested(08-05H) > Dead/ColdCall/WrongFit(08-05H)

[2] MEDIATRENZ
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-12H)

[2] MINDTEL
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Dead/ColdCall/Not Interested(08-12H)

[2] Mahendravijay ♌
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Mahesh Sonker
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Interested
     created=2026-07-28 age=20d idle=20d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Interested(07-28S)

[2] Marktine Technology Solutions Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-08-03 age=14d idle=14d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Interested(08-03H)

[2] Mars Web Solution
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-07-23 age=25d idle=13d moves=4(h3) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-27H) > Interested(07-27H) > Dead/Interested/NoShow(08-04H)

[2] Maruti Techlabs
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/ColdCall/Not Interested(08-10H)

[2] Mechlin Technologies
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=5d moves=4(h3) notes=3 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H) > Dead/ColdCall/WrongFit(08-12H) > Dead/ColdCall/Not Interested(08-12H)

[2] Mechsoft Digital Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-23 age=25d idle=21d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Interested(07-27H)

[2] Medidart
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-04 age=13d idle=13d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Dead/ColdCall/Not Interested(08-04H)

[2] Megamax Services
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-03 age=14d idle=14d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Dead/ColdCall/Not Interested(08-03H)

[2] Metalstreet
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/Not Interested(08-06H)

[2] MindCrew Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=0d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H) > Dead/ColdCall/Not Interested(08-17H)

[2] Mistral Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-23 age=25d idle=21d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-27H) > Interested(07-27H)

[2] Mobilab
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-03 age=14d idle=13d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Dead/ColdCall/Not Interested(08-04H)

[2] Mohit Bhatia
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-07-29 age=19d idle=12d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Interested(08-05H) > Dead/ColdCall/WrongFit(08-05H)

[2] Montbleu Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-11 age=6d idle=4d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H) > Dead/ColdCall/WrongFit(08-13H)

[2] Moon Technolabs
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/ColdCall/Not Interested(08-12H)

[2] Moshi Moshi
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-23 age=25d idle=21d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Interested(07-27H)

[2] Mukesh Alex
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-28S)

[2] Multiple Organizations 
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-07-30 age=18d idle=11d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-05H) > No Pickup(08-06H)

[2] Mundrisoft Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Dead/ColdCall/Not Interested(08-14H)

[2] NITHILAM.TECH
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-08-05 age=12d idle=12d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > Dead/ColdCall/Not Interested(08-05H)

[2] NXP India
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-10H)

[2] Narola Infotech
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/ColdCall/Not Interested(08-10H)

[2] Neetable
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-23 age=25d idle=21d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Dead/ColdCall/Not Interested(07-27H)

[2] Nerve Solutions
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] NetAnalytiks
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] Nethues Technologies
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=0d moves=3(h2) notes=5 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-10H) > Dead/ColdCall/Not Interested(08-17H)

[2] Netweb Software Pvt Ltd
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > Interested(08-14H)

[2] NeuroPixel.AI
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-03 age=14d idle=14d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Dead/ColdCall/Not Interested(08-03H)

[2] NextGen Healthcare India
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Dead/ColdCall/Not Interested(08-12H)

[2] Nielsen
     src=Outflo Outreach ( Startups ) | owner=Ishpreet Sood | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-21 age=27d idle=12d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-21S) > Dead/ColdCall/Not Interested(08-05H)

[2] Nihilent Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-14H)

[2] Nineleaps
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-12H)

[2] Niteen Shastri
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Notetech Software
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-14H)

[2] NotionMindz Technology LLP
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=2 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > Interested(08-14H)

[2] Nucleus Software
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-07-30 age=18d idle=11d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-05H) > No Pickup(08-06H)

[2] OMNIST TECHHUB SOLUTIONS PRIVATE LIMITED
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Interested(08-17H)

[2] Olyv
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Interested
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-06H)

[2] Omik Dahat
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-07-30 age=18d idle=0d moves=5(h3) notes=3 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-05H) > Call Attempted (retired)(08-05H) > Interested(08-05S) > No Pickup(08-17H)

[2] Onato
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-07-20 age=28d idle=12d moves=4(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-20S) > Interested(07-21H) > Call Attempted (retired)(07-23S) > Dead/ColdCall/WrongNumber(08-05S)

[2] OpsTree Global
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-10H)

[2] OyeLabs
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=0d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H) > Dead/ColdCall/Not Interested(08-17H)

[2] Parkhya Solutions Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-12H)

[2] Parth Verma
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=1(h0) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-28S)

[2] Pattem Digital Technologies Private Limited
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Dead/ColdCall/Not Interested(08-17H)

[2] PepperTap
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-04 age=13d idle=11d moves=3(h2) notes=1 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-04H) > Dead/ColdCall/Not Interested(08-06H)

[2] Pixel Web Solutions
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-12H)

[2] Pixelstat
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Interested(08-17H)

[2] Podium Systems Private Limited
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=6d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Dead/ColdCall/WrongFit(08-11H) > Dead/ColdCall/Not Interested(08-11H)

[2] Prakhar Software Solutions Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/ColdCall/Not Interested(08-10H)

[2] Pristine Pro Tech Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-13H)

[2] Prolance
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-03 age=14d idle=11d moves=3(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Interested(08-04H) > Dead/ColdCall/WrongFit(08-06H)

[2] PurpleTalk India Pvt Ltd
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-14H)

[2] Qruize Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-13H)

[2] Qseap Infotech Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-12H)

[2] QualiTlabs
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-12H)

[2] Qubiqon Consulting India Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-13H)

[2] Questt
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-07-30 age=18d idle=4d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-13H)

[2] REGRIP
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-03 age=14d idle=11d moves=3(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Interested(08-04H) > Dead/ColdCall/WrongFit(08-06H)

[2] Raghul Gandhi
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Rahul Bhuraria
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=12d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Dead/ColdCall/Not Interested(08-05H)

[2] Rakesh Mondal
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Renu SB Creation Software Pvt Ltd (SB Creation)
     src=Founder Search ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Interested(08-17H)

[2] Rudhra Info Solutions
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-14H)

[2] SAVIC Inc.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-08-07 age=10d idle=0d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-12H) > Dead/ColdCall/WrongNumber(08-17H)

[2] SKS TECH SOLUTION
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=10d moves=3(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H) > Dead/ColdCall/Not Interested(08-07H)

[2] SSM InfoTech Solutions Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-08-07 age=10d idle=0d moves=3(h2) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-12H) > Dead/ColdCall/WrongNumber(08-17H)

[2] Sahana System Limited
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-07 age=10d idle=10d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-07H) > Dead/ColdCall/WrongFit(08-07H)

[2] Sanjay C.
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Sankey Solutions
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-07H) > No Pickup(08-07H)

[2] Sayy AI
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Interested
     created=2026-07-30 age=18d idle=12d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-05H)

[2] Scalex Technology Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-23 age=25d idle=25d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Dead/ColdCall/Not Interested(07-23H)

[2] Secuodsoft Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-14 age=3d idle=3d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H) > Interested(08-14H)

[2] Shanky Munoth
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] ShareMoney/ Statements AI
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-08-04 age=13d idle=13d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Dead/ColdCall/Not Interested(08-04H)

[2] Shine Dezign Infonet Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/ColdCall/Not Interested(08-07H)

[2] Shivendra Soni
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Dead/ColdCall/WrongNumber
     created=2026-07-29 age=19d idle=11d moves=5(h3) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Interested(08-05H) > Call Attempted (retired)(08-05H) > Interested(08-05S) > Dead/ColdCall/WrongNumber(08-06H)

[2] Shivrai technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-07-23 age=25d idle=13d moves=6(h5) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-23H) > Interested(07-23H) > Call Attempted (retired)(07-28H) > Interested(07-28H) > Dead/Interested/NoShow(08-04H)

[2] Signicent Information Solutions LLP
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-13 age=4d idle=4d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H) > Dead/ColdCall/Not Interested(08-13H)

[2] Sinergia Media Labs Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-14H)

[2] Sm Softwares
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-23 age=25d idle=25d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Dead/ColdCall/Not Interested(07-23H)

[2] Smartify Software Solutions LLP
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Dead/ColdCall/Not Interested(08-17H)

[2] Softtrix Tech Solutions Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/ColdCall/Not Interested(08-10H)

[2] SolutionChamps Technologies
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Dead/ColdCall/Not Interested(08-17H)

[2] Somnetics (Som Imaging Informatics Pvt. Ltd.)
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] Soumyadeep Biswas
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Spine Software Systems Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-07-28 age=20d idle=13d moves=5(h3) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Interested(07-28H) > Cold Call(07-28S) > Interested(07-28H) > Dead/Interested/NoShow(08-04H)

[2] SplendorNet Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-14H)

[2] Sriram Ravichandran
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Stellantis
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/Not Interested(08-06H)

[2] Sumedha Softech Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Dead/ColdCall/Not Interested(08-17H)

[2] Sun Plus Software Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-28 age=20d idle=20d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Interested(07-28H)

[2] Sundew
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-12H)

[2] Surge Classes
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=0d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-06H) > Dead/ColdCall/Not Interested(08-17H)

[2] SustainableX
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-08-05 age=12d idle=11d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > Interested(08-05H) > Dead/ColdCall/Not Interested(08-06H)

[2] Suventure Services Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-07-30 age=18d idle=18d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(07-30H)

[2] TMRW House of Brands
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Interested
     created=2026-07-30 age=18d idle=12d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-05H)

[2] Tanmay Pahuja
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Dead/ColdCall/Not Interested(07-29H)

[2] TantranZm
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Dead/ColdCall/Not Interested(08-11H)

[2] Tanuj Khurana
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Tapas Das
     src=Linkedin Campaign ( IT Services ) | owner=Lamiya Saleem | pipe=Campaign | stage=Interested
     created=2026-08-06 age=11d idle=4d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-06S) > Interested(08-13H)

[2] Taskbob
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-04 age=13d idle=13d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > Dead/ColdCall/Not Interested(08-04H)

[2] Tech Active
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=5(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > (deleted stage 3992480478)(07-21H) > (deleted stage 3992480477)(07-21H) > Dead/ColdCall/Not Interested(07-23S)

[2] Techasoft Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Interested(08-17H)

[2] Techinfini Solutions Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] Technostacks
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-11 age=6d idle=0d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-12H) > Dead/ColdCall/WrongFit(08-17H)

[2] Technource
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-11 age=6d idle=6d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H) > Dead/ColdCall/WrongFit(08-11H)

[2] Techweirdo 2
     src=Scraping Algo ( IT services ) | owner=Shobit Gupta | pipe=Scraped | stage=Interested
     created=2026-07-28 age=20d idle=20d moves=1(h0) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Interested(07-28S)

[2] Testaing
     src=Linkedin Campaign ( IT Services ) | owner=Lamiya Saleem | pipe=Campaign | stage=Interested
     created=2026-08-04 age=13d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-13H)

[2] The NineHertz
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-08-03 age=14d idle=14d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Interested(08-03H)

[2] The One Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Dead/ColdCall/Not Interested(08-12H)

[2] TheKSquare Group
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-08-04 age=13d idle=12d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-05H) > Dead/ColdCall/WrongFit(08-05H)

[2] Theremin
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-07-30 age=18d idle=4d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Interested(08-13H)

[2] ThinkPalm Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Interested
     created=2026-08-03 age=14d idle=14d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Interested(08-03H)

[2] Thirdessential IT Solutions Pvt. Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Interested(08-17H)

[2] ThoughtSpot
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Dead/ColdCall/WrongNumber
     created=2026-08-04 age=13d idle=11d moves=3(h2) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-04H) > Dead/ColdCall/WrongNumber(08-06H)

[2] TinyOwl
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-04 age=13d idle=13d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Dead/ColdCall/Not Interested(08-04H)

[2] Toingg
     src=Linkedin Campaign ( IT Services ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/Interested/NoShow
     created=2026-08-06 age=11d idle=7d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-06S) > Dead/Interested/NoShow(08-10H)

[2] Toptal
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=12d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/Not Interested(08-05H)

[2] Torus Robotics
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-03 age=14d idle=13d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Dead/ColdCall/Not Interested(08-04H)

[2] Trailytics AI
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=4d moves=5(h4) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H) > Dead/ColdCall/Not Interested(08-13H) > Interested(08-13H) > Dead/ColdCall/Not Interested(08-13H)

[2] Tricentis
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-08-04 age=13d idle=12d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-04H) > Dead/ColdCall/WrongFit(08-05H)

[2] Truebil
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=11d moves=4(h2) notes=4 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > Interested(08-05S) > No Pickup(08-06H)

[2] Truviq Systems
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=4 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] Uptricks Services Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=0d moves=3(h2) notes=3 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H) > Dead/ColdCall/Not Interested(08-17H)

[2] Userology
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-08-05 age=12d idle=11d moves=5(h3) notes=4 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > Interested(08-05H) > Call Attempted (retired)(08-05H) > Interested(08-05S) > No Pickup(08-06H)

[2] VAYUZ Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] Varun Miglani
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-07-29 age=19d idle=0d moves=3(h2) notes=3 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Interested(08-05H) > Dead/ColdCall/WrongFit(08-17H)

[2] Vays Infotech Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=3 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] Venkataraghavan Srinivasan
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-29 age=19d idle=19d moves=1(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Dead/ColdCall/Not Interested(07-29S)

[2] Versatiletech
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] VertexPlus
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-10H)

[2] Vibhanshu Chhangani
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-07-29 age=19d idle=12d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Interested(08-05H) > Dead/ColdCall/WrongFit(08-05H)

[2] Virtualyyst Tech Private Limited
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/ColdCall/WrongFit
     created=2026-08-04 age=13d idle=12d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-04H) > Dead/ColdCall/WrongFit(08-05H)

[2] Visionyle Solutions
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Dead/ColdCall/Not Interested(08-12H)

[2] Vrinsoft Technology Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=10d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H) > Dead/ColdCall/Not Interested(08-07H)

[2] Watsoo Express Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-14 age=3d idle=0d moves=3(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > Interested(08-14H) > Dead/ColdCall/Not Interested(08-17H)

[2] WebKorps
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-10H)

[2] Webandcrafts
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-10H)

[2] Webvillee Technology Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-12H)

[2] Worxpertise Group
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Dead/ColdCall/Not Interested(08-10H)

[2] Xeeed IO
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > Dead/ColdCall/Not Interested(08-05S)

[2] Xiarch Solutions Pvt Ltd
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-13 age=4d idle=3d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-13H) > Dead/ColdCall/WrongFit(08-14H)

[2] Xinthe Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Dead/ColdCall/Not Interested(08-17H)

[2] Yumist
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-04 age=13d idle=13d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Interested(08-04H) > Dead/ColdCall/Not Interested(08-04H)

[2] ZeroCodeHR LLP
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-14H)

[2] Zerozilla
     src=Founder Search ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Interested
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > Interested(08-17H)

[2] Znifa Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-13 age=4d idle=0d moves=3(h2) notes=3 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-13H) > Dead/ColdCall/WrongFit(08-17H)

[2] ZopNow
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-08-04 age=13d idle=13d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Dead/ColdCall/Not Interested(08-04H)

[2] Zscaler
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/Not Interested(08-06H)

[2] Zuci Systems
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=Dead/ColdCall/Not Interested
     created=2026-08-04 age=13d idle=13d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Dead/ColdCall/Not Interested(08-04H)

[2] Zylitix Solutions LLP
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-13 age=4d idle=0d moves=3(h2) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > Interested(08-13H) > Dead/ColdCall/WrongFit(08-17H)

[2] ascent
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-15 age=33d idle=25d moves=5(h3) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Cold Call(07-20H) > (deleted stage 3992480477)(07-21H) > Dead/ColdCall/Not Interested(07-23S)

[2] bluCursor Infotech Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > Interested(08-11H)

[2] eWandzDigital
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-28 age=20d idle=20d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > Dead/ColdCall/Not Interested(07-28H)

[2] external experts
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/Not Interested
     created=2026-07-22 age=26d idle=25d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > (deleted stage 3992480477)(07-22H) > Dead/ColdCall/Not Interested(07-23S)

[2] iAgami
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-11 age=6d idle=6d moves=3(h2) notes=3 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H) > Interested(08-11H)

[2] iB Arts Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/Interested/NoShow
     created=2026-07-22 age=26d idle=13d moves=4(h3) notes=2 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > Interested(07-23H) > Dead/Interested/NoShow(08-04H)

[2] izmo ltd
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Interested
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > Interested(08-12H)

[1] 10 Decoders Consultancy Services Private Limited
     src=Scraped ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] 1K Kirana
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] 2Base Technologies
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] 3ELIXIR SOLUTIONS
     src=Scraping Algo ( IT services ) | owner=Ishpreet Sood | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] 3i Infotech Ltd
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-08-14 age=3d idle=3d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H) > Dead/ColdCall/WrongNumber(08-14H)

[1] 4Fin
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] 4Seer Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] 75way Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] 7Span
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[1] A5E Consulting Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] ADTECH Corp.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] ALEAIT SOLUTIONS PVT. LTD.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > Call Attempted (retired)(07-21H) > Dead/ColdCall/WrongNumber(08-05S)

[1] APSTIA PRIVATE LIMITED
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] ARD Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] ARM Worldwide
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Aalpha Information Systems India Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[1] Aaseya IT Services Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] AbiShar Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] AbleCredit
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Absolute App Labs
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[1] Ackrolix innovations
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=4(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/WrongFit(07-30H) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Acsia Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Addon Solutions Pvt Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > No Pickup(08-05S)

[1] Addsoft Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] Advantal Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > No Pickup(08-05S)

[1] Agaram Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] AgilizTech Software Services Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] Agrex Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] Ahex Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Aimbeat
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] Airo Global Software
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-22H) > Call Attempted (retired)(07-22H) > No Pickup(08-05S)

[1] Airovo Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[1] Ajmera Infotech Inc.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Akili Systems
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[1] Aktiv Software
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-22H) > Call Attempted (retired)(07-22H) > No Pickup(08-05S)

[1] Albatroz (India) Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] Alcax Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[1] AlgoAnalytics
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Alle
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Allianze Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[1] Alliedge Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] Allshore Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Alphaleo Technology Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Ambab Infotech Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-22H) > Call Attempted (retired)(07-22H) > No Pickup(08-05S)

[1] Ambiguous Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[1] Amol Manohar Pardeshi
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Call Attempted (retired)(07-29H) > No Pickup(08-05S)

[1] AnAr Solutions Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Angular Minds
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=2 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > No Pickup(08-05S)

[1] Anivar A Aravind
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=3(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Call Attempted (retired)(07-29H) > No Pickup(08-05S)

[1] Ankur Gupta
     src=Linkedin Campaign ( IT Services ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Apagen Solutions Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] App India
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[1] AppWorks Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Appentus Technologies
     src=Private Codebase Tracker sheet ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Appface Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-07-15 age=33d idle=25d moves=4(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Call Attempted (retired)(07-20H) > Dead/ColdCall/WrongFit(07-23H)

[1] Appic Softwares
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] Applied Cloud Computing
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-12H)

[1] Appscomp Widgets Pvt Ltd.,
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] Appstean
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480476)(07-20H) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] Appther Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=6(h4) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Call Attempted (retired)(07-20H) > Dead/ColdCall/Not Interested(07-23H) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Apptians
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=5(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Cold Call(07-20H) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[1] Apptunix
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Apptware
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] Appventurez
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > No Pickup(08-05S)

[1] Appzia Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Appzlogic
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-07 age=10d idle=7d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H) > Dead/ColdCall/WrongFit(08-10H)

[1] Apt Software Avenues Pvt Ltd
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Aquadsoft
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-21H) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[1] ArcelorMittal Digital Consulting
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Arche Global Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Archimedis Digital Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Ariston IT Services
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Arkatiss
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] Arobit Business Solutions Pvt. Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > No Pickup(08-05S)

[1] Arodek Technology Consulting Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-17H)

[1] Arohatech
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-07-15 age=33d idle=25d moves=5(h4) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Call Attempted (retired)(07-20H) > Dead/GMeet/Privacy Concerns(07-23H) > Dead/ColdCall/WrongFit(07-23H)

[1] Aron Web Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] Arramton Infotech Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Call Attempted (retired)(07-21H) > No Pickup(08-05S)

[1] Arvaan Technolab
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-07-30 age=18d idle=18d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > Dead/ColdCall/WrongFit(07-30H)

[1] Ascent24 Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] Ascomp Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=4(h2) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > (deleted stage 3992480463)(07-20H) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] Ashay Tamhane
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=2(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Call Attempted (retired)(07-29S) > No Pickup(08-05S)

[1] Ashield Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Askgalore Digital
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-15 age=33d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-15S) > Call Attempted (retired)(07-20H) > No Pickup(08-05S)

[1] Asset Telematics Pvt Ltd
     src=Founder Search ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Assimilate Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] AtliQ Technologies
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] BCC UNITED
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] BCI (Bar Code India)
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Banao Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Bankai Infotech
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Batoi Systems Pvt Ltd
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Beno Support Technologies Pvt. Ltd
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > No Pickup(08-14H)

[1] BeyondB
     src=Linkedin Campaign ( IT Services ) | owner=Lamiya Saleem | pipe=Campaign | stage=No Pickup
     created=2026-08-06 age=11d idle=4d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-06S) > No Pickup(08-13H)

[1] Bhadani Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=5(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/WrongFit(07-30H) > Cold Call(07-30H) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Biconomy
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-13H)

[1] Bigscal Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > No Pickup(08-05S)

[1] Bikash Dash
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=2(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Call Attempted (retired)(07-29S) > No Pickup(08-05S)

[1] Bit Canny Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-31H) > No Pickup(08-05S)

[1] Biz4Solutions LLC
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] BizAcuity Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Biztech Consulting & Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=6(h4) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Dead/ColdCall/WrongFit(07-30H) > Dead/Interested/NoShow(07-30H) > Dead/ColdCall/WrongFit(07-30H) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Blackcoffer
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Blue Sky Analytics
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-07-30 age=18d idle=13d moves=5(h4) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(08-03H) > Dead/ColdCall/Not Interested(08-03H) > Dead/ColdCall/WrongFit(08-04H) > Dead/ColdCall/WrongNumber(08-04H)

[1] BlueLearn
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] BluePi
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Blueprint Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Bonami Software
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Boston Technology Corporation
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > No Pickup(08-05S)

[1] Botminds AI Technologies Private Limited
     src=Scraped ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-17H)

[1] Bpointer Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] BrainMobi
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-31H) > No Pickup(08-05S)

[1] Brainerhub
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Brainium Information Technologies
     src=Private Codebase Tracker sheet ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Brainmine Web Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > No Pickup(08-05S)

[1] BridgeUp
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Brilyant
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-12H)

[1] Brio Technologies
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Briskinfosec Technology and Consulting Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Brosis Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-31H) > No Pickup(08-05S)

[1] Bueno Finance
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Business Intelligence Professionals Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] CEDCOSS Technologies Private Limited
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-12H)

[1] CFSS Cyber & Forensics Security Solutions
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] CMARIX
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] CREST Infosystems Pvt Ltd
     src=Private Codebase Tracker sheet ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Cactus Technology Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Calibraint
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-31H) > No Pickup(08-05S)

[1] Capanicus
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Capital Numbers
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Chamunda Tech-Net Services Pvt.Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-31H) > No Pickup(08-05S)

[1] Chqbook
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-06H)

[1] Cientra
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Cimba.ai
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-06H)

[1] Circle Health
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Clik
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] CloudKaptan Consultancy Services Pvt Ltd
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] CloudifyOps
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Cloute Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Codebuddy Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Codelogicx Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Codestore Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-31H) > No Pickup(08-05S)

[1] Codingmart Technologies Private Limited
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Cogentnext Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Coindelta
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] ComUnus Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Commergence
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Communication Crafts
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Computronics Systems (India) Private Limited
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-07 age=10d idle=10d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H) > Dead/ColdCall/WrongFit(08-07H)

[1] Consagous Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-31H) > No Pickup(08-05S)

[1] Consint Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Constient Global Solutions
     src=Private Codebase Tracker sheet ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Contus Tech
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-03 age=14d idle=14d moves=4(h3) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > Dead/Interested/NoShow(08-03H) > Dead/ColdCall/WrongFit(08-03H)

[1] Convosight
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Cosmic Payments
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Cosyn Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] Crater
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] CreateBytes
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Credentia Verification Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Credex Technology Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Crejo.Fun
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Crescentek
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > No Pickup(08-05S)

[1] Cresol Infoserv Pvt Ltd
     src=Linkedin Campaign ( IT Services ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-08-06 age=11d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-06S) > No Pickup(08-17H)

[1] Crestech Software
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Creware Technologies Pvt
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Cubet Techno Labs Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Custom-Soft
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > No Pickup(08-05S)

[1] Cynoteck Technology Solutions
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Datamorphosis Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] Day One Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > No Pickup(08-05S)

[1] Dazo
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Deft Infosystems (P) Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > No Pickup(08-05S)

[1] Destm Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > No Pickup(08-05S)

[1] Dev IT Serv
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Dev Information Technology Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] DevAngles Software Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Dew Solutions Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Differenz System
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] DigiLantern
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Digiapt Software Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Digital Convergence Technologies Pune Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Dignizant Technologies LLP
     src=Private Codebase Tracker sheet ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Diksha Technologies
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Divami
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Dolphin Web Solution
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Doormint
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Doshaheen
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Drish Infotech Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Dunzo
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] EC Infosolutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > No Pickup(08-05S)

[1] EMINENTURE
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] EWall Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Ebluesoft Infotect Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] Ecosmob Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Edstem Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Ejyle Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] Elicit Digital
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > No Pickup(08-05S)

[1] Email Mavlers
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Embarkingonvoyage Digital Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Emergent
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-06H)

[1] Emizen Tech Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] EnH
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-07 age=10d idle=7d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H) > Dead/ColdCall/WrongFit(08-10H)

[1] EnactOn Technologies Private Limited
     src=Private Codebase Tracker sheet ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Envigo
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Enviri Global Service Centre
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Epixel Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > No Pickup(08-05S)

[1] Esolz Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > No Pickup(08-05S)

[1] Euphoric Thought Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=3 tasks=3 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Exaltare Technologies Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Exclusive-OR (XOR) Labs Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Explorex
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Exponentia.ai Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] F13 Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] FEXLE Services Private Limited
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] FamApp
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] FanGame Live
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Fastcurve
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=1 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > No Pickup(08-05S)

[1] Fegno Technologies
     src=Private Codebase Tracker sheet ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] FifthTry
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-06H)

[1] FindYahan
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Finoit Technologies, Inc
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Finzy
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Flashdoor
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Flexsin
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Fluentgrid Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Fluper
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Fokuz
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Foogle Tech Software
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] FreeStand
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=5d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-12H)

[1] Frenzi
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] FrontRow
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Fusion Informatics Limited
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Futuresoft India
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] GFN D'selva Infotech Pvt. Ltd.
     src=Private Codebase Tracker sheet ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-07-30 age=18d idle=14d moves=4(h3) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-31H) > Dead/Interested/NoShow(07-31H) > Dead/ColdCall/WrongFit(08-03H)

[1] GSA Techworld
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] GYTWorkz Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Galaxy Weblinks
     src=Founder Search ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Gamitronics
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Gateway Internet Protocol Management Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] Geekay Infotech
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] Gird technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Global Groupware Solutions Ltd
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] Globtier Infotech Limited
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Goavega Software India Pvt Ltd
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Gofrugal
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-08-07 age=10d idle=7d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H) > Dead/ColdCall/WrongNumber(08-10H)

[1] GreatFour Systems Private Limited
     src=Scraped ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] GroMo
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Gurmukh Singh Chauhan
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=2(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Call Attempted (retired)(07-29S) > No Pickup(08-05S)

[1] Gurpreet Singh Modi
     src=Linkedin Campaign ( IT Services ) | owner=Lamiya Saleem | pipe=Campaign | stage=No Pickup
     created=2026-08-10 age=7d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-10S) > No Pickup(08-13H)

[1] HNR Tech
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Hacker Associate
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Harbinger Systems Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Harrier Information Systems
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Heliware
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Hexagon India
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Hidden Brains InfoTech
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] HotelKey
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > No Pickup(08-05S)

[1] Housejoy
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] HummingWave Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Ideesys
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > No Pickup(08-05S)

[1] Illuminz
     src=Founder Search ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Imenso Software
     src=Founder Search ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Impero IT Services Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] InCruiter
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Inceptive Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=1 tasks=2 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > No Pickup(08-05S)

[1] Indglobal Digital
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > No Pickup(08-05S)

[1] Indian Cyber Security Solutions (CyberSecOps Pvt.Ltd.)
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Indovision Services Private Limited
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-12H)

[1] Inferenz Tech Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Infiflex Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] InfoCepts Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Infognana Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Infoneo Technologies Private Limited
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-08-11 age=6d idle=5d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H) > Dead/ColdCall/WrongNumber(08-12H)

[1] Infopercept
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Infoskaters Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-07-22 age=26d idle=25d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > Dead/ColdCall/WrongFit(07-23H)

[1] Infowind Technologies
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-11 age=6d idle=5d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H) > Dead/ColdCall/WrongFit(08-12H)

[1] InfraBeat Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-12H)

[1] InitiateFirst Information Services Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Inno Valley Works Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Innovative Logic Lab Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Input Zero Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Insane AI
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Inspirisys Solutions Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Intellismith
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Invezza Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Invimatic Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-23 age=25d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-27H) > No Pickup(08-05S)

[1] Ishttaa TechCraft Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Isourse
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Jamtech Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Jconnect Infotech
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Jitendra Sarangi
     src=Linkedin Campaign ( IT Services ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Juleo
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Jupitice Justice Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] JustDeliveries
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Justifi.World
     src=Linkedin Campaign ( IT Services ) | owner=Ishpreet Sood | pipe=Campaign | stage=No Pickup
     created=2026-08-05 age=12d idle=12d moves=3(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > Call Attempted (retired)(08-05H) > No Pickup(08-05S)

[1] KPMG
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=No Pickup
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-06H)

[1] Kaagaz
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-13H)

[1] Kansoft
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Kapil Tomar
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=2(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Call Attempted (retired)(07-29S) > No Pickup(08-05S)

[1] Kedar Swadi
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=3(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Call Attempted (retired)(07-29H) > No Pickup(08-05S)

[1] Klaus IT Solutions Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-08-07 age=10d idle=7d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H) > Dead/ColdCall/WrongNumber(08-10H)

[1] Knoewit | The AI Unpacked
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-06H)

[1] Knowl
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-06H)

[1] Konverge Technologies
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-12H)

[1] Kratikal
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Krazy Mantra Group of Companies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Krish Software Services (India) Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] KritiKal Solutions Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Kushagra Tyagi
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=3(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Call Attempted (retired)(07-29H) > No Pickup(08-05S)

[1] LOGICWIND
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Langhar
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-08-04 age=13d idle=13d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > Dead/ColdCall/WrongNumber(08-04H)

[1] Latent View Analytics Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Lido
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Lighthouse Info Systems Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] LimeTray
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Lobotus Technology Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-23 age=25d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-27H) > No Pickup(08-05S)

[1] LocalBanya
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-08-04 age=13d idle=13d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > Dead/ColdCall/WrongNumber(08-04H)

[1] Locus Rags
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-03 age=14d idle=14d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > Dead/ColdCall/WrongFit(08-03H)

[1] Love Chopra
     src=Linkedin Campaign ( IT Services ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-08-10 age=7d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-10S) > No Pickup(08-14H)

[1] MMJS Dataphi Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Manabendra Pattnaik
     src=Linkedin Campaign ( IT Services ) | owner=Lamiya Saleem | pipe=Campaign | stage=No Pickup
     created=2026-08-10 age=7d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-10S) > No Pickup(08-13H)

[1] Mango IT Solutions
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Mass Software Solutions Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Max Mobility
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] MedPay
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Merino Consulting Services
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] MetaDesign Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] MetaSys Software Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] MicroGenesis TechSoft
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Mindfire Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Mindstix Software Labs
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Mitroz Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-23 age=25d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-27H) > No Pickup(08-05S)

[1] MobileFirst Applications | Fintegration
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Mobiloitte
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Monepeak Fintech Private Limited (CARD91)
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Moolya
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Mudit Aggarwal
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=3(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Call Attempted (retired)(07-29H) > No Pickup(08-05S)

[1] MyWash
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Mykare Health
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] NWORX
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-13H)

[1] Neebal Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Netwin Infosolutions
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Network kings
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Neuphony
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] NexGen Tech Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] NexSemi Systems Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-23 age=25d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-27H) > No Pickup(08-05S)

[1] Nexus Corporate Solution Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Nimap Infotech
     src=Private Codebase Tracker sheet ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Niyati Agarwal
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=2(h0) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Call Attempted (retired)(07-29S) > No Pickup(08-05S)

[1] Noventiq India
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-08-07 age=10d idle=7d moves=3(h2) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H) > Dead/ColdCall/WrongNumber(08-10H)

[1] NuCore Software Solutions Pvt Ltd
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Oak Tree Software
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] OdiTek Solutions
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] OfficePulse
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Oga
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] OneClickWash
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Open Network For Digital Commerce (ONDC)
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] OpenXcell
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-23 age=25d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-27H) > No Pickup(08-05S)

[1] Opinio
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] OptiSol Business Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] OroSoft Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Otipy
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Oye Rickshaw
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-13H)

[1] PROVAB TECHNOSOFT
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-11H)

[1] Pace Wisdom Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-23 age=25d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-27H) > No Pickup(08-05S)

[1] Pairee Infotech Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Parcelled
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Payatu
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Perfios
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-23 age=25d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-27H) > No Pickup(08-05S)

[1] Personal Projects
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(08-05H) > No Pickup(08-05S)

[1] Pi Data Centers
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] PiTangent Analytics And Technology Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Pickcel
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-23 age=25d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Pipra Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Planet Web Solutions Pvt. Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Pluss
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Plutomen Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] PokerDangal
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Probey Services
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-23 age=25d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Procedure Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] ProfitWheel
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-06H)

[1] Progton Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-23 age=25d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] ProwessSoft
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] QAAgility Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-17H)

[1] QED42
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-23 age=25d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] QSQUARE BIZSOFT Private Limited
     src=Linkedin Campaign ( IT Services ) | owner=Lamiya Saleem | pipe=Campaign | stage=No Pickup
     created=2026-08-05 age=12d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > No Pickup(08-13H)

[1] QTalk
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] QalbIT Infotech Pvt Ltd.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Qapitol
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] QodeNext
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Qualityze Inc
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-23 age=25d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Quarks Technosoft Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Questpond
     src=Linkedin Campaign ( IT Services ) | owner=Lamiya Saleem | pipe=Campaign | stage=No Pickup
     created=2026-08-05 age=12d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > No Pickup(08-13H)

[1] Quocent Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] R360 Group
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] RV Solutions Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Rahul N.
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=3(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-29S) > Call Attempted (retired)(07-29H) > No Pickup(08-05S)

[1] Railofy
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Ramprasad Subramanian
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=2(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Call Attempted (retired)(07-29S) > No Pickup(08-05S)

[1] Rang De
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Rapyder Cloud Solutions
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-08-07 age=10d idle=5d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-12H) > Dead/ColdCall/WrongNumber(08-12H)

[1] Real Time Data Services
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-12H)

[1] Reflections Info Systems
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] RefreshMint
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-13H)

[1] RemoteState
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Resilient AI Solutions
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] RevFin
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Rishabh Software Pvt Ltd
     src=Scraped ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Robotico Digital®
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Rooba Finance
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] SD Innovations
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] SDET Tech
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] SDLC Corp
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] SE Mentor Solutions
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] SIDANA VENTURES
     src=Outflo Outreach ( Startups ) | owner=Lamiya Saleem | pipe=Campaign | stage=No Pickup
     created=2026-08-05 age=12d idle=12d moves=3(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > Call Attempted (retired)(08-05H) > No Pickup(08-05S)

[1] SUMERU DIGITAL SOLUTIONS
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] SVARAPPS Technologies Group
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Saarthi Pedagogy
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-13H)

[1] Sachiko Gaming
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=4(h2) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Dead/ColdCall/WrongFit(08-03H) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Safe Software and Integrated Solutions Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] Sagarsoft (India) Ltd
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Sahana Srinivasan
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=2(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Call Attempted (retired)(07-29S) > No Pickup(08-05S)

[1] Salt Web Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=Dead/ColdCall/WrongFit
     created=2026-08-13 age=4d idle=3d moves=3(h2) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H) > Dead/ColdCall/WrongFit(08-14H)

[1] Sankhyana Consultancy Services Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Sapiens
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-06H)

[1] Satyukt
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] ScatterPie Analytics
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] SecureLayer7
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Seekho
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Seneca Global IT Services Pvt Ltd
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Seqrite
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Servosys Solutions
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-12H)

[1] Sharat Kaul
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=2(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Call Attempted (retired)(07-28S) > No Pickup(08-05S)

[1] Shivam Chhuneja
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=2(h0) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Call Attempted (retired)(07-29S) > No Pickup(08-05S)

[1] Shyam Future Tech Private Limited
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Siddhatech Software Services Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Signity Software Solutions Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Simform
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > Dead/ColdCall/WrongNumber(08-05S)

[1] Simplior Technologies Pvt Ltd.
     src=Founder Search ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Singularity Automation
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Sketch Brahma Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] SmartCheck
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] SmartX Technologies
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-23 age=25d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-23S) > Call Attempted (retired)(07-23H) > No Pickup(08-05S)

[1] Soft Suave Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Softcell Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Solace Infotech Private Limited
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Squash Apps Private Limited
     src=Founder Search ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Stark Digital Media Services Pvt Ltd
     src=Founder Search ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] StratLytics Consulting Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Streamvector Technology Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Sumanas Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] SuperLearn
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Sydler Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Synconics Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Synoverge Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Systweak Software
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] TECHVED Consulting India Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] TVS Next
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Taggle
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Talentas Technology Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Talentica Software
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] Tavant Technologies India Pvt Ltd
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] TaxiForSure
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Tech Prastish Software solutions Pvt. Ltd .
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Tech4biz Solutions Private Limited
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-28 age=20d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-28S) > Call Attempted (retired)(07-28H) > No Pickup(08-05S)

[1] TechChefz Digital
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] TechDefence
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] TechVerito
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Techigent Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Technodysis
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Technorizen Software
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Techsaga Corporations
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Techsharks Internet Services Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Techspawn Solutions
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Teleglobal International
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Tesseract Learning Inc
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] TestUnity
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] TestVagrant Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Think360.ai
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] Thinkitive Technologies Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] ThoughtSol Infotech Ltd.
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-12H)

[1] Tilicho Labs LLP
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Totality Corp
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Townrush
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] TraceX
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Tridhya Tech Limited
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] TruSpeQ Consulting Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Truetech
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Turain Software Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Tyto Software Private Limited
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Udayy
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Umbrella Infocare
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Urban Dhobi
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] VEGA Intellisoft Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] VTNetzwelt
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Vasundhara Infotech
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Vayavya Labs
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Velotio
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Vidya
     src=Linkedin Campaign ( IT Services ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-08-05 age=12d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-05S) > No Pickup(08-17H)

[1] Vikas Singh
     src=Outflo Outreach ( Startups ) | owner=- | pipe=Campaign | stage=No Pickup
     created=2026-07-29 age=19d idle=12d moves=2(h0) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Call Attempted (retired)(07-29S) > No Pickup(08-05S)

[1] VividMinds Technologies
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Vortex Infosolutions LLP
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Votary Softech Solutions Pvt. Ltd.
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] WarpDrive Tech Works
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Webner
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] WhizHack Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Wissen Technology
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Workcog Inc
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Wyreflow Technologies
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] XILLIGENCE
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=10d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-07H)

[1] Xcaliber Infotech Pvt. Ltd. - A Phoenix Group Company
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Xencia Technology Solutions
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] XongoLab Technologies LLP
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] XtraNet Technologies Limited
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-12H)

[1] Xuriti
     src=Tracxn Sheet ( Startups ) | owner=Ishpreet Sood | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] YUJ Designs Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] Yudiz Solutions
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] Zansaar
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Zediant Technologies Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-14H)

[1] Zeeve
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] Zelite
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] Zetagile
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-17 age=0d idle=0d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-17S) > No Pickup(08-17H)

[1] Zocket
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > Dead/ColdCall/WrongNumber(08-05S)

[1] Zoko
     src=Tracxn Sheet ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-06H)

[1] Zones India
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] ZuperMeal
     src=Scraping Algo ( Startups ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=1 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] Zyple Software Solutions Pvt Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-03H) > No Pickup(08-05S)

[1] de facto Infotech
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=2 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] doodleblue Innovations
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-12H)

[1] eQuest Solutions
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(07-30H) > No Pickup(08-05S)

[1] eSec Forte® Technologies
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] factors.ai
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-03 age=14d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-03S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] hikeQA
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] iAssure International Technologies Pvt. Ltd
     src=Scraping Algo ( IT services ) | owner=- | pipe=Scraped | stage=Dead/ColdCall/WrongNumber
     created=2026-07-22 age=26d idle=12d moves=3(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-22S) > Call Attempted (retired)(07-22H) > Dead/ColdCall/WrongNumber(08-05S)

[1] iPrime Services Private Limited
     src=NASSCOM ( IT Services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-14 age=3d idle=3d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-14S) > No Pickup(08-14H)

[1] iWork Technologies Pvt Ltd
     src=NASSCOM ( IT Services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-13 age=4d idle=4d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-13S) > No Pickup(08-13H)

[1] koinearth
     src=Tracxn Sheet ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-07-30 age=18d idle=12d moves=3(h1) notes=0 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] mChemist
     src=Scraping Algo ( Startups ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-04 age=13d idle=12d moves=3(h1) notes=3 tasks=1 LoC=- PR=- ratio=-
     path: Cold Call(08-04S) > Call Attempted (retired)(08-04H) > No Pickup(08-05S)

[1] orangemantra
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] phonon, automating outcomes
     src=Scraping Algo ( IT services ) | owner=Yuktha Anand | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=6d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-11H)

[1] smartSense Consulting Solutions
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-11 age=6d idle=5d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-11S) > No Pickup(08-12H)

[1] techugo
     src=Scraping Algo ( IT services ) | owner=Lamiya Saleem | pipe=Scraped | stage=No Pickup
     created=2026-08-07 age=10d idle=7d moves=2(h1) notes=1 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(08-07S) > No Pickup(08-10H)

[1] xaults
     src=Outflo Outreach ( Startups ) | owner=Yuktha Anand | pipe=Campaign | stage=No Pickup
     created=2026-07-30 age=18d idle=11d moves=2(h1) notes=2 tasks=0 LoC=- PR=- ratio=-
     path: Cold Call(07-30S) > No Pickup(08-06H)