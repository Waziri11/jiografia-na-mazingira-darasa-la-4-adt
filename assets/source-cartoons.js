(function () {
  "use strict";

  const decorate = () => {
    document.querySelectorAll("[data-id]").forEach((element) => {
      const label = (element.textContent || "").trim().replace(/\s+/g, " ");

      if (/^Fikiri$/i.test(label)) {
        element.classList.add("source-cartoon-title", "source-cartoon-fikiri");
        return;
      }

      if (!/^Kazi ya(?:\s+kufanya)?(?:\s+namba)?\s+\d+/i.test(label)) return;

      const section = element.closest("section");
      const sourceIcon = section && section.querySelector(
        'img[src*="_activity_icon.png"], img[src$="pg045_activity_icon.png"]'
      );

      element.classList.add("source-cartoon-label");
      if (!sourceIcon) {
        element.classList.add("source-cartoon-title", "source-cartoon-kazi");
      }
    });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", decorate, { once: true });
  } else {
    decorate();
  }

  new MutationObserver(decorate).observe(document.documentElement, {
    childList: true,
    subtree: true,
    characterData: true,
  });
})();
