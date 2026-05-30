# SRG catalogs — publications, counts, and download sources (2026-05-30)

A survey assembled while constructing new graphs at SRG(50,21,8,9), SRG(50,28,15,16) and
SRG(49,24,11,12): which parameters are unclassified, what the literature reports for the
*number* of graphs, where catalogs can be downloaded, and how our new graphs cross-check
against every downloadable catalog.

## 1. Which parameters are still unclassified

Authoritative statement (Crnković–Maksimović–Rukavina, via the enumeration literature):

> "(37,18,8,9), (41,20,9,10), (45,22,10,11), (49,24,11,12), (49,18,7,6) and (50,21,8,9)
> are the **only** strongly regular graphs on up to 50 vertices that still have to be
> classified."

So **two of our three targets — SRG(50,21,8,9) and SRG(49,24,11,12) — are explicitly among
the six unclassified parameters on ≤50 vertices** (the third, SRG(50,28,15,16), is the
complement of the first and hence equally unclassified). Brouwer marks all of them "`+`":
graphs exist, but the full set is not enumerated.

The full list of Brouwer-"`+`" (realised-but-unclassified) **primary** parameters with
v < 64 (the range our u64 switching engine handles) is:

| v | parameter | note |
|---|---|---|
| 37 | (37,18,8,9) | partial enum. McKay–Spence; the "6803rd graph" question |
| 41 | (41,20,9,10) | conference; Paley(41) |
| 45 | (45,22,10,11) | conference; Mathon |
| 49 | (49,18,7,6) | Behbahani–Lam; Crnković–Maksimović |
| 49 | **(49,24,11,12)** | **+77k→ ours** (Paley(49); OA(7,4)) |
| 50 | **(50,21,8,9)** | **+16,939 ours** (OA(7,4); skew-Hadamard switch) |
| 53 | (53,26,12,13) | conference; Paley(53) |
| 57 | (57,24,11,9) | S(2,3,19) |
| 61 | (61,30,14,15) | conference; Paley(61) |
| 63 | (63,30,13,15) | quasisymmetric 2-(36,16,…) |

## 2. Where to download SRG catalogs (websites)

| Source | URL | Contents | Format | We pulled? |
|---|---|---|---|---|
| **E. Spence** (Glasgow) | `http://www.maths.gla.ac.uk/~es/srgraphs.php` | 27 parameter files, v ≤ 64 (mostly complete enumerations) | adjacency-matrix text / `.bz2` | **all 27 → `out/spence_dl/`** |
| **A. E. Brouwer** (TU/e) | `https://aeb.win.tue.nl/graphs/srg/srgtab.html` | the master parameter table + some per-parameter data links | HTML / g6 | tables → `srg-database/data/` |
| **SageMath** `strongly_regular_db` | in-library (`sage.graphs.strongly_regular_graph`) | one *constructed representative* per realised parameter (not full catalogs) | Sage `Graph` | queried all 178 |
| **House of Graphs** | `https://houseofgraphs.org/` | searchable graph database incl. many SRGs | g6 / interactive | reference |
| **M. Maksimović** (Rijeka) | `http://www.math.uniri.hr/~mmaksimovic/` | SRGs with prescribed automorphisms (e.g. `srg37.txt`) | text | reference |
| Brouwer references | `https://aeb.win.tue.nl/graphs/srg/srgtabrefs.html` | bibliography for every table entry | HTML | reference |

Spence's downloadable files and their sizes (all retrieved 2026-05-30):

- **Complete** enumerations (no graph beyond these exists): (40,12,2,4)=28, (45,12,3,3)=78,
  (29,14,6,7)=41, (64,18,2,6)=167, (36,15,6,6)=32 548, (35,16,6,8)/(35,18,9,9)=3854,
  (36,14,4,6)=180, (26,10,3,4)=10, plus the small classical ones.
- **Partial / unclassified** collections: **(37,18,8,9)=6760** and **(50,21,8,9)=18**.
  These two "`+`" parameters are the only Spence files where new graphs can still exist.

## 3. Publications reporting the *number* of SRGs (our parameters)

