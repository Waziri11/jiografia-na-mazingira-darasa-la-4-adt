/*
 * Keeps read-aloud audio, its text highlight, and sign-language video on one
 * page-level timeline. This runs before the ADT runtime so it can observe the
 * runtime's off-DOM Audio element without changing the compiled runtime.
 */
(function () {
  "use strict";

  var NativeAudio = window.Audio;
  var activeAudio = null;
  var signVideo = null;
  var timeline = new Map();
  var totalAudioDuration = 0;
  var timelinePromise = null;
  var timelineMode = null;
  var timelineGeneration = 0;
  var resumeTimer = 0;

  function filenameFromUrl(url) {
    try {
      return decodeURIComponent(new URL(url, location.href).pathname.split("/").pop() || "");
    } catch (_) {
      return String(url || "").split("/").pop().split("?")[0];
    }
  }

  function currentLanguage() {
    return document.documentElement.lang || "sw";
  }

  function mediaDuration(url) {
    return new Promise(function (resolve) {
      var probe = new NativeAudio();
      var settled = false;
      var finish = function (value) {
        if (settled) return;
        settled = true;
        probe.removeAttribute("src");
        probe.load();
        resolve(Number.isFinite(value) ? value : 0);
      };
      probe.preload = "metadata";
      probe.onloadedmetadata = function () { finish(probe.duration); };
      probe.onerror = function () { finish(0); };
      probe.src = url;
      window.setTimeout(function () { finish(0); }, 10000);
    });
  }

  function buildTimeline(mode) {
    mode = mode || "standard";
    if (timelinePromise && timelineMode === mode) return timelinePromise;
    timelineMode = mode;
    timeline.clear();
    totalAudioDuration = 0;
    var generation = ++timelineGeneration;
    timelinePromise = (async function () {
      var lang = currentLanguage();
      var response = await fetch("./content/i18n/" + lang + "/audios.json");
      if (!response.ok) return;
      var catalog = await response.json();
      var filenames = [];
      document.querySelectorAll("#content [data-id]").forEach(function (element) {
        var id = element.getAttribute("data-id");
        var easyFilename = id && catalog[id + "_easy_read"];
        var filename = id && (mode === "easy" && easyFilename ? easyFilename : catalog[id]);
        if (filename && !filenames.includes(filename)) filenames.push(filename);
      });
      var durations = await Promise.all(filenames.map(function (filename) {
        return mediaDuration("./content/i18n/" + lang + "/audio/" + filename);
      }));
      var offset = 0;
      var nextTimeline = new Map();
      filenames.forEach(function (filename, index) {
        var duration = durations[index];
        nextTimeline.set(filename, { offset: offset, duration: duration });
        offset += duration;
      });
      if (generation !== timelineGeneration) return;
      timeline = nextTimeline;
      totalAudioDuration = offset;
      syncNow(true);
    })().catch(function (error) {
      console.warn("[accessibility-sync] timeline unavailable", error);
    });
    return timelinePromise;
  }

  function ensureTimelineForAudio(audio) {
    var filename = filenameFromUrl(audio && (audio.currentSrc || audio.src));
    var mode = filename.includes("_easy_read") ? "easy" : "standard";
    return buildTimeline(mode);
  }

  function desiredVideoTime() {
    if (!activeAudio || !signVideo || !signVideo.duration || !totalAudioDuration) return null;
    var item = timeline.get(filenameFromUrl(activeAudio.currentSrc || activeAudio.src));
    if (!item) return null;
    var elapsed = Math.min(totalAudioDuration, item.offset + activeAudio.currentTime);
    return (elapsed / totalAudioDuration) * signVideo.duration;
  }

  function syncNow(force) {
    if (!activeAudio || !signVideo) return;
    signVideo.muted = true;
    signVideo.defaultMuted = true;
    signVideo.playbackRate = activeAudio.playbackRate || 1;
    var desired = desiredVideoTime();
    if (desired !== null && (force || Math.abs(signVideo.currentTime - desired) > 0.45)) {
      try { signVideo.currentTime = desired; } catch (_) {}
    }
  }

  function resumeSignVideo() {
    window.clearTimeout(resumeTimer);
    resumeTimer = window.setTimeout(function () {
      if (!activeAudio || activeAudio.paused || !signVideo) return;
      syncNow(true);
      signVideo.play().catch(function () {});
    }, 0);
  }

  function attachAudio(audio) {
    activeAudio = audio;
    audio.addEventListener("loadedmetadata", function () {
      ensureTimelineForAudio(audio);
      syncNow(true);
    });
    audio.addEventListener("play", function () {
      activeAudio = audio;
      ensureTimelineForAudio(audio);
      resumeSignVideo();
    });
    audio.addEventListener("timeupdate", function () { syncNow(false); });
    audio.addEventListener("ratechange", function () { syncNow(false); });
    audio.addEventListener("pause", function () {
      if (!audio.ended) signVideo && signVideo.pause();
    });
    audio.addEventListener("ended", function () { signVideo && signVideo.pause(); });
    return audio;
  }

  function TrackedAudio(src) {
    return attachAudio(new NativeAudio(src));
  }
  TrackedAudio.prototype = NativeAudio.prototype;
  Object.setPrototypeOf(TrackedAudio, NativeAudio);
  window.Audio = TrackedAudio;

  function attachVideo(video) {
    if (video.dataset.accessibilitySyncAttached === "true") return;
    video.dataset.accessibilitySyncAttached = "true";
    video.setAttribute("aria-label", "Video ya lugha ya ishara iliyosawazishwa na sauti na maandishi");
    video.muted = true;
    video.defaultMuted = true;
    video.addEventListener("play", function (event) {
      // Prevent the runtime's mutual-exclusion handler from stopping TTS.
      event.stopPropagation();
      if (activeAudio && !activeAudio.paused) syncNow(true);
    }, true);
    video.addEventListener("loadedmetadata", function () {
      signVideo = video;
      if (activeAudio) ensureTimelineForAudio(activeAudio);
      else buildTimeline("standard");
      if (activeAudio && !activeAudio.paused) resumeSignVideo();
    });
    signVideo = video;
  }

  new MutationObserver(function () {
    document.querySelectorAll("video").forEach(attachVideo);
  }).observe(document.documentElement, { childList: true, subtree: true });

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("video").forEach(attachVideo);
    buildTimeline("standard");
  });
})();
