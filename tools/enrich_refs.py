#!/usr/bin/env python3
"""Look up DOIs for the entries of Brouwer's SRG reference list (srgtabrefs.html)
that carry no DOI link, via the public Crossref REST API.

Usage (network needed; run rarely, the result is committed):
    python3 -I tools/enrich_refs.py <srgtabrefs.html> data/library/sources/ref_links.tsv

A Crossref hit is accepted only when the normalised title similarity is >= 0.90
and the publication year agrees (+-1) with the year printed in Brouwer's entry.
Everything else is written as 'unmatched' (the site then links Brouwer's own
reference entry, which is always resolvable).  Rows already present in the
output file are kept (manual corrections survive re-runs: put 'manual' in the
method column).
"""
import difflib, html, json, re, sys, time, urllib.parse, urllib.request

UA = "Mozilla/5.0 (compatible; srg-library-refresh)"


def norm(s):
    s = html.unescape(s).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_refs(path):
    t = open(path, encoding="utf-8").read()
    out = []
    for p in re.split(r"<p>\s*", t):
        m = re.search(r'<a name="([^"]+)"', p)
        if not m:
            continue
        links = re.findall(r'href="([^"]+)"', p)
        ti = re.search(r"<i>(.*?)</i>", p, re.S)
        title = re.sub(r"<[^>]+>", "", ti.group(1)) if ti else ""
        # titles split by an italic break, e.g. "<i>Structure and uniqueness of the</i> (81,20,1,6) <i>strongly ...</i>"
        its = re.findall(r"<i>(.*?)</i>", p, re.S)
        if len(its) > 1:
            seg = p[p.find("<i>"):p.rfind("</i>") + 4]
            title = re.sub(r"<[^>]+>", "", seg)
        txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", p))).strip()
        years = re.findall(r"\b(1[89]\d\d|20\d\d)\b", txt)
        out.append(dict(key=m.group(1), title=re.sub(r"\s+", " ", html.unescape(title)).strip(),
                        text=txt, links=links, year=int(years[-1]) if years else None))
    return out


def crossref(q):
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(
        {"query.bibliographic": q, "rows": 5, "select": "DOI,title,issued,container-title,author"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["message"]["items"]


def main():
    src, dst = sys.argv[1], sys.argv[2]
    keep = {}
    try:
        for ln in open(dst, encoding="utf-8"):
            if ln.startswith("key\t") or not ln.strip():
                continue
            p = ln.rstrip("\n").split("\t")
            if len(p) >= 3 and p[2] == "manual":
                keep[p[0]] = ln.rstrip("\n")
    except OSError:
        pass
    rows = []
    for r in parse_refs(src):
        if r["key"] in keep:
            rows.append(keep[r["key"]])
            continue
        if any("doi.org/" in l for l in r["links"]):
            d = [l for l in r["links"] if "doi.org/" in l][0].split("doi.org/")[1]
            rows.append("\t".join([r["key"], d, "brouwer-link", "1.00", r["title"], ""]))
            continue
        if not r["title"] or "email" in r["text"].lower():
            rows.append("\t".join([r["key"], "", "unmatched", "", r["title"], "no title or email entry"]))
            continue
        best = (0.0, None)
        try:
            items = crossref(r["text"])
        except Exception as e:  # network error: record and go on
            rows.append("\t".join([r["key"], "", "unmatched", "", r["title"], "crossref error " + type(e).__name__]))
            continue
        for it in items:
            t = " ".join(it.get("title") or [])
            sim = difflib.SequenceMatcher(None, norm(t), norm(r["title"])).ratio()
            y = None
            try:
                y = it["issued"]["date-parts"][0][0]
            except Exception:
                pass
            ok_year = (r["year"] is None or y is None or abs(int(y) - r["year"]) <= 1)
            if sim > best[0] and ok_year:
                best = (sim, it, t, y)
        if best[1] is not None and best[0] >= 0.90:
            rows.append("\t".join([r["key"], best[1]["DOI"], "crossref", "%.2f" % best[0], r["title"],
                                   "crossref title: %s (%s)" % (best[2], best[3])]))
        else:
            note = ("best %.2f: %s (%s) %s" % (best[0], best[2], best[3], best[1]["DOI"])) if best[1] else "no hit"
            rows.append("\t".join([r["key"], "", "unmatched", "%.2f" % best[0], r["title"], note]))
        time.sleep(1.0)
    with open(dst, "w", encoding="utf-8") as f:
        f.write("key\tdoi\tmethod\tsimilarity\tbrouwer_title\tnote\n")
        for ln in rows:
            f.write(ln.replace("\n", " ") + "\n")
    print(len(rows), "refs;", sum(1 for x in rows if "\tcrossref\t" in x), "matched by crossref")


if __name__ == "__main__":
    main()
