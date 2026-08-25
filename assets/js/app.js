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
