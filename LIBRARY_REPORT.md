# SRG Library — build report (2026-11-07)

Local only; nothing pushed or published. Open `library.html` directly in a browser (no server needed).

## What was built

New static pages beside the existing `index.html` (v ≤ 100) and `z3.html`, which are unchanged:

| page | content |
|---|---|
| `library.html` | Landing view. Six headline tiles; a **map** of all 2,431 parameter pairs (v across; k, −s or μ up; ● exists / ■ does not exist / ○ open, colour-blind-safe colours that passed the palette validator in light and dark); a family / "classified" / "changed" highlight; hover or tap gives (v,k,λ,μ), status, count of known graphs and the first construction, click opens the row. Below: a **stacked bar per range of 100 vertices**, a list of **status changes** between Brouwer's tables of 2026-10-13 and 2026-11-07, and a searchable, filterable **table** (parameters, comment text, status, v range, family, complements, "with counts"). Each row opens a **detail view** (`library.html#row=v-k-l-mu`, a drawer) with status + link to Brouwer's page for that row, complement, exact spectrum (checked against Brouwer's columns), known graphs with each count's source, constructions (family chips + Brouwer's comments on both lines, with his reference links), nonexistence reasons, published Kovaľ deposits, partial results from the literature, Sage's answer, seed-database placeholder, downloads, and the full references. |
| `families.html` | 23 families (Paley, T(n), Latin square OA(n,m) / n², Steiner S(2,K,V), GQ(s,t), pg(s,t,α), regular two-graphs, polar, affine polar, two-weight codes, RSHCD, switching, Wallis–Fon-Der-Flaass, quasi-symmetric designs, van Lint–Schrijver, Goethals–Seidel, Godsil, Pasechnik, Mathon, ETFs, bilinear forms, lines of PG/AG, sporadic graphs): description, parameter formula where there is one, the pairs whose comment names it, references. |
| `stats.html` | Pairs by status and v range, nonexistence reasons, what is known per realised pair, sources of counts, Sage versus Brouwer, validation summary. |
| `references.html` | Complete bibliography (143 entries): Brouwer's 113 references in his wording, further literature, the Kovaľ deposits, books/catalogues/software; each entry lists the pairs that cite it; Spence's five references verbatim. |
| `downloads.html` | The Library's own data (CC BY 4.0), Brouwer, Spence (26 parameter files with counts), Ihringer (27 collections), Kovaľ deposits, Sage, House of Graphs, and a per-pair table of download links. Third-party files are linked, never copied. |
| `about.html` | Sources with fetch dates, method, what is deliberately not shown, the 57_24_11_9 caveat, how to cite, licence, rebuilding. |

Engineering: vanilla JS (no library), shared `assets/library.css` / `assets/library.js` / `assets/library-page.js`; light/dark via tokens (`prefers-color-scheme` + a theme button); works from `file://` (data are loaded as `.js` wrappers of the JSON files); checked at 1280 px and in a 375 px frame (no horizontal page scroll; wide tables scroll inside their box).

Data (`data/library/`, rebuilt by `build_library.py`, stdlib Python):
`index.json` (one compact line per parameter set), `rows-0001-0100.json` … `rows-1201-1300.json` (full records), `refs.json`, `families.json`, `reasons.json`, `downloads.json`, `meta.json` (dates, statistics, warnings) — each also as `.js`. Curated inputs in `data/library/sources/`:
`sage_constructions.tsv`, `ref_links.tsv` (Crossref DOI lookups + 4 manual), `ref_urls.tsv`, `dead_links.tsv`, `spence_counts.tsv`, `ihringer_rows.tsv`, `our_deposits.tsv`, `srgdb_catalogs.tsv`, `counts_literature.tsv`, `link_check.tsv`.
Tools: `tools/sage_constructions.py` (inside `sagemath/sagemath:latest`, `--network none --cpus 1`), `tools/enrich_refs.py` (Crossref), `tools/validate_library.py` (`--online` resolves every DOI/arXiv/URL).

Rebuild: `MSYS_NO_PATHCONV=1 wsl python3 -I /mnt/c/Users/akova/IdeaProjects/srg-database/build_library.py` then `… tools/validate_library.py [--online]`.

## Sources and dates

| source | used for | date |
|---|---|---|
| A. E. Brouwer, srgtab1-50 … srgtab1251-1300 + srgtabrefs (live, 27 GETs) | status, comments, eigenvalue columns, references | fetched 2026-11-07 07:36 UTC (raw copy `D:\srg-library\external\brouwer\2026-11-07\`; identical to the 2026-11-02 copy) |
| Brouwer snapshot of 2026-10-13 (`orbit-gen/out/brouwer_check_1013`) | list of status changes only | 2026-10-13 08:12 UTC |
| E. Spence, srgraphs.php + 27 data files (local copy on D:) | counts read from the files (TOTAL line / number of matrices), completeness notes, links | copied 2026-11-07 |
| F. Ihringer, srgs.php (local copy on D:) | per-row counts, method and seed from the page text; links | copied 2026-11-07 |
| SageMath 10.10 strongly_regular_db | existence answer + constructor for all 4,538 sets | run 2026-11-07 |
| srg-open-cases papers.html / graphs.html | 20 public Kovaľ deposits, graphs per deposit | read 2026-11-07 |
| programme ledger | only PROVED-OURS-AUDITED rows whose source is a public Zenodo DOI (maps the 70 BMV pairs to their deposit), and the PROVED-LIT "no Cayley graph" records of arXiv:2507.23039 | 2026-11-07 |
| literature.tsv | only 6 whitelisted items, metadata re-checked on arXiv/Crossref/Zenodo (the rest of the file has summarised titles and internal notes) | 2026-11-07 |
| literature counts (web research) | 14 published counts, each with DOI/arXiv/URL and the quoted sentence | 2026-11-07 |
| Crossref / DataCite / arXiv APIs | DOIs for Brouwer's references; link check | 2026-11-07 |
| seed database (`orbit-gen/out/seeddb_2026_11_07`) | **placeholder**: no REPORT.md yet; `build_library.py` imports a per-row table (`constructions.tsv`, `seed_constructions.tsv` or `rows.tsv` with `row` + `construction`) as soon as REPORT.md exists | — |

## Row counts

- 4,538 parameter sets = **2,431 pairs** (all lines of Brouwer's 26 pages up to v = 1300).
- Status per pair (Brouwer, 2026-11-07): **688 exist (+), 384 do not exist (−), 1,359 open (?)**.
- Known graphs per realised pair: **112 complete classifications** (Brouwer's "!" 101 + "N!" 11; Spence, Bondarenko–Radchenko agree where they overlap), **46 with a published lower bound > 1**, 530 "at least one".
- Pairs with a count from: Brouwer 112, Spence 26, Ihringer 17, literature 13, Kovaľ deposits 21, srg-database switching catalogues 3.
- Constructions: **647 of 688** realised pairs carry at least one family label; every realised pair shows Brouwer's comment.
- References: 559 pairs have a specific reference (Brouwer reference, deposit, literature or count source); 143 bibliography entries (deposits already in Brouwer's list under the same DOI are merged into his entry).
- Nonexistence reasons over the 384 "−" pairs: conference condition 130, absolute bound 101, Krein 91, specific paper 100, μ = 1 condition 5, Neumaier 4, no regular two-graph 3 (a pair can have several).
- Kovaľ deposits are attached to 106 pairs (70 of them the BMV paper); download links on 70 pairs.
- Changes 2026-10-13 → 2026-11-07: 20 pairs (13 to "+", 7 to "−").
- Sage: True 1,165 / False 460 / Unknown 2,905 parameter sets; no disagreement with Brouwer.

## Validation

`tools/validate_library.py --online` (result in `data/library/sources/link_check.tsv`):

1. **Every row of Brouwer's table up to 1300 appears**: 4,538 lines in the pages = 4,538 rows, 0 missing, 0 extra, 0 duplicates. Each status symbol agrees with the row colour.
2. Spectra recomputed exactly for all 4,538 sets agree with Brouwer's r^f, s^g columns (0 mismatches). Every "Krein", "Absolute bound" and "Conf" label was re-checked against the inequalities, and every set failing a classical condition is "−" (0 warnings).
3. Family formulas reproduce every labelled row: Paley 118/118, two-graph 339/339, Latin square 338/338, triangular 47/47, GQ 26/26, Steiner 82/82, pg 18/18 (Wallis' "AR+S(2,…)" and "switch OA" labels are not counted as Steiner / Latin square graphs).
4. **References**: 143 entries, 0 without a link. DOIs, arXiv ids and URLs resolved online: final run: 91 DOIs, 22 arXiv ids and 29 URLs all resolve (0 failures). Two problems found and fixed on the first run: the Spence 1995 DOI (corrected to 10.1016/0024-3795(95)00158-N) and a dead NC State URL in Brouwer's Mesner64 entry (omitted; Brouwer's entry is linked). 20 entries (emails recorded by Brouwer, theses, 1898–1976 items without DOI) resolve only through their entry in Brouwer's reference page. No "in preparation" entry.
5. Forbidden strings (internal vocabulary, local paths, e-mail addresses, "in preparation", CONFIDENTIAL/PRIVATE) in the published JSON: 0.
6. Restricted rows (srg(300,117,60,36), srg(232,77,36,20), all v = 442, with complements; 8 sets): Brouwer status/comment and computed spectrum only — checked.

### Hand spot-check of 20 rows against Brouwer's raw pages

Raw `<tr>` of the fetched page compared with the Library record (status/symbol, r^f s^g, comment, page, counts):

| row | Brouwer | Library | ok |
|---|---|---|---|
| (5,2,0,1) | ! · 0.6182² −1.6182² · pentagon; Paley(5); Seidel 2-graph* | + / 1 complete; (−1±√5)/2, f=g=2; Paley, two-graph | yes |
| (16,6,2,2) | 2! · 2⁶ −2⁹ · Shrikhande graph; 4²; … RSHCD+ | 2 complete (Brouwer, Spence) | yes |
| (21,10,4,5) | − · Conf | conference condition | yes |
| (36,15,6,6) | 32548! · 3¹⁵ −3²⁰ · complete enumeration by McKay & Spence; OA(6,3); NO⁻(6,2); RSHCD+; 2-graph | 32,548 complete | yes |
| (37,18,8,9) | + · partial enumeration by McKay & Spence; … Paley(37) | ≥ 6,802 (Maksimović–Rukavina 2022; also 6,766 and Spence 6,760) | yes |
| (57,14,1,4) | − · Wilbrink-Brouwer | specific paper, ref WilbrinkBrouwer83 | yes |
| (64,18,2,6) | 167! · 2⁴⁵ −6¹⁸ · Haemers & Spence; GQ(3,5); … | 167 complete; GQ, two-weight codes | yes |
| (99,14,1,2) | ? · 3⁵⁴ −4⁴⁴ · (no comment) | open; Kovaľ structure preprint linked | yes |
| (100,22,0,6) | ! · 2⁷⁷ −8²² · Higman-Sims; unique by Gewirtz | 1 complete | yes |
| (162,21,0,3) | ? · 3¹⁰⁵ −6⁵⁶ | open | yes |
| (217,66,15,22) | + · 4¹⁵⁴ −11⁶² · Kovaľ + AI; pg(6,10,2)? | ≥ 1 (deposit 23454170); pg? not counted as family | yes |
| (243,22,1,2) | + · 4¹³² −5¹¹⁰ · Berlekamp–vanLint–Seidel; not unique - Djematene + AI; Golay code | ≥ 4 (Djematene deposit); rediscovery note on our deposit | yes |
| (288,112,36,48) | + · 4²²⁴ −16⁶³ · Kovaľ + AI; pg(7,15,3)? | ≥ 1 (deposit 23870797) | yes |
| (300,117,60,36) | ? · 27²⁶ −3²⁷³ | open, restricted (Brouwer only) | yes |
| (351,140,73,44) | − · Liao-Yu | specific paper | yes |
| (442,210,99,100) | + · 10²²¹ −11²²⁰ · Plummer; 2-graph | + ≥ 1, restricted (Brouwer only) | yes |
| (729,112,1,20) | ! · 4⁶¹⁶ −23¹¹² · Hill cap …; Bondarenko-Radchenko | 1 complete (Brouwer; Bondarenko–Radchenko) | yes |
| (833,416,207,208) | + · 13.931416⁴¹⁶ −14.931416⁴¹⁶ · Kovaľ + AI; 2-graph* | ≥ 24 (deposit 23771335) | yes |
| (1026,369,144,126) | + · 27²⁴⁶ −9⁷⁷⁹ · Jasper | ≥ 1 | yes |
| (1296,595,274,272) | + · 19⁵⁹⁵ −17⁷⁰⁰ · Kovaľ + AI; OA(36,17)? | ≥ 6 (deposit 23296158) | yes |

## Needed edit in README.md / index.html (not made — for the author)

- `README.md` (Results table) and `index.html` call the 1,122,556 srg(57,24,11,9) graphs (and their 1,122,556 complements) **new**. Ihringer's collection lists 31,490,375 graphs for this row, and Kaski–Östergård (Math. Comp. 73 (2004) 2075–2092, doi:10.1090/S0025-5718-04-01626-6) state that the block graphs of the 11,084,874,829 Steiner triple systems of order 19 give a lower bound on the number of non-isomorphic srg(57,24,11,9) — so asymmetric GM-switched graphs could be among them as well. Suggested wording until a comparison is done: "1,122,556 constructed by GM switching (overlap with Ihringer's collection and with the STS(19) block graphs not yet checked)".
- The same caution applies to the "new" claims for (49,24,11,12) (Maksimović 2023 reports 1,183 descendants of known two-graphs on 50 points) and (50,21,8,9) (checked disjoint from Spence's 18 only).
- `README.md` and `catalogs/README.md` give 395,966 for (49,24,11,12) and a total of 2,674,956; `index.html` gives 418,389 and 2,697,379. The Library uses 418,389 (index.html, commit 4a78336 "Final count").
- Suggest adding a link to `library.html` from `README.md` and `index.html`.

## Open issues

1. **Seed database**: placeholder only (no `REPORT.md` in `out/seeddb_2026_11_07/`); the import expects a per-row table — adjust the file name / columns in `build_library.py` (search "seed database") once its format is known.
2. **Timeline**: not drawn. Brouwer's table dates only cited papers; classical constructions and bounds carry no dates, so a "settled per year" chart would mislead. The page shows the status changes between two snapshots instead.
3. **Counts not yet included** (need a check first): counts derived from Latin squares (main classes ↔ non-isomorphic Latin square graphs, e.g. 147 for OA(7,3) → srg(49,18,7,6), 283,657 for order 8) and from Steiner triple systems of order 21; second-hand counts for (63,30,13,15) and (81,30,9,12); Behbahani–Lam–Östergård 342 for (49,18,7,6) (smaller than 727 anyway).
4. **20 references** resolve only through Brouwer's entry (emails recorded in his table, theses, Paulus 1973, Petersen 1898, Tarry 1901, Hill 1973/76, Rozenfel'd 1973, Mesner 1964, Chang 1960, etc.). DOIs could be added by hand for a few (e.g. Gavrilyuk–Makhnev 2005 Doklady, Makhnev 2017 already has one).
5. House of Graphs is linked generally, not per row (no stable per-parameter URL found).
6. Family labels are the Library's reading of Brouwer's comments (regular expressions); "two-graph" counts both "2-graph" and "2-graph*". A realised pair without a label is realised by a construction Brouwer names individually.
7. The Library repeats Brouwer's attribution "Kovaľ + AI" verbatim. For the 70 BMV pairs the deposit page credits D. Obata for 35 of them; the Library links Obata's Zenodo record on those 35 pairs and does not count rows per person.
8. Licence of the Library data is set to CC BY 4.0 on `about.html`, pending the author's decision.
9. Data size: `data/library/` is ~9 MB (JSON + identical `.js` wrappers); fine for GitHub Pages.
