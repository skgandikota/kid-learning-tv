"use strict";

const panel = document.getElementById("videos-panel");
const videoError = document.getElementById("video-error");
const selected = [];
let library = [];
let playback = null;
let pollTimer = null;

function duration(seconds) {
  const total = Math.max(0, Math.ceil(seconds || 0));
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

async function videoRequest(path, body) {
  const response = await fetch(path, body === undefined ? { cache: "no-store" } : {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content,
    },
    body: JSON.stringify(body),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Video request failed.");
  return result;
}

async function action(button, callback) {
  videoError.textContent = "";
  button.disabled = true;
  try {
    await callback();
  } catch (error) {
    videoError.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

function renderSelection() {
  const list = document.getElementById("video-selection");
  list.replaceChildren();
  for (const id of selected) {
    const item = document.createElement("li");
    item.textContent = library.find((video) => video.id === id)?.title || "Video no longer in folder";
    list.append(item);
  }
  document.getElementById("play-selection").disabled = selected.length === 0;
  panel.querySelectorAll("[data-select-video]").forEach((button) => {
    const order = selected.indexOf(button.dataset.selectVideo);
    button.textContent = order < 0 ? "Select" : String(order + 1);
    button.setAttribute("aria-pressed", String(order >= 0));
  });
}

function renderLibrary() {
  const container = document.getElementById("video-library");
  container.replaceChildren();
  if (!library.length) container.textContent = "No videos yet. Download one above or add MP4/WebM files to the folder.";
  for (const item of library) {
    const row = document.createElement("div");
    row.className = "library-row";
    const name = document.createElement("span");
    name.textContent = item.error ? `${item.title}: ${item.error}` : `${item.title} (${duration(item.duration)})`;
    const select = document.createElement("button");
    select.type = "button";
    select.dataset.selectVideo = item.id;
    select.disabled = Boolean(item.error);
    select.setAttribute("aria-label", `Select ${item.title}`);
    select.addEventListener("click", () => {
      const index = selected.indexOf(item.id);
      if (index >= 0) selected.splice(index, 1);
      else if (selected.length < 50) selected.push(item.id);
      else videoError.textContent = "Select at most 50 videos.";
      renderSelection();
    });
    const play = document.createElement("button");
    play.type = "button";
    play.textContent = "Play";
    play.disabled = Boolean(item.error);
    play.setAttribute("aria-label", `Play ${item.title}`);
    play.addEventListener("click", () => action(play, () => startPlaylist([item.id])));
    row.append(name, select, play);
    container.append(row);
  }
  renderSelection();
}

function renderPlayback(state) {
  playback = state;
  document.getElementById("food-time").setAttribute("aria-pressed", String(state.mode === "food"));
  const controls = document.getElementById("playback-controls");
  controls.hidden = !["video", "finished"].includes(state.mode);
  const queue = document.getElementById("active-playlist");
  queue.replaceChildren();
  state.queue.forEach((item, index) => {
    const row = document.createElement("li");
    row.textContent = item.title;
    if (index === state.index && state.mode === "video") row.className = "current-video";
    queue.append(row);
  });
  const connected = state.tv_connected ? "" : "TV is not connected. Open/refresh the TV page on the laptop. ";
  document.getElementById("playback-status").textContent = state.mode === "finished"
    ? "Screen time finished." : `${connected}${state.buffering ? "Loading... " : ""}${state.paused ? "Paused. " : ""}${duration(state.remaining)} total remaining`;
  document.getElementById("playback-error").textContent = state.error;
  const seek = document.getElementById("video-seek");
  if (document.activeElement !== seek) {
    seek.max = state.current?.duration || 1;
    seek.value = state.position;
  }
  document.getElementById("video-times").textContent = `${duration(state.position)} / ${duration(state.current?.duration)}`;
  const pause = document.getElementById("pause-video");
  pause.dataset.videoAction = state.paused ? "resume" : "pause";
  pause.textContent = state.paused ? "Resume" : "Pause";
  controls.querySelectorAll("button, input").forEach((element) => {
    element.disabled = state.mode !== "video" && element.dataset.videoAction !== "stop";
  });
  const volume = document.getElementById("video-volume");
  if (document.activeElement !== volume) volume.value = Math.round(state.volume * 100);
  document.getElementById("mute-video").textContent = state.volume === 0 ? "Unmute" : "Mute";
}

function renderDownloads(jobs) {
  const container = document.getElementById("downloads");
  container.replaceChildren();
  for (const job of jobs) {
    const line = document.createElement("p");
    line.textContent = `${job.title}: ${job.status} ${Math.round(job.progress || 0)}%${job.error ? ` - ${job.error}` : ""}`;
    container.append(line);
  }
}

async function refreshVideos() {
  const data = await videoRequest("/api/parent/videos");
  document.getElementById("video-folder").textContent = `Laptop folder: ${data.folder}`;
  if (JSON.stringify(library) !== JSON.stringify(data.videos)) {
    library = data.videos;
    renderLibrary();
  }
  renderDownloads(data.downloads);
  renderPlayback(data.playback);
}

async function pollVideos() {
  if (panel.hidden) return;
  try {
    await refreshVideos();
    if (videoError.dataset.pollError === "true") {
      videoError.textContent = "";
      delete videoError.dataset.pollError;
    }
  } catch (error) {
    videoError.textContent = error.message;
    videoError.dataset.pollError = "true";
  } finally {
    if (!panel.hidden) pollTimer = setTimeout(pollVideos, 1000);
  }
}

async function startPlaylist(ids) {
  renderPlayback((await videoRequest("/api/parent/videos/play", { ids })).playback);
}

async function control(body) {
  renderPlayback((await videoRequest("/api/parent/videos/control", body)).playback);
}

document.getElementById("open-videos").addEventListener("click", (event) => {
  panel.hidden = !panel.hidden;
  event.currentTarget.setAttribute("aria-expanded", String(!panel.hidden));
  clearTimeout(pollTimer);
  if (!panel.hidden) pollVideos();
});
document.getElementById("download-video").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  action(form.querySelector("button"), async () => {
    await videoRequest("/api/parent/videos/download", {
      url: document.getElementById("youtube-url").value.trim(),
      title: document.getElementById("video-title").value.trim(),
    });
    form.reset();
    await refreshVideos();
  });
});
document.getElementById("play-selection").addEventListener("click", (event) => action(event.currentTarget, () => startPlaylist([...selected])));
document.getElementById("clear-selection").addEventListener("click", () => { selected.length = 0; renderSelection(); });
panel.querySelectorAll("[data-video-action]").forEach((button) => {
  button.addEventListener("click", () => action(button, () => control({ action: button.dataset.videoAction })));
});
document.getElementById("video-seek").addEventListener("change", (event) => {
  action(event.currentTarget, () => control({ action: "seek", position: Number(event.target.value) }));
});
document.getElementById("video-volume").addEventListener("change", (event) => {
  action(event.currentTarget, () => control({ action: "volume", volume: Number(event.target.value) / 100 }));
});
document.getElementById("mute-video").addEventListener("click", (event) => {
  action(event.currentTarget, () => control({ action: "volume", volume: playback?.volume === 0 ? 0.7 : 0 }));
});
