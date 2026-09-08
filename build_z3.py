#!/usr/bin/env python3
"""build_z3.py — builds z3.html: order-3 automorphisms of strongly regular graphs on <= 100 vertices.
Two tables from data/:
  data/z3_known.json     "recover the known": every known SRG + explicit order-3 automorphism in our catalogue,
                         its true quotient (f, o, n2, m, rank) and the verdict of each pipeline stage
                         (filter, frame existence, generator, lift) — produced by orbit-gen/scripts/z3_known_catalog.py
  data/p3_frontier.json  the fixed-point map of the open parameter sets — produced by
                         orbit-gen/scripts/p3_frontier_map.py (frame-diagonal identity + character-block trace,
                         CLOSED overlay from the CHANGELOG)
Self-contained HTML (same dark style as index.html). Run: python3 build_z3.py
"""
import json, html, os
here = os.path.dirname(os.path.abspath(__file__))
known = json.load(open(os.path.join(here, "data", "z3_known.json"))) if os.path.exists(os.path.join(here, "data", "z3_known.json")) else []
front = json.load(open(os.path.join(here, "data", "p3_frontier.json")))

def esc(x): return html.escape(str(x))
def params(P): return "(%d,%d,%d,%d)" % tuple(P)

# ---------- table 1: known graphs ----------
def badge(v, kind):
    if v is None or v == "": return '<span class="b-mut">—</span>'
    s = str(v)
    good = ("OK", "VERIFIED", "FEASIBLE", "True")
    bad = ("FAIL", "NONE", "INFEASIBLE", "False", "ERROR", "TIMEOUT")
    cls = "b-good" if any(s.startswith(g) for g in good) else ("b-bad" if any(s.startswith(b) for b in bad) else "b-mut")
    if kind == "gen" and s.startswith("COMPLETE"): cls = "b-good"
    return f'<span class="badge {cls}">{esc(s)}</span>'

rows1 = []
for r in known:
    if "error" in r:
        rows1.append(f'<tr><td>{esc(r["graph"])}</td><td class="param">{params(r["params"])}</td><td colspan="9" class="mut">construction error: {esc(r["error"])}</td></tr>'); continue
    if "note" in r:
        rows1.append(f'<tr><td>{esc(r["graph"])}</td><td class="param">{params(r["params"])}</td><td>{r["f"]}</td><td>{r["o"]}</td><td colspan="7" class="mut">{esc(r["note"])}</td></tr>'); continue
    truth = r.get("generator_has_truth")
    rows1.append("<tr>" + "".join([
        f'<td>{esc(r["graph"])}</td>', f'<td class="param">{params(r["params"])}</td>',
        f'<td>{r["f"]}</td>', f'<td>{r["o"]}</td>', f'<td>{r["n2"]}</td>', f'<td>{r["m"]}</td>', f'<td>{r["a"]}</td>',
        f'<td>{badge(r.get("filter"), "filter")}</td>', f'<td>{badge(r.get("frame"), "frame")}</td>',
        f'<td>{badge(r.get("generator"), "gen")} {("<span class=\"mut\">truth found: " + ("yes" if truth else "no") + "</span>") if truth is not None else ""}</td>',
        f'<td>{badge(r.get("lift"), "lift")}</td>',
    ]) + "</tr>")
n_known = len([r for r in known if "error" not in r and "note" not in r])
n_lift = len([r for r in known if r.get("lift") == "VERIFIED"])
n_filter = len([r for r in known if r.get("filter") == "OK"])
n_gen_c = len([r for r in known if str(r.get("generator", "")).startswith("COMPLETE")])
n_gen_t = len([r for r in known if str(r.get("generator", "")).startswith("TIMEOUT")])
n_frame_f = len([r for r in known if r.get("frame") == "FEASIBLE"])
n_frame_run = len([r for r in known if r.get("frame")])

