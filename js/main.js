import { site } from "./site.config.js";

const $ = (s, r = document) => r.querySelector(s);
const el = (tag, cls, html) => { const n = document.createElement(tag); if (cls) n.className = cls; if (html != null) n.innerHTML = html; return n; };
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// Static facts from config
$("#since").textContent = site.since;
$("#formerly").textContent = site.formerly;
$("#ig").href = site.instagram.url;
$("#ig").textContent = `Instagram @${site.instagram.handle}`;
document.querySelectorAll("[data-messenger]").forEach((a) => { a.href = site.messengerUrl; a.rel = "noopener"; a.target = "_blank"; });

// Branches
$("#branch-list").append(...site.branches.map((b) => {
  const li = el("li", "branch reveal", `<p class="eyebrow">Branch</p><h3>${esc(b.name)}</h3><p>${esc([b.floor, b.area].filter(Boolean).join(" · "))}</p>`);
  return li;
}));

// Header
const header = $(".site-header");
const onScroll = () => header.classList.toggle("scrolled", scrollY > 40);
addEventListener("scroll", onScroll, { passive: true });
onScroll();

// Catalog
const res = await fetch("data/products.json");
const products = await res.json();
const cats = ["All", ...new Set(products.map((p) => p.category))];
const grid = $("#grid");
grid.append(...products.map((p) => {
  const li = el("li", "card reveal");
  li.dataset.category = p.category;
  li.innerHTML = `
    <figure><img src="assets/img/products/${esc(p.images[0])}" alt="${esc(p.alt)}" loading="lazy" width="768" height="1024"></figure>
    <p class="eyebrow">${esc(p.category.replace(/s$/, ""))}</p>
    <h3>${esc(p.name)}</h3>
    <p class="price">${p.price == null ? "Price on request" : esc(p.price)}</p>
    <a class="reserve-link" href="${esc(site.messengerUrl)}" target="_blank" rel="noopener" aria-label="Reserve ${esc(p.name)} on Messenger">Reserve</a>`;
  const img = $("img", li);
  if (p.images[1]) {
    li.addEventListener("pointerenter", () => { img.src = `assets/img/products/${p.images[1]}`; });
    li.addEventListener("pointerleave", () => { img.src = `assets/img/products/${p.images[0]}`; });
  }
  return li;
}));
const chips = $("#chips");
chips.append(...cats.map((c, i) => {
  const b = el("button", "chip", esc(c));
  b.type = "button";
  b.setAttribute("aria-pressed", i === 0);
  b.addEventListener("click", () => {
    chips.querySelectorAll(".chip").forEach((x) => x.setAttribute("aria-pressed", x === b));
    grid.querySelectorAll(".card").forEach((card) => { card.hidden = c !== "All" && card.dataset.category !== c; });
  });
  return b;
}));

// Reveal on scroll (once)
const io = new IntersectionObserver((entries) => entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }), { threshold: 0.12 });
document.querySelectorAll(".reveal").forEach((n) => io.observe(n));

// Scroll showcase: pre-rendered frame sequence drawn on a canvas
const stage = $("#stage");
const chapters = [...document.querySelectorAll(".chapter")];
const pin = $(".stage-pin");
const fallback = () => {
  $("#hero-canvas").hidden = true;
  $(".stage-fallback").hidden = false;
  chapters[0].classList.add("on"); // no scroll driver without 3D, so keep the headline visible
};
try {
  const { initHero } = await import("./hero-seq.js");
  const ok = await initHero({
    canvas: $("#hero-canvas"),
    stage,
    onProgress: (p, push) => {
      chapters.forEach((c) => c.classList.toggle("on", p >= +c.dataset.from && p <= +c.dataset.to));
      // Background morph: the glow drifts and deepens to gold as the camera pushes in on the stone,
      // while two hairline rings expand and turn with the scroll.
      const set = (k, v) => pin.style.setProperty(k, v);
      set("--bx", `${50 + Math.sin(p * Math.PI * 2) * 14}%`);
      set("--by", `${56 - push * 12}%`);
      set("--warm", push.toFixed(3));
      set("--orbit", (0.72 + p * 0.9 + push * 0.25).toFixed(3));
      set("--orbit-o", (0.35 + push * 0.65).toFixed(3));
      set("--spin", `${(p * 50).toFixed(2)}deg`);
    },
  });
  if (!ok) fallback();
} catch (err) {
  console.warn("Showcase unavailable, showing photo fallback.", err);
  fallback();
}
