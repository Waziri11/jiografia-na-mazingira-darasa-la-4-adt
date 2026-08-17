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
  var settleTimer = 0;
  var pauseTimer = 0;
  var syncFrame = 0;

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

  function isNarrationAudio(audio) {
    var source = audio && (audio.currentSrc || audio.src) || "";
    return /\/content\/i18n\/[^/]+\/audio\//.test(source);
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
    return Math.min(signVideo.duration, elapsed);
  }

  function expectedVideoRate() {
    return activeAudio && activeAudio.playbackRate || 1;
  }

  function syncNow(hardSeek) {
    if (!activeAudio || !signVideo) return;
    signVideo.muted = true;
    signVideo.defaultMuted = true;
    var desired = desiredVideoTime();
    if (desired === null) return;

    var drift = desired - signVideo.currentTime;
    var baseRate = expectedVideoRate();

    // Seeking on every audio `timeupdate` makes the video decoder continually
    // discard frames. Seek only after a real timeline jump; correct ordinary
    // clock drift with a small, temporary playback-rate adjustment instead.
    if (hardSeek || Math.abs(drift) > 2) {
      try { signVideo.currentTime = desired; } catch (_) {}
      signVideo.playbackRate = Math.max(0.25, Math.min(4, baseRate));
      return;
    }

    var correction = Math.max(-0.08, Math.min(0.08, drift * 0.04));
    signVideo.playbackRate = Math.max(0.25, Math.min(4, baseRate * (1 + correction)));
  }

  function stopSyncLoop() {
    if (!syncFrame) return;
    window.cancelAnimationFrame(syncFrame);
    syncFrame = 0;
  }

  function startSyncLoop() {
    stopSyncLoop();
    var tick = function () {
      if (!activeAudio || activeAudio.paused || !signVideo) {
        syncFrame = 0;
        return;
      }
      syncNow(false);
      syncFrame = window.requestAnimationFrame(tick);
    };
    syncFrame = window.requestAnimationFrame(tick);
  }

  function resumeSignVideo() {
    window.clearTimeout(resumeTimer);
    window.clearTimeout(settleTimer);
    var resume = function () {
      if (!activeAudio || activeAudio.paused || !signVideo) return;
      syncNow(true);
      signVideo.play().then(startSyncLoop).catch(function () {});
    };
    resumeTimer = window.setTimeout(resume, 0);
    // The runtime marks TTS active in the microtask after audio.play(). That
    // state update can replace or pause the video after the first attempt.
    settleTimer = window.setTimeout(resume, 200);
  }

  function attachAudio(audio) {
    audio.addEventListener("loadedmetadata", function () {
      if (!isNarrationAudio(audio)) return;
      activeAudio = audio;
      ensureTimelineForAudio(audio);
      syncNow(true);
    });
    audio.addEventListener("play", function () {
      if (!isNarrationAudio(audio)) return;
      window.clearTimeout(pauseTimer);
      activeAudio = audio;
      ensureTimelineForAudio(audio);
      resumeSignVideo();
    });
    audio.addEventListener("ratechange", function () {
      if (audio === activeAudio) syncNow(false);
    });
    audio.addEventListener("pause", function () {
      if (audio !== activeAudio) return;
      stopSyncLoop();
      if (!audio.ended) signVideo && signVideo.pause();
    });
    audio.addEventListener("ended", function () {
      if (audio !== activeAudio) return;
      window.clearTimeout(pauseTimer);
      pauseTimer = window.setTimeout(function () {
        if (audio !== activeAudio || !audio.paused) return;
        stopSyncLoop();
        signVideo && signVideo.pause();
      }, 150);
    });
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
    var videoReady = function () {
      signVideo = video;
      if (activeAudio) ensureTimelineForAudio(activeAudio);
      else buildTimeline("standard");
      if (activeAudio && !activeAudio.paused) resumeSignVideo();
    };
    video.addEventListener("loadedmetadata", videoReady);
    signVideo = video;
    // A cached source can finish loading before MutationObserver attaches the
    // listener, especially when React replaces the video between audio clips.
    if (video.readyState >= 1) videoReady();
  }

  // Register before the compiled runtime. React delegates media events from an
  // ancestor, so stopping the event on the video itself is too late: the
  // runtime has already paused narration by then.
  document.addEventListener("play", function (event) {
    var video = event.target;
    if (!(video instanceof HTMLVideoElement)) return;
    event.stopImmediatePropagation();
    signVideo = video;
    video.muted = true;
    video.defaultMuted = true;
    if (activeAudio && !activeAudio.paused) syncNow(true);
  }, true);

  new MutationObserver(function () {
    document.querySelectorAll("video").forEach(attachVideo);
  }).observe(document.documentElement, { childList: true, subtree: true });

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("video").forEach(attachVideo);
    buildTimeline("standard");
  });
})();
