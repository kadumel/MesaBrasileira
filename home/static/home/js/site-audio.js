(function () {
  "use strict";

  const audio = document.querySelector("[data-site-audio]");
  if (!audio) return;

  const STORAGE_KEY = "mesa-samba";
  const VOLUME = 0.42;

  function getToggle() {
    return document.querySelector("[data-site-audio-toggle]");
  }

  function audioSrc() {
    const source = audio.querySelector("source");
    return (source && source.getAttribute("src")) || audio.currentSrc || "";
  }

  function readState() {
    try {
      return JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "{}");
    } catch (_) {
      return {};
    }
  }

  function writeState(patch) {
    try {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(Object.assign(readState(), patch, { src: audioSrc() }))
      );
    } catch (_) {}
  }

  function restoreTime() {
    const state = readState();
    const src = audioSrc();
    if (state.src && src && state.src !== src) return;
    if (typeof state.time === "number" && isFinite(state.time) && state.time > 0.4) {
      try {
        audio.currentTime = state.time;
      } catch (_) {}
    }
  }

  function persist(extra) {
    writeState(
      Object.assign({ time: audio.currentTime || 0 }, extra || {})
    );
  }

  function wantsPlay() {
    return readState().wantPlay !== false;
  }

  function isAudible() {
    return !audio.paused && !audio.muted && audio.volume > 0;
  }

  function syncToggle() {
    const toggle = getToggle();
    if (!toggle) return;
    const playing = !audio.paused;
    toggle.classList.toggle("is-playing", playing);
    toggle.setAttribute("aria-pressed", playing ? "true" : "false");
    toggle.setAttribute("aria-label", playing ? "Pausar música" : "Tocar música");
  }

  async function tryPlay() {
    audio.volume = VOLUME;
    try {
      audio.muted = false;
      await audio.play();
    } catch (_) {
      audio.muted = true;
      try {
        await audio.play();
        audio.muted = false;
      } catch (_) {}
    }
    persist({ wantPlay: true });
    syncToggle();
    if (audio.paused) {
      throw new Error("autoplay-blocked");
    }
  }

  function pauseForUser() {
    persist({ wantPlay: false });
    audio.pause();
    syncToggle();
  }

  function bindUnlock() {
    const unlock = (event) => {
      if (event && event.target && event.target.closest("[data-site-audio-toggle]")) {
        return;
      }
      window.removeEventListener("pointerdown", unlock);
      window.removeEventListener("keydown", unlock);
      if (!wantsPlay()) return;
      audio.muted = false;
      tryPlay().catch(() => {});
    };
    window.addEventListener("pointerdown", unlock, { passive: true });
    window.addEventListener("keydown", unlock);
  }

  audio.volume = VOLUME;
  audio.addEventListener("loadedmetadata", restoreTime, { once: true });
  if (audio.readyState >= 1) restoreTime();

  let lastPersist = 0;
  audio.addEventListener("timeupdate", () => {
    const now = Date.now();
    if (now - lastPersist < 800) return;
    lastPersist = now;
    persist();
  });

  window.addEventListener("pagehide", persist);
  window.addEventListener("beforeunload", persist);

  audio.addEventListener("play", syncToggle);
  audio.addEventListener("pause", syncToggle);

  document.addEventListener("click", (event) => {
    const toggle = event.target && event.target.closest
      ? event.target.closest("[data-site-audio-toggle]")
      : null;
    if (!toggle) return;
    event.preventDefault();
    if (audio.paused) {
      tryPlay().catch(() => bindUnlock());
    } else {
      pauseForUser();
    }
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", syncToggle);
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      persist();
      if (isAudible()) {
        audio.dataset.tabPause = "1";
        audio.pause();
      }
      return;
    }
    if (audio.dataset.tabPause === "1") {
      delete audio.dataset.tabPause;
      if (!wantsPlay()) {
        syncToggle();
        return;
      }
      tryPlay().catch(() => bindUnlock());
    }
  });

  syncToggle();

  if (!wantsPlay()) {
    audio.pause();
    syncToggle();
    return;
  }

  tryPlay()
    .then(() => {
      if (!isAudible()) bindUnlock();
    })
    .catch(bindUnlock);
})();
