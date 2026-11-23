/* Tablero del índice sintético («¿Cómo estamos?», portada).
 *
 * Los datos los escribe build.py en <script id="indice-data"> (indice_sintetico.resumen_portada):
 *   provincial:    [{eje, label, b, u, subejes: [{label, b, u, n}]}]
 *   departamental: [{depto, general: {b, u}, ejes: {eje: {b, u}}, n_ejes, n_ind}]
 *   prov_ref:      {general: {b, u}, <eje>: {b, u}}
 * Dos vistas, con un toggle: Provincial (ejes y subejes, base vs último dato) y Departamental
 * (ranking de los departamentos en el índice elegido, con la provincia como referencia).
 * Escala fija 0-100 en las dos: es la escala del índice. Sin JavaScript el bloque queda oculto.
 */
(function () {
  "use strict";
  var raiz = document.getElementById("indice-tablero");
  var fuente = document.getElementById("indice-data");
  if (!raiz || !fuente || !window.echarts) return;
  var D;
  try { D = JSON.parse(fuente.textContent); } catch (e) { return; }

  var nf = new Intl.NumberFormat("es-AR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  function fmt(v) { return v == null ? "—" : nf.format(v).replace("-", "−"); }
  function dif(b, u) {
    if (b == null || u == null) return "";
    var d = u - b;
    if (Math.abs(d) < 0.05) return "sin cambio";
    return (d > 0 ? "▲ +" : "▼ −") + nf.format(Math.abs(d)) + " puntos";
  }
  function cssvar(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  function colores() {
    return { ink: cssvar("--ink"), ink2: cssvar("--ink-2"), muted: cssvar("--muted"),
             grid: cssvar("--grid"), accent: cssvar("--accent"), surface: cssvar("--surface") };
  }
  var BASE = "Base " + D.anio_base, ULT = "Último dato";
  var ejeLabel = {}; D.ejes.forEach(function (e) { ejeLabel[e.id] = e.label; });

  var elChart = raiz.querySelector("[data-ind-chart]");
  var elTitulo = raiz.querySelector("[data-ind-titulo]");
  var elNota = raiz.querySelector("[data-ind-nota]");
  var segNivel = raiz.querySelector("[data-ind-nivel]");
  var segEje = raiz.querySelector("[data-ind-eje]");
  var estado = { nivel: "prov", eje: "general" };
  var chart = null;

  raiz.hidden = false;

  function anchoEtiqueta() {
    var w = elChart.clientWidth || 600;
    return Math.max(96, Math.min(190, Math.round(w * 0.36)));
  }

  function base(C, filas) {
    return {
      animationDuration: 300,
      textStyle: { fontFamily: "inherit" },
      grid: { left: 8, right: 44, top: 34, bottom: 8, containLabel: true },
      legend: { top: 0, left: 0, itemWidth: 14, itemHeight: 10,
                textStyle: { color: C.ink2, fontSize: 12 } },
      xAxis: { type: "value", min: 0, max: 100, interval: 25,
               axisLabel: { color: C.muted, fontSize: 11 },
               splitLine: { lineStyle: { color: C.grid } } },
      yAxis: { type: "category", inverse: true, data: filas,
               axisTick: { show: false }, axisLine: { lineStyle: { color: C.grid } } },
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" }, confine: true }
    };
  }

  // ---------------------------------------------------------------- Provincial
  function vistaProvincial(C) {
    var filas = [], meta = [];
    D.provincial.forEach(function (e) {
      filas.push("e" + filas.length); meta.push({ eje: true, label: e.label, b: e.b, u: e.u,
        n: e.subejes.reduce(function (a, s) { return a + s.n; }, 0) });
      e.subejes.forEach(function (s) {
        filas.push("s" + filas.length); meta.push({ eje: false, label: s.label, b: s.b, u: s.u, n: s.n });
      });
    });
    var o = base(C, filas);
    o.yAxis.axisLabel = {
      width: anchoEtiqueta(), overflow: "truncate", color: C.ink,
      formatter: function (v) {
        var m = meta[filas.indexOf(v)];
        return m.eje ? "{e|" + m.label + "}" : "{s|" + m.label + "}";
      },
      rich: { e: { fontWeight: 700, fontSize: 12.5, color: C.ink },
              s: { fontSize: 12, color: C.ink2, padding: [0, 0, 0, 10] } }
    };
    o.tooltip.formatter = function (ps) {
      var m = meta[ps[0].dataIndex];
      return "<strong>" + m.label + "</strong>" + (m.eje ? " (eje)" : "") +
        "<br>" + BASE + ": " + fmt(m.b) + "<br>" + ULT + ": <strong>" + fmt(m.u) + "</strong>" +
        "<br>" + dif(m.b, m.u) + "<br><span style='opacity:.75'>" + m.n + " indicador" +
        (m.n === 1 ? "" : "es") + "</span>";
    };
    var etiqueta = { show: true, position: "right", color: C.ink, fontSize: 11,
                     formatter: function (p) { return fmt(p.value); } };
    o.series = [
      { name: BASE, type: "bar", barGap: "8%", barCategoryGap: "32%",
        itemStyle: { color: C.muted, opacity: 0.45 },
        data: meta.map(function (m) { return m.b; }) },
      { name: ULT, type: "bar", label: etiqueta,
        itemStyle: { color: C.accent },
        data: meta.map(function (m) {
          return { value: m.u, itemStyle: m.eje ? { borderColor: C.ink, borderWidth: 1 } : {} };
        }) }
    ];
    elTitulo.textContent = "Índice provincial por eje y subeje (escala 0-100)";
    elNota.textContent = "En negrita, cada eje: el promedio de sus subejes. Las barras grises son " +
      "la base " + D.anio_base + "; las de color, el último dato. Muchas series del eje " +
      "sociocultural (censo, trienios) tienen un único período: valen lo mismo en la base y en " +
      "el último dato, así que todavía no mueven el índice.";
    return { opcion: o, filas: filas.length };
  }

  // ---------------------------------------------------------------- Departamental
  function vistaDepartamental(C) {
    var clave = estado.eje;
    var val = function (d) { return clave === "general" ? d.general : d.ejes[clave]; };
    var con = D.departamental.filter(function (d) { return val(d).u != null; });
    var sin = D.departamental.filter(function (d) { return val(d).u == null; });
    con.sort(function (a, b) { return val(b).u - val(a).u; });
    var parcial = function (d) { return clave === "general" && d.n_ejes < 3; };
    var filas = con.map(function (d) { return d.depto + (parcial(d) ? " *" : ""); });
    var ref = D.prov_ref[clave];

    var o = base(C, filas);
    o.yAxis.axisLabel = { width: anchoEtiqueta(), overflow: "truncate", color: C.ink, fontSize: 12 };
    o.tooltip.formatter = function (ps) {
      var d = con[ps[0].dataIndex], v = val(d);
      var faltan = D.ejes.filter(function (e) { return d.ejes[e.id].u == null; })
        .map(function (e) { return e.label; });
      return "<strong>" + d.depto + "</strong><br>" + BASE + ": " + fmt(v.b) +
        "<br>" + ULT + ": <strong>" + fmt(v.u) + "</strong><br>" + dif(v.b, v.u) +
        "<br><span style='opacity:.75'>" + d.n_ind + " indicadores; " + d.n_ejes + " de 3 ejes" +
        (faltan.length ? " (sin " + faltan.join(", ") + ")" : "") + "</span>";
    };
    o.series = [
      { name: ULT, type: "bar", barCategoryGap: "34%", itemStyle: { color: C.accent },
        label: { show: true, position: "right", color: C.ink, fontSize: 11,
                 formatter: function (p) { return fmt(p.value); } },
        data: con.map(function (d) { return val(d).u; }),
        markLine: ref && ref.u != null ? {
          symbol: "none", silent: true,
          lineStyle: { color: C.ink, type: "dashed", width: 1.2 },
          label: { show: false },
          data: [{ xAxis: ref.u }]
        } : undefined },
      { name: BASE, type: "scatter", symbol: "rect", symbolSize: [3, 14], z: 5,
        itemStyle: { color: C.ink },
        data: con.map(function (d) { return val(d).b; }) }
    ];
    var nombre = clave === "general" ? "Índice general" : "Eje " + ejeLabel[clave];
    elTitulo.textContent = nombre + " por departamento: último dato (escala 0-100)" +
      (ref && ref.u != null ? " · línea punteada: provincia " + fmt(ref.u) : "");

    var notas = [];
    var parciales = con.filter(parcial);
    if (parciales.length) {
      notas.push("* Promedia sólo los ejes con dato: " + parciales.map(function (d) {
        var f = D.ejes.filter(function (e) { return d.ejes[e.id].u == null; })
          .map(function (e) { return e.label; });
        return d.depto + " (sin " + f.join(", ") + ")";
      }).join("; ") + ".");
    }
    if (sin.length) notas.push("Sin dato en este eje: " + sin.map(function (d) { return d.depto; }).join(", ") + ".");
    notas.push("La marca vertical corta es la base " + D.anio_base + "; la línea punteada, el índice " +
      "provincial, que se calcula con su propia selección de indicadores.");
    notas.push("En los indicadores que son totales (toneladas, puestos de trabajo…) cada " +
      "departamento se compara con su propia historia, así que el ranking refleja más la " +
      "trayectoria que el nivel; en las tasas y porcentajes la escala es común a todos.");
    elNota.textContent = notas.join(" ");
    return { opcion: o, filas: filas.length };
  }

  // ---------------------------------------------------------------- dibujo
  function dibujar() {
    var C = colores();
    var v = estado.nivel === "prov" ? vistaProvincial(C) : vistaDepartamental(C);
    elChart.style.height = Math.max(260, v.filas * 28 + 64) + "px";
    if (chart) chart.dispose();
    chart = echarts.init(elChart, null, { renderer: "svg" });
    chart.setOption(v.opcion);
    elChart.setAttribute("aria-label", elTitulo.textContent);
  }

  function enlazar(seg, campo) {
    seg.querySelectorAll("button").forEach(function (b) {
      b.addEventListener("click", function () {
        seg.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", "true");
        estado[campo] = b.getAttribute("data-v");
        segEje.hidden = estado.nivel !== "dept";
        dibujar();
      });
    });
  }
  enlazar(segNivel, "nivel");
  enlazar(segEje, "eje");

  dibujar();
  var t;
  window.addEventListener("resize", function () {
    clearTimeout(t); t = setTimeout(dibujar, 150);
  });
  window.addEventListener("cess-theme-change", dibujar);
})();
