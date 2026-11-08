#!/usr/bin/env python3
"""build_library.py -- rebuild the data of the SRG Library (library.html and its pages).

Standard library only.  Reads the sources listed in SOURCES (paths can be changed on the
command line, see --help), writes data/library/*.json and the matching *.js wrappers
(the pages load the .js files so that they also work from file://).

Run on the author's machine (host Windows has no Python):
    MSYS_NO_PATHCONV=1 wsl python3 -I /mnt/c/Users/akova/IdeaProjects/srg-database/build_library.py

Sources, in order of authority
  1. A. E. Brouwer, Parameters of strongly regular graphs, https://aeb.win.tue.nl/graphs/srg/srgtab.html
     (local snapshot of all 26 range pages + srgtabrefs.html; status, comments and references)
  2. E. Spence, Strongly regular graphs on at most 64 vertices (local copy of the page and data files;
     counts are read from the files, the files themselves are only linked)
  3. F. Ihringer, Many SRGs, https://math.ihringer.org/srgs.php (page text only; files linked)
  4. SageMath strongly_regular_db (tools/sage_constructions.py -> data/library/sources/sage_constructions.tsv)
  5. Published deposits of A. Kovaľ (data/library/sources/our_deposits.tsv) and the public-grade
     records of the programme ledger (PROVED-OURS-AUDITED with a public Zenodo DOI, PROVED-LIT)
  6. Published literature (data/library/sources/counts_literature.tsv, docs/literature/literature.tsv)
Everything that is not public-grade is filtered out here (see EXCLUDE_* below).
"""
import argparse, bz2, collections, datetime, glob, gzip, html, json, math, os, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))


def P(path):
    """Accept Windows-style paths when running under WSL."""
    if os.name != "nt":
        m = re.match(r"^([A-Za-z]):[\\/](.*)$", path)
        if m:
            return "/mnt/%s/%s" % (m.group(1).lower(), m.group(2).replace("\\", "/"))
    return path


DEFAULTS = dict(
    brouwer=r"D:\srg-library\external\brouwer\2026-11-07",
    brouwer_old=r"C:\Users\akova\IdeaProjects\orbit-gen\out\brouwer_check_1013",
    spence=r"D:\srg-library\external\spence",
    ihringer=r"D:\srg-library\external\ihringer\srgs.php.html",
    ledger=r"C:\Users\akova\IdeaProjects\orbit-gen\out\programme_ledger_2026_10_19\ledger.tsv",
    literature=r"C:\Users\akova\IdeaProjects\orbit-gen\docs\literature\literature.tsv",
    open_cases=r"C:\Users\akova\IdeaProjects\srg-open-cases",
    seeddb=r"C:\Users\akova\IdeaProjects\orbit-gen\out\seeddb_2026_11_07",
    out=os.path.join(HERE, "data", "library"),
)
SRC = os.path.join(HERE, "data", "library", "sources")
BROUWER_BASE = "https://aeb.win.tue.nl/graphs/srg/"
BROUWER_TABLE = "https://www.win.tue.nl/~aeb/graphs/srg/srgtab.html"
OPEN_CASES = "https://tonykoval.github.io/srg-open-cases/"
OPEN_CASES_REPO = "https://github.com/tonykoval/srg-open-cases/blob/main/"
SPENCE_PAGE = "https://www.maths.gla.ac.uk/~es/srgraphs.php"
SPENCE_FILES = "https://www.maths.gla.ac.uk/~es/SRGs/"
IHRINGER_PAGE = "https://math.ihringer.org/srgs.php"

# ---------------------------------------------------------------- exclusion rules
# Rows for which the Library shows Brouwer's public status/comment and computed spectra ONLY.
EXCLUDE_EXTRA_ROWS = {"232_77_36_20"}   # + complements, see below  (300_117_60_36 released 2026-11-08: deposited, zenodo.24056552)
EXCLUDE_EXTRA_V = {442}                                    # all 442 rows: Brouwer only
PUBLIC_DEPOSIT_PREFIX = "10.5281/zenodo."
LIT_ID_DROP = re.compile(r"^(other:|cite:|routine:|sweep:|brouwer-|spence-web|local:|email)", re.I)
LIT_TEXT_DROP = re.compile(r"\((title as summarised|title not recorded)|confidential|private|unpublished|in preparation", re.I)
# literature.tsv items shown on the site: only these, with metadata checked against arXiv / Crossref / Zenodo
# (2026-11-07); the row lists come from literature.tsv.  Everything else in that file is internal.
LIT_WHITELIST = {
    "arXiv:2610.20259": ("Z.-Q. Liao, J. Wang, W.-H. Yu & J. Cai", "Nonexistence of strongly regular graphs via Gegenbauer positivity and SRG counting", "arXiv:2610.20259 (Oct. 2026)", 2026),
    "arXiv:2507.23039": ("S. R. Nelson & E. Swartz", "Character theoretic techniques for nonabelian partial difference sets", "arXiv:2507.23039 (2025; Appendix B of v3)", 2025),
    "arXiv:2308.02978": ("P. G. Cesarz & A. J. Woldar", "On the automorphism group of a putative Conway 99-graph", "arXiv:2308.02978 (2023)", 2023),
    "arXiv:2306.08369": ("A. L. Gavrilyuk & V. V. Kabanov", "Strongly regular graphs decomposable into a divisible design graph and a Hoffman coclique", "arXiv:2306.08369 (2023)", 2023),
    "doi:10.1007/s10623-024-01563-y": ("A. L. Gavrilyuk & V. V. Kabanov", "Strongly regular graphs decomposable into a divisible design graph and a Delsarte clique", "Des. Codes Cryptogr. (2025)", 2025),
    "zenodo:22682072": ("D. Obata", "srg-eigenlattice-obstruction: v0.1.1 — 37 parameter sets ruled out", "software record, Zenodo (Sep. 2026)", 2026),
}
LIT_RELATIONS = {"settles-open-row", "pre-empts-us", "cites-us", "related-method", "background",
                 "cited-by-us", "audited-by-us", "duplicate-of-ours"}

# ---------------------------------------------------------------- helpers

def rid(v, k, l, m):
    return "%d_%d_%d_%d" % (v, k, l, m)


def comp_params(v, k, l, m):
    return (v, v - k - 1, v - 2 - 2 * k + m, v - 2 * k + l)


def read(p, enc="utf-8"):
    with open(p, encoding=enc, errors="replace") as f:
        return f.read()


def read_tsv(p, comment="#"):
    rows = []
    if not os.path.exists(p):
        return rows
    hdr = None
    for ln in read(p).splitlines():
        if not ln.strip() or ln.startswith(comment):
            continue
        parts = ln.split("\t")
        if hdr is None:
            hdr = parts
            continue
        parts += [""] * (len(hdr) - len(parts))
        rows.append(dict(zip(hdr, parts)))
    return rows


def plain(h):
    """Brouwer comment HTML -> plain text with ^ for sup and _ for sub."""
    t = re.sub(r"<sup>(.*?)</sup>", r"^\1", h, flags=re.S)
    t = re.sub(r"<sub>(.*?)</sub>", r"_\1", t, flags=re.S)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t).replace("\xa0", " ").replace("\\*", "*")
    return re.sub(r"\s+", " ", t).strip()


def clean_comment_html(h):
    """Keep sup/sub/i/b and links; rewrite links (refs -> our references page, rest absolute)."""
    h = h.replace("\\*", "*").replace("&nbsp;", " ")
    h = re.sub(r"\s+", " ", h).strip()
    out = []
    pos = 0
    for m in re.finditer(r"<(/?)([a-zA-Z]+)([^>]*)>", h):
        out.append(html.escape(html.unescape(h[pos:m.start()]), quote=False))
        pos = m.end()
        close, tag, attrs = m.group(1), m.group(2).lower(), m.group(3)
        if tag in ("sup", "sub", "i", "b", "em", "tt"):
            out.append("<%s%s>" % (close, tag))
        elif tag == "a":
            if close:
                out.append("</a>")
            else:
                hm = re.search(r'href="([^"]*)"', attrs)
                href = hm.group(1) if hm else ""
                rm = re.match(r"^srgtabrefs\.html#(.+)$", href)
                if rm:
                    out.append('<a class="ref" href="references.html#b-%s" data-ref="%s">' % (
                        html.escape(rm.group(1)), html.escape(rm.group(1))))
                elif href:
                    if not re.match(r"^[a-z]+:", href):
                        href = BROUWER_BASE + href
                    out.append('<a href="%s" rel="noopener">' % html.escape(href))
                else:
                    out.append("<a>")
        # every other tag is dropped
    out.append(html.escape(html.unescape(h[pos:]), quote=False))
    s = "".join(out)
    # balance stray closing tags conservatively
    for tag in ("a", "sup", "sub", "i", "b", "em", "tt"):
        o, c = s.count("<%s>" % tag) + s.count("<%s " % tag), s.count("</%s>" % tag)
        if c > o:
            for _ in range(c - o):
                s = s.replace("</%s>" % tag, "", 1)
        elif o > c:
            s += "</%s>" % tag * (o - c)
    return s.strip()


