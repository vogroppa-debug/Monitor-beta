/* search.js — Buscador de la portada. Indexa el catálogo con MiniSearch y
   devuelve los tableros (y gráficos) relacionados con la consulta. */
(function () {
  "use strict";
  var base = window.CESS_BASE || ".";

  function fold(s) {
    return String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  var input = document.getElementById("search-input");
  var resultsWrap = document.getElementById("resultados-wrap");
  var results = document.getElementById("resultados");
  var explorar = document.getElementById("explorar");
  if (!input) return;

  fetch(base + "/data/catalog.json").then(function (r) { return r.json(); }).then(function (cat) {
    var temas = cat.temas;
    var byId = {};
    temas.forEach(function (t) { byId[t.id] = t; });

    var docs = temas.map(function (t) {
      return {
        id: t.id, title: t.title, resumen: t.resumen, area_label: t.area_label,
        keywords: (t.keywords || []).join(" "),
        tags: (t.tags_labels || []).join(" "),
        departamentos: (t.departamentos || []).join(" "),
        metricas: (t.metricas || []).join(" "),
        charts_text: (t.charts || []).map(function (c) { return c.title + " " + c.descr; }).join(" ")
      };
    });

    var mini = new MiniSearch({
      fields: ["title", "resumen", "keywords", "tags", "departamentos", "metricas", "area_label", "charts_text"],
      storeFields: ["id"],
      processTerm: function (term) { return fold(term); },
      searchOptions: {
        prefix: true, fuzzy: 0.2,
        boost: { title: 3, keywords: 3, departamentos: 3, tags: 2, metricas: 2 },
        combineWith: "OR"
      }
    });
    mini.addAll(docs);

    function run(q) {
      q = (q || "").trim();
      if (!q) {
        resultsWrap.hidden = true; results.innerHTML = "";
        if (explorar) explorar.hidden = false;
        return;
      }
      var hits = mini.search(q);
      renderResults(q, hits);
    }

    function renderResults(q, hits) {
      resultsWrap.hidden = false;
      if (explorar) explorar.hidden = true;
      if (!hits.length) {
        results.innerHTML = '<p class="result-empty">Sin tableros para “' + escapeHtml(q) +
          '”. Se puede probar con otra palabra (ej.: <em>vino</em>, <em>escuelas</em>, <em>petróleo</em>, <em>Orán</em>).</p>';
        return;
      }
      results.innerHTML = "";
      hits.slice(0, 12).forEach(function (h) {
        var t = byId[h.id];
        var el = document.createElement("div");
        el.className = "card result";
        var chips = (t.charts || []).map(function (c) {
          return '<a class="chip" href="' + base + '/tema/' + t.id + '.html#grafico-' + c.id + '">' +
                 escapeHtml(c.title) + "</a>";
        }).join("");
        var tagChips = (t.tags_labels || []).map(function (tl) {
          return '<span class="tag-chip">' + escapeHtml(tl) + "</span>";
        }).join("");
        var qf = fold(q);
        var isHit = function (d) { return qf.length >= 2 && fold(d).indexOf(qf) !== -1; };
        // Los departamentos que coinciden con la búsqueda van primero (para que se vean).
        var deptos = (t.departamentos || []).slice().sort(function (a, b) {
          return (isHit(b) ? 1 : 0) - (isHit(a) ? 1 : 0);
        });
        var deptoChips = deptos.slice(0, 10).map(function (d) {
          return '<span class="geo-chip' + (isHit(d) ? " is-hit" : "") + '">' + escapeHtml(d) + "</span>";
        }).join("");
        if (deptos.length > 10) deptoChips += '<span class="geo-chip geo-more">+' + (deptos.length - 10) + "</span>";
        el.innerHTML =
          '<span class="card-area">' + escapeHtml(t.area_label) + "</span>" +
          '<h4 class="card-title"><a href="' + base + "/tema/" + t.id + '.html">' + escapeHtml(t.title) + "</a></h4>" +
          (tagChips ? '<div class="tag-chips">' + tagChips + "</div>" : "") +
          '<p class="card-desc">' + escapeHtml(t.resumen) + "</p>" +
          (deptoChips ? '<div class="geo-chips" aria-label="Departamentos con datos">' + deptoChips + "</div>" : "") +
          '<div class="result-charts">' + chips + "</div>";
        results.appendChild(el);
      });
    }

    function escapeHtml(s) {
      return String(s).replace(/[&<>"]/g, function (m) {
        return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[m];
      });
    }

    // Eventos
    var deb;
    input.addEventListener("input", function () {
      clearTimeout(deb); deb = setTimeout(function () { run(input.value); }, 120);
    });
    document.querySelectorAll(".search-suggestions .chip").forEach(function (b) {
      b.addEventListener("click", function () {
        input.value = b.getAttribute("data-q"); run(input.value); input.focus();
      });
    });
    // Soporte de ?q= y foco al llegar por #buscador
    var params = new URLSearchParams(location.search);
    if (params.get("q")) { input.value = params.get("q"); run(input.value); }
    if (location.hash === "#buscador") input.focus();
  }).catch(function (e) { console.error("No se pudo cargar el catálogo:", e); });
})();