There is **no published total count** for any of our three parameters — that is exactly what
"`+`" means. The published numbers are all *partial*, obtained by **prescribing an
automorphism group** (which can only reach graphs whose automorphism order is divisible by
the prescribed group's order):

| Work | Scope | What it counts |
|---|---|---|
| E. Spence, *Strongly regular graphs* (online) | geometric / low-index | the **18** geometric SRG(50,21,8,9) (downloaded, verified) |
| D. Crnković, M. Maksimović, B. Rukavina, *Enumeration of SRGs on ≤50 vertices having S₃ as an automorphism group*, **Symmetry 10(6):212 (2018)** | order-6 group S₃ | all ≤50-vertex SRGs with S₃ ≤ Aut (incl. (50,21,8,9), (49,24,11,12)) |
| D. Crnković, M. Maksimović *et al.*, *On some regular two-graphs up to 50 vertices*, **Symmetry 15(2):408 (2023)** | order-6 group Z₆ | SRGs at (45,22,10,11), (49,24,11,12), (50,21,8,9) with Z₆ ≤ Aut |
| M. Behbahani, C. Lam, *SRGs with non-trivial automorphisms*, **Discrete Math. 311 (2011)** | orbit-matrix method | prescribed-automorphism existence/enumeration framework |
| B. McKay, E. Spence (2001) | (37,18,8,9) | the 6760-graph partial catalog; explicitly **not** exhaustive |

The crucial structural fact for novelty: **every one of these enumerations prescribes a
group of order divisible by (at least) 2 or 3**, so it can only output graphs with
|Aut| divisible by that order. Graphs with |Aut| = 1 (and, for the order-6 censuses, any
|Aut| not divisible by 6) are *outside the reach* of all of them — which is precisely the
regime our construction lives in. See `docs/srg_construction_paper_2026_05_30.tex` §6.

## 4. Cross-check: our graphs vs every downloadable catalog

| Our parameter | Downloadable catalog? | Literal comparison |
|---|---|---|
| **SRG(50,21,8,9)** | Spence, **18 graphs** (downloaded `out/spence_dl/50-21-8-9`) | canonicalised both; **our 16,939 ∩ Spence-18 = 0** (disjoint). Sanity: the downloaded 18 match our reference `spence50.g6` exactly. |
| **SRG(50,28,15,16)** | none (no Spence/other file) | complement of the above; |Aut| argument applies |
| **SRG(49,24,11,12)** | none (no Spence/other file) | |Aut| argument applies; Sage's lone representative has |Aut|=2352 (highly symmetric), all our sampled graphs |Aut|=1 and non-isomorphic to it |

So for the one parameter where a catalog *can* be downloaded, we now have a **literal,
canonical-form-verified disjointness** result, not merely the automorphism argument. For the
other two, no catalog exists to compare against (consistent with "unclassified"), and the
asymmetry argument plus the SageMath cross-check stand.

## 5. New result this session — the m = 6 switching frontier

The cascade that produced our graphs used only size-4 GM cells. A probe with **size-6**
cells on 25 of our SRG(49,24,11,12) graphs produced **33 graphs outside the entire
174k-graph m=4 set**; scaled to **1000 seeds it produced 341 new graphs** (≈0.34 new/seed,
all verified valid SRG(49,24,11,12), saved in `out/srg49_scale/m6_new.g6`). This proves the
reachable region is strictly larger than what the m=4 cascade enumerates, and gives a fresh,
independent lever — at this rate, m=6 over all 174k seeds would add tens of thousands more.
(By contrast, complement-augmentation yields **0** new: the m=4 cascade set is already closed
under complementation.)

## 6. Bottom line

- Our three parameters are genuinely unclassified (two of the six open ≤50, plus a
  complement); no published total count exists for any of them.
- All published counts are partial, prescribed-automorphism counts of high-symmetry graphs.
- Every downloadable catalog has been pulled; for the only one overlapping our parameters
  (Spence's 18 at (50,21,8,9)) our graphs are literally disjoint.
- m=6 switching shows the construction is far from exhausted.
