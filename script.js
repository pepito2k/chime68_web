// Small touches of motion: scroll reveals and the hero's typed label.
// Nothing here runs when the reader asks for reduced motion.
(function () {
  if (!window.matchMedia || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  document.documentElement.classList.add("js");

  // Stagger the items of each group by their place in it.
  document.querySelectorAll(".stats li, .cards > *, .families > *, .systems > *, .gallery > *, .split > *, .keys li").forEach(function (el) {
    el.style.setProperty("--i", Array.prototype.indexOf.call(el.parentNode.children, el) % 6);
  });

  var reveal = document.querySelectorAll(".section-head, .cards > *, .families > *, .systems > *, .systems-note, .gallery > *, .split > *, .keys-title, .keys, .keys-note, .callout, .table-wrap, #browser pre, .after");
  if ("IntersectionObserver" in window) {
    var seen = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          seen.unobserve(e.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    reveal.forEach(function (el) {
      el.setAttribute("data-reveal", "");
      seen.observe(el);
    });
  }

  // Type out the hero's label, as a terminal would.
  var label = document.querySelector(".hero .eyebrow");
  if (label) {
    var text = label.textContent;
    label.setAttribute("aria-label", text);
    label.textContent = "";
    label.classList.add("typing");
    var n = 0;
    setTimeout(function step() {
      label.textContent = text.slice(0, ++n);
      if (n < text.length) setTimeout(step, 38);
    }, 350);
  }
})();