# ---------- table 2: frontier map ----------
rows2 = []
for S in front["sets"]:
    P = params(S["params"])
    if not S.get("rows"):
        rows2.append(f'<tr><td class="param">{P}</td><td colspan="6" class="mut">{esc(S.get("note",""))}</td></tr>'); continue
    first = True
    for x in S["rows"]:
        st = x["status"]
        cls = {"IMPOSSIBLE": "b-bad", "CLOSED": "b-bad", "OPEN": "b-open"}[st]
        cases = ", ".join(f'(n<sub>2</sub>={c["n2"]}, m={c["m"]}, a={c["a"]})' for c in x["cases"]) or "—"
        rows2.append("<tr>" + f'<td class="param">{P if first else ""}</td>' + f'<td>{x["f"]}</td><td>{x["o"]}</td>' +
                     f'<td>{"yes" if x["diag0_rows"] else "no"} / {"yes" if x["diag2_rows"] else "no"}</td>' +
                     f'<td>{cases}</td><td><span class="badge {cls}">{st}</span></td><td class="cmt">{esc(x["evidence"])}</td></tr>')
        first = False
tot_imp = sum(S.get("summary", {}).get("impossible", 0) for S in front["sets"])
tot_closed = sum(S.get("summary", {}).get("closed", 0) for S in front["sets"])
tot_open = sum(S.get("summary", {}).get("open", 0) for S in front["sets"])

