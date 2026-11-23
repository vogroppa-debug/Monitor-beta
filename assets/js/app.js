/* app.js — navegación, menú responsive y cambio de tema (claro/oscuro). */
(function () {
  "use strict";

  /* ---- Tema claro/oscuro ---- */
  var root = document.documentElement;
  function currentTheme() {
    var t = root.getAttribute("data-theme");
    if (t) return t;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  var toggle = document.querySelector(".theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("cess-theme", next); } catch (e) {}
      window.dispatchEvent(new CustomEvent("cess-theme-change", { detail: { theme: next } }));
    });
  }
  // Si el usuario está en modo automático y cambia el SO, avisar a los gráficos.
  if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
      if (!root.getAttribute("data-theme")) {
        window.dispatchEvent(new CustomEvent("cess-theme-change", { detail: { theme: currentTheme() } }));
      }
    });
  }

  /* ---- Menú móvil ---- */
  var navToggle = document.querySelector(".nav-toggle");
  var mainnav = document.getElementById("mainnav");
  if (navToggle && mainnav) {
    navToggle.addEventListener("click", function () {
      var open = mainnav.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", String(open));
    });
  }

  /* ---- Dropdown de "Temas" ---- */
  document.querySelectorAll(".navgroup").forEach(function (g) {
    var btn = g.querySelector(".navgroup-btn");
    if (!btn) return;
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = g.classList.toggle("open");
      btn.setAttribute("aria-expanded", String(open));
    });
  });
  document.addEventListener("click", function (e) {
    document.querySelectorAll(".navgroup.open").forEach(function (g) {
      if (!g.contains(e.target)) {
        g.classList.remove("open");
        var b = g.querySelector(".navgroup-btn");
        if (b) b.setAttribute("aria-expanded", "false");
      }
    });
  });

  /* ---- Tabla de indicadores: subejes desplegables (portada) ---- */
  var tbodies = Array.prototype.filter.call(document.querySelectorAll(".tabla-ind tbody"),
    function (tb) { return tb.querySelector(".subeje-toggle"); });
  if (tbodies.length) {
    // Los anchos se fijan con la tabla ENTERA, antes de cerrar nada. Si no, el navegador los
    // calcula con las filas visibles y cada subeje que se abre corre todas las columnas.
    document.querySelectorAll(".tabla-ind").forEach(function (t) {
      var total = t.getBoundingClientRect().width;
      if (!total) return;
      t.querySelectorAll("thead th").forEach(function (th) {
        th.style.width = (th.getBoundingClientRect().width / total * 100).toFixed(3) + "%";
      });
      t.style.minWidth = Math.round(total) + "px";
      t.style.tableLayout = "fixed";
    });
    var poner = function (tb, abierto) {
      tb.classList.toggle("sub-cerrado", !abierto);
      tb.querySelector(".subeje-toggle").setAttribute("aria-expanded", String(abierto));
    };
    tbodies.forEach(function (tb) {
      poner(tb, false);
      tb.querySelector(".subeje-toggle").addEventListener("click", function () {
        poner(tb, tb.classList.contains("sub-cerrado"));
      });
    });
    var acciones = document.querySelector(".tabla-ind-acciones");
    if (acciones) acciones.hidden = false;
    document.querySelectorAll("[data-tabla-accion]").forEach(function (b) {
      b.addEventListener("click", function () {
        var abrir = b.getAttribute("data-tabla-accion") === "abrir";
        tbodies.forEach(function (tb) { poner(tb, abrir); });
      });
    });
  }

  /* ---- Enlaces a un <details> (p. ej. el listado de indicadores del índice): lo abren ---- */
  function abrirDetalle(id) {
    var t = id && document.getElementById(id);
    if (t && t.tagName === "DETAILS") t.open = true;
  }
  document.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest('a[href^="#"]');
    if (a) abrirDetalle(a.getAttribute("href").slice(1));
  });
  // Entrando con el ancla en la dirección: el navegador salta antes de que se dibujen los
  // gráficos de arriba, que después empujan la página; se vuelve a llevar a la vista ya abierto.
  if (location.hash) {
    var idHash = decodeURIComponent(location.hash.slice(1));
    abrirDetalle(idHash);
    var dHash = document.getElementById(idHash);
    if (dHash && dHash.tagName === "DETAILS") {
      window.addEventListener("load", function () { dHash.scrollIntoView(); });
    }
  }

  /* ---- Filtro por eje del PDES (portada) ---- */
  var pills = document.querySelectorAll(".eje-pill");
  if (pills.length) {
    var blocks = document.querySelectorAll(".eje-block");
    pills.forEach(function (p) {
      p.addEventListener("click", function () {
        var sel = p.getAttribute("data-eje");
        pills.forEach(function (q) {
          var on = q === p;
          q.classList.toggle("is-active", on);
          q.setAttribute("aria-selected", String(on));
        });
        blocks.forEach(function (b) {
          b.hidden = !(sel === "all" || b.getAttribute("data-eje") === sel);
        });
      });
    });
  }
})();
