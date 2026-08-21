// Keep long-lived GitHub Pages sessions synchronized with the latest book build.
(function () {
  "use strict";

  var script = document.currentScript;
  if (!script || !script.src) return;

  var scriptUrl = new URL(script.src, location.href);
  var loadedBuild = scriptUrl.searchParams.get("v") || "";
  var bookRoot = new URL("../", scriptUrl);
  var checking = false;

  async function checkForUpdate() {
    if (checking || document.visibilityState === "hidden") return;
    checking = true;
    try {
      var hashUrl = new URL(".build-hash", bookRoot);
      hashUrl.searchParams.set("t", String(Date.now()));
      var response = await fetch(hashUrl.href, {
        cache: "no-store",
        headers: { "Cache-Control": "no-cache" }
      });
      if (!response.ok) return;

      var publishedBuild = (await response.text()).trim();
      if (!publishedBuild || publishedBuild.indexOf(loadedBuild) === 0) return;

      var refreshToken = publishedBuild.slice(0, 12);
      var pageUrl = new URL(location.href);
      if (pageUrl.searchParams.get("adt-build") === refreshToken) return;
      pageUrl.searchParams.set("adt-build", refreshToken);
      location.replace(pageUrl.href);
    } catch (_) {
      // Offline readers should continue normally and retry when connectivity returns.
    } finally {
      checking = false;
    }
  }

  checkForUpdate();
  window.setInterval(checkForUpdate, 60000);
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") checkForUpdate();
  });
})();
