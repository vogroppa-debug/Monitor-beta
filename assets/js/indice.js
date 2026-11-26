/* Tablero del índice sintético («¿Cómo va el plan?», portada), en líneas.
 *
 * Los datos los escribe build.py en <script id="indice-data"> (indice_sintetico.resumen_portada):
 *   anios:         [2018, ..., último año]
 *   provincial:    {general: [..], ejes: [{id, label, serie: [..], subejes: [{label, n, serie}]}]}
 *   departamental: [{depto, general: [..], ejes: {eje: [..]}, n_ejes, n_ind}]
 * Cada serie trae un valor por año de `anios` (escala 0-100).
 *
 * Provincial: un gráfico; con «General», el índice general y los tres ejes; con un eje, ese eje y
 * sus subejes. Departamental: pequeños múltiplos, uno por departamento, del índice elegido. No hay
 * ranking ni barras: en los totales cada departamento se mide contra su propia historia, así que lo
 * que se lee es la trayectoria de cada uno, no la comparación entre ellos.
 */
(function () {
  "use strict";
  var raiz = document.getElementById("indice-tablero");
  var fuente = document.getElementById("indice-data");
  if (!raiz || !fuente || !window.echarts) return;
  var D;
  try { D = JSON.parse(fuente.textContent); } catch (e) { return; }

  var PAL_LIGHT = ["#2a78d6", "#e8681f", "#16a97a", "#9b4dd4", "#e0a000", "#0f9aad", "#db3f8f"];
  var PAL_DARK = ["#3f8ae0", "#f0793a", "#1fbe8b", "#b26ae0", "#f0b52a", "#2bb6c8", "#ef5aa1"];
  function isDark() {
    var t = document.documentElement.getAttribute("data-theme");
    if (t) return t === "dark";
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  var nf = new Intl.NumberFormat("es-AR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  function fmt(v) { return v == null ? "—" : nf.format(v); }
  function cssvar(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
  function colores() {
    return { ink: cssvar("--ink"), ink2: cssvar("--ink-2"), muted: cssvar("--muted"),
             grid: cssvar("--grid"), pal: isDark() ? PAL_DARK : PAL_LIGHT };
  }
  var anios = D.anios.map(String);
  var iBase = anios.indexOf(String(D.anio_base));
  var ejeLabel = {}; D.ejes.forEach(function (e) { ejeLabel[e.id] = e.label; });

  var elChart = raiz.querySelector("[data-ind-chart]");
  var elGrid = raiz.querySelector("[data-ind-grid]");
  var elTitulo = raiz.querySelector("[data-ind-titulo]");
  var elNota = raiz.querySelector("[data-ind-nota]");
  var segNivel = raiz.querySelector("[data-ind-nivel]");
  var segEje = raiz.querySelector("[data-ind-eje]");
  var estado = { nivel: "prov", eje: "general" };
  var instancias = [];

  raiz.hidden = false;

  // Eje Y: se ajusta a los datos (como las líneas de los tableros), siempre dentro de la escala
  // 0-100 del índice. Intervalo de 10 o 20 según el rango, y los extremos en múltiplos del
  // intervalo, para que las marcas queden parejas (no 20-40-60-80-90).
  function rangoY(series, chico) {
    var vs = [];
    series.forEach(function (s) { s.forEach(function (v) { if (v != null) vs.push(v); }); });
    if (!vs.length) return { min: 0, max: 100, interval: 20 };
    var a = Math.min.apply(null, vs) - 2, b = Math.max.apply(null, vs) + 2;
    var paso = (b - a) > (chico ? 30 : 50) ? 20 : 10;
    return { min: Math.max(0, Math.floor(a / paso) * paso),
             max: Math.min(100, Math.ceil(b / paso) * paso), interval: paso };
  }

  function opcion(C, series, chico) {
    var r = rangoY(series.map(function (s) { return s.data; }), chico);
    return {
      animationDuration: 300,
      textStyle: { fontFamily: "inherit" },
      color: C.pal,
      grid: chico ? { left: 4, right: 10, top: 10, bottom: 4, containLabel: true }
                  : { left: 8, right: 24, top: 40, bottom: 8, containLabel: true },
      legend: chico ? { show: false } : { top: 0, left: 0, itemWidth: 18, itemHeight: 10,
                                          textStyle: { color: C.ink2, fontSize: 12 } },
      tooltip: {
        trigger: "axis", confine: true,
        valueFormatter: function (v) { return fmt(v); }
      },
      xAxis: { type: "category", data: anios, boundaryGap: false,
               axisLabel: { color: C.muted, fontSize: chico ? 10 : 11, hideOverlap: true },
               axisLine: { lineStyle: { color: C.grid } }, axisTick: { show: false } },
      yAxis: { type: "value", min: r.min, max: r.max, interval: r.interval,
               axisLabel: { color: C.muted, fontSize: chico ? 10 : 11 },
               splitLine: { lineStyle: { color: C.grid } } },
      series: series.map(function (s, i) {
        var o = { name: s.name, type: "line", data: s.data, connectNulls: false,
                  symbol: "circle", symbolSize: chico ? 0 : (s.fuerte ? 6 : 4), showSymbol: !chico,
                  // Los componentes (ejes, o subejes) van en guiones para no confundirse con la
                  // línea gruesa y continua del índice que resumen.
                  lineStyle: { width: s.fuerte ? 3 : 1.8, type: s.fuerte ? "solid" : [6, 4] },
                  emphasis: { focus: chico ? "none" : "series" } };
        if (s.color) o.itemStyle = { color: s.color };
        if (i === 0 && iBase >= 0) {
          o.markLine = { symbol: "none", silent: true,
            lineStyle: { color: C.muted, type: "dashed", width: 1 },
            label: chico ? { show: false } : { formatter: "Base " + D.anio_base, color: C.muted,
                                              fontSize: 11, position: "end" },
            data: [{ xAxis: anios[iBase] }] };
        }
        return o;
      })
    };
  }

  function limpiar() {
    instancias.forEach(function (c) { c.dispose(); });
    instancias = [];
    elGrid.innerHTML = "";
  }

  // ---------------------------------------------------------------- Provincial
  function vistaProvincial(C) {
    var series, titulo;
    if (estado.eje === "general") {
      series = [{ name: "Índice general", data: D.provincial.general, fuerte: true, color: C.ink }]
        .concat(D.provincial.ejes.map(function (e) { return { name: e.label, data: e.serie }; }));
      titulo = "Índice provincial: general y por eje";
      elNota.textContent = "Escala 0-100: 100 es el mejor valor histórico de cada indicador y 0 el " +
        "peor. Cada dato rige hasta el siguiente (un censo vale hasta el próximo), así que los " +
        "indicadores censales y de trienios mueven la línea en escalón. En " + D.anio_base +
        " la línea pasa por la base de las tarjetas y en " + anios[anios.length - 1] +
        " por el último dato.";
    } else {
      var e = D.provincial.ejes.filter(function (x) { return x.id === estado.eje; })[0];
      series = [{ name: e.label, data: e.serie, fuerte: true, color: C.ink }]
        .concat(e.subejes.map(function (s) {
          return { name: s.label + " (" + s.n + ")", data: s.serie };
        }));
      titulo = "Índice provincial: eje " + e.label + " y sus subejes";
      elNota.textContent = "La línea gruesa es el eje: el promedio de sus subejes. Entre " +
        "paréntesis, la cantidad de indicadores de cada subeje. Un subeje con un solo indicador " +
        "censal o de trienio queda plano entre mediciones.";
    }
    elTitulo.textContent = titulo;
    elChart.hidden = false; elGrid.hidden = true;
    var c = echarts.init(elChart, null, { renderer: "svg" });
    c.setOption(opcion(C, series, false));
    elChart.setAttribute("aria-label", titulo);
    instancias.push(c);
  }

  // ---------------------------------------------------------------- Departamental
  function vistaDepartamental(C) {
    var clave = estado.eje;
    var nombre = clave === "general" ? "Índice general" : "Eje " + ejeLabel[clave];
    elTitulo.textContent = nombre + " por departamento";
    elChart.hidden = true; elGrid.hidden = false;
    var sin = [], parciales = [];
    var color = clave === "general" ? C.ink : C.pal[D.ejes.map(function (e) { return e.id; }).indexOf(clave) + 1];
    D.departamental.forEach(function (d) {
      var serie = clave === "general" ? d.general : d.ejes[clave];
      if (!serie || serie.every(function (v) { return v == null; })) { sin.push(d.depto); return; }
      var parcial = clave === "general" && d.n_ejes < 3;
      if (parcial) parciales.push(d);
      var cell = document.createElement("div"); cell.className = "facet";
      var h = document.createElement("div"); h.className = "facet-title";
      h.textContent = d.depto + (parcial ? " *" : "");
      var p = document.createElement("div"); p.className = "facet-plot";
      cell.appendChild(h); cell.appendChild(p); elGrid.appendChild(cell);
      var c = echarts.init(p, null, { renderer: "svg" });
      c.setOption(opcion(C, [{ name: d.depto, data: serie, fuerte: true, color: color }], true));
      instancias.push(c);
    });
    var notas = ["Cada recuadro tiene su propia escala vertical: se lee la trayectoria de cada " +
      "departamento, no la comparación entre ellos. En los indicadores que son totales " +
      "(toneladas, puestos de trabajo…) cada departamento se mide contra su propia historia."];
    if (parciales.length) {
      notas.push("* Promedia sólo los ejes con dato: " + parciales.map(function (d) {
        var f = D.ejes.filter(function (e) {
          return (d.ejes[e.id] || []).every(function (v) { return v == null; });
        }).map(function (e) { return e.label; });
        return d.depto + (f.length ? " (sin " + f.join(", ") + ")" : "");
      }).join("; ") + ".");
    }
    if (sin.length) notas.push("Sin dato en este eje: " + sin.join(", ") + ".");
    notas.push("La línea punteada marca la base " + D.anio_base + ".");
    elNota.textContent = notas.join(" ");
  }

  // ---------------------------------------------------------------- dibujo
  function dibujar() {
    limpiar();
    var C = colores();
    if (estado.nivel === "prov") vistaProvincial(C); else vistaDepartamental(C);
  }

  function enlazar(seg, campo) {
    seg.querySelectorAll("button").forEach(function (b) {
      b.addEventListener("click", function () {
        seg.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", "true");
        estado[campo] = b.getAttribute("data-v");
        dibujar();
      });
    });
  }
  enlazar(segNivel, "nivel");
  enlazar(segEje, "eje");

  dibujar();
  var t;
  window.addEventListener("resize", function () {
    clearTimeout(t); t = setTimeout(function () { instancias.forEach(function (c) { c.resize(); }); }, 150);
  });
  window.addEventListener("cess-theme-change", dibujar);
})();
