"use strict";

const picture = document.getElementById("food-time-image");
const endPicture = document.getElementById("screen-time-ended");
const video = document.getElementById("tv-video");
const overlay = document.getElementById("video-overlay");
const loading = document.getElementById("video-loading");
const countdown = document.getElementById("video-countdown");
const progress = document.getElementById("playlist-progress");
let state = null;
let sourceKey = "";
let appliedSeek = -1;
let buffering = false;
let reporting = false;
let loadingSource = false;
let playPending = false;

function clock(seconds) {
  const value = Math.max(0, Math.ceil(seconds));
  return `${Math.floor(value / 60)}:${String(value % 60).padStart(2, "0")}`;
}

async function report(event = "progress", error = "") {
  if (!state || reporting || loadingSource) return;
  reporting = true;
  const current = state;
  try {
    const response = await fetch("/api/tv/playback", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content,
      },
      body: JSON.stringify({
        session: current.session, revision: current.revision, event, error,
        position: current.mode === "video" && Number.isFinite(video.currentTime) ? video.currentTime : 0,
        buffering,
      }),
    });
    if (!response.ok && response.status !== 409) throw new Error(`TV report failed (${response.status}).`);
  } catch (failure) {
    console.error(failure);
  } finally {
    reporting = false;
  }
}

async function play() {
  if (playPending || !state || state.mode !== "video" || state.paused || !video.paused) return;
  playPending = true;
  const key = sourceKey;
  try {
    await video.play();
  } catch (error) {
    if (error.name !== "AbortError" && key === sourceKey && state?.mode === "video" && !state.paused) {
      await report("error", `Cannot start video: ${error.message} Open the TV in kiosk mode, then press Resume on your phone.`);
    }
  } finally {
    playPending = false;
  }
}

function apply(next) {
  if (!next || !Number.isInteger(next.revision)) throw new Error("Invalid display state.");
  if (state && next.session === state.session && next.revision < state.revision) return;
  state = next;
  window.dispatchEvent(new CustomEvent("tv-display", { detail: next }));
  picture.hidden = state.mode !== "food";
  endPicture.hidden = state.mode !== "finished";
  video.hidden = overlay.hidden = state.mode !== "video";
  if (state.mode !== "video") {
    video.pause();
    if (sourceKey) {
      sourceKey = "";
      video.removeAttribute("src");
      video.load();
    }
    loadingSource = false;
    buffering = false;
    return;
  }
  video.volume = state.volume;
  const key = `${state.session}:${state.index}`;
  if (key !== sourceKey) {
    sourceKey = key;
    appliedSeek = -1;
    loadingSource = buffering = true;
    video.src = `/api/videos/${encodeURIComponent(state.current.id)}`;
    video.load();
  }
  if (video.readyState >= 1 && state.seek_revision !== appliedSeek) {
    video.currentTime = Math.min(state.position, video.duration || state.current.duration);
    appliedSeek = state.seek_revision;
    loadingSource = false;
  }
  if (state.paused) video.pause();
  else if (!loadingSource) play();
}

video.addEventListener("loadedmetadata", () => {
  if (!state || state.mode !== "video") return;
  loadingSource = false;
  video.currentTime = Math.min(state.position, video.duration || state.current.duration);
  appliedSeek = state.seek_revision;
  if (!state.paused) play();
});
video.addEventListener("waiting", () => { buffering = true; });
video.addEventListener("seeking", () => { buffering = true; });
video.addEventListener("playing", () => { buffering = false; });
video.addEventListener("canplay", () => { buffering = false; });
video.addEventListener("ended", () => report("ended"));
video.addEventListener("error", () => {
  if (state?.mode !== "video") return;
  loadingSource = false;
  report("error", `Video could not load or decode (code ${video.error?.code || "unknown"}). Check its file/encoding on the laptop.`);
});
document.addEventListener("contextmenu", (event) => event.preventDefault());
document.addEventListener("keydown", (event) => {
  if (event.key !== "F11" && !["blank", "quiz-menu", "quiz", "matching", "typing-menu", "typing"].includes(state?.mode)) event.preventDefault();
});

async function updateDisplay() {
  try {
    const response = await fetch("/api/display", { cache: "no-store" });
    if (!response.ok) throw new Error(`TV display update failed (${response.status}).`);
    apply((await response.json()).playback);
  } catch (error) {
    console.error(error);
  } finally {
    setTimeout(updateDisplay, 500);
  }
}

setInterval(() => {
  if (!state || state.mode !== "video") return;
  const before = state.queue.slice(0, state.index).reduce((sum, item) => sum + item.duration, 0);
  const elapsed = before + (loadingSource ? state.position : video.currentTime);
  countdown.textContent = clock(state.total - elapsed);
  progress.value = state.total > 0 ? Math.min(1, elapsed / state.total) : 0;
  loading.hidden = !buffering;
}, 200);
setInterval(() => {
  report(state?.mode === "video" && video.ended && !state.paused ? "ended" : "progress");
}, 1000);
updateDisplay();