HTML = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SRG Database — automorphisms of order 3</title>
<style>
:root{{--bg:#0e1116;--panel:#161b22;--line:#222b36;--txt:#d7dde5;--mut:#8b97a6;--accent:#4ea1ff}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--txt);font:14px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}}
header{{padding:24px 28px 14px;border-bottom:1px solid var(--line)}} h1{{margin:0 0 4px;font-size:22px}} h2{{font-size:17px;margin:28px 0 8px}}
.sub{{color:var(--mut);font-size:13px;max-width:980px}} .sub a,a{{color:var(--accent)}}
.cards{{display:flex;flex-wrap:wrap;gap:12px;padding:16px 28px}} .card{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 16px;min-width:130px}}
.card .num{{font-size:22px;font-weight:700}} .card .lab{{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.04em}}
.wrap{{padding:0 28px 60px}} table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}
th,td{{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{position:sticky;top:0;background:#11161d;white-space:nowrap;font-size:12px;text-transform:uppercase;letter-spacing:.03em;color:var(--mut)}}
td.param{{font-weight:600;white-space:nowrap}} .mut{{color:var(--mut);font-size:12px}} .cmt{{color:var(--mut);font-size:12px;max-width:420px}}
.badge{{display:inline-block;border-radius:6px;padding:1px 8px;font-size:12px;font-weight:600}}
.b-good{{color:#7ee2a0;background:#0f2417}} .b-bad{{color:#f09a9a;background:#250f0f}} .b-open{{color:#f0cd6a;background:#2a2208}} .b-mut{{color:var(--mut)}}
tr:hover{{background:#11161d}} .box{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:12px 0;max-width:980px}}
code{{background:#0b0e13;border:1px solid var(--line);border-radius:4px;padding:1px 5px}}
footer{{color:var(--mut);font-size:12px;padding:20px 28px;border-top:1px solid var(--line);max-width:1000px}}
</style></head><body>
<header><h1>Automorphisms of order 3 — the known graphs recovered, the open parameters mapped</h1>
<div class="sub">Companion page of the <a href="index.html">SRG Database</a>. Every claim here is produced by a script in
<a href="https://github.com/tonykoval/orbit-gen">orbit-gen</a> and can be re-run; the tables are regenerated from
<code>data/z3_known.json</code> and <code>data/p3_frontier.json</code> by <code>build_z3.py</code>. Generated {esc(front.get("generated",""))}.</div></header>

<div class="cards">
<div class="card"><div class="num">{n_known}</div><div class="lab">known graph + order-3 action</div></div>
<div class="card"><div class="num">{n_lift}/{n_known}</div><div class="lab">true quotient lifted back</div></div>
<div class="card"><div class="num">{n_filter}/{n_known}</div><div class="lab">pass the frame + trace filter</div></div>
<div class="card"><div class="num">{n_gen_c} / {n_gen_t}</div><div class="lab">generator complete / timeout</div></div>
<div class="card"><div class="num">{n_frame_f}/{n_frame_run}</div><div class="lab">frame existence feasible (rank ≤ 5 runs)</div></div>
<div class="card"><div class="num">{tot_imp + tot_closed}</div><div class="lab">(open set, f) rows excluded</div></div>
<div class="card"><div class="num">{tot_open}</div><div class="lab">(open set, f) rows still open</div></div>
</div>

<div class="wrap">
<div class="box"><b>Method, in one paragraph.</b> Let σ be an automorphism of order 3 of an srg(n,k,λ,μ) with integer eigenvalues
r &gt; s, d = r − s, f fixed vertices and o = (n−f)/3 orbits. The adjacency matrix restricted to a nontrivial character of
⟨σ⟩ is an o×o Hermitian block C over Z[ω] with C<sub>ii</sub> ∈ {{0, −1}} and off-diagonal entries 0 or units, and
(C − rI)(C − sI) = 0. Two consequences are checkable without any orbit matrix: <i>(i)</i> with G = rI − C, G² = dG forces every
row to contain exactly g<sub>ii</sub>(d − g<sub>ii</sub>) unit entries — r(d−r) if a<sub>ii</sub> = 0, (r+1)(d−r−1) if a<sub>ii</sub> = 2 — so a row
type needs o − 1 ≥ that many columns; <i>(ii)</i> the trace of C equals −n<sub>2</sub> (n<sub>2</sub> = number of orbits with
a<sub>ii</sub> = 2), so r·m + s·(o−m) = −n<sub>2</sub> must have an integer solution m (the r-multiplicity of the block). When no
(n<sub>2</sub>, m) survives, the fixed-point count f is impossible (<b>IMPOSSIBLE</b>). When one survives with a small rank
a = min(m, o−m), the existence of the block is decided exactly by a CP-SAT model over Z[ω] tight frames
(<code>tools/eisenlift/frame_enum_cpsat2.py</code>): every basis-Gram class INFEASIBLE means <b>CLOSED</b>. The first table shows
the same pipeline on known graphs, where it must (and does) find what exists; the second shows the open parameter sets.</div>

<h2>1. Recover the known — every stage on graphs that exist</h2>
<div class="sub">Filter = does the true (n<sub>2</sub>, m) pass the frame + trace filter and do all rows have the predicted number of
unit entries; frame = existence of the character block for that (f, n<sub>2</sub>) decided without the orbit matrix (run for rank
a ≤ 5); generator = the orbit-matrix backtracker <code>search … --method backtrack</code> with a fixed timeout, and whether the true
quotient is among its outputs; lift = <code>eisenlift</code> rebuilds a verified SRG from the true quotient.</div>
<table><thead><tr><th>graph, action</th><th>parameters</th><th>f</th><th>o</th><th>n<sub>2</sub></th><th>m</th><th>rank a</th><th>filter</th><th>frame</th><th>generator</th><th>lift</th></tr></thead>
<tbody>{"".join(rows1)}</tbody></table>

<h2>2. The open parameter sets — which fixed-point counts an order-3 automorphism may have</h2>
<div class="sub">For each open set and each f ≡ n (mod 3): whether orbit rows with a<sub>ii</sub> = 0 / a<sub>ii</sub> = 2 fit at all,
the surviving (n<sub>2</sub>, m, rank) cases, and the status. IMPOSSIBLE rows are hand lemmas (verified on the known graphs above);
CLOSED rows carry a computational proof; OPEN rows are where a graph with an order-3 automorphism could still live.</div>
<table><thead><tr><th>parameters</th><th>f</th><th>o</th><th>rows a<sub>ii</sub>=0 / 2 fit</th><th>surviving cases (n<sub>2</sub>, m, rank)</th><th>status</th><th>evidence</th></tr></thead>
<tbody>{"".join(rows2)}</tbody></table>
</div>
<footer>Tony Koval, 2026. Scripts: <code>orbit-gen/scripts/z3_known_catalog.py</code>, <code>scripts/p3_trace_filter.py</code>,
<code>scripts/p3_frontier_map.py</code>, <code>tools/eisenlift/frame_enum_cpsat2.py</code>, <code>tools/eisenlift/eisenlift.c</code>. Status of the
lemmas: hand arguments with positive and negative computational controls; the CLOSED rows are computational proofs by a new tool
validated on the known graphs, not yet independently re-derived by a second formulation.</footer>
</body></html>"""
open(os.path.join(here, "z3.html"), "w", encoding="utf-8").write(HTML)
print("z3.html written:", n_known, "known rows;", tot_imp, "impossible +", tot_closed, "closed +", tot_open, "open frontier rows")
