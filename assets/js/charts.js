/* charts.js — Controlador de la página de tema + fábrica de gráficos ECharts.
   La agregación (filtrar/agrupar/sumar/promediar) ocurre acá, en el navegador,
   para que los filtros sean interactivos. Soporta:
     · KPIs por VARIACIÓN INTERANUAL (no valor absoluto),
     · métricas no sumables (agg:"mean"),
     · vista de GRILLA por departamento (pequeños múltiplos) + selector de depto. */
(function () {
  "use strict";

  // Paleta categórica validada (dataviz skill), por modo.
  var PAL_LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"];
  var PAL_DARK  = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"];

  var nfFull = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 0 });
  var nfCompact = new Intl.NumberFormat("es-AR", { notation: "compact", maximumFractionDigits: 1 });
  var nfPct = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 1 });
  var ALL = "__ALL__";

  function isDark() {
    var t = document.documentElement.getAttribute("data-theme");
    if (t) return t === "dark";
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  function palette() { return isDark() ? PAL_DARK : PAL_LIGHT; }
  function cssvar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
  function chrome() {
    return { ink: cssvar("--ink"), ink2: cssvar("--ink-2"), grid: cssvar("--grid"),
             muted: cssvar("--muted"), accent: cssvar("--accent") };
  }

  // -------------------------------------------------------- Agregación
  function makeIndex(fields) { var m = {}; fields.forEach(function (f, i) { m[f] = i; }); return m; }

  function aggregate(rows, ix, opts) {
    // opts: {metrica, fixed:{dim:val}, x, seriesBy, exclude:[], seriesExclude:[], agg:'sum'|'mean'}
    var vi = ix.valor, mi = ix.metrica, xi = ix[opts.x];
    var si = opts.seriesBy ? ix[opts.seriesBy] : null;
    var agg = opts.agg || "sum";
    var fixedPairs = [];
    Object.keys(opts.fixed || {}).forEach(function (d) {
      if (ix[d] !== undefined && opts.fixed[d] !== null && opts.fixed[d] !== ALL)
        fixedPairs.push([ix[d], opts.fixed[d]]);
    });
    var exclude = {}; (opts.exclude || []).forEach(function (v) { exclude[v] = 1; });
    var sExcl = {}; (opts.seriesExclude || []).forEach(function (v) { sExcl[v] = 1; });

    var acc = {}, cnt = {};   // x -> serie -> suma / conteo
    var xset = {}, sset = {};
    for (var r = 0; r < rows.length; r++) {
      var row = rows[r];
      if (row[mi] !== opts.metrica) continue;
      var ok = true;
      for (var k = 0; k < fixedPairs.length; k++) {
        if (String(row[fixedPairs[k][0]]) !== String(fixedPairs[k][1])) { ok = false; break; }
      }
      if (!ok) continue;
      var xv = row[xi];
      if (exclude[xv]) continue;
      var sv = si === null ? "_" : row[si];
      if (sExcl[sv]) continue;
      if (!acc[xv]) { acc[xv] = {}; cnt[xv] = {}; }
      acc[xv][sv] = (acc[xv][sv] || 0) + (+row[vi] || 0);
      cnt[xv][sv] = (cnt[xv][sv] || 0) + 1;
      xset[xv] = 1; sset[sv] = 1;
    }
    if (agg === "mean") {
      Object.keys(acc).forEach(function (x) {
        Object.keys(acc[x]).forEach(function (s) { acc[x][s] = acc[x][s] / cnt[x][s]; });
      });
    }
    return { acc: acc, xs: Object.keys(xset), series: Object.keys(sset) };
  }

  function sortX(xs, x) {
    if (x === "anio") return xs.map(Number).sort(function (a, b) { return a - b; });
    return xs.slice().sort();
  }
  function round2(v) { return Math.round(v * 100) / 100; }

  // Ejes X temporales: un cero al final de la serie suele indicar dato faltante
  // (período aún no cargado), no una caída real. Se recorta la COLA de ceros.
  var TIME_X = { anio: 1, trimestre: 1, mes: 1, periodo: 1, fecha: 1 };
  function trimTrailingZero(xs, acc) {
    var out = xs.slice();
    while (out.length) {
      var x = out[out.length - 1], tot = 0, a = acc[x] || {};
      Object.keys(a).forEach(function (s) { tot += a[s] || 0; });
      if (tot === 0) out.pop(); else break;   // solo desde el final
    }
    return out;
  }
  function niceMax(v) {
    if (!(v > 0)) return 1;
    var mag = Math.pow(10, Math.floor(Math.log10(v)));
    var steps = [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10];
    for (var i = 0; i < steps.length; i++) { if (steps[i] * mag >= v) return steps[i] * mag; }
    return 10 * mag;
  }

  // Resuelve métrica + filtros efectivos + eje X (+ modo %) a partir del estado de controles.
  function resolveState(ch, state) {
    var metric = state.metric || ch.metrica;
    var fixed = Object.assign({}, ch.fixed || {});
    var x = ch.x;
    var percent = false, unidad = ch.unidad;
    (ch.controls || []).forEach(function (ctl) {
      if (ctl.kind === "select") {
        var v = state[ctl.dim];
        if (v === ALL) { if (ctl.allValue != null) fixed[ctl.dim] = ctl.allValue; }
        else if (v != null) fixed[ctl.dim] = v;
      } else if (ctl.kind === "year" && state[ctl.dim] != null) {
        fixed[ctl.dim] = state[ctl.dim];
      } else if (ctl.kind === "freq") {
        var o = (ctl.options || []).filter(function (op) { return op.value === state.freq; })[0] || ctl.options[0];
        if (o) { x = o.x; if (o.grano != null) fixed.grano = o.grano; }
      } else if (ctl.kind === "mode") {
        var m = (ctl.options || []).filter(function (op) { return op.value === state.mode; })[0] || ctl.options[0];
        if (m) { if (m.metric) metric = m.metric; percent = !!m.percent; if (m.unidad) unidad = m.unidad; }
      }
    });
    return { metric: metric, fixed: fixed, x: x, percent: percent, unidad: unidad };
  }

  // -------------------------------------------------------- Opciones ECharts
  function baseOption(ch, forGrid) {
    var c = chrome();
    return {
      color: palette(),
      textStyle: { fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif", color: c.ink2 },
      grid: { left: 6, right: forGrid ? 8 : 18, top: forGrid ? 10 : 16, bottom: 8, containLabel: true },
      tooltip: {
        trigger: (ch.type === "barh") ? "item" : "axis",
        valueFormatter: function (v) { return nfFull.format(v || 0); },
        backgroundColor: cssvar("--surface"), borderColor: cssvar("--border"),
        textStyle: { color: c.ink }
      },
      legend: { show: false }
    };
  }
  function axisStyle() {
    var c = chrome();
    return {
      axisLine: { lineStyle: { color: c.grid } },
      axisTick: { show: false },
      axisLabel: { color: c.muted, hideOverlap: true },
      splitLine: { lineStyle: { color: c.grid, type: "solid" } }
    };
  }

  // Devuelve el máximo (apilado o por punto) para compartir eje entre facetas.
  function aggMax(ch, data, ix, fixed, metric, seriesBy) {
    var agg = (data.metricas[metric] || {}).agg || "sum";
    var res = aggregate(data.rows, ix, { metrica: metric, fixed: fixed, x: ch.x,
      seriesBy: seriesBy, exclude: ch.exclude, seriesExclude: ch.seriesExclude, agg: agg });
    var mx = 0;
    res.xs.forEach(function (x) {
      if (ch.stack) {
        var s = 0; Object.keys(res.acc[x]).forEach(function (k) { s += res.acc[x][k] || 0; });
        if (s > mx) mx = s;
      } else {
        Object.keys(res.acc[x]).forEach(function (k) { if (res.acc[x][k] > mx) mx = res.acc[x][k]; });
      }
    });
    return mx;
  }

  // Construye la opción ECharts para un gráfico dado (fixed/metric ya resueltos).
  // opts: {forGrid, yMax, seriesBy}  (seriesBy override para grilla)
  function optionFor(ch, data, ix, fixed, metric, opts) {
    opts = opts || {};
    var seriesBy = opts.seriesBy !== undefined ? opts.seriesBy : ch.seriesBy;
    var agg = (data.metricas[metric] || {}).agg || "sum";
    var res = aggregate(data.rows, ix, {
      metrica: metric, fixed: fixed, x: ch.x, seriesBy: seriesBy,
      exclude: ch.exclude, seriesExclude: ch.seriesExclude, agg: agg
    });
    var opt = baseOption(ch, opts.forGrid), ax = axisStyle();
    var c = chrome();

    if (ch.type === "barh") {
      var pairs = res.xs.map(function (x) { return [x, res.acc[x]._ || 0]; });
      pairs = pairs.filter(function (p) { return p[1] > 0; });
      pairs.sort(function (a, b) { return (ch.sort === "asc") ? a[1] - b[1] : b[1] - a[1]; });
      // Rankings de universo grande (146 paises de destino) se recortan a los primeros N: el alto
      // del grafico crece linealmente con las categorias y sin tope se vuelve impracticable.
      if (ch.topN && pairs.length > ch.topN) pairs = pairs.slice(0, ch.topN);
      var cats = pairs.map(function (p) { return p[0]; });
      var vals = pairs.map(function (p) { return p[1]; });
      opt.grid.right = 60;
      opt.xAxis = Object.assign({ type: "value", axisLabel: { color: c.muted, formatter: function (v) { return nfCompact.format(v); } } }, { splitLine: ax.splitLine, axisLine: { show: false }, axisTick: { show: false } });
      opt.yAxis = Object.assign({ type: "category", data: cats, inverse: true }, { axisLine: { lineStyle: { color: c.grid } }, axisTick: { show: false }, axisLabel: { color: c.ink2 } });
      opt.series = [{
        type: "bar", data: vals, itemStyle: { color: palette()[0], borderRadius: [0, 4, 4, 0] },
        barMaxWidth: 26,
        label: { show: true, position: "right", color: c.ink2, formatter: function (p) { return nfCompact.format(p.value); } }
      }];
      return { option: opt, table: tableFromBarh(cats, vals, ch), height: Math.max(320, cats.length * 30 + 60) };
    }

    // line / stacked-area / bar / stacked-bar
    var xs = sortX(res.xs, ch.x).map(String);
    if (TIME_X[ch.x] && ch.type !== "barh") xs = trimTrailingZero(xs, res.acc);
    var seriesKeys = res.series.slice().sort();
    var isArea = ch.type === "stacked-area";
    var isBar = ch.type === "bar" || ch.type === "stacked-bar";
    var stack = ch.stack ? "total" : undefined;
    var single = seriesBy == null || (seriesKeys.length === 1 && seriesKeys[0] === "_");

    // Modo "% del total": normalizar cada x para que las series sumen 100.
    var pctMode = !!opts.percent;
    var colTot = {};
    if (pctMode) {
      xs.forEach(function (x) {
        var s = 0; seriesKeys.forEach(function (sk) { s += (res.acc[x] || {})[sk] || 0; });
        colTot[x] = s;
      });
    }

    var series = seriesKeys.map(function (sk) {
      var arr = xs.map(function (x) {
        var v = (res.acc[x] || {})[sk] || 0;
        if (pctMode) { var t = colTot[x] || 0; v = t ? v / t * 100 : 0; }
        return round2(v);
      });
      var name = (sk === "_") ? (data.metricas[metric] ? data.metricas[metric].label : metric) : sk;
      var s = { name: name, data: arr };
      if (isBar) { s.type = "bar"; s.stack = stack; s.barMaxWidth = 34; s.itemStyle = { borderRadius: stack ? 0 : [4, 4, 0, 0] }; }
      else {
        s.type = "line"; s.stack = stack; s.smooth = false;
        s.symbol = "circle"; s.symbolSize = opts.forGrid ? 0 : 6;
        s.lineStyle = { width: isArea ? 1 : 2 }; s.showSymbol = !opts.forGrid && xs.length <= 24;
        if (isArea) s.areaStyle = { opacity: 0.85 };
      }
      return s;
    });

    var yAxis = {
      type: "value",
      axisLabel: { color: c.muted, formatter: function (v) { return pctMode ? nfCompact.format(v) + " %" : nfCompact.format(v); } },
      splitLine: ax.splitLine, axisLine: { show: false }, axisTick: { show: false }
    };
    // Eje Y: líneas no apiladas -> auto-ajuste con margen (scale); apiladas/barras -> base 0.
    var lineAdaptive = (ch.type === "line" && !ch.stack && !pctMode);
    if (pctMode) { yAxis.min = 0; yAxis.max = 100; }
    else if (lineAdaptive) { yAxis.scale = true; }
    else if (opts.yMax != null) { yAxis.max = opts.yMax; }
    opt.xAxis = Object.assign({ type: "category", boundaryGap: isBar, data: xs }, ax);
    if (opts.forGrid) { opt.xAxis.axisLabel = Object.assign({}, opt.xAxis.axisLabel, { fontSize: 9, interval: "auto" }); yAxis.axisLabel.fontSize = 9; }
    opt.yAxis = yAxis;
    if (!opts.forGrid && !single) {
      opt.legend = { show: true, bottom: 0, textStyle: { color: c.ink2 }, itemWidth: 14, itemHeight: 10, icon: "roundRect" };
      opt.grid.bottom = 28;
    }
    opt.series = series;
    return { option: opt, table: tableFromSeries(xs, seriesKeys, series, ch), height: 380,
             seriesKeys: seriesKeys, seriesNames: series.map(function (s) { return s.name; }) };
  }

  // -------------------------------------------------------- Tablas (vista datos)
  var DIM_LABEL = {
    departamento: "Departamento", municipio: "Municipio", localidad: "Localidad",
    unidad_geografica: "Unidad geográfica", sector: "Sector", rubro: "Rubro",
    pais_destino: "País de destino", continente: "Continente", gran_rubro: "Tipo de producto",
    central: "Central", partida: "Partida", impuesto: "Impuesto", cultivo: "Cultivo",
    concepto: "Concepto", categoria: "Categoría", nivel: "Nivel", funcion: "Función"
  };
  function dimLabel(d) { return DIM_LABEL[d] || cap(String(d).replace(/_/g, " ")); }
  function tableFromBarh(cats, vals, ch) {
    var h = "<table><thead><tr><th>" + esc(dimLabel(ch.x)) + "</th><th>Valor</th></tr></thead><tbody>";
    cats.forEach(function (c, i) { h += "<tr><td>" + esc(c) + "</td><td>" + nfFull.format(vals[i]) + "</td></tr>"; });
    return h + "</tbody></table>";
  }
  function tableFromSeries(xs, keys, series, ch) {
    var head = "<table><thead><tr><th>" + xLabel(ch.x) + "</th>";
    series.forEach(function (s) { head += "<th>" + esc(s.name) + "</th>"; });
    head += "</tr></thead><tbody>";
    xs.forEach(function (x, r) {
      head += "<tr><td>" + esc(x) + "</td>";
      series.forEach(function (s) { head += "<td>" + nfFull.format(s.data[r]) + "</td>"; });
      head += "</tr>";
    });
    return head + "</tbody></table>";
  }
  function xLabel(x) { return x === "anio" ? "Año" : (x === "periodo" ? "Período" : (x === "trimestre" ? "Trimestre" : dimLabel(x))); }
  function esc(s) { return String(s).replace(/[&<>]/g, function (m) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[m]; }); }

  // -------------------------------------------------------- Controles
  function opt(v, t) { var o = document.createElement("option"); o.value = v; o.textContent = t; return o; }
  function cap(s) { return String(s).charAt(0).toUpperCase() + String(s).slice(1); }

  function renderControls(container, ch, data, state, onChange) {
    container.innerHTML = "";
    (ch.controls || []).forEach(function (ctl) {
      var wrap = document.createElement("div");
      wrap.className = "control";
      var id = ch.id + "-" + (ctl.dim || ctl.kind);

      if (ctl.kind === "select") {
        var lab = document.createElement("label"); lab.textContent = ctl.label; lab.setAttribute("for", id);
        var sel = document.createElement("select"); sel.id = id;
        if (ctl.all) sel.appendChild(opt(ALL, ctl.allLabel || "Todos"));
        (ctl.values || []).forEach(function (v) { sel.appendChild(opt(v, cap(v))); });
        sel.value = state[ctl.dim];
        sel.addEventListener("change", function () { state[ctl.dim] = sel.value; onChange(); });
        wrap.appendChild(lab); wrap.appendChild(sel);

      } else if (ctl.kind === "year") {
        var lab2 = document.createElement("label"); lab2.textContent = ctl.label; lab2.setAttribute("for", id);
        var sel2 = document.createElement("select"); sel2.id = id;
        (ctl.values || []).slice().sort(function (a, b) { return b - a; }).forEach(function (v) { sel2.appendChild(opt(v, v)); });
        sel2.value = state[ctl.dim];
        sel2.addEventListener("change", function () { state[ctl.dim] = +sel2.value; onChange(); });
        wrap.appendChild(lab2); wrap.appendChild(sel2);

      } else if (ctl.kind === "metric") {
        var lab3 = document.createElement("label"); lab3.textContent = ctl.label;
        var seg = document.createElement("div"); seg.className = "seg"; seg.setAttribute("role", "group");
        ctl.options.forEach(function (m) {
          var b = document.createElement("button");
          b.type = "button"; b.textContent = ctl.labels[m];
          b.setAttribute("aria-pressed", String(state.metric === m));
          b.addEventListener("click", function () {
            state.metric = m;
            seg.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
            b.setAttribute("aria-pressed", "true");
            onChange();
          });
          seg.appendChild(b);
        });
        wrap.appendChild(lab3); wrap.appendChild(seg);

      } else if (ctl.kind === "freq") {
        var lab4 = document.createElement("label"); lab4.textContent = ctl.label || "Frecuencia";
        var seg4 = document.createElement("div"); seg4.className = "seg"; seg4.setAttribute("role", "group");
        (ctl.options || []).forEach(function (o) {
          var b = document.createElement("button");
          b.type = "button"; b.textContent = o.label;
          b.setAttribute("aria-pressed", String(state.freq === o.value));
          b.addEventListener("click", function () {
            state.freq = o.value;
            seg4.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
            b.setAttribute("aria-pressed", "true");
            onChange();
          });
          seg4.appendChild(b);
        });
        wrap.appendChild(lab4); wrap.appendChild(seg4);

      } else if (ctl.kind === "mode") {
        var lab5 = document.createElement("label"); lab5.textContent = ctl.label || "Valores";
        var seg5 = document.createElement("div"); seg5.className = "seg"; seg5.setAttribute("role", "group");
        (ctl.options || []).forEach(function (o) {
          var b = document.createElement("button");
          b.type = "button"; b.textContent = o.label;
          b.setAttribute("aria-pressed", String(state.mode === o.value));
          b.addEventListener("click", function () {
            state.mode = o.value;
            seg5.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
            b.setAttribute("aria-pressed", "true");
            onChange();
          });
          seg5.appendChild(b);
        });
        wrap.appendChild(lab5); wrap.appendChild(seg5);
      }
      container.appendChild(wrap);
    });
  }

  // Toggle Total | Grilla por departamento (solo line/stacked-area con geoDim).
  function appendViewToggle(container, ch, state, onChange) {
    var wrap = document.createElement("div"); wrap.className = "control";
    var lab = document.createElement("label"); lab.textContent = "Vista";
    var seg = document.createElement("div"); seg.className = "seg"; seg.setAttribute("role", "group");
    [["total", "Total"], ["grid", "Grilla por departamento"]].forEach(function (o) {
      var b = document.createElement("button"); b.type = "button"; b.textContent = o[1];
      b.setAttribute("aria-pressed", String(state.view === o[0]));
      b.addEventListener("click", function () {
        state.view = o[0];
        seg.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", "true");
        onChange();
      });
      seg.appendChild(b);
    });
    wrap.appendChild(lab); wrap.appendChild(seg);
    container.appendChild(wrap);
  }

  // -------------------------------------------------------- KPIs (variación interanual del último dato)
  // Mapa período->total para la métrica del KPI a la granularidad pedida; xs recorta ceros finales.
  function kpiSeriesMap(data, ix, k, xDim, granoVal, agg) {
    var fx = Object.assign({}, k.fixed);
    if (granoVal != null && ix.grano !== undefined) fx.grano = granoVal;
    var res = aggregate(data.rows, ix, {
      metrica: k.metrica, fixed: fx, x: xDim, seriesBy: null, agg: agg
    });
    var xs = sortX(res.xs, xDim).map(String);
    var map = {};
    xs.forEach(function (x) { map[x] = (res.acc[x] || {})._ || 0; });
    return { xs: trimTrailingZero(xs, res.acc), map: map };
  }

  // Mismo período del año anterior (texto): "2026"->"2025", "2026-T1"->"2025-T1", "2026-11"->"2025-11".
  function kpiPrevPeriod(p) {
    var m = String(p).match(/^(\d{4})(.*)$/);
    return m ? (String(parseInt(m[1], 10) - 1) + m[2]) : null;
  }

  // Granos disponibles para una métrica (o null si el tema no usa el campo grano).
  function kpiGranos(data, ix, metrica) {
    if (ix.grano === undefined) return null;
    var mi = ix.metrica, gi = ix.grano, s = {};
    data.rows.forEach(function (r) { if (r[mi] === metrica) s[r[gi]] = 1; });
    return s;
  }

  // freq: {value, map:{value->{x,grano}}} del gráfico conductor, o null (=> anual).
  function renderKpis(mount, data, ix, freq) {
    mount.innerHTML = "";
    var freqOpt = (freq && freq.map) ? freq.map[freq.value] : null;
    data.kpis.forEach(function (k) {
      var agg = k.agg || (data.metricas[k.metrica] || {}).agg || "sum";
      var granos = kpiGranos(data, ix, k.metrica);
      var annualGrano = function () {
        if (granos === null) return null;
        if (granos["anual"]) return "anual";
        var ks = Object.keys(granos); return ks.length ? ks[0] : null;
      };
      // Granularidad: la del control de frecuencia si la métrica la tiene; si no, anual.
      var xDim = "anio", granoVal = annualGrano();
      if (freqOpt && (granos === null || granos[freqOpt.grano])) {
        xDim = freqOpt.x;
        granoVal = (granos === null) ? null : freqOpt.grano;
      }
      var ser = kpiSeriesMap(data, ix, k, xDim, granoVal, agg);
      if (!ser.xs.length && xDim !== "anio") {
        xDim = "anio"; granoVal = annualGrano();
        ser = kpiSeriesMap(data, ix, k, xDim, granoVal, agg);
      }
      // En modo anual, descartar años finales INCOMPLETOS (si existe grano más fino):
      // un año parcial vs. uno completo dibujaría una caída ficticia.
      if (xDim === "anio" && freq && freq.map) {
        var fine = null;
        Object.keys(freq.map).forEach(function (v) {
          var o = freq.map[v]; if (o.x === "trimestre" || o.x === "mes") fine = o;
        });
        if (fine && granos && granos[fine.grano]) {
          var fs = kpiSeriesMap(data, ix, k, fine.x, fine.grano, agg);
          var cnt = {}, maxc = 0;
          fs.xs.forEach(function (p) { var y = String(p).slice(0, 4); cnt[y] = (cnt[y] || 0) + 1; });
          Object.keys(cnt).forEach(function (y) { if (cnt[y] > maxc) maxc = cnt[y]; });
          if (maxc > 0) ser.xs = ser.xs.filter(function (y) { return (cnt[String(y)] || 0) >= maxc; });
        }
      }
      var last = ser.xs.length ? ser.xs[ser.xs.length - 1] : null;
      var now = last != null ? ser.map[last] : null;
      var prevKey = last != null ? kpiPrevPeriod(last) : null;
      var prev = (prevKey != null && ser.map[prevKey] != null) ? ser.map[prevKey] : null;

      var el = document.createElement("div"); el.className = "kpi";

      // KPI de NIVEL con signo (p. ej. resultado fiscal): el % interanual es engañoso
      // cuando el valor cambia de signo o cruza el cero. Se muestra el nivel con signo,
      // color por superávit/déficit, y el dato del mismo período del año previo.
      if (k.display === "nivel" && now != null) {
        var pos = now >= 0;
        var clsN = Math.abs(now) < 1 ? "flat" : (pos ? "up" : "down");
        var ctxN = (last != null ? esc(String(last)) : "");
        if (prev != null) ctxN += " · " + esc(String(prevKey)) + ": " +
          (prev < 0 ? "−" : "") + nfCompact.format(Math.abs(prev)) + " " + esc(k.unidad);
        el.innerHTML =
          '<div class="kpi-value kpi-delta ' + clsN + '">' + (pos ? "" : "−") +
          nfCompact.format(Math.abs(now)) + '<span class="kpi-unit">' + esc(k.unidad) + '</span></div>' +
          '<div class="kpi-label">' + esc(k.label) + '</div>' +
          '<div class="kpi-context">' + ctxN + '</div>';
        mount.appendChild(el);
        return;
      }

      if (now == null || prev == null || prev === 0) {
        // Sin base de comparación: mostrar el valor absoluto del último dato.
        el.innerHTML =
          '<div class="kpi-value">' + (now == null ? "—" : nfFull.format(now)) +
          '<span class="kpi-unit">' + esc(k.unidad) + '</span></div>' +
          '<div class="kpi-label">' + esc(k.label) + '</div>' +
          '<div class="kpi-context">' + (last != null ? esc(String(last)) : "") +
          ' · sin base de comparación</div>';
        mount.appendChild(el);
        return;
      }

      var pct = (now / prev - 1) * 100;
      var cls = Math.abs(pct) < 0.05 ? "flat" : (pct > 0 ? "up" : "down");
      var arrow = cls === "flat" ? "≈" : (cls === "up" ? "▲" : "▼");
      var pctTxt = cls === "flat" ? "0" : nfPct.format(Math.abs(pct));
      el.innerHTML =
        '<div class="kpi-value kpi-delta ' + cls + '">' + arrow + " " + pctTxt + " %</div>" +
        '<div class="kpi-label">' + esc(k.label) + '</div>' +
        '<div class="kpi-context">de ' + nfCompact.format(prev) + " a " + nfCompact.format(now) +
        " " + esc(k.unidad) + " · " + esc(String(prevKey)) + " → " + esc(String(last)) + "</div>";
      mount.appendChild(el);
    });
  }

  // -------------------------------------------------------- Render por tarjeta
  // Tokens que NO son un departamento real (enmascarados / provincial).
  var NON_GEO = ["Enmascarado", "Sin datos", "Sin asignar", "Sin Asignar", "SIN DATOS", "ENMASCARADO", "Salta", "Total Salta",
                 "Otros Deptos./Local. No Publicables", "Otros Deptos./Local. No Publicable"];
  function excluded(ch) {
    var ex = {}; (ch.exclude || []).forEach(function (v) { ex[v] = 1; });
    NON_GEO.forEach(function (v) { ex[v] = 1; });
    return ex;
  }

  // Valores de la dimensión geográfica que EFECTIVAMENTE tienen datos bajo el
  // filtro vigente (evita facetas vacías, p. ej. país cuando se fija nivel=depto).
  function geoValuesWithData(ch, data, ix, fixed, metric, geo) {
    var mi = ix.metrica, gi = ix[geo];
    var pairs = [];
    Object.keys(fixed || {}).forEach(function (d) {
      if (ix[d] !== undefined && d !== geo && fixed[d] !== null && fixed[d] !== ALL)
        pairs.push([ix[d], fixed[d]]);
    });
    var ex = excluded(ch), seen = {}, list = [];
    data.rows.forEach(function (row) {
      if (row[mi] !== metric) return;
      for (var i = 0; i < pairs.length; i++) if (String(row[pairs[i][0]]) !== String(pairs[i][1])) return;
      var g = row[gi];
      if (ex[g] || seen[g]) return;
      seen[g] = 1; list.push(g);
    });
    return list.sort();
  }

  function makeCard(card, ch, data, ix, ctx) {
    ctx = ctx || {};
    var plotEl = card.querySelector(".chart-plot");
    var ctlBox = card.querySelector(".chart-controls");
    var tableBox = card.querySelector(".chart-table-body");
    var hasGrid = (ch.type === "line" || ch.type === "stacked-area") && ch.geoDim;

    var state = {};
    (ch.controls || []).forEach(function (ctl) {
      if (ctl.kind === "select") state[ctl.dim] = ctl.all ? ALL : (ctl.default != null ? ctl.default : (ctl.values || [])[0]);
      else if (ctl.kind === "year") state[ctl.dim] = ctl.default;
      else if (ctl.kind === "metric") state.metric = ctl.options[0];
      else if (ctl.kind === "freq") state.freq = ctl.default != null ? ctl.default : (ctl.options[0] || {}).value;
      else if (ctl.kind === "mode") state.mode = ctl.default != null ? ctl.default : (ctl.options[0] || {}).value;
    });
    if (hasGrid) state.view = "total";

    var local = { instances: [], mode: null, lastFreq: state.freq };
    function clearPlot() {
      local.instances.forEach(function (c) { c.dispose(); });
      local.instances = []; plotEl.innerHTML = ""; plotEl.classList.remove("as-grid");
      plotEl.style.height = "";
    }

    function renderSingle() {
      if (local.mode !== "single") { clearPlot(); local.mode = "single"; }
      var chart = local.instances[0];
      if (!chart) { chart = echarts.init(plotEl, null, { renderer: "canvas" }); local.instances = [chart]; }
      var st = resolveState(ch, state);
      var ech = Object.assign({}, ch, { x: st.x });
      var built = optionFor(ech, data, ix, st.fixed, st.metric, { percent: st.percent });
      plotEl.style.height = built.height + "px";
      chart.resize();
      chart.setOption(built.option, true);
      if (tableBox) tableBox.innerHTML = built.table;
    }

    function renderGrid() {
      clearPlot(); local.mode = "grid"; plotEl.classList.add("as-grid"); plotEl.style.height = "auto";
      var geo = ch.geoDim;
      var st = resolveState(ch, state);
      var ech = Object.assign({}, ch, { x: st.x });
      var deps = geoValuesWithData(ech, data, ix, st.fixed, st.metric, geo);
      var gridSeriesBy = (ch.seriesBy === geo) ? null : ch.seriesBy; // evita colapso de series

      // Cada faceta se escala con SUS propios valores: con eje común, el departamento más grande
      // aplasta a los chicos contra el piso. Líneas no apiladas -> autoescala de ECharts (min y
      // max). Apiladas -> máximo propio, pero base 0: el areaStyle rellena hasta el piso del eje,
      // así que recortarlo dejaría las bandas flotando y sin altura proporcional al valor.
      var lineAdaptive = (ch.type === "line" && !ch.stack && !st.percent);
      var fixeds = deps.map(function (dp) { var f = Object.assign({}, st.fixed); f[geo] = dp; return f; });
      var yMaxes = fixeds.map(function (f) {
        if (lineAdaptive || st.percent) return null;   // en % el eje va fijo 0-100 (optionFor)
        return niceMax(aggMax(ech, data, ix, f, st.metric, gridSeriesBy));
      });

      // Leyenda común (si hay series que no sean la geografía).
      var legendNames = null;
      deps.forEach(function (dp, i) {
        var built = optionFor(ech, data, ix, fixeds[i], st.metric, { forGrid: true, yMax: yMaxes[i], seriesBy: gridSeriesBy, percent: st.percent });
        // Sin puntos tras recortar los ceros del final: faceta en blanco (p. ej. un departamento
        // que figura en la fuente pero no produce). No se dibuja el recuadro vacío.
        if (!built.option.xAxis.data.length) return;
        var cell = document.createElement("div"); cell.className = "facet";
        var h = document.createElement("div"); h.className = "facet-title"; h.textContent = dp;
        var pdiv = document.createElement("div"); pdiv.className = "facet-plot";
        cell.appendChild(h); cell.appendChild(pdiv); plotEl.appendChild(cell);
        var c = echarts.init(pdiv, null, { renderer: "canvas" });
        c.setOption(built.option, true);
        local.instances.push(c);
        if (!legendNames && gridSeriesBy && built.seriesNames && built.seriesNames.length > 1) legendNames = built.seriesNames;
      });

      if (legendNames) {
        var leg = document.createElement("div"); leg.className = "facets-legend";
        var pal = palette();
        legendNames.forEach(function (nm, i) {
          var it = document.createElement("span"); it.className = "facets-legend-item";
          it.innerHTML = '<i style="background:' + pal[i % pal.length] + '"></i>' + esc(nm);
          leg.appendChild(it);
        });
        plotEl.insertBefore(leg, plotEl.firstChild);
      }
      if (tableBox) tableBox.innerHTML = '<p class="muted">La vista en tabla está disponible en la vista <strong>Total</strong>.</p>';
    }

    function render() {
      if (hasGrid && state.view === "grid") renderGrid(); else renderSingle();
      // Al cambiar la frecuencia del gráfico conductor, recomputar los KPIs a esa granularidad.
      if (ctx.isDriver && state.freq !== local.lastFreq) {
        local.lastFreq = state.freq;
        if (ctx.onFreq) ctx.onFreq(state.freq);
      }
    }
    function resize() { local.instances.forEach(function (c) { c.resize(); }); }

    renderControls(ctlBox, ch, data, state, render);
    if (hasGrid) appendViewToggle(ctlBox, ch, state, render);
    render();
    return { render: render, resize: resize };
  }

  // -------------------------------------------------------- Bootstrap
  function init() {
    var page = document.querySelector(".tema-page");
    if (!page) return;
    var id = page.getAttribute("data-tema");
    var base = page.getAttribute("data-base") || ".";
    fetch(base + "/data/" + id + ".json").then(function (r) { return r.json(); }).then(function (data) {
      var ix = makeIndex(data.fields);
      var kpiMount = document.getElementById("kpis");

      // Gráfico "conductor" de la frecuencia de los KPIs: el primero con control freq.
      var driverId = null, driverFreqMap = null, driverFreq = null;
      data.charts.forEach(function (ch) {
        if (driverId) return;
        var fc = (ch.controls || []).filter(function (c) { return c.kind === "freq"; })[0];
        if (fc) {
          driverId = ch.id; driverFreqMap = {};
          (fc.options || []).forEach(function (o) { driverFreqMap[o.value] = o; });
          driverFreq = fc.default != null ? fc.default : (fc.options[0] || {}).value;
        }
      });
      function paintKpis(freqVal) {
        if (kpiMount) renderKpis(kpiMount, data, ix,
          driverFreqMap ? { value: freqVal, map: driverFreqMap } : null);
      }
      paintKpis(driverFreq);

      var cards = [];
      data.charts.forEach(function (ch) {
        var card = document.querySelector('.chart-card[data-chart-id="' + ch.id + '"]');
        if (!card) return;
        cards.push(makeCard(card, ch, data, ix,
          { isDriver: ch.id === driverId, onFreq: paintKpis }));
      });

      window.addEventListener("resize", function () { cards.forEach(function (c) { c.resize(); }); });
      // Al cambiar el tema, recomputar cada gráfico (nueva paleta + colores de texto/grilla).
      window.addEventListener("cess-theme-change", function () { cards.forEach(function (c) { c.render(); }); });
    }).catch(function (e) {
      document.querySelectorAll(".chart-plot").forEach(function (p) {
        p.innerHTML = '<div class="chart-empty">No se pudieron cargar los datos.</div>';
      });
      console.error(e);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