SUP = str.maketrans("0123456789+-–−", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻⁻")
SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def pretty(t):
    """Plain comment text with ^x / _x turned into Unicode super/subscripts where possible."""
    t = re.sub(r"\^([0-9+\-–−]+)", lambda m: m.group(1).translate(SUP), t)
    return re.sub(r"_(\d+)", lambda m: m.group(1).translate(SUB), t)


# ---------------------------------------------------------------- spectra and feasibility

def spectrum(v, k, l, m):
    D = (l - m) ** 2 + 4 * (k - m)
    sq = math.isqrt(D)
    if sq * sq == D:
        r = Fraction(l - m + sq, 2)
        s = Fraction(l - m - sq, 2)
        f = Fraction(-k - (v - 1) * s, 1) / (r - s)
        g = Fraction(k + (v - 1) * r, 1) / (r - s)
        return dict(integral=True, r=int(r) if r.denominator == 1 else float(r),
                    s=int(s) if s.denominator == 1 else float(s),
                    f=int(f) if f.denominator == 1 else float(f),
                    g=int(g) if g.denominator == 1 else float(g),
                    r_txt=str(r), s_txt=str(s), D=D)
    rr = (l - m + math.sqrt(D)) / 2
    ss = (l - m - math.sqrt(D)) / 2
    fg = (v - 1) / 2
    return dict(integral=False, r=rr, s=ss, f=fg, g=fg, D=D,
                r_txt="(%d+√%d)/2" % (l - m, D) if l - m else "√%d/2" % D,
                s_txt="(%d−√%d)/2" % (l - m, D) if l - m else "−√%d/2" % D)


def feasibility(v, k, l, m, sp):
    """Classical conditions (Brouwer-Haemers, Spectra of Graphs, §9.1): Krein, absolute bound,
    conference-graph condition.  Used only to cross-check Brouwer's labels."""
    res = {}
    if sp["integral"]:
        r, s, f, g = sp["r"], sp["s"], sp["f"], sp["g"]
        res["krein1_ok"] = (r + 1) * (k + r + 2 * r * s) <= (k + r) * (s + 1) ** 2
        res["krein2_ok"] = (s + 1) * (k + s + 2 * r * s) <= (k + s) * (r + 1) ** 2
        res["absolute_ok"] = (v <= f * (f + 3) / 2) and (v <= g * (g + 3) / 2)
    else:
        n = v
        ok = True
        # v must be a sum of two squares
        x = 0
        found = False
        while x * x <= n:
            y = math.isqrt(n - x * x)
            if y * y == n - x * x:
                found = True
                break
            x += 1
        res["conference_sum_of_two_squares"] = found
    return res


# ---------------------------------------------------------------- Brouwer table

STATUS_BY_COLOR = {"#b0ffb0": "+", "#ffb0b0": "-", "#ffffb0": "?"}


def parse_brouwer(d):
    files = sorted(glob.glob(os.path.join(d, "srgtab[0-9]*.html")) + glob.glob(os.path.join(d, "t[0-9]*.html")),
                   key=lambda x: int(re.search(r"(\d+)-\d+\.html$", x).group(1)))
    rows = []
    for fp in files:
        rng = re.search(r"(\d+)-(\d+)\.html$", fp).groups()
        page = BROUWER_BASE + "srgtab%s-%s.html" % rng
        t = read(fp)
        last_v = None
        primary = None
        for m in re.finditer(r'<tr bgcolor="(#[0-9a-fA-F]+)">(.*?)</tr>', t, re.S):
            cells = re.findall(r"<td[^>]*>(.*?)</td>", m.group(2), re.S)
            if len(cells) != 8:
                raise SystemExit("unexpected row in %s: %r" % (fp, cells))
            stat = plain(cells[0])
            vtxt = plain(cells[1])
            v = int(vtxt) if vtxt else last_v
            last_v = v
            k, l, mu = int(plain(cells[2])), int(plain(cells[3])), int(plain(cells[4]))
            rf, sg = cells[5], cells[6]
            rec = dict(id=rid(v, k, l, mu), v=v, k=k, l=l, mu=mu,
                       color=m.group(1).lower(), status_raw=stat,
                       b_r=plain(re.sub(r"<sup>.*", "", rf)), b_f=plain((re.findall(r"<sup>(.*?)</sup>", rf) or [""])[0]),
                       b_s=plain(re.sub(r"<sup>.*", "", sg)).replace("–", "-").replace("−", "-"),
                       b_g=plain((re.findall(r"<sup>(.*?)</sup>", sg) or [""])[0]),
                       comment_raw=cells[7], page=page, page_file=os.path.basename(fp))
            if stat:
                rec["primary"] = True
                primary = rec
            else:
                rec["primary"] = False
                cp = comp_params(primary["v"], primary["k"], primary["l"], primary["mu"])
                if (v, k, l, mu) != cp:
                    raise SystemExit("complement mismatch %s after %s" % (rec["id"], primary["id"]))
                rec["of"] = primary["id"]
                primary["comp"] = rec["id"]
                rec["status_raw"] = primary["status_raw"]
            rows.append(rec)
    return rows


def status_of(raw, color):
    s = STATUS_BY_COLOR.get(color)
    if raw == "-":
        exp = "-"
    elif raw == "?":
        exp = "?"
    elif raw == "+" or re.fullmatch(r"\d*!", raw):
        exp = "+"
    else:
        exp = None
    return s, exp


def parse_brouwer_refs(path):
    t = read(path)
    refs = collections.OrderedDict()
    for p in re.split(r"<p>\s*", t):
        m = re.search(r'<a name="([^"]+)"', p)
        if not m:
            continue
        key = m.group(1)
        links = [h for h in re.findall(r'href="([^"]+)"', p)]
        its = re.findall(r"<i>(.*?)</i>", p, re.S)
        title = ""
        if its:
            seg = p[p.find("<i>"):p.rfind("</i>") + 4]
            title = plain(seg)
        # authors: text of the first anchor (+ possible continuation before <br>)
        head = p.split("<br>")[0]
        authors = plain(head)
        if not title:
            # entries without italics: "Authors,<br> Title,<br> email, ..."
            segs = [plain(x) for x in p.split("<br>")]
            title = segs[1].rstrip(",") if len(segs) > 1 else ""
        full = plain(p)
        years = re.findall(r"\b(1[89]\d\d|20\d\d)\b", full)
        refs[key] = dict(key=key, authors=authors.rstrip(","), title=title.rstrip(","), text=full,
                         links=links, year=int(years[-1]) if years else None,
                         email=bool(re.search(r"\bemail\b", full, re.I)))
    return refs


# ---------------------------------------------------------------- Spence

SPENCE_REFS = [
    ("spence1", "Spence00", "E Spence, The Strongly Regular (40,12,2,4) Graphs Elec. Journ. Combin. Vol 7(1) 2000."),
    ("spence2", "Spence95", "E Spence, Regular Two-Graphs on 36 Vertices, Lin.Alg. and its App., 226-228 (1995) 459-497."),
    ("spence3", "McKaySpence01", "B McKay and E Spence, Classification of regular two-graphs on 36 and 38 vertices, Australasian Journal of Combinatorics, vol.24, p.293 (2001)"),
    ("spence4", "HaemersSpence01", "W Haemers and E Spence, The Pseudo-Geometric Graphs for Generalised Quadrangles of Order (3, t), European J. Combin. 22 (2001), no. 6, 839-845"),
    ("spence5", "Coolsaet_et_al06", "Coolsaet K., J. Degraer, E. Spence, The Strongly Regular (45,12,3,3) graphs, Electronic Journal of Combinatorics, Vol 13 (1), R32, 2006."),
]
# Spence's own notes on completeness (srgraphs.php, read 2026-11-07)
SPENCE_NOTES = {
    "29_14_6_7": ("complete", "spence1", "41 graphs; complete (Spence; independently Bussemaker)"),
    "40_12_2_4": ("complete", "spence1", "28 graphs; search completed, one graph more than the 27 previously known [1]"),
    "36_15_6_6": ("complete", "spence3", "32,548 graphs; lower bound of [2] shown to be exact with McKay [3]"),
    "36_14_4_6": ("complete", "spence3", "180 graphs; exact [2,3]"),
    "35_18_9_9": ("complete", "spence3", "3,854 descendants of the 227 regular two-graphs on 36 vertices [3]"),
    "37_18_8_9": ("lower", "spence3", "6,760 descendants of the 191 regular two-graphs on 38 vertices obtained in [3]; 'very likely not exhaustive'"),
    "45_12_3_3": ("complete", "spence5", "precisely 78 graphs [5]"),
    "64_18_2_6": ("complete", "spence4", "all SRG(64,18,2,6) determined with Haemers [4]"),
    "50_21_8_9": ("lower", None, "18 graphs obtained from the 18 Steiner systems S(2,4,25)"),
}


def count_spence_file(path, v):
    op = bz2.open if path.endswith(".bz2") else open
    with op(path, "rt", errors="replace") as f:
        data = f.read()
    m = re.search(r"TOTAL NUMBER OF STRONGLY REGULAR GRAPHS\s*=\s*(\d+)", data)
    run = blocks = 0
    for ln in data.splitlines():
        ln = ln.strip()
        if len(ln) == v and set(ln) <= set("01"):
            run += 1
        else:
            blocks += run // v
            run = 0
    blocks += run // v
    return blocks, (int(m.group(1)) if m else None)


def load_spence(d):
    cache = os.path.join(SRC, "spence_counts.tsv")
    sd = os.path.join(d, "SRGs")
    if os.path.isdir(sd):
        rows = []
        for fp in sorted(glob.glob(os.path.join(sd, "*"))):
            name = os.path.basename(fp)
            base = name[:-4] if name.endswith(".bz2") else name
            if not re.fullmatch(r"\d+-\d+-\d+-\d+", base):
                continue
            if name.endswith(".bz2") and os.path.exists(os.path.join(sd, base)):
                continue  # plain file present; count it once
            v = int(base.split("-")[0])
            n, total = count_spence_file(fp, v)
            rows.append(dict(row=base.replace("-", "_"), file=name, matrices=str(n), total_line=str(total or "")))
        # keep the .bz2 name as the link target when both exist (smaller download)
        for r in rows:
            if os.path.exists(os.path.join(sd, r["file"] + ".bz2")):
                r["file_bz2"] = r["file"] + ".bz2"
        with open(cache, "w", encoding="utf-8") as f:
            f.write("# Counts read from E. Spence's data files (local copy of %s, 2026-11-07): number of 0/1 matrices and the TOTAL line\n" % SPENCE_PAGE)
            f.write("row\tfile\tmatrices\ttotal_line\tfile_bz2\n")
            for r in rows:
                f.write("\t".join([r["row"], r["file"], r["matrices"], r["total_line"], r.get("file_bz2", "")]) + "\n")
    return read_tsv(cache)


# ---------------------------------------------------------------- Ihringer

def load_ihringer(path):
    cache = os.path.join(SRC, "ihringer_rows.tsv")
    if os.path.exists(path):
        t = read(path)
        rows = []
        section = ""
        for m in re.finditer(r"<h[1-4][^>]*>(.*?)</h[1-4]>|<li>\s*<a href=\"([^\"]+)\">([^<]*)</a>([^<]*)", t, re.S):
            if m.group(1) is not None:
                section = plain(m.group(1))
                continue
            url, label, rest = m.group(2), plain(m.group(3)), plain(m.group(4))
            pm = re.search(r"SRG\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)", label)
            if not pm:
                continue
            cm = re.match(r"^,\s*([\d,]+)(?: graphs)?,\s*(.*)$", rest)
            if not cm:
                continue
            n = int(cm.group(1).replace(",", ""))
            rows.append(dict(row=rid(*map(int, pm.groups())), count=str(n), label=label,
                             method=cm.group(2).rstrip("."), section=section, url=url))
        with open(cache, "w", encoding="utf-8") as f:
            f.write("# From the page text of %s (local copy, 2026-11-07). Files are only linked, not copied.\n" % IHRINGER_PAGE)
            f.write("row\tcount\tlabel\tmethod\tsection\turl\n")
            for r in rows:
                f.write("\t".join(r[c] for c in ("row", "count", "label", "method", "section", "url")) + "\n")
    return read_tsv(cache)


IHRINGER_SECTION_REF = {
    "Graphs in the Accepted Paper": "ihringer2012",
    "Bonus Graphs": "ihringer2012",
    "The 4-Vertex Condition": "ihringer2107",
    "More Kantor-type Switching": "ihringer2204",
}

# ---------------------------------------------------------------- families

FAMILIES = [
    dict(id="paley", name="Paley graphs", pat=r"\bPaley\((\d+)\)",
         formula="Paley(q), q ≡ 1 (mod 4) a prime power: srg(q, (q−1)/2, (q−5)/4, (q−1)/4)",
         check=lambda a, p: p == (a[0], (a[0] - 1) // 2, (a[0] - 5) // 4, (a[0] - 1) // 4),
         desc="Vertices are the elements of GF(q), adjacent when their difference is a non-zero square. Self-complementary conference graphs.",
         refs=["paley1933", "bvm2022"]),
    dict(id="triangular", name="Triangular graphs T(n)", pat=r"\bT\((\d+)\)",
         formula="T(n) = line graph of K_n: srg(n(n−1)/2, 2(n−2), n−2, 4)",
         check=lambda a, p: p == (a[0] * (a[0] - 1) // 2, 2 * (a[0] - 2), a[0] - 2, 4),
         desc="The 2-subsets of an n-set, adjacent when they meet. Unique for n ≠ 8; for n = 8 there are the three Chang graphs as well.",
         refs=["Chang60", "bvm2022"]),
    dict(id="latin", name="Latin square graphs OA(n,m) and lattice graphs n²", pat=r"(?<![A-Za-z(])(?<!switch )OA\((\d+),(\d+)\)(?!\?)(?!\+)|^(\d+)\^2$",
         formula="from an orthogonal array OA(n,m) (m−2 mutually orthogonal Latin squares): srg(n², m(n−1), (m−1)(m−2)+n−2, m(m−1)); the lattice graph n² = L₂(n) is m = 2",
         check=lambda a, p: (lambda n, m: p == (n * n, m * (n - 1), (m - 1) * (m - 2) + n - 2, m * (m - 1)))(*(a if len(a) == 2 else (a[0], 2))),
         desc="Vertices are the n² cells, adjacent when in the same row, column, or carrying the same symbol in one of the squares.",
         refs=["bvm2022"]),
    dict(id="steiner", name="Block graphs of Steiner systems S(2,K,V)", pat=r"(?<![A-Za-z+])S\(2,(\d+),(\d+)\)(?!\?)",
         formula="blocks of an S(2,K,V), adjacent when they meet: v = V(V−1)/(K(K−1)), k = K(V−K)/(K−1), λ = (K−1)² + (V−1)/(K−1) − 2, μ = K²",
         check=lambda a, p: (lambda K, V: p == (V * (V - 1) // (K * (K - 1)), K * (V - K) // (K - 1), (K - 1) ** 2 + (V - 1) // (K - 1) - 2, K * K))(*a),
         desc="Steiner 2-designs give graphs whose number usually grows very fast with V (e.g. S(2,3,19) for srg(57,24,11,9)).",
         refs=["GoethalsSeidel70", "bvm2022"]),
    dict(id="gq", name="Generalized quadrangles GQ(s,t)", pat=r"\bGQ\((\d+),(\d+)\)(?!\?)",
         formula="collinearity graph of a GQ(s,t): srg((s+1)(st+1), s(t+1), s−1, t+1)",
         check=lambda a, p: (lambda s, t: p == ((s + 1) * (s * t + 1), s * (t + 1), s - 1, t + 1))(*a),
         desc="Points of the quadrangle, adjacent when collinear. Includes the classical polar spaces of rank 2.",
         refs=["bvm2022"]),
    dict(id="pg", name="Partial geometries pg(s,t,α)", pat=r"\bpg\((\d+),(\d+),(\d+)\)(?!\?)(?! does not exist)",
         formula="collinearity graph of a pg(s,t,α): srg((s+1)(st+α)/α, s(t+1), s−1+t(α−1), α(t+1))",
         check=lambda a, p: (lambda s, t, al: p == ((s + 1) * (s * t + al) // al, s * (t + 1), s - 1 + t * (al - 1), al * (t + 1)))(*a),
         desc="Geometric graphs: points of a partial geometry, adjacent when collinear. In open rows Brouwer writes pg(s,t,α)? for a geometry that would realise the row.",
         refs=["bvm2022"]),
    dict(id="twograph", name="Regular two-graphs (2-graph, 2-graph*)", pat=r"(?<!no )\b2-graph(\*?)(?!\?)",
         formula="2-graph*: k = 2μ, a descendant of a regular two-graph on v+1 points; 2-graph: v = 2(2k−λ−μ), a regular graph in the switching class of a regular two-graph on v points",
         check=lambda a, p: (p[1] == 2 * p[3]) if a and a[0] == "*" else (p[0] == 2 * (2 * p[1] - p[2] - p[3])),
         desc="Seidel switching classes; the relation between a regular two-graph and its descendants/regular members is the standard one (Seidel, Taylor).",
         refs=["Seidel68", "bvm2022"]),
    dict(id="polar", name="Classical polar and unitary graphs", pat=r"(?<![A-Za-z])(?:N?O|NU|U|Sp)(?:\^[+–−-])?(?:,orth)?\(\d+,\d+\)(?!\?)|polar graph|dual polar",
         formula=None, check=None,
         desc="Graphs on the points of a finite polar space (O, Sp, U) and on the non-isotropic points (NO, NU), in Brouwer's notation.",
         refs=["bvm2022"]),
    dict(id="affinepolar", name="Affine polar graphs VO±, VNO±", pat=r"\bVN?O\^?[+–−-]?\(",
         formula=None, check=None,
         desc="Cayley graphs on a vector space defined by a quadratic form; projective two-weight codes in disguise.",
         refs=["bvm2022"]),
    dict(id="twoweight", name="Projective two-weight codes", pat=r"projective [^;]*code with weights",
         formula="a projective [n,m] code over GF(q) with weights w₁ < w₂ gives srg(q^m, n(q−1), ·, ·) with eigenvalues n(q−1) − q·w₁ and n(q−1) − q·w₂",
         check=None,
         desc="Cayley graphs on GF(q)^m (Delsarte; Calderbank–Kantor). Brouwer names the code and often its finder.",
         refs=["CalderbankKantor86", "bvm2022"]),
    dict(id="rshcd", name="Regular symmetric Hadamard matrices with constant diagonal (RSHCD±)", pat=r"RSHCD\^?[+–−-]?(?!\?)",
         formula=None, check=None,
         desc="A regular symmetric Hadamard matrix of order 4u² with constant diagonal gives graphs on 4u² vertices with λ = μ or λ = μ − 2.",
         refs=["bvm2022"]),
    dict(id="switching", name="Switching constructions", pat=r"\bswitch(?:ed)?\b",
         formula=None, check=None,
         desc="Graphs obtained from a known one by Seidel, Godsil–McKay or Wallis–Fon-Der-Flaass type switching (Brouwer: 'switch OA(n,m)+*', 'switch skewhad', 'switched Brady graph').",
         refs=["bvm2022"]),
    dict(id="wallis", name="Wallis–Fon-Der-Flaass (affine designs)", pat=r"\bWallis\d?\b",
         formula=None, check=None,
         desc="From an affine design AR(q,…) and a Steiner system (Wallis 1971, Fon-Der-Flaass 2002); generalised by Muzychuk.",
         refs=["Muzychuk07"]),
    dict(id="quasisym", name="Quasi-symmetric designs", pat=r"quasisymmetric",
         formula=None, check=None, desc="Block graphs of quasi-symmetric 2-designs (blocks adjacent when they meet in the larger intersection number).",
         refs=["bvm2022"]),
    dict(id="vanlintschrijver", name="van Lint–Schrijver", pat=r"vanLint-Schrijver",
         formula=None, check=None, desc="Cyclotomic constructions of two-weight codes and partial geometries by finite fields.",
         refs=["vanLintSchrijver81"]),
    dict(id="goethalsseidel", name="Goethals–Seidel", pat=r"Goethals-Seidel\(",
         formula=None, check=None, desc="Graphs from Steiner systems and Hadamard matrices.", refs=["GoethalsSeidel70"]),
    dict(id="godsil", name="Godsil (Krein covers)", pat=r"\bGodsil\(",
         formula=None, check=None, desc="Strongly regular graphs from Krein covers of complete graphs.", refs=["Godsil92"]),
    dict(id="pasechnik", name="Pasechnik", pat=r"\bPasechnik\(",
         formula=None, check=None, desc="Graphs of type L_{2n−1}(4n−1) from skew-symmetric association schemes.", refs=["Pasechnik92"]),
    dict(id="mathon", name="Mathon", pat=r"\bMathon\b",
         formula=None, check=None, desc="Conference matrices of order pq²+1 and related graphs.", refs=["Mathon78"]),
    dict(id="etf", name="Equiangular tight frames", pat=r"\bETF\b|Fickus",
         formula=None, check=None, desc="Graphs from equiangular tight frames (Fickus et al.).", refs=["Fickus_et_al15", "Fickus_et_al16"]),
    dict(id="bilinear", name="Bilinear forms graphs", pat=r"\bBilin",
         formula=None, check=None, desc="Bilinear forms graphs Bilin_{d×e}(q).", refs=["bvm2022"]),
    dict(id="lines", name="Lines of projective and affine spaces", pat=r"[Ll]ines in (?:PG|AG)\(",
         formula=None, check=None, desc="Grassmann-type graphs on the lines of PG(n,q) or AG(n,q).", refs=["bvm2022"]),
    dict(id="sporadic", name="Sporadic and named graphs", pat=r"Petersen|Clebsch|Shrikhande|Schläfli|Higman-Sims|McLaughlin|Hoffman-Singleton|Sims-Gewirtz|Hall-Janko|Chang graphs|Suz graph|subconstituent|Gewirtz|Witt",
         formula=None, check=None, desc="Named graphs and graphs from sporadic groups or exceptional designs.", refs=["bvm2022"]),
]
for F in FAMILIES:
    F["rx"] = re.compile(F["pat"])

# ---------------------------------------------------------------- nonexistence reasons
REASONS = collections.OrderedDict([
    ("absolute", dict(name="Absolute bound", pat=r"^Absolute bound$|^Abs\+",
                      desc="v ≤ f(f+3)/2 and v ≤ g(g+3)/2 (Delsarte–Goethals–Seidel; Neumaier's sharpening when the bound is attained).",
                      refs=["dgs1977", "bh2012"])),
    ("krein", dict(name="Krein conditions", pat=r"^Krein ?\d$",
                   desc="(r+1)(k+r+2rs) ≤ (k+r)(s+1)² and (s+1)(k+s+2rs) ≤ (k+s)(r+1)² (Scott; Krein parameters q¹₁₁, q²₂₂ ≥ 0). Brouwer writes Krein1 / Krein2 for the condition that fails.",
                   refs=["bh2012"])),
    ("conference", dict(name="Conference graph condition", pat=r"^Conf$",
                        desc="A conference graph on v vertices exists only if v is a sum of two squares (van Lint–Seidel; Belevitch).",
                        refs=["bh2012"])),
    ("neumaier", dict(name="Neumaier", pat=r"Neumaier",
                      desc="Neumaier's claw bound / the absolute bound in the tight case (Brouwer: 'Abs+Neumaier'), or Brouwer–Neumaier for μ = 2.",
                      refs=["BrouwerNeumaier88", "bh2012"])),
    ("mu1", dict(name="μ = 1 condition", pat=r"^mu=1$",
                 desc="Brouwer's label 'mu=1': the row fails a known necessary condition for strongly regular graphs with μ = 1; the table gives no reference.",
                 refs=["bvm2022"])),
    ("twograph", dict(name="No regular two-graph", pat=r"^no \d+-graph\*?$",
                      desc="The graph would be a descendant of (or lie in the switching class of) a regular two-graph that does not exist.",
                      refs=["bvm2022"])),
    ("paper", dict(name="Specific paper", pat=None, desc="A nonexistence proof for this row (or its family) in a paper cited by Brouwer.", refs=[])),
])

# extra bibliography entries used by the Library itself (all resolvable)
LIB_BIB = {
    "brouwer_table": dict(authors="A. E. Brouwer", title="Parameters of strongly regular graphs", venue="website, tables srgtab1-50 … srgtab1251-1300 and srgtabrefs", year=None,
                          url=BROUWER_BASE + "srgtab.html"),
    "bvm2022": dict(authors="A. E. Brouwer & H. Van Maldeghem", title="Strongly Regular Graphs", venue="Encyclopedia of Mathematics and its Applications 182, Cambridge University Press, 2022", year=2022,
                    doi="10.1017/9781009057226"),
    "bh2012": dict(authors="A. E. Brouwer & W. H. Haemers", title="Spectra of Graphs", venue="Universitext, Springer, New York, 2012 (Chapter 9)", year=2012,
                   doi="10.1007/978-1-4614-1939-6"),
    "dgs1977": dict(authors="P. Delsarte, J. M. Goethals & J. J. Seidel", title="Spherical codes and designs", venue="Geometriae Dedicata 6 (1977) 363–388", year=1977,
                    doi="10.1007/BF03187604"),
    "paley1933": dict(authors="R. E. A. C. Paley", title="On orthogonal matrices", venue="J. Math. Phys. 12 (1933) 311–320", year=1933,
                      doi="10.1002/sapm1933121311"),
    "CalderbankKantor86": dict(authors="R. Calderbank & W. M. Kantor", title="The geometry of two-weight codes", venue="Bull. London Math. Soc. 18 (1986) 97–122", year=1986,
                               doi="10.1112/blms/18.2.97"),
    "spence_web": dict(authors="E. Spence", title="Strongly Regular Graphs on at most 64 vertices", venue="web page, University of Glasgow (read 2026-11-07)", year=None, url=SPENCE_PAGE),
    "Spence95": dict(authors="E. Spence", title="Regular two-graphs on 36 vertices", venue="Linear Algebra Appl. 226–228 (1995) 459–497", year=1995, doi="10.1016/0024-3795(95)00158-N"),
    "ihringer_web": dict(authors="F. Ihringer", title="Many SRGs", venue="web page (read 2026-11-07)", year=None, url=IHRINGER_PAGE),
    "ihringer2012": dict(authors="F. Ihringer", title="Switching for small strongly regular graphs", venue="Australas. J. Combin. 84 (2022) 28–48; arXiv:2012.08390", year=2022, arxiv="2012.08390"),
    "ihringer2107": dict(authors="A. E. Brouwer, F. Ihringer & W. M. Kantor", title="Strongly regular graphs satisfying the 4-vertex condition", venue="arXiv:2107.00076", year=2021, arxiv="2107.00076"),
    "ihringer2204": dict(authors="E. R. van Dam & K. Guo", title="Pseudo-geometric strongly regular graphs with a regular point", venue="arXiv:2204.04755 (the Kantor-type switching that Ihringer's page enumerates)", year=2022, arxiv="2204.04755"),
    "sage": dict(authors="The Sage Developers", title="SageMath, the Sage Mathematics Software System (strongly_regular_db)", venue="version 10.10 (docker image sagemath/sagemath:latest, run 2026-11-07)", year=2026,
                 url="https://doc.sagemath.org/html/en/reference/graphs/sage/graphs/strongly_regular_db.html"),
    "hog": dict(authors="K. Coolsaet, S. D'hondt & J. Goedgebeur", title="House of Graphs 2.0: a database of interesting graphs and more", venue="Discrete Appl. Math. 325 (2023) 97–107", year=2023,
                doi="10.1016/j.dam.2022.10.013"),
    "srgdb_index": dict(authors="A. Kovaľ", title="SRG Database (v ≤ 100) and GM-switching catalogues", venue="github.com/tonykoval/srg-database, v100.html and catalogs/ (2026)", year=2026,
                        url="https://github.com/tonykoval/srg-database"),
}
LIB_BIB_FIXES = {}

# ---------------------------------------------------------------- main build


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k, v in DEFAULTS.items():
        ap.add_argument("--" + k.replace("_", "-"), default=v)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    for k in DEFAULTS:
        setattr(a, k, P(getattr(a, k)))
    log = [] if a.quiet else None
    os.makedirs(a.out, exist_ok=True)
    warnings = []

    # ---- Brouwer
    rows = parse_brouwer(a.brouwer)
    brefs = parse_brouwer_refs(os.path.join(a.brouwer, "srgtabrefs.html"))
    fetch = read(os.path.join(a.brouwer, "FETCH_TIME_UTC.txt")).strip() if os.path.exists(os.path.join(a.brouwer, "FETCH_TIME_UTC.txt")) else ""
    byid = {r["id"]: r for r in rows}
    old_status = {}
    if os.path.isdir(a.brouwer_old):
        for r in parse_brouwer(a.brouwer_old):
            old_status[r["id"]] = STATUS_BY_COLOR.get(r["color"])
    old_fetch = ""
    if os.path.exists(os.path.join(a.brouwer_old, "FETCH_TIME_UTC.txt")):
        old_fetch = read(os.path.join(a.brouwer_old, "FETCH_TIME_UTC.txt")).split()[0]

    excluded = set()
    for r in rows:
        if r["v"] in EXCLUDE_EXTRA_V:
            excluded.add(r["id"])
    for x in list(EXCLUDE_EXTRA_ROWS):
        if x in byid:
            excluded.add(x)
            excluded.add(byid[x].get("comp") or byid[x].get("of") or x)

    # ---- per-row base record
    for r in rows:
        st, exp = status_of(r["status_raw"], r["color"])
        if exp is not None and st != exp:
            warnings.append("status symbol %r vs colour %s on %s" % (r["status_raw"], r["color"], r["id"]))
        r["status"] = st
        raw = r["status_raw"]
        r["bcount"] = None
        if raw == "!":
            r["bcount"] = 1
        elif re.fullmatch(r"\d+!", raw):
            r["bcount"] = int(raw[:-1])
        sp = spectrum(r["v"], r["k"], r["l"], r["mu"])
        r["spec"] = sp
        # cross-check with Brouwer's printed spectrum
        try:
            if sp["integral"]:
                ok = (int(r["b_r"]) == sp["r"] and int(r["b_s"]) == sp["s"] and int(r["b_f"]) == sp["f"] and int(r["b_g"]) == sp["g"])
            else:
                ok = (abs(float(r["b_r"]) - sp["r"]) < 6e-4 and abs(float(r["b_s"]) - sp["s"]) < 6e-4 and int(r["b_f"]) == sp["f"] and int(r["b_g"]) == sp["g"])
        except ValueError:
            ok = False
        r["spec_ok"] = ok
        if not ok:
            warnings.append("spectrum mismatch %s: brouwer %s^%s %s^%s computed %s^%s %s^%s" % (
                r["id"], r["b_r"], r["b_f"], r["b_s"], r["b_g"], sp["r_txt"], sp["f"], sp["s_txt"], sp["g"]))
        r["conference"] = (not sp["integral"]) or (r["k"] == (r["v"] - 1) / 2 and r["l"] == (r["v"] - 5) / 4 and r["mu"] == (r["v"] - 1) / 4)
        r["feas"] = feasibility(r["v"], r["k"], r["l"], r["mu"], sp)
        r["comment_html"] = clean_comment_html(r["comment_raw"])
        r["comment_text"] = plain(r["comment_raw"])
        r["comment_parts"] = [x.strip() for x in re.split(r";\s*", r["comment_text"]) if x.strip()]
        r["ref_keys"] = sorted(set(re.findall(r"srgtabrefs\.html#([^\"]+)", r["comment_raw"])), key=str.lower)
        for k in r["ref_keys"]:
            if k not in brefs:
                warnings.append("row %s cites unknown Brouwer ref %s" % (r["id"], k))

    # ---- families (union over the pair; Brouwer writes some labels on the complement line)
    fam_rows = collections.defaultdict(set)
    fam_check = collections.defaultdict(lambda: [0, 0, []])
    for r in rows:
        r["families"] = []
        r["fam_labels"] = []
    for r in rows:
        if r["status"] != "+":
            continue
        for part in r["comment_parts"]:
            if part.endswith("?") or "does not exist" in part:
                continue
            for F in FAMILIES:
                for m in F["rx"].finditer(part):
                    if F["id"] not in r["families"]:
                        r["families"].append(F["id"])
                    r["fam_labels"].append([F["id"], m.group(0)])
                    if F["check"]:
                        args = tuple(int(g) if g and g.isdigit() else g for g in m.groups() if g is not None)
                        try:
                            okf = F["check"](args, (r["v"], r["k"], r["l"], r["mu"]))
                        except Exception:
                            okf = False
                        fam_check[F["id"]][0 if okf else 1] += 1
                        if not okf:
                            fam_check[F["id"]][2].append("%s:%s" % (r["id"], m.group(0)))
    for r in rows:
        if r["primary"]:
            other = byid.get(r.get("comp"))
            union = list(r["families"]) + [f for f in (other["families"] if other else []) if f not in r["families"]]
            r["pair_families"] = union
            if other:
                other["pair_families"] = union
            for f in union:
                fam_rows[f].add(r["id"])
        elif "pair_families" not in r:
            r["pair_families"] = r["families"]

    # ---- nonexistence reasons
    for r in rows:
        r["reasons"] = []
        if r["status"] != "-":
            continue
        src = r if r["comment_parts"] or r["primary"] else byid[r["of"]]
        pr_ = r if r["primary"] else byid[r["of"]]
        parts = list(pr_["comment_parts"]) + (list(byid[pr_["comp"]]["comment_parts"]) if pr_.get("comp") else [])
        for part in parts:
            hit = False
            for key, R in REASONS.items():
                if R["pat"] and re.search(R["pat"], part):
                    if key not in r["reasons"]:
                        r["reasons"].append(key)
                    hit = True
            if not hit and "paper" not in r["reasons"]:
                r["reasons"].append("paper")
        # cross-check the classical labels against our own computation
        fz = r["feas"]
        if "krein" in r["reasons"] and fz.get("krein1_ok", True) and fz.get("krein2_ok", True):
            warnings.append("Brouwer says Krein on %s but both Krein conditions hold here" % r["id"])
        if "absolute" in r["reasons"] and fz.get("absolute_ok") is True and not any("Neumaier" in p for p in parts):
            warnings.append("Brouwer says absolute bound on %s but the bound holds here" % r["id"])
        if "conference" in r["reasons"] and fz.get("conference_sum_of_two_squares", False):
            warnings.append("Brouwer says Conf on %s but v is a sum of two squares" % r["id"])
    # rows that violate a classical condition but are not '-' (would be a parsing problem)
    for r in rows:
        fz = r["feas"]
        bad = (fz.get("krein1_ok") is False or fz.get("krein2_ok") is False or fz.get("absolute_ok") is False
               or fz.get("conference_sum_of_two_squares") is False)
        if bad and r["status"] != "-":
            warnings.append("row %s fails a classical condition but has status %s" % (r["id"], r["status"]))

    # ---- counts: Brouwer, Spence, Ihringer, our deposits, srg-database catalogues, literature
    counts = collections.defaultdict(list)
    for r in rows:
        if r["primary"] and r["bcount"] is not None:
            counts[r["id"]].append(dict(n=r["bcount"], kind="complete", src="brouwer", bib="brouwer_table",
                                        note="Brouwer's table: '%s'" % r["status_raw"], url=r["page"]))
    spence = load_spence(a.spence)
    spence_rows = {}
    for s in spence:
        n = int(s["total_line"] or s["matrices"])
        if s["total_line"] and s["matrices"] and int(s["total_line"]) != int(s["matrices"]):
            warnings.append("Spence %s: TOTAL line %s but %s matrices" % (s["file"], s["total_line"], s["matrices"]))
        kind, sref, note = SPENCE_NOTES.get(s["row"], ("complete", None, ""))
        if s["row"] not in SPENCE_NOTES:
            # small classical rows: Spence's file agrees with a complete classification in Brouwer's table
            b = byid.get(s["row"])
            pr = b if (b and b["primary"]) else (byid.get(b["of"]) if b else None)
            kind = "complete" if (pr and pr["bcount"] == n) else "lower"
            note = "%d graph%s in Spence's file" % (n, "" if n == 1 else "s")
        link = s.get("file_bz2") or s["file"]
        spence_rows[s["row"]] = dict(file=link, url=SPENCE_FILES + link, n=n)
        counts[s["row"]].append(dict(n=n, kind=kind, src="spence", bib="spence_web", spence_ref=sref, note=note,
                                     url=SPENCE_FILES + link))
    ihr = load_ihringer(a.ihringer)
    ihr_rows = collections.defaultdict(list)
    for h in ihr:
        ihr_rows[h["row"]].append(h)
        counts[h["row"]].append(dict(n=int(h["count"]), kind="lower", src="ihringer",
                                     bib=IHRINGER_SECTION_REF.get(h["section"], "ihringer_web"),
                                     note="%s — %s (section '%s' of Ihringer's page)" % (h["label"], h["method"], h["section"]), url=h["url"]))
    # our public deposits
    deposits = read_tsv(os.path.join(SRC, "our_deposits.tsv"))
    ledger_rows = collections.defaultdict(set)
    lit_partial = collections.defaultdict(list)
    if os.path.exists(a.ledger):
        lines = read(a.ledger).splitlines()
        hdr = lines[1].split("\t")
        for ln in lines[2:]:
            p = dict(zip(hdr, ln.split("\t")))
            if p.get("grade") == "PROVED-OURS-AUDITED":
                for d in re.findall(r"10\.5281/zenodo\.\d+", p.get("source", "")):
                    ledger_rows[d].add(p["row"])
            elif p.get("grade") == "PROVED-LIT" and p.get("method") == "cayley-any-group-lit" and "arXiv:2507.23039" in p.get("source", ""):
                lit_partial[p["row"]].append(dict(kind="no-cayley", bib="arXiv:2507.23039",
                                                  text="No Cayley graph with these parameters (or with the complementary parameters) on any group of order v."))
    public_dois = {d["doi"] for d in deposits}
    ours = collections.defaultdict(list)
    for d in deposits:
        drows = [x for x in d["rows"].split(";") if x and x != "ledger"]
        if d["rows"] == "ledger" or True:
            drows += sorted(x for x in ledger_rows.get(d["doi"], ()) if x not in drows)
        cnt = dict(x.split(":") for x in d["counts"].split(";") if x)
        for x in drows:
            if x not in byid:
                warnings.append("deposit %s names row %s which is not in Brouwer's table" % (d["doi"], x))
                continue
            pr = x if byid[x]["primary"] else byid[x]["of"]
            ours[pr].append(dict(doi=d["doi"], kind=d["kind"], title=d["title"],
                                 page=(OPEN_CASES + d["page"]) if d["page"] else "", n=int(cnt[x]) if x in cnt else None))
            if x in cnt:
                counts[pr].append(dict(n=int(cnt[x]), kind="lower", src="ours", bib="dep:" + d["doi"],
                                       note="graphs in the deposit (no classification claimed)", url="https://doi.org/" + d["doi"]))
    for d, rs in ledger_rows.items():
        if d not in public_dois:
            warnings.append("ledger cites %s (not in the public deposit list) — ignored" % d)
    # GM-switching catalogues of this repository (public since 2026-05/09)
    for c in read_tsv(os.path.join(SRC, "srgdb_catalogs.tsv")):
        counts[c["row"]].append(dict(n=int(c["n"]), kind="lower", src="srgdb", bib="srgdb_index", note=c["note"], url=c["url"]))
    # literature counts (curated, every line with a DOI/URL)
    for c in read_tsv(os.path.join(SRC, "counts_literature.tsv")):
        if not (c.get("doi") or c.get("url") or c.get("arxiv")):
            warnings.append("literature count without link dropped: %r" % c)
            continue
        counts[c["row"]].append(dict(n=int(c["n"]), kind=c["kind"], src="literature", bib="lit:" + c["key"],
                                     note=c["note"], url=("https://doi.org/" + c["doi"]) if c.get("doi") else (c["url"] or "https://arxiv.org/abs/" + c["arxiv"])))
    lit_counts_bib = {c["key"]: c for c in read_tsv(os.path.join(SRC, "counts_literature.tsv"))}

    # move counts to the primary id of the pair
    pcounts = collections.defaultdict(list)
    for x, lst in counts.items():
        if x not in byid:
            warnings.append("count for %s which is not in Brouwer's table: %r" % (x, lst[:1]))
            continue
        pr = x if byid[x]["primary"] else byid[x]["of"]
        for c in lst:
            c = dict(c)
            if pr != x:
                c["via"] = x
            pcounts[pr].append(c)
    for x in list(pcounts):
        if x in excluded:
            pcounts[x] = [c for c in pcounts[x] if c["src"] == "brouwer"]

    # headline count per pair + consistency checks
    for r in rows:
        if not r["primary"]:
            continue
        lst = pcounts.get(r["id"], [])
        comp = [c["n"] for c in lst if c["kind"] == "complete"]
        low = [c["n"] for c in lst if c["kind"] == "lower"]
        if len(set(comp)) > 1:
            warnings.append("conflicting complete counts on %s: %s" % (r["id"], lst))
        if comp and low and max(low) > min(comp):
            warnings.append("lower bound above complete count on %s: %s" % (r["id"], lst))
        if r["status"] == "-":
            head = dict(label="0", n=0, kind="none")
        elif comp:
            head = dict(label="%s" % format(comp[0], ","), n=comp[0], kind="complete")
        elif low:
            head = dict(label="≥ %s" % format(max(low), ","), n=max(low), kind="lower")
        elif r["status"] == "+":
            head = dict(label="≥ 1", n=1, kind="exists")
        else:
            head = dict(label="?", n=None, kind="open")
        if r["status"] == "?" and (comp or low):
            warnings.append("open row %s has counts %s" % (r["id"], lst))
        r["head"] = head
        r["counts"] = lst
    for r in rows:
        if not r["primary"]:
            p = byid[r["of"]]
            r["head"], r["counts"] = p["head"], p["counts"]

    # ---- Sage
    sage = {}
    for s in read_tsv(os.path.join(SRC, "sage_constructions.tsv")):
        sage[rid(int(s["v"]), int(s["k"]), int(s["l"]), int(s["mu"]))] = s
    sage_conflicts = []
    for r in rows:
        s = sage.get(r["id"])
        r["sage"] = None
        if s:
            r["sage"] = dict(existence=s["existence"], constructor=s["constructor"], test=s["test"])
            if s["existence"] == "True" and r["status"] != "+":
                sage_conflicts.append("%s Sage True, Brouwer %s" % (r["id"], r["status"]))
            if s["existence"] == "False" and r["status"] == "+":
                sage_conflicts.append("%s Sage False, Brouwer +" % r["id"])
    warnings += ["sage: " + x for x in sage_conflicts]

    # ---- seed database of the other lane (placeholder until its REPORT.md exists)
    seed_status = "pending"
    seed = {}
    if os.path.exists(os.path.join(a.seeddb, "REPORT.md")):
        seed_status = "imported"
        for fn in ("constructions.tsv", "seed_constructions.tsv", "rows.tsv"):
            fp = os.path.join(a.seeddb, fn)
            if os.path.exists(fp):
                for s in read_tsv(fp):
                    key = s.get("row") or (rid(int(s["v"]), int(s["k"]), int(s["l"]), int(s["mu"])) if s.get("v") else None)
                    if key:
                        seed.setdefault(key, []).append(s.get("construction") or s.get("name") or "")
                break
        else:
            seed_status = "report-present-no-table"

    # ---- literature items per row (public, filtered)
    lit = collections.defaultdict(list)
    lit_bib = {}
    if os.path.exists(a.literature):
        for e in read_tsv(a.literature):
            iid = e.get("id", "")
            if not iid or LIT_ID_DROP.search(iid):
                continue
            if LIT_TEXT_DROP.search(e.get("title", "")) or LIT_TEXT_DROP.search(e.get("authors", "")):
                continue
            if e.get("relation") not in LIT_RELATIONS:
                continue
            url = e.get("url", "")
            if not re.match(r"^https?://", url) or "external_untrusted" in url:
                continue
            if re.search(r"kova[lľ]", e.get("authors", ""), re.I):
                continue  # our own deposits come from our_deposits.tsv
            rws = [x for x in re.split(r"[;,\s]+", e.get("rows", "")) if re.fullmatch(r"\d+_\d+_\d+_\d+", x)]
            if not rws:
                continue
            if iid not in LIT_WHITELIST:
                continue
            wa, wt, wv, wy = LIT_WHITELIST[iid]
            lit_bib["lit2:" + iid] = dict(authors=wa, title=wt, venue=wv, year=wy, url=url)
            for x in rws:
                if x in byid:
                    pr = x if byid[x]["primary"] else byid[x]["of"]
                    if pr not in excluded and "lit2:" + iid not in lit[pr]:
                        lit[pr].append("lit2:" + iid)

    # ---- downloads per pair
    oc_data = os.path.join(a.open_cases, "data")
    oc_files = sorted(os.listdir(oc_data)) if os.path.isdir(oc_data) else []
    downloads = collections.defaultdict(list)
    for r in rows:
        if not r["primary"]:
            continue
        x = r["id"]
        ids = [x] + ([r["comp"]] if r.get("comp") else [])
        for y in ids:
            if y in spence_rows:
                downloads[x].append(dict(label="Spence: %s (%d graph%s, 0/1 matrices)" % (spence_rows[y]["file"], spence_rows[y]["n"], "" if spence_rows[y]["n"] == 1 else "s"),
                                         url=spence_rows[y]["url"], src="spence"))
            for h in ihr_rows.get(y, []):
                downloads[x].append(dict(label="Ihringer: %s, %s graphs (graph6, gzip; %s)" % (h["label"], format(int(h["count"]), ","), h["section"]),
                                         url=h["url"], src="ihringer"))
        if x in excluded:
            continue
        vv, kk, ll, mm = r["v"], r["k"], r["l"], r["mu"]
        pat = re.compile(r"^srg%d_%d_%d_%d(_|\.)" % (vv, kk, ll, mm))
        for fn in oc_files:
            if fn.endswith(".g6") and pat.match(fn):
                downloads[x].append(dict(label="Kovaľ deposit mirror: %s (graph6)" % fn, url=OPEN_CASES_REPO + "data/" + fn, src="ours"))
        for o in ours.get(x, []):
            if o["kind"] in ("existence", "uniqueness", "rediscovery"):
                downloads[x].append(dict(label="Zenodo %s (paper + data archive)" % o["doi"].split(".")[-1], url="https://doi.org/" + o["doi"], src="ours"))
        if x in ("50_21_8_9", "49_24_11_12", "57_24_11_9"):
            downloads[x].append(dict(label="srg-database catalogs/srg_constructed_catalogs.tar.gz (graph6; samples for 49 and 57)",
                                     url="catalogs/srg_constructed_catalogs.tar.gz", src="srgdb"))

    # ---- bibliography
    ref_links = {x["key"]: x for x in read_tsv(os.path.join(SRC, "ref_links.tsv"))}
    ref_urls = {x["key"]: x for x in read_tsv(os.path.join(SRC, "ref_urls.tsv"))}
    dead = {x["url"] for x in read_tsv(os.path.join(SRC, "dead_links.tsv"))}
    bib = collections.OrderedDict()
    for k, b in brefs.items():
        links = []
        for h in b["links"]:
            if not re.match(r"^[a-z]+:", h):
                h = BROUWER_BASE + h
            if h not in dead:
                links.append(h)
        doi = ""
        for h in links:
            m = re.search(r"doi\.org/(10\..+)$", h)
            if m:
                doi = m.group(1)
        rl = ref_links.get(k)
        doi_src = "brouwer" if doi else ""
        if not doi and rl and rl.get("doi"):
            doi, doi_src = rl["doi"], rl["method"]
        arx = ""
        for h in links:
            m = re.search(r"arxiv\.org/abs/([\w./-]+)", h)
            if m:
                arx = re.sub(r"v\d+$", "", m.group(1))
        extra = ref_urls.get(k, {}).get("url", "")
        bib["b-" + k] = dict(id="b-" + k, key=k, src="brouwer", authors=b["authors"], title=pretty(b["title"]), text=pretty(b["text"]),
                             year=b["year"], doi=doi, doi_src=doi_src, arxiv=arx,
                             urls=[h for h in links if "doi.org/" not in h and "arxiv.org/abs" not in h] + ([extra] if extra else []),
                             brouwer_anchor=BROUWER_BASE + "srgtabrefs.html#" + k, email=b["email"], rows=[])
    for k, b in LIB_BIB.items():
        if k in ("Spence95",) and "b-Spence95" in bib:
            continue
        bib["l-" + k] = dict(id="l-" + k, key=k, src="library", authors=b["authors"], title=b["title"], text="%s, %s, %s." % (b["authors"], b["title"], b["venue"]),
                             year=b.get("year"), doi=b.get("doi", ""), arxiv=b.get("arxiv", ""), urls=[b["url"]] if b.get("url") else [],
                             brouwer_anchor="", email=False, rows=[], note=LIB_BIB_FIXES.get(k, ""))
    dep_alias = {}
    for d in deposits:
        same = [b["id"] for b in bib.values() if b["src"] == "brouwer" and b.get("doi", "").lower() == d["doi"].lower()]
        if same:
            dep_alias["d-" + d["doi"]] = same[0]
            continue
        bib["d-" + d["doi"]] = dict(id="d-" + d["doi"], key=d["doi"], src="deposit", authors="A. Kovaľ", title=d["title"],
                                    text="A. Kovaľ, %s, preprint with data, Zenodo, 2026, doi:%s." % (d["title"], d["doi"]),
                                    year=2026, doi=d["doi"], arxiv="", urls=[OPEN_CASES + d["page"]] if d["page"] else [], brouwer_anchor="",
                                    email=False, rows=[])
    alias = {}

    def same_as(doi, arx, url, text):
        for b in bib.values():
            if (doi and b.get("doi", "").lower() == doi.lower()) or (arx and b.get("arxiv") == arx) or (url and url in b.get("urls", [])) or (text and b.get("text") == text):
                return b["id"]
        return None
    for k, c in lit_counts_bib.items():
        prev = same_as(c.get("doi", ""), c.get("arxiv", ""), c.get("url", ""), c["citation"])
        if prev:
            alias["c-" + k] = prev
            continue
        bib["c-" + k] = dict(id="c-" + k, key=k, src="literature", authors=c["authors"], title=c["title"], text=c["citation"],
                             year=int(c["year"]) if c.get("year", "").isdigit() else None, doi=c.get("doi", ""),
                             arxiv=c.get("arxiv", ""), urls=[c["url"]] if c.get("url") else [], brouwer_anchor="", email=False, rows=[])
    for k, b in lit_bib.items():
        m = re.search(r"arxiv\.org/abs/([\w.]+?)(v\d+)?$", b["url"])
        dm = re.search(r"doi\.org/(10\..+)$", b["url"])
        prev = same_as(dm.group(1) if dm else "", m.group(1) if m else "", b["url"], "")
        if prev:
            alias["t-" + k[5:]] = prev
            continue
        bib["t-" + k[5:]] = dict(id="t-" + k[5:], key=k[5:], src="literature", authors=b["authors"], title=b["title"],
                                 text="%s, %s, %s." % (b["authors"], b["title"], b["venue"].strip()), year=b["year"],
                                 doi=dm.group(1) if dm else "", arxiv=m.group(1) if m else "", urls=[] if (m or dm) else [b["url"]],
                                 brouwer_anchor="", email=False, rows=[])

    def bib_id(token):
        if token.startswith("dep:"):
            return dep_alias.get("d-" + token[4:], "d-" + token[4:])
        if token.startswith("lit:"):
            return alias.get("c-" + token[4:], "c-" + token[4:])
        if token.startswith("lit2:"):
            return alias.get("t-" + token[5:], "t-" + token[5:])
        if token.startswith("arXiv:") and ("t-" + token in bib or "t-" + token in alias):
            return alias.get("t-" + token, "t-" + token)
        if "b-" + token in bib:
            return "b-" + token
        if "l-" + token in bib:
            return "l-" + token
        return None

    # ---- assemble per-row records
    stat_counter = collections.Counter()
    full = {}
    for r in rows:
        x = r["id"]
        pr = x if r["primary"] else r["of"]
        ex = pr in excluded
        refs_used = list(r["ref_keys"])
        rec = dict(id=x, v=r["v"], k=r["k"], l=r["l"], mu=r["mu"], primary=r["primary"],
                   pair=pr, comp=r.get("comp") or r.get("of"),
                   status=r["status"], status_raw=r["status_raw"], brouwer_page=r["page"],
                   spectrum=dict(r=r["spec"]["r_txt"], f=r["spec"]["f"], s=r["spec"]["s_txt"], g=r["spec"]["g"],
                                 r_num=round(r["spec"]["r"], 4), s_num=round(r["spec"]["s"], 4), integral=r["spec"]["integral"],
                                 brouwer="%s^%s %s^%s" % (r["b_r"], r["b_f"], r["b_s"], r["b_g"]), agrees=r["spec_ok"]),
                   conference=r["conference"],
                   comment_html=r["comment_html"], comment_text=r["comment_text"],
                   brouwer_refs=["b-" + k for k in r["ref_keys"] if "b-" + k in bib],
                   families=r["pair_families"] if not ex else [x2 for x2 in r["pair_families"]],
                   fam_labels=r["fam_labels"],
                   reasons=r["reasons"] if r["primary"] else byid[pr]["reasons"],
                   head=r["head"],
                   counts=[] if ex else r["counts"],
                   ours=[] if ex else ours.get(pr, []),
                   literature=[] if ex else lit.get(pr, []),
                   partial=[] if ex else [dict(p, bib=bib_id(p["bib"])) for p in lit_partial.get(r["id"], []) + (lit_partial.get(r.get("comp") or r.get("of"), []) if False else [])],
                   sage=None if ex else r["sage"],
                   seed=None if ex else seed.get(x),
                   downloads=downloads.get(pr, []) if not ex else [d for d in downloads.get(pr, []) if d["src"] in ("spence", "ihringer")],
                   restricted=ex,
                   status_old=old_status.get(x))
        if ex:
            rec["counts"] = [c for c in r["counts"] if c["src"] == "brouwer"]
        # bibliography ids used by this row
        used = set(rec["brouwer_refs"])
        for c in rec["counts"]:
            b = bib_id(c["bib"])
            if b:
                c["bib_id"] = b
                used.add(b)
            if c.get("spence_ref"):
                used.add(bib_id(dict((s[0], s[1]) for s in SPENCE_REFS)[c["spence_ref"]]) or "")
        for o in rec["ours"]:
            used.add(dep_alias.get("d-" + o["doi"], "d-" + o["doi"]))
        for t in rec["literature"]:
            b = bib_id(t)
            if b:
                used.add(b)
        for p in rec["partial"]:
            if p.get("bib"):
                used.add(p["bib"])
        for f in rec["families"]:
            for fr in next(F for F in FAMILIES if F["id"] == f)["refs"]:
                if bib_id(fr):
                    used.add(bib_id(fr))
        for rs in rec["reasons"]:
            for fr in REASONS[rs]["refs"]:
                if bib_id(fr):
                    used.add(bib_id(fr))
        used.discard("")
        rec["bib"] = sorted(used)
        for b in used:
            if b in bib and pr not in bib[b]["rows"]:
                bib[b]["rows"].append(pr)
        rec["main"] = pretty(r["comment_parts"][0] if r["comment_parts"] else "")
        full[x] = rec
    for x, rec in full.items():
        if not rec["main"] and not rec["primary"]:
            p = full[rec["pair"]]
            if p["main"]:
                rec["main"] = "complement of: " + p["main"]

    # ---- statistics (per parameter pair = primary row)
    prim = [full[r["id"]] for r in rows if r["primary"]]
    by_status = collections.Counter(p["status"] for p in prim)
    ranges = []
    for lo in range(1, 1301, 100):
        hi = lo + 99
        c = collections.Counter(p["status"] for p in prim if lo <= p["v"] <= hi)
        ranges.append(dict(lo=lo, hi=hi, plus=c["+"], minus=c["-"], open=c["?"]))
    head_kind = collections.Counter(p["head"]["kind"] for p in prim)
    reasons_c = collections.Counter(rs for p in prim if p["status"] == "-" for rs in p["reasons"])
    fam_c = {f["id"]: len(fam_rows[f["id"]]) for f in FAMILIES}
    changes = []
    if old_status:
        for p in prim:
            o = old_status.get(p["id"])
            if o != p["status"]:
                changes.append(dict(id=p["id"], old=o, new=p["status"]))
    srcs_c = collections.Counter()
    for p in prim:
        for s in sorted(set(c["src"] for c in p["counts"])):
            srcs_c[s] += 1
    stats = dict(pairs=len(prim), sets=len(rows), by_status=dict(by_status), ranges=ranges,
                 head_kind=dict(head_kind), reasons=dict(reasons_c), families=fam_c, changes=changes,
                 count_sources=dict(srcs_c),
                 with_counts=sum(1 for p in prim if p["counts"]),
                 with_constructions=sum(1 for p in prim if p["families"]),
                 with_comment=sum(1 for p in prim if p["comment_text"] or (p["comp"] and full[p["comp"]]["comment_text"])),
                 with_refs=sum(1 for p in prim if p["brouwer_refs"] or (p["comp"] and full[p["comp"]]["brouwer_refs"]) or p["ours"] or p["literature"] or p["partial"]
                               or any(c["src"] in ("literature", "spence", "ihringer") for c in p["counts"])),
                 with_ours=sum(1 for p in prim if p["ours"]),
                 with_downloads=sum(1 for p in prim if p["downloads"]),
                 sage=dict(collections.Counter((full[x]["sage"] or {}).get("existence", "n/a") for x in full)),
                 family_checks={k: dict(ok=v[0], bad=v[1], bad_examples=v[2][:10]) for k, v in fam_check.items()},
                 restricted=sorted(excluded))

    # ---- write
    def write(name, obj):
        js = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        with open(os.path.join(a.out, name + ".json"), "w", encoding="utf-8") as f:
            f.write(js)
        with open(os.path.join(a.out, name + ".js"), "w", encoding="utf-8") as f:
            f.write("(window.SRGLIB=window.SRGLIB||{})[%s]=%s;\n" % (json.dumps(name), js))
    index = []
    for r in rows:
        rec = full[r["id"]]
        index.append([rec["id"], rec["v"], rec["k"], rec["l"], rec["mu"], rec["status"], 1 if rec["primary"] else 0,
                      rec["comp"] or "", rec["head"]["label"], rec["head"]["kind"], rec["main"][:90],
                      rec["families"], rec["spectrum"]["r_num"], rec["spectrum"]["s_num"], 1 if rec["conference"] else 0,
                      1 if rec["ours"] else 0, rec["reasons"]])
    write("index", dict(fields=["id", "v", "k", "l", "mu", "status", "primary", "comp", "count", "count_kind", "main",
                                "families", "r", "s", "conference", "ours", "reasons"], rows=index))
    for lo in range(1, 1301, 100):
        hi = lo + 99
        write("rows-%04d-%04d" % (lo, hi), {x: rec for x, rec in full.items() if lo <= rec["v"] <= hi})
    for b in bib.values():
        b["rows"].sort(key=lambda z: tuple(int(t) for t in z.split("_")))
    write("refs", dict(entries=list(bib.values()), spence_refs=[dict(n=i + 1, text=t, bib=bib_id(k) or "") for i, (_, k, t) in enumerate(SPENCE_REFS)]))
    write("families", [dict(id=F["id"], name=F["name"], formula=F["formula"], desc=F["desc"],
                            refs=[bib_id(x) for x in F["refs"] if bib_id(x)],
                            rows=sorted(fam_rows[F["id"]], key=lambda z: tuple(int(t) for t in z.split("_"))),
                            check=dict(ok=fam_check[F["id"]][0], bad=fam_check[F["id"]][1]) if F["check"] else None) for F in FAMILIES])
    write("downloads", dict(
        spence=[dict(row=s["row"], file=spence_rows[s["row"]]["file"], url=spence_rows[s["row"]]["url"], n=spence_rows[s["row"]]["n"],
                     kind=next((c["kind"] for c in pcounts.get(s["row"] if byid[s["row"]]["primary"] else byid[s["row"]]["of"], []) if c["src"] == "spence"), ""))
                for s in spence],
        ihringer=[dict(row=h["row"], count=int(h["count"]), label=h["label"], method=h["method"], section=h["section"], url=h["url"]) for h in ihr],
        deposits=[dict(doi=d["doi"], title=d["title"], kind=d["kind"], page=(OPEN_CASES + d["page"]) if d["page"] else "") for d in deposits],
        rows={x: [d for d in lst] for x, lst in downloads.items() if lst and x not in excluded}))
    write("reasons", [dict(id=k, name=R["name"], desc=R["desc"], refs=[bib_id(x) for x in R["refs"] if bib_id(x)], pairs=reasons_c.get(k, 0)) for k, R in REASONS.items()])
    meta = dict(built=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                brouwer_fetch=fetch, brouwer_old_fetch=old_fetch, brouwer_table=BROUWER_TABLE, brouwer_base=BROUWER_BASE,
                spence_page=SPENCE_PAGE, ihringer_page=IHRINGER_PAGE, sage_version="SageMath 10.10 (2026-09-28)",
                seeddb=seed_status, stats=stats, warnings=warnings,
                counts_literature=len(lit_counts_bib))
    write("meta", meta)
    print("rows %d (pairs %d): + %d, - %d, ? %d" % (len(rows), len(prim), by_status["+"], by_status["-"], by_status["?"]))
    print("pairs with counts %d, constructions %d, refs %d, ours %d, downloads %d" % (
        stats["with_counts"], stats["with_constructions"], stats["with_refs"], stats["with_ours"], stats["with_downloads"]))
    print("family checks:", {k: (v[0], v[1]) for k, v in fam_check.items()})
    print("warnings: %d" % len(warnings))
    for w in warnings[:80]:
        print("  W", w)


if __name__ == "__main__":
    main()
