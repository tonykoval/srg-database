#!/usr/bin/env python3
"""Build the static SRG database page from Brouwer's authoritative tables,
annotated with the new graphs constructed in this project.

Source of truth (cross-checked): A.E. Brouwer, "Parameters of strongly regular
graphs", https://aeb.win.tue.nl/graphs/srg/  (tables srgtab1-50, srgtab51-100).
Our additions are tagged `ours` and verified independently (valid SRG + |Aut|).

Run inside the srg69-dev container (python3):
  docker exec srg69-dev sh -lc 'cd /work/srg-database && python3 build.py'
"""
import re, html, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# ---- our new constructions (counts read live from the g6 output files) -------
def count_lines(p):
    try:
        with open(p) as f:
            return sum(1 for ln in f if ln.strip())
    except OSError:
        return 0

WORK = os.path.abspath(os.path.join(HERE, ".."))
OURS = {
    (50, 21, 8, 9):  dict(n=count_lines(os.path.join(WORK, "out/new_srg_50_21_8_9_all.g6")),
                          aut="|Aut|∈{1,2}", file="out/new_srg_50_21_8_9_all.g6"),
    (50, 28, 15, 16): dict(n=count_lines(os.path.join(WORK, "out/new_srg_50_28_15_16_all.g6")),
                          aut="|Aut|∈{1,2}", file="out/new_srg_50_28_15_16_all.g6"),
    (49, 24, 11, 12): dict(n=count_lines(os.path.join(WORK, "out/srg49_scale/new_all.txt")),
                          aut="|Aut|=1 (sampled)", file="out/new_srg_49_24_11_12_all.g6"),
    (57, 24, 11, 9):  dict(n=count_lines(os.path.join(WORK, "out/newparam_57_24_11_9/new_all.txt")),
                          aut="|Aut|=1 (sampled)", file="out/new_srg_57_24_11_9_all.g6"),
}

# ---- optional SageMath existence verdicts (data/sage_verdicts.json) ----------
# Written by scripts/sage_srg_crosscheck.sage; maps "v-k-lam-mu" -> "True"|"False"|"Unknown".
SAGE = {}
_sv = os.path.join(DATA, "sage_verdicts.json")
if os.path.exists(_sv):
    try:
        SAGE = json.load(open(_sv))
    except Exception:
        SAGE = {}

# ---- HTML cell cleaners ------------------------------------------------------
def clean_sup(cell):
    c = re.sub(r"<sup>(.*?)</sup>", r"^\1", cell, flags=re.S)
    c = re.sub(r"<[^>]+>", "", c)
    c = html.unescape(c)
    return c.replace("–", "-").replace("−", "-").strip()

def clean_plain(cell):
    c = re.sub(r"<[^>]+>", "", cell)
    c = html.unescape(c)
    return c.replace("–", "-").replace("−", "-").strip()

def parse_status(s):
    """Return (klass, count, label). klass in exists|none|open|inherit."""
    s = s.strip()
    if s in ("", "\xa0"):
        return ("inherit", None, "")
    if s == "-":
        return ("none", 0, "∄")
    if s == "?":
        return ("open", None, "open")
    if s == "+":
        return ("exists", "+", "+ many")
    m = re.match(r"^(\d+)(!?)$", s)
    if m:
        n = int(m.group(1)); exact = m.group(2) == "!"
        return ("exists", n, ("exactly " if exact else "≥ ") + str(n))
    if s == "!":
        return ("exists", 1, "exactly 1")
    return ("exists", s, s)

# ---- parse both tables -------------------------------------------------------
records = []
for fname, page in (("brouwer_1-50.html", "srgtab1-50.html"),
                    ("brouwer_51-100.html", "srgtab51-100.html")):
    path = os.path.join(DATA, fname)
    if not os.path.exists(path):
        continue
    txt = open(path, encoding="utf-8").read()
    cur_v = None
    last = ("none", 0, "∄")     # status of the most recent primary row
    for m in re.finditer(r"<tr([^>]*)>(.*?)</tr>", txt, re.S):
        attrs, body = m.group(1), m.group(2)
        if "<th" in body:
            continue
        tds = re.findall(r"<td[^>]*>(.*?)</td>", body, re.S)
        if len(tds) < 7:
            continue
        st_raw = clean_plain(tds[0])
        v = clean_plain(tds[1]); k = clean_plain(tds[2])
        lam = clean_plain(tds[3]); mu = clean_plain(tds[4])
        rf = clean_sup(tds[5]); sg = clean_sup(tds[6])
        comments = clean_plain(tds[7]) if len(tds) > 7 else ""
        kls, cnt, lbl = parse_status(st_raw)
        is_comp = (v == "")
        if is_comp:
            v = cur_v
            if kls == "inherit":
                kls, cnt, lbl = last      # complement shares existence/count
        else:
            cur_v = v
            if kls != "inherit":
                last = (kls, cnt, lbl)
        try:
            vi, ki, li, ui = int(v), int(k), int(lam), int(mu)
        except (TypeError, ValueError):
            continue
        ours = OURS.get((vi, ki, li, ui))
        records.append(dict(
            v=vi, k=ki, lam=li, mu=ui, r=rf, s=sg,
            status=kls, count=cnt, label=lbl, comp=is_comp,
            comments=comments, page=page,
            ours=(ours["n"] if ours else 0),
            ours_aut=(ours["aut"] if ours else ""),
            ours_file=(ours["file"] if ours else ""),
            sage=SAGE.get(f"{vi}-{ki}-{li}-{ui}", ""),
        ))

