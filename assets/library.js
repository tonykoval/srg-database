/* SRG Library — shared code (vanilla JS, no dependencies). Works from file:// and http(s)://:
   data are loaded as <script> files data/library/<name>.js that register themselves in window.SRGLIB. */
(function () {
  "use strict";
  var SRG = (window.SRG = {});
  var cache = {};
  var BASE = (document.currentScript && document.currentScript.getAttribute("data-base")) || "";

  SRG.load = function (name) {
    if (cache[name]) return cache[name];
    cache[name] = new Promise(function (res, rej) {
      if (window.SRGLIB && window.SRGLIB[name]) return res(window.SRGLIB[name]);
      var s = document.createElement("script");
      s.src = BASE + "data/library/" + name + ".js";
      s.onload = function () { (window.SRGLIB && window.SRGLIB[name]) ? res(window.SRGLIB[name]) : rej(new Error("no data " + name)); };
      s.onerror = function () { rej(new Error("could not load " + s.src)); };
      document.head.appendChild(s);
    });
    return cache[name];
  };
  SRG.rangeFile = function (v) {
    var lo = Math.floor((v - 1) / 100) * 100 + 1;
    var p = function (n) { return ("000" + n).slice(-4); };
    return "rows-" + p(lo) + "-" + p(lo + 99);
  };
  SRG.esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  SRG.fmt = function (n) { return n == null ? "" : Number(n).toLocaleString("en-US"); };
  SRG.params = function (id) { return "(" + id.split("_").join(",") + ")"; };
  SRG.rowHref = function (id) { return "library.html#row=" + id.split("_").join("-"); };
  SRG.STATUS = {
    "+": { cls: "yes", name: "exists", long: "exists (Brouwer “+”)" },
    "-": { cls: "no", name: "does not exist", long: "does not exist (Brouwer “−”)" },
    "?": { cls: "open", name: "open", long: "open (Brouwer “?”)" }
  };
  SRG.statusHtml = function (st) {
    var s = SRG.STATUS[st] || SRG.STATUS["?"];
    return '<span class="st"><span class="key ' + s.cls + '" aria-hidden="true"></span>' + s.name + "</span>";
  };

  // ---------- theme
  function getTheme() { try { return localStorage.getItem("srglib-theme"); } catch (e) { return null; } }
  function setTheme(t) {
    if (t) document.documentElement.setAttribute("data-theme", t); else document.documentElement.removeAttribute("data-theme");
    try { if (t) localStorage.setItem("srglib-theme", t); else localStorage.removeItem("srglib-theme"); } catch (e) {}
  }
  var saved = getTheme();
  if (saved) document.documentElement.setAttribute("data-theme", saved);

  // ---------- header / footer
  var PAGES = [
    ["library", "library.html", "Overview & table"],
    ["families", "families.html", "Families"],
    ["stats", "stats.html", "Statistics"],
    ["references", "references.html", "References"],
    ["downloads", "downloads.html", "Downloads"],
    ["about", "about.html", "About"],
    ["v100", "index.html", "v ≤ 100 (2026-05)"],
    ["z3", "z3.html", "Order-3 automorphisms"]
  ];
  SRG.header = function () {
    var h = document.querySelector("header.top");
    if (!h) return;
    var cur = document.body.getAttribute("data-page");
    var nav = PAGES.map(function (p) {
      return '<a href="' + p[1] + '"' + (p[0] === cur ? ' aria-current="page"' : "") + ">" + p[2] + "</a>";
    }).join("");
    h.innerHTML = '<div class="wrap"><a class="brand" href="library.html">SRG Library <span>v ≤ 1300</span></a>' +
      '<nav class="nav" aria-label="Site">' + nav + "</nav>" +
      '<button class="theme-btn" type="button" id="themeBtn" aria-label="Switch colour theme">Theme</button></div>';
    var b = document.getElementById("themeBtn");
    function label() {
      var t = document.documentElement.getAttribute("data-theme");
      b.textContent = t === "dark" ? "Dark" : t === "light" ? "Light" : "Auto";
      b.title = "Colour theme: " + b.textContent + " (click to change)";
    }
    b.addEventListener("click", function () {
      var t = document.documentElement.getAttribute("data-theme");
      setTheme(t === null ? "dark" : t === "dark" ? "light" : null);
      label();
    });
    label();
  };
  SRG.sourceLine = function (meta) {
    var d = (meta.brouwer_fetch || "").slice(0, 10);
    return 'Status per A. E. Brouwer’s table (fetched ' + SRG.esc(d) + '), <a href="' + meta.brouwer_table + '">' +
      meta.brouwer_table + "</a>. Every row links to Brouwer’s page for that row.";
  };
  SRG.footer = function (meta) {
    var f = document.querySelector("footer.foot");
    if (!f) return;
    f.innerHTML = '<div class="wrap">SRG Library · data built ' + SRG.esc((meta.built || "").slice(0, 10)) +
      " from Brouwer’s table fetched " + SRG.esc((meta.brouwer_fetch || "").slice(0, 16).replace("T", " ")) + " UTC · " +
      'Library data CC BY 4.0 (third-party data under their own terms) · <a href="about.html">About and how to cite</a></div>';
  };

  // ---------- references
  var refsP = null;
  SRG.refs = function () {
    if (!refsP) refsP = SRG.load("refs").then(function (r) {
      var m = {}; r.entries.forEach(function (e) { m[e.id] = e; }); r.map = m; return r;
    });
    return refsP;
  };
  SRG.bibHtml = function (e, opts) {
    opts = opts || {};
    var links = [];
    if (e.doi) links.push('<a href="https://doi.org/' + SRG.esc(e.doi) + '">doi:' + SRG.esc(e.doi) + "</a>");
    if (e.arxiv) links.push('<a href="https://arxiv.org/abs/' + SRG.esc(e.arxiv) + '">arXiv:' + SRG.esc(e.arxiv) + "</a>");
    (e.urls || []).forEach(function (u) {
      var lab = u.replace(/^https?:\/\//, "").replace(/\/$/, "");
      if (lab.length > 60) lab = lab.slice(0, 57) + "…";
      links.push('<a href="' + SRG.esc(u) + '">' + SRG.esc(lab) + "</a>");
    });
    if (e.brouwer_anchor) links.push('<a href="' + SRG.esc(e.brouwer_anchor) + '">entry in Brouwer’s references</a>');
    var txt = SRG.esc(e.text);
    var extra = "";
    if (e.email) extra = ' <span class="muted small">(a communication recorded in Brouwer’s table; no public paper)</span>';
    if (e.doi_src && e.doi_src !== "brouwer") extra += ' <span class="muted small">(DOI added by the Library via ' + (e.doi_src === "manual" ? "a checked manual lookup" : "Crossref, title match") + ")</span>";
    return '<div class="bibent" id="' + (opts.anchor ? SRG.esc(e.id) : "") + '">' + txt + extra +
      '<div class="links">' + links.join(" ") + "</div></div>";
  };

  // ---------- row detail (used on library.html)
  SRG.detail = function (id, el) {
    var v = +id.split("_")[0];
    return Promise.all([SRG.load(SRG.rangeFile(v)), SRG.refs(), SRG.load("families"), SRG.load("reasons"), SRG.load("meta")]).then(function (a) {
      var rows = a[0], refs = a[1], fams = a[2], reasons = a[3], meta = a[4];
      var r = rows[id];
      if (!r) { el.innerHTML = '<p>No row ' + SRG.esc(SRG.params(id)) + ' in Brouwer’s table (v ≤ 1300).</p>'; return null; }
      var pr = r.primary ? r : rows[r.pair];
      var other = r.comp ? rows[r.comp] : null;
      var famMap = {}; fams.forEach(function (f) { famMap[f.id] = f; });
      var resMap = {}; reasons.forEach(function (x) { resMap[x.id] = x; });
      var E = SRG.esc, h = [];
      var bdate = (meta.brouwer_fetch || "").slice(0, 10);
      // status
      h.push('<div class="sec"><h3>Status</h3><dl class="kv">');
      h.push("<dt>Brouwer’s table</dt><dd>" + SRG.statusHtml(r.status) + ' · symbol “' + E(pr.status_raw || r.status) + '” · fetched ' + E(bdate) +
        ' · <a href="' + E(r.brouwer_page) + '">open Brouwer’s page for this row</a> (' + E(r.brouwer_page.split("/").pop()) + ")</dd>");
      if (r.status_old && r.status_old !== r.status) h.push("<dt>Change</dt><dd>" + E(r.status_old) + " → " + E(r.status) + " since Brouwer’s table of " + E((meta.brouwer_old_fetch || "").slice(0, 10)) + "</dd>");
      h.push("<dt>Parameters</dt><dd><span class=mono>srg" + E(SRG.params(r.id)) + "</span>" + (r.primary ? "" : " (listed by Brouwer as the complement)") + "</dd>");
      if (other) h.push('<dt>Complement</dt><dd><a class="mono" href="' + SRG.rowHref(other.id) + '" data-row="' + E(other.id) + '">srg' + E(SRG.params(other.id)) + "</a></dd>");
      var sp = r.spectrum;
      h.push("<dt>Eigenvalues</dt><dd><span class=mono>" + r.k + "<sup>1</sup>, " + E(sp.r) + "<sup>" + sp.f + "</sup>, " + E(sp.s) + "<sup>" + sp.g + "</sup></span>" +
        (sp.integral ? "" : " ≈ " + sp.r_num.toFixed(3) + ", " + sp.s_num.toFixed(3)) + (r.conference ? " · conference graph parameters" : "") +
        (sp.agrees ? ' <span class="muted small">(agrees with Brouwer’s r<sup>f</sup>, s<sup>g</sup>)</span>' : ' <span class="warn small">differs from Brouwer: ' + E(sp.brouwer) + "</span>") + "</dd>");
      h.push("</dl></div>");
      if (r.restricted) h.push('<div class="sec warn"><p class="note">For this parameter set the Library shows Brouwer’s public status and comment and the computed spectrum only.</p></div>');
      // counts
      var hd = r.head;
      var hdtxt = hd.kind === "complete" ? "exactly " + E(hd.label) + " (complete classification)" : hd.kind === "lower" ? E(hd.label) + " (lower bound)" :
        hd.kind === "exists" ? "at least 1 (no count recorded)" : hd.kind === "none" ? "none (the graph does not exist)" : "unknown (existence open)";
      h.push('<div class="sec"><h3>Known graphs</h3><p><b>' + hdtxt + "</b></p>");
      if (r.counts.length) {
        h.push("<ul>");
        r.counts.forEach(function (c) {
          var b = c.bib_id && refs.map[c.bib_id];
          h.push("<li><b>" + (c.kind === "complete" ? "" : "≥ ") + SRG.fmt(c.n) + "</b> " + (c.kind === "complete" ? "(complete)" : "(lower bound)") + " — " + E(c.note) +
            (c.via ? ' <span class="muted small">(given for the complement ' + E(SRG.params(c.via)) + ")</span>" : "") +
            (b ? ' · <a href="references.html#' + E(b.id) + '">' + E(shortCite(b)) + "</a>" : "") +
            (c.url ? ' · <a href="' + E(c.url) + '">source</a>' : "") + "</li>");
        });
        h.push("</ul>");
        if (r.counts.length > 1) h.push('<p class="note">Counts from different sources are not added: their overlap is generally not known. The headline is the largest lower bound, or the complete count.</p>');
      }
      h.push("</div>");
      // constructions / comments
      h.push('<div class="sec"><h3>Constructions and Brouwer’s comments</h3>');
      if (r.families.length) {
        h.push('<div class="chips" style="margin-bottom:8px">' + r.families.map(function (f) {
          return '<a class="chip" href="families.html#' + E(f) + '">' + E(famMap[f] ? famMap[f].name : f) + "</a>";
        }).join("") + "</div>");
      }
      [r, other].forEach(function (x) {
        if (!x) return;
        h.push('<p class="small muted" style="margin:6px 0 3px">Comment on the line srg' + E(SRG.params(x.id)) + ":</p>");
        h.push('<div class="brc">' + (x.comment_html || '<span class="muted">(no comment)</span>') + "</div>");
      });
      h.push('<p class="note" style="margin-top:6px">Comments are Brouwer’s, reproduced from his table with links to the references; the family chips are the Library’s reading of them.</p></div>');
      // nonexistence
      if (r.status === "-" && r.reasons.length) {
        h.push('<div class="sec"><h3>Why it does not exist</h3><ul>');
        r.reasons.forEach(function (k) {
          var R = resMap[k]; if (!R) return;
          h.push("<li><b>" + E(R.name) + ".</b> " + E(R.desc) + (k === "paper" ? " See the references below." : "") + "</li>");
        });
        h.push("</ul></div>");
      }
      // ours
      if (r.ours && r.ours.length) {
        h.push('<div class="sec"><h3>Published results by A. Kovaľ</h3><ul>');
        r.ours.forEach(function (o) {
          h.push("<li>" + E(o.title) + ' — <a href="https://doi.org/' + E(o.doi) + '">doi:' + E(o.doi) + "</a>" +
            (o.page ? ' · <a href="' + E(o.page) + '">result page</a>' : "") + (o.n ? " · " + SRG.fmt(o.n) + " graph" + (o.n === 1 ? "" : "s") + " in the deposit" : "") +
            (o.kind === "rediscovery" ? '<br><span class="note">Per the correction on the deposit page: the three graphs were found earlier by D. Djematene (public repository, 13 Oct 2026); eight graphs are known.</span>' : "") + "</li>");
        });
        h.push('</ul><p class="note">Preprints with data on Zenodo; not yet peer-reviewed. Brouwer’s status above is the reference.</p></div>');
      }
      if (r.partial && r.partial.length) {
        h.push('<div class="sec"><h3>Partial results in the literature</h3><ul>');
        r.partial.forEach(function (p) {
          var b = p.bib && refs.map[p.bib];
          h.push("<li>" + E(p.text) + (b ? ' — <a href="references.html#' + E(b.id) + '">' + E(shortCite(b)) + "</a>" : "") + "</li>");
        });
        h.push("</ul></div>");
      }
      // sage / seed db
      h.push('<div class="sec"><h3>SageMath</h3>');
      if (r.sage) {
        h.push("<p>graphs.strongly_regular_graph(" + r.id.split("_").join(",") + ", existence=True) → <b>" + E(r.sage.existence) + "</b>" +
          (r.sage.existence === "True" ? " · constructor <code>" + E(r.sage.constructor) + "</code>" + (r.sage.test ? " (recognised by <code>" + E(r.sage.test) + "</code>)" : "") : "") + "</p>");
        h.push('<p class="note">SageMath 10.10, strongly_regular_db, run 2026-11-07. “Unknown” means Sage has no construction and no nonexistence proof; Brouwer’s status is the reference.</p>');
      } else h.push('<p class="note">Not shown.</p>');
      h.push('<p class="note">Seed-database constructions: ' + (r.seed ? E(r.seed.join("; ")) : "pending (to be imported from the seed-database build)") + "</p></div>");
      // downloads
      h.push('<div class="sec"><h3>Downloads and data</h3><ul>');
      (r.downloads || []).forEach(function (d) { h.push('<li><a href="' + E(d.url) + '">' + E(d.label) + "</a></li>"); });
      h.push('<li><a href="' + E(r.brouwer_page) + '">Brouwer’s table, ' + E(r.brouwer_page.split("/").pop()) + "</a></li>");
      h.push('<li><a href="https://houseofgraphs.org/">House of Graphs</a> (search by invariants)</li>');
      h.push('</ul><p class="note">Third-party files are linked, not copied; they remain under their authors’ terms.</p></div>');
      // literature + refs
      var bibs = r.bib.map(function (b) { return refs.map[b]; }).filter(Boolean);
      var litIds = {}; (r.literature || []).forEach(function (t) { litIds["t-" + t.slice(5)] = 1; });
      h.push('<div class="sec"><h3>References</h3>');
      if (bibs.length) bibs.sort(function (x, y) { return (x.year || 9999) - (y.year || 9999) || x.text.localeCompare(y.text); }).forEach(function (b) { h.push(SRG.bibHtml(b)); });
      else h.push('<p class="note">No reference attached; see Brouwer’s page.</p>');
      if (Object.keys(litIds).length) h.push('<p class="note">Includes further literature naming this parameter set.</p>');
      h.push("</div>");
      el.innerHTML = h.join("");
      return r;
    });
  };
  function shortCite(b) {
    var a = (b.authors || "").split(/,| & | and /)[0].trim().split(" ").pop();
    return (a || b.key || "ref") + (b.year ? " " + b.year : "");
  }
  SRG.shortCite = shortCite;

  document.addEventListener("DOMContentLoaded", function () {
    SRG.header();
    SRG.load("meta").then(function (m) {
      SRG.footer(m);
      var sl = document.querySelectorAll("[data-source-line]");
      for (var i = 0; i < sl.length; i++) sl[i].innerHTML = SRG.sourceLine(m);
    }).catch(function (e) {
      var sl = document.querySelectorAll("[data-source-line]");
      for (var i = 0; i < sl.length; i++) sl[i].textContent = "Data could not be loaded: " + e.message;
    });
  });
})();
