#!/usr/bin/env python3
"""Validate the SRG Library data (run after build_library.py).

    python3 -I tools/validate_library.py [--brouwer DIR] [--online]

Checks
  1. every row of Brouwer's local table pages (v <= 1300) is in data/library/index.json, and nothing else;
  2. every bibliography entry has at least one resolvable link (DOI / arXiv / URL / Brouwer anchor);
     with --online each DOI is resolved (Crossref, or DataCite for 10.5281/*), each arXiv id via the
     arXiv API, and each other URL with a HEAD/GET request; results -> data/library/sources/link_check.tsv
  3. no forbidden strings in the published data ("in preparation", private paths, e-mail addresses,
     internal ledger vocabulary);
  4. restricted rows carry Brouwer data only.
Exit status 1 if any check fails.
"""
import argparse, glob, html, json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(HERE, "data", "library")
UA = "Mozilla/5.0 (compatible; srg-library-refresh)"


def P(path):
    if os.name != "nt":
        m = re.match(r"^([A-Za-z]):[\\/](.*)$", path)
        if m:
            return "/mnt/%s/%s" % (m.group(1).lower(), m.group(2).replace("\\", "/"))
    return path


def get(url, method="GET", accept=None):
    h = {"User-Agent": UA}
    if accept:
        h["Accept"] = accept
    req = urllib.request.Request(url, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read(200000) if method == "GET" else b""
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return "ERR " + type(e).__name__, b""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brouwer", default=r"D:\srg-library\external\brouwer\2026-11-07")
    ap.add_argument("--online", action="store_true")
    a = ap.parse_args()
    fails = []
    idx = json.load(open(os.path.join(LIB, "index.json"), encoding="utf-8"))
    F = {f: i for i, f in enumerate(idx["fields"])}
    ids = [r[F["id"]] for r in idx["rows"]]
    # 1. rows
    src = []
    for fp in glob.glob(os.path.join(P(a.brouwer), "srgtab[0-9]*.html")):
        t = open(fp, encoding="utf-8", errors="replace").read()
        lastv = None
        for m in re.finditer(r'<tr bgcolor="#[0-9a-fA-F]+">(.*?)</tr>', t, re.S):
            c = [html.unescape(re.sub(r"<[^>]+>", "", x)).replace("\xa0", "").strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", m.group(1), re.S)]
            v = c[1] or lastv
            lastv = v
            src.append("%s_%s_%s_%s" % (v, c[2], c[3], c[4]))
    miss = sorted(set(src) - set(ids))
    extra = sorted(set(ids) - set(src))
    print("1. rows: Brouwer pages %d lines, Library %d rows, missing %d, extra %d, duplicates %d" % (
        len(src), len(ids), len(miss), len(extra), len(ids) - len(set(ids))))
    if miss or extra or len(src) != len(ids) or len(ids) != len(set(ids)):
        fails.append("rows: missing %s extra %s" % (miss[:5], extra[:5]))
    # 2. references
    refs = json.load(open(os.path.join(LIB, "refs.json"), encoding="utf-8"))["entries"]
    nolink = [e["id"] for e in refs if not (e.get("doi") or e.get("arxiv") or e.get("urls") or e.get("brouwer_anchor"))]
    only_anchor = [e["id"] for e in refs if not (e.get("doi") or e.get("arxiv") or e.get("urls")) and e.get("brouwer_anchor")]
    print("2. references: %d entries, %d without any link, %d resolvable only through Brouwer's reference entry" % (len(refs), len(nolink), len(only_anchor)))
    if nolink:
        fails.append("references without link: %s" % nolink)
    if a.online:
        out = []
        dois = sorted({e["doi"] for e in refs if e.get("doi")})
        for d in dois:
            if d.lower().startswith("10.5281/"):
                st, _ = get("https://api.datacite.org/dois/" + urllib.parse.quote(d))
                via = "datacite"
            else:
                st, _ = get("https://api.crossref.org/works/" + urllib.parse.quote(d))
                via = "crossref"
            out.append(("doi", d, via, str(st)))
            time.sleep(0.4)
        arx = sorted({e["arxiv"] for e in refs if e.get("arxiv")})
        for i in range(0, len(arx), 20):
            chunk = arx[i:i + 20]
            st, body = get("https://export.arxiv.org/api/query?max_results=50&id_list=" + ",".join(chunk))
            txt = body.decode("utf-8", "replace")
            for x in chunk:
                ok = ("arxiv.org/abs/" + x) in txt and "<title>Error</title>" not in txt
                out.append(("arxiv", x, "arxiv-api", "200" if ok else "NOT-FOUND"))
            time.sleep(1)
        urls = sorted({u for e in refs for u in e.get("urls", [])} | {"https://aeb.win.tue.nl/graphs/srg/srgtabrefs.html"})
        for u in urls:
            st, _ = get(u, "HEAD")
            if st != 200:
                st, _ = get(u, "GET")
            out.append(("url", u, "http", str(st)))
            time.sleep(0.4)
        bad = [o for o in out if o[3] != "200"]
        with open(os.path.join(LIB, "sources", "link_check.tsv"), "w", encoding="utf-8") as f:
            f.write("# link check of refs.json, %s\nkind\tid\tvia\tstatus\n" % time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()))
            for o in out:
                f.write("\t".join(o) + "\n")
        print("   online: %d DOIs, %d arXiv ids, %d URLs checked; %d not OK" % (len(dois), len(arx), len(urls), len(bad)))
        for o in bad:
            print("   NOT OK", o)
        if bad:
            fails.append("links not resolving: %d" % len(bad))
    # 3. forbidden strings
    pat = re.compile(r"in preparation|/mnt/|C:\\\\|out/|docs/|PROVED-OURS|COMPUTED-|INFEASIBLE|UNKNOWN-INCOMPLETE|external_untrusted|@[a-z0-9.-]+\.[a-z]{2,}|CONFIDENTIAL|PRIVATE", re.I)
    hits = []
    for fp in sorted(glob.glob(os.path.join(LIB, "*.json"))):
        t = open(fp, encoding="utf-8").read()
        for m in pat.finditer(t):
            hits.append("%s: %s" % (os.path.basename(fp), t[max(0, m.start() - 60):m.end() + 40].replace("\n", " ")))
    print("3. forbidden strings: %d hits" % len(hits))
    for h in hits[:20]:
        print("   ", h)
    if hits:
        fails.append("forbidden strings: %d" % len(hits))
    # 4. restricted rows
    meta = json.load(open(os.path.join(LIB, "meta.json"), encoding="utf-8"))
    bad = []
    for x in meta["stats"]["restricted"]:
        v = int(x.split("_")[0])
        lo = (v - 1) // 100 * 100 + 1
        rows = json.load(open(os.path.join(LIB, "rows-%04d-%04d.json" % (lo, lo + 99)), encoding="utf-8"))
        r = rows[x]
        if r["ours"] or r["literature"] or r["partial"] or r["sage"] or r["seed"] or any(c["src"] != "brouwer" for c in r["counts"]):
            bad.append(x)
    print("4. restricted rows: %d, carrying non-Brouwer data: %d" % (len(meta["stats"]["restricted"]), len(bad)))
    if bad:
        fails.append("restricted rows with extra data: %s" % bad)
    print("RESULT:", "PASS" if not fails else "FAIL " + "; ".join(fails))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