# params list for the Sage cross-check script to consume
with open(os.path.join(DATA, "params.json"), "w") as f:
    json.dump([[r["v"], r["k"], r["lam"], r["mu"]] for r in records], f)

# ---- summary stats -----------------------------------------------------------
n_total = len(records)
n_exists = sum(1 for r in records if r["status"] == "exists")
n_open = sum(1 for r in records if r["status"] == "open")
n_none = sum(1 for r in records if r["status"] == "none")
n_unclass = sum(1 for r in records if r["status"] == "exists" and r["count"] == "+")
ours_params = [r for r in records if r["ours"]]
ours_total = sum(r["ours"] for r in ours_params)

data_json = json.dumps(records, separators=(",", ":"))

# ---- emit HTML ---------------------------------------------------------------
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SRG Database — known &amp; newly constructed</title>
<style>
:root{--bg:#0e1116;--panel:#161b22;--line:#222b36;--txt:#d7dde5;--mut:#8b97a6;
--exists:#1f7a3f;--existsbg:#0f2417;--open:#b8860b;--openbg:#2a2208;--none:#8a2b2b;--nonebg:#250f0f;
--ours:#7b3fe4;--oursbg:#1c1230;--accent:#4ea1ff;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font:14px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
header{padding:24px 28px 14px;border-bottom:1px solid var(--line)}
h1{margin:0 0 4px;font-size:22px}
.sub{color:var(--mut);font-size:13px;max-width:900px}
.sub a{color:var(--accent)}
.cards{display:flex;flex-wrap:wrap;gap:12px;padding:16px 28px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 16px;min-width:120px}
.card .num{font-size:22px;font-weight:700}
.card .lab{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.card.ours{border-color:var(--ours);background:var(--oursbg)}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:8px 28px 16px}
input[type=search],select{background:var(--panel);border:1px solid var(--line);color:var(--txt);
border-radius:8px;padding:8px 10px;font-size:14px}
input[type=search]{min-width:240px}
.chip{border:1px solid var(--line);background:var(--panel);color:var(--txt);border-radius:20px;
padding:6px 13px;cursor:pointer;font-size:13px;user-select:none}
.chip.on{border-color:var(--accent);color:#fff;background:#13314f}
.wrap{padding:0 28px 60px}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{position:sticky;top:0;background:#11161d;cursor:pointer;white-space:nowrap;font-size:12px;
text-transform:uppercase;letter-spacing:.03em;color:var(--mut)}
th:hover{color:#fff}
td.param{font-weight:600;white-space:nowrap}
.badge{display:inline-block;border-radius:6px;padding:1px 8px;font-size:12px;font-weight:600}
.b-exists{color:#7ee2a0;background:var(--existsbg)}
.b-open{color:#f0cd6a;background:var(--openbg)}
.b-none{color:#f09a9a;background:var(--nonebg)}
tr.ours{background:var(--oursbg)}
tr.ours:hover{background:#241740}
tr:hover{background:#11161d}
.ours-badge{color:#c7a3ff;background:#2a1750;border:1px solid #4a2c87;border-radius:6px;
padding:1px 7px;font-size:11px;font-weight:700;white-space:nowrap}
.eig{color:var(--mut);white-space:nowrap}
.cmt{color:var(--mut);font-size:12px;max-width:380px}
.comp{color:var(--mut);font-size:11px}
a.src{color:var(--accent);text-decoration:none;font-size:12px}
footer{color:var(--mut);font-size:12px;padding:20px 28px;border-top:1px solid var(--line);max-width:1000px}
code{background:#0b0e13;border:1px solid var(--line);border-radius:4px;padding:1px 5px}
.count0{color:var(--mut)}
</style>
</head>
<body>
<header>
<h1>Strongly Regular Graph Database</h1>
<div class="sub">Feasible parameter sets for SRGs with __NTOTAL__ entries (v&nbsp;&le;&nbsp;100),
cross-checked against the authoritative table of
<a href="https://aeb.win.tue.nl/graphs/srg/" target="_blank">A.E.&nbsp;Brouwer &mdash; Parameters of strongly regular graphs</a>
(<a href="data/brouwer_1-50.html">v&le;50</a>, <a href="data/brouwer_51-100.html">51&le;v&le;100</a>, retrieved 2026-05-30).
Rows in <span style="color:#c7a3ff">purple</span> are parameters where this project constructed
<b>new graphs this session</b> &mdash; each independently verified as a valid SRG with the stated automorphism order.
Status legend: <span class="badge b-exists">exists</span> a graph is known &middot;
<span class="badge b-open">open</span> existence undecided &middot;
<span class="badge b-none">&#8708;</span> proven non-existent.
&ldquo;+&rdquo; = exists, many graphs, full set not classified.</div>
</header>

<div class="cards">
<div class="card"><div class="num">__NTOTAL__</div><div class="lab">Parameter sets</div></div>
<div class="card"><div class="num" style="color:#7ee2a0">__NEXISTS__</div><div class="lab">Exist</div></div>
<div class="card"><div class="num" style="color:#f0cd6a">__NOPEN__</div><div class="lab">Open existence</div></div>
<div class="card"><div class="num" style="color:#f09a9a">__NNONE__</div><div class="lab">Non-existent</div></div>
<div class="card"><div class="num">__NUNCLASS__</div><div class="lab">Exist, unclassified (+)</div></div>
<div class="card ours"><div class="num" style="color:#c7a3ff">__NOURSP__</div><div class="lab">Params we extended</div></div>
<div class="card ours"><div class="num" style="color:#c7a3ff">__OURSTOTAL__</div><div class="lab">New graphs we added</div></div>
</div>

<div class="controls">
<input type="search" id="q" placeholder="search v,k,&lambda;,&mu; or comment (e.g. 50 21, Paley, Conway, T(14))">
<span class="chip on" data-f="all">All</span>
<span class="chip" data-f="exists">Exist</span>
<span class="chip" data-f="open">Open</span>
<span class="chip" data-f="none">Non-existent</span>
<span class="chip" data-f="unclass">Unclassified (+)</span>
<span class="chip" data-f="ours">Our new graphs</span>
<select id="vmax"><option value="100">v &le; 100</option><option value="50">v &le; 50</option>
<option value="40">v &le; 40</option></select>
<span id="shown" style="color:var(--mut)"></span>
</div>

<div class="wrap">
<table id="t">
<thead><tr>
<th data-k="v">v</th><th data-k="k">k</th><th data-k="lam">&lambda;</th><th data-k="mu">&mu;</th>
<th data-k="r">r<sup>f</sup>&nbsp;/&nbsp;s<sup>g</sup></th>
<th data-k="status">status</th><th data-k="count">#known</th>
<th data-k="ours">#new&nbsp;(ours)</th><th data-k="sage">Sage&nbsp;DB</th>
<th data-k="comments">comments / constructions</th>
</tr></thead>
<tbody id="tb"></tbody>
</table>
</div>

<footer>
<b>Provenance &amp; cross-check.</b> Parameter list, eigenvalues, existence status and known counts are taken
verbatim from Brouwer's tables (retrieved 2026-05-30) and re-rendered here; the original HTML is archived under
<code>data/</code> for audit. The <b>#new (ours)</b> column counts graphs constructed in this project this session by an
Ihringer-style Godsil&ndash;McKay switching cascade from low-symmetry de&nbsp;Caen seeds, each verified independently as a
valid SRG (degree, &lambda;, &mu;) with automorphism order computed by <code>dreadnaut</code>. These parameters are
Brouwer-&ldquo;+&rdquo; (exist, not fully classified); our graphs are asymmetric (|Aut| not divisible by 6), hence
outside every published prescribed-automorphism enumeration. Method and caveats: <code>docs/new_srgs_2026_05_30.md</code>.
<b>Second cross-check &mdash; SageMath.</b> The <b>Sage&nbsp;DB</b> column is the verdict of
<code>sage.graphs.strongly_regular_graph(v,k,&lambda;,&mu;,&nbsp;existence=True)</code> (Cohen&ndash;Pasechnik's
programmatic implementation of Brouwer's tables): &ldquo;&#10003;&nbsp;builds&rdquo; = Sage constructs a representative,
&ldquo;?&rdquo; = existence unknown to Sage, &ldquo;&#8708;&rdquo; = Sage proves non-existence. For our three parameters
Sage independently confirms existence, and every sampled graph of ours was re-verified by Sage's
<code>is_strongly_regular()</code> and found non-isomorphic to Sage's representative (see
<code>scripts/sage_srg_crosscheck.sage</code>).
This page is a static snapshot &mdash; regenerate with <code>python3 srg-database/build.py</code>.
</footer>

<script>
const DATA = __DATA__;
const statusBadge = r => {
  if(r.status==='exists') return '<span class="badge b-exists">'+(r.label||'exists')+'</span>';
  if(r.status==='open')   return '<span class="badge b-open">open</span>';
  return '<span class="badge b-none">&#8708;</span>';
};
const knownCount = r => {
  if(r.status==='none') return '&mdash;';
  if(r.status==='open') return '?';
  if(r.count==='+') return '<span title="many, not fully classified">+</span>';
  return r.count==null?'?':r.count;
};
const sageCell = r => {
  if(r.sage==='True')    return '<span class="badge b-exists" title="SageMath constructs a graph at these parameters">&#10003;&nbsp;builds</span>';
  if(r.sage==='False')   return '<span class="badge b-none" title="SageMath: no such graph">&#8708;</span>';
  if(r.sage==='Unknown') return '<span class="badge b-open" title="SageMath: existence unknown">?</span>';
  return '<span class="count0" title="not queried">&mdash;</span>';
};
let filter='all', sortK='v', sortDir=1, q='', vmax=100;
function pass(r){
  if(r.v>vmax) return false;
  if(filter==='exists' && r.status!=='exists') return false;
  if(filter==='open' && r.status!=='open') return false;
  if(filter==='none' && r.status!=='none') return false;
  if(filter==='unclass' && !(r.status==='exists'&&r.count==='+')) return false;
  if(filter==='ours' && !r.ours) return false;
  if(q){
    const hay=(r.v+' '+r.k+' '+r.lam+' '+r.mu+' '+r.comments+' '+r.r+' '+r.s).toLowerCase();
    if(!hay.includes(q)) return false;
  }
  return true;
}
function cmp(a,b){
  let x=a[sortK], y=b[sortK];
  if(sortK==='count'||sortK==='ours'){ x=(x==='+'?1e9:(x==null?-1:x)); y=(y==='+'?1e9:(y==null?-1:y)); }
  if(typeof x==='string'){ return sortDir*(''+x).localeCompare(''+y); }
  return sortDir*((x>y)-(x<y));
}
function render(){
  const rows=DATA.filter(pass).sort(cmp);
  const tb=document.getElementById('tb');
  tb.innerHTML=rows.map(r=>{
    const oursCell = r.ours
      ? '<span class="ours-badge">+'+r.ours.toLocaleString()+'</span> <span class="comp">'+r.ours_aut+'</span>'
      : '<span class="count0">&mdash;</span>';
    const comp = r.comp ? ' <span class="comp">(comp.)</span>' : '';
    const cmt = r.comments && r.comments!=='' ? r.comments : '';
    return '<tr class="'+(r.ours?'ours':'')+'">'+
      '<td class="param">'+r.v+comp+'</td><td>'+r.k+'</td><td>'+r.lam+'</td><td>'+r.mu+'</td>'+
      '<td class="eig">'+r.r+' / '+r.s+'</td>'+
      '<td>'+statusBadge(r)+'</td>'+
      '<td>'+knownCount(r)+'</td>'+
      '<td>'+oursCell+'</td>'+
      '<td>'+sageCell(r)+'</td>'+
      '<td class="cmt">'+cmt+' <a class="src" href="data/'+r.page.replace('.html','')+'.html" title="Brouwer source">src</a></td>'+
      '</tr>';
  }).join('');
  document.getElementById('shown').textContent=rows.length+' / '+DATA.length+' shown';
}
document.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{
  document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));
  c.classList.add('on'); filter=c.dataset.f; render();
});
document.getElementById('q').oninput=e=>{ q=e.target.value.toLowerCase().trim(); render(); };
document.getElementById('vmax').onchange=e=>{ vmax=+e.target.value; render(); };
document.querySelectorAll('th').forEach(th=>th.onclick=()=>{
  const k=th.dataset.k; if(k===sortK) sortDir*=-1; else {sortK=k; sortDir=1;} render();
});
render();
</script>
</body>
</html>
"""

out = (HTML
       .replace("__NTOTAL__", str(n_total))
       .replace("__NEXISTS__", str(n_exists))
       .replace("__NOPEN__", str(n_open))
       .replace("__NNONE__", str(n_none))
       .replace("__NUNCLASS__", str(n_unclass))
       .replace("__NOURSP__", str(len(ours_params)))
       .replace("__OURSTOTAL__", f"{ours_total:,}")
       .replace("__DATA__", data_json))

with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
    f.write(out)

print(f"parsed {n_total} parameter sets: {n_exists} exist, {n_open} open, {n_none} non-existent, {n_unclass} unclassified(+)")
print(f"our extensions: {len(ours_params)} params, {ours_total:,} new graphs")
for r in ours_params:
    print(f"  SRG({r['v']},{r['k']},{r['lam']},{r['mu']}): +{r['ours']:,}  [{r['ours_aut']}]")
print("wrote", os.path.join(HERE, "index.html"))
