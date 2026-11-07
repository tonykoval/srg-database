/* library.html: headline tiles, status map, range bars, changes, table, row detail drawer. */
(function () {
  "use strict";
  var E = SRG.esc;
  var NS = "http://www.w3.org/2000/svg";
  var F; // field index
  var ROWS = [], PRIM = [], META, FAMS;
  var shown = { "+": true, "-": true, "?": true };

  Promise.all([SRG.load("index"), SRG.load("meta"), SRG.load("families")]).then(function (a) {
    var idx = a[0]; META = a[1]; FAMS = a[2];
    F = {}; idx.fields.forEach(function (f, i) { F[f] = i; });
    ROWS = idx.rows.map(function (r) {
      return { id: r[F.id], v: r[F.v], k: r[F.k], l: r[F.l], mu: r[F.mu], st: r[F.status], primary: !!r[F.primary], comp: r[F.comp],
        count: r[F.count], ck: r[F.count_kind], main: r[F.main], fam: r[F.families], r: r[F.r], s: r[F.s], conf: !!r[F.conference], ours: !!r[F.ours] };
    });
    PRIM = ROWS.filter(function (r) { return r.primary; });
    var changed = {}; (META.stats.changes || []).forEach(function (c) { changed[c.id] = c; });
    PRIM.forEach(function (r) { r.changed = !!changed[r.id]; });
    tiles(); legend(); famSelects(); drawMap(); bars(); changes(); initTable(); route();
    window.addEventListener("hashchange", route);
    var t; window.addEventListener("resize", function () { clearTimeout(t); t = setTimeout(drawMap, 120); });
  }).catch(function (e) {
    document.getElementById("tiles").textContent = "Could not load the data (" + e.message + ").";
  });

  // ---------------------------------------------------------------- tiles
  function tiles() {
    var s = META.stats, b = s.by_status;
    var hk = s.head_kind;
    var t = [
      ["Parameter pairs", SRG.fmt(s.pairs), SRG.fmt(s.sets) + " parameter sets with complements", ""],
      ["Exist", SRG.fmt(b["+"] || 0), "at least one graph known", "yes"],
      ["Do not exist", SRG.fmt(b["-"] || 0), "ruled out", "no"],
      ["Open", SRG.fmt(b["?"] || 0), "existence unknown", "open"],
      ["Classified completely", SRG.fmt(hk.complete || 0), "exact number of graphs known", ""],
      ["With a count", SRG.fmt((hk.complete || 0) + (hk.lower || 0)), "complete or a published lower bound > 1", ""]
    ];
    document.getElementById("tiles").innerHTML = t.map(function (x) {
      return '<div class="tile"><div class="lab">' + (x[3] ? '<span class="key ' + x[3] + '" aria-hidden="true"></span>' : "") + E(x[0]) +
        '</div><div class="val">' + x[1] + '</div><div class="sub">' + E(x[2]) + "</div></div>";
    }).join("");
  }

  // ---------------------------------------------------------------- map
  function legend() {
    var L = document.getElementById("mapLegend");
    var s = META.stats.by_status;
    L.innerHTML = [["+", "yes", "exists"], ["-", "no", "does not exist"], ["?", "open", "open"]].map(function (x) {
      return '<button type="button" aria-pressed="true" data-st="' + x[0] + '"><span class="key ' + x[1] + '"></span>' + x[2] + " (" + SRG.fmt(s[x[0]] || 0) + ")</button>";
    }).join("");
    L.addEventListener("click", function (ev) {
      var b = ev.target.closest("button"); if (!b) return;
      var st = b.getAttribute("data-st"); shown[st] = !shown[st];
      b.setAttribute("aria-pressed", shown[st] ? "true" : "false");
      drawMap();
    });
    ["yAxis", "famHi", "hiOther"].forEach(function (id) { document.getElementById(id).addEventListener("change", drawMap); });
  }
  function famSelects() {
    var opts = FAMS.filter(function (f) { return f.rows.length; }).map(function (f) {
      return '<option value="' + E(f.id) + '">' + E(f.name) + " (" + f.rows.length + ")</option>";
    }).join("");
    document.getElementById("famHi").insertAdjacentHTML("beforeend", opts);
    document.getElementById("fFam").insertAdjacentHTML("beforeend", opts);
  }
  var pts = [], geom = null;
  function yval(r, mode) { return mode === "k" ? r.k : mode === "mu" ? r.mu : -r.s; }
  function drawMap() {
    var svg = document.getElementById("map");
    var box = document.getElementById("mapbox");
    var W = 1000, H = 520, ml = 50, mr = 14, mt = 12, mb = 38;
    var pxw = box.clientWidth || 1000;
    var unit = W / pxw;                       // viewBox units per CSS pixel
    ml = Math.max(ml, 40 * unit); mb = Math.max(mb, 34 * unit); mt = Math.max(mt, 8 * unit);
    var narrow = pxw < 560;
    H = narrow ? 760 : 520;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    var mode = document.getElementById("yAxis").value;
    var fam = document.getElementById("famHi").value;
    var oth = document.getElementById("hiOther").value;
    var ymax = 0; PRIM.forEach(function (r) { ymax = Math.max(ymax, yval(r, mode)); });
    var ystep = niceStep(ymax / 8); ymax = Math.ceil(ymax / ystep) * ystep;
    var X = function (v) { return ml + (v / 1300) * (W - ml - mr); };
    var Y = function (y) { return H - mb - (y / ymax) * (H - mt - mb); };
    var g = [];
    for (var y = 0; y <= ymax + 1e-9; y += ystep) {
      g.push('<line class="gridline" x1="' + ml + '" x2="' + (W - mr) + '" y1="' + Y(y) + '" y2="' + Y(y) + '"/>');
      g.push('<text x="' + (ml - 6) + '" y="' + (Y(y) + 4 * unit) + '" text-anchor="end" style="font-size:' + (11 * unit) + 'px">' + y + "</text>");
    }
    var xs = narrow ? 300 : 100;
    for (var v = 0; v <= 1300; v += xs) {
      g.push('<text x="' + X(v) + '" y="' + (H - mb + 16 * unit) + '" text-anchor="middle" style="font-size:' + (11 * unit) + 'px">' + v + "</text>");
    }
    g.push('<line class="axisline" x1="' + ml + '" x2="' + (W - mr) + '" y1="' + Y(0) + '" y2="' + Y(0) + '"/>');
    g.push('<text x="' + (W - mr) + '" y="' + (H - 4 * unit) + '" text-anchor="end" style="font-size:' + (11.5 * unit) + 'px">number of vertices v</text>');
    var ylab = mode === "k" ? "valency k" : mode === "mu" ? "μ" : "−s (smallest eigenvalue)";
    g.push('<text x="' + ml + '" y="' + (mt + 2 * unit) + '" text-anchor="start" dx="4" dy="' + (10 * unit) + '" style="font-size:' + (11.5 * unit) + 'px">' + E(ylab) + "</text>");
    var famSet = null;
    if (fam) { famSet = {}; (FAMS.filter(function (f) { return f.id === fam; })[0] || { rows: [] }).rows.forEach(function (x) { famSet[x] = 1; }); }
    var hiTest = null;
    if (oth === "complete") hiTest = function (r) { return r.ck === "complete"; };
    else if (oth === "counted") hiTest = function (r) { return r.ck === "complete" || r.ck === "lower"; };
    else if (oth === "conference") hiTest = function (r) { return r.conf; };
    else if (oth === "ours") hiTest = function (r) { return r.ours; };
    else if (oth === "changed") hiTest = function (r) { return r.changed; };
    var rad = Math.max(2.2, 3.6 * unit * (narrow ? 0.85 : 1));
    var sw = 1.1 * unit;
    var order = ["?", "+", "-"];
    pts = [];
    var marks = [];
    order.forEach(function (st) {
      if (!shown[st]) return;
      PRIM.forEach(function (r) {
        if (r.st !== st) return;
        var cx = X(r.v), cy = Y(yval(r, mode));
        var on = (!famSet || famSet[r.id]) && (!hiTest || hiTest(r));
        var cls = (st === "+" ? "pt-yes" : st === "-" ? "pt-no" : "pt-open") + (on ? "" : " dim");
        if (st === "+") marks.push('<circle class="' + cls + '" cx="' + cx.toFixed(1) + '" cy="' + cy.toFixed(1) + '" r="' + rad.toFixed(2) + '" stroke-width="' + (0.6 * unit).toFixed(2) + '"/>');
        else if (st === "-") { var q = rad * 0.86; marks.push('<rect class="' + cls + '" x="' + (cx - q).toFixed(1) + '" y="' + (cy - q).toFixed(1) + '" width="' + (2 * q).toFixed(1) + '" height="' + (2 * q).toFixed(1) + '" rx="' + (0.6 * unit).toFixed(1) + '" stroke-width="' + (0.6 * unit).toFixed(2) + '"/>'); }
        else marks.push('<circle class="' + cls + '" cx="' + cx.toFixed(1) + '" cy="' + cy.toFixed(1) + '" r="' + (rad * 0.92).toFixed(2) + '" stroke-width="' + (1.5 * unit).toFixed(2) + '"/>');
        pts.push({ r: r, x: cx, y: cy, on: on });
      });
    });
    svg.innerHTML = svg.querySelector("title").outerHTML + svg.querySelector("desc").outerHTML + '<g class="axis">' + g.join("") + "</g><g>" + marks.join("") + '</g><circle id="hiRing" class="pt-hi" r="0" cx="-10" cy="-10"/>';
    geom = { W: W, H: H, unit: unit, rad: rad };
  }
  function niceStep(x) {
    var p = Math.pow(10, Math.floor(Math.log10(Math.max(x, 1e-9)))), m = x / p;
    return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 5 ? 5 : 10) * p;
  }
  (function hover() {
    var box = document.getElementById("mapbox"), tip = document.getElementById("tip");
    function nearest(ev) {
      var svg = document.getElementById("map");
      var rc = svg.getBoundingClientRect();
      if (!geom || !rc.width) return null;
      var sx = (ev.clientX - rc.left) * (geom.W / rc.width), sy = (ev.clientY - rc.top) * (geom.H / rc.height);
      var best = null, bd = Infinity, lim = 24 * geom.unit;
      for (var i = 0; i < pts.length; i++) {
        var p = pts[i]; var d = (p.x - sx) * (p.x - sx) + (p.y - sy) * (p.y - sy);
        if (d < bd && (p.on || bd === Infinity)) { bd = d; best = p; }
      }
      return best && bd <= lim * lim ? { p: best, rc: rc } : null;
    }
    function show(ev) {
      var n = nearest(ev); var ring = document.getElementById("hiRing");
      if (!n) { tip.style.display = "none"; if (ring) ring.setAttribute("r", 0); box.style.cursor = ""; return null; }
      var r = n.p.r, S = SRG.STATUS[r.st];
      ring.setAttribute("cx", n.p.x); ring.setAttribute("cy", n.p.y); ring.setAttribute("r", geom.rad + 3 * geom.unit);
      ring.setAttribute("stroke-width", 1.6 * geom.unit);
      tip.innerHTML = '<b class="mono">srg' + E(SRG.params(r.id)) + "</b><br>" +
        '<span class="key ' + S.cls + '" style="margin-right:6px"></span>' + E(S.name) +
        " · known graphs: <b>" + E(r.count) + "</b>" + (r.ck === "complete" ? " (complete)" : "") +
        (r.main ? '<br><span class="tl">' + E(r.main) + "</span>" : "") + '<br><span class="tl small">click to open · Brouwer’s page linked inside</span>';
      tip.style.display = "block";
      var bx = box.getBoundingClientRect();
      var x = ev.clientX - bx.left + 14, y = ev.clientY - bx.top + 14;
      if (x + tip.offsetWidth > bx.width) x = Math.max(4, ev.clientX - bx.left - tip.offsetWidth - 14);
      if (y + tip.offsetHeight > bx.height) y = Math.max(4, ev.clientY - bx.top - tip.offsetHeight - 14);
      tip.style.left = x + "px"; tip.style.top = y + "px";
      box.style.cursor = "pointer";
      return r;
    }
    box.addEventListener("pointermove", show);
    box.addEventListener("pointerleave", function () { tip.style.display = "none"; var ring = document.getElementById("hiRing"); if (ring) ring.setAttribute("r", 0); });
    box.addEventListener("click", function (ev) {
      var r = show(ev);
      if (r) location.hash = "row=" + r.id.split("_").join("-");
    });
  })();

  // ---------------------------------------------------------------- range bars
  function bars() {
    var el = document.getElementById("rbars");
    el.innerHTML = META.stats.ranges.map(function (g) {
      var tot = g.plus + g.minus + g.open || 1;
      var seg = function (n, cls, name) {
        return n ? '<div class="seg ' + cls + '" style="flex:' + n + ' 1 0" title="' + name + ": " + n + " of " + tot + '" aria-label="' + name + " " + n + '"></div>' : "";
      };
      return '<div class="rbar"><div class="lab">' + g.lo + "–" + g.hi + '</div><div class="track" role="img" aria-label="v ' + g.lo + "–" + g.hi + ": " + g.plus + " exist, " + g.minus + " do not exist, " + g.open + ' open">' +
        seg(g.plus, "yes", "exists") + seg(g.minus, "no", "does not exist") + seg(g.open, "open", "open") + "</div>" +
        '<div class="nums">' + g.plus + " exist · " + g.minus + " do not · " + g.open + " open · " + tot + " pairs</div></div>";
    }).join("");
  }

  // ---------------------------------------------------------------- changes
  function changes() {
    var c = META.stats.changes || [];
    var el = document.getElementById("changes");
    if (!c.length) { el.innerHTML = '<p class="note">No status changes between the two snapshots.</p>'; return; }
    el.innerHTML = '<p class="small">' + c.length + " parameter pairs changed status between Brouwer’s table of " + E((META.brouwer_old_fetch || "").slice(0, 10)) +
      " and " + E((META.brouwer_fetch || "").slice(0, 10)) + ':</p><div class="tablebox"><table><thead><tr><th>parameters</th><th>before</th><th>now</th></tr></thead><tbody>' +
      c.map(function (x) {
        return '<tr><td><a class="rowlink" href="' + SRG.rowHref(x.id) + '">' + E(SRG.params(x.id)) + "</a></td><td>" + SRG.statusHtml(x.old) + "</td><td>" + SRG.statusHtml(x.new) + "</td></tr>";
      }).join("") + "</tbody></table></div>";
  }

  // ---------------------------------------------------------------- table
  var page = 0, PER = 100, filtered = [];
  function initTable() {
    ["q", "fStatus", "vmin", "vmax", "fFam", "fComp", "fCount"].forEach(function (id) {
      var el = document.getElementById(id);
      el.addEventListener(el.type === "search" || el.type === "number" ? "input" : "change", function () { page = 0; filter(); });
    });
    document.getElementById("prev").addEventListener("click", function () { if (page > 0) { page--; render(); } });
    document.getElementById("next").addEventListener("click", function () { if ((page + 1) * PER < filtered.length) { page++; render(); } });
    filter();
  }
  function filter() {
    var q = document.getElementById("q").value.trim().toLowerCase();
    var st = document.getElementById("fStatus").value;
    var vmin = +document.getElementById("vmin").value || 1, vmax = +document.getElementById("vmax").value || 1300;
    var fam = document.getElementById("fFam").value;
    var comp = document.getElementById("fComp").checked, cnt = document.getElementById("fCount").checked;
    var nums = q.match(/^[\d\s,()_\-]+$/) ? q.replace(/[()]/g, "").split(/[\s,_\-]+/).filter(Boolean).map(Number) : null;
    filtered = ROWS.filter(function (r) {
      if (!comp && !r.primary) return false;
      if (st && r.st !== st) return false;
      if (r.v < vmin || r.v > vmax) return false;
      if (fam && r.fam.indexOf(fam) < 0) return false;
      if (cnt && !(r.ck === "complete" || r.ck === "lower")) return false;
      if (q) {
        if (nums) {
          var p = [r.v, r.k, r.l, r.mu];
          for (var i = 0; i < nums.length; i++) if (p[i] !== nums[i]) return false;
        } else if ((r.main || "").toLowerCase().indexOf(q) < 0) return false;
      }
      return true;
    });
    render();
  }
  function render() {
    var tb = document.getElementById("tbody");
    var slice = filtered.slice(page * PER, page * PER + PER);
    tb.innerHTML = slice.map(function (r) {
      var sp = r.s === Math.round(r.s) ? "" : "";
      return '<tr class="' + (r.primary ? "" : "comp") + '"><td><a class="rowlink" href="' + SRG.rowHref(r.id) + '">' + E(SRG.params(r.id)) + "</a></td>" +
        "<td>" + SRG.statusHtml(r.st) + '</td><td class="num">' + E(r.count) + (r.ck === "complete" ? ' <span class="muted small">exact</span>' : "") + "</td>" +
        '<td class="mono">' + fmtEig(r.r) + ", " + fmtEig(r.s) + "</td>" +
        '<td class="cmt">' + E(r.main) + "</td></tr>";
    }).join("") || '<tr><td colspan="5" class="muted">No rows match.</td></tr>';
    var n = filtered.length;
    document.getElementById("pinfo").textContent = n ? (page * PER + 1) + "–" + Math.min(n, page * PER + PER) + " of " + SRG.fmt(n) + " rows" : "0 rows";
    document.getElementById("prev").disabled = page === 0;
    document.getElementById("next").disabled = (page + 1) * PER >= n;
  }
  function fmtEig(x) { return Math.abs(x - Math.round(x)) < 1e-9 ? String(Math.round(x)).replace("-", "−") : x.toFixed(3).replace("-", "−"); }

  // ---------------------------------------------------------------- detail drawer
  var lastFocus = null;
  function route() {
    var m = location.hash.match(/^#row=(\d+)-(\d+)-(\d+)-(\d+)$/);
    var d = document.getElementById("drawer"), bg = document.getElementById("dbg");
    if (!m) { d.classList.remove("open"); bg.classList.remove("open"); if (lastFocus) lastFocus.focus(); return; }
    var id = [m[1], m[2], m[3], m[4]].join("_");
    lastFocus = document.activeElement;
    document.getElementById("dtitle").textContent = "srg" + SRG.params(id);
    document.getElementById("dbody").innerHTML = '<p class="muted">Loading…</p>';
    d.classList.add("open"); bg.classList.add("open");
    d.scrollTop = 0;
    SRG.detail(id, document.getElementById("dbody")).then(function (r) {
      var a = document.getElementById("dbrouwer");
      if (r) { a.href = r.brouwer_page; a.style.display = ""; a.textContent = "Brouwer’s page"; } else a.style.display = "none";
      document.title = "srg" + SRG.params(id) + " — SRG Library";
      document.getElementById("dclose").focus();
    });
  }
  function close() { history.pushState("", document.title, location.pathname + location.search); document.title = "SRG Library"; route(); }
  document.getElementById("dclose").addEventListener("click", close);
  document.getElementById("dbg").addEventListener("click", close);
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && document.getElementById("drawer").classList.contains("open")) close(); });
})();
