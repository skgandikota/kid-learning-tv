"use strict";

const screenIds = ["home-screen", "choice-screen", "play-screen", "locked-screen", "rocky-screen", "video-screen", "learning-screen"];
const video = document.getElementById("video-player");
let appState = null;
let rockyTimer = null;
let lastSpoken = "";
let lastMediaSource = "";
let lastMediaCommand = -1;
let lastProgressSent = 0;
let lastTimerStart = null;
let breakActionSent = false;

async function childAction(action, data = {}) {
  const response = await fetch("/api/child/action", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, ...data }),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "That action did not work.");
  if (result.state) render(result.state);
  return result;
}

function makeButton(label, action, data = {}, className = "activity-card") {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.textContent = label;
  button.dataset.action = action;
  Object.entries(data).forEach(([key, value]) => { button.dataset[key] = value; });
  return button;
}

function showChoices(title, choices) {
  document.getElementById("home-screen").classList.add("hidden");
  document.getElementById("play-screen").classList.add("hidden");
  document.getElementById("choice-screen").classList.remove("hidden");
  document.getElementById("choice-title").textContent = title;
  const cards = document.getElementById("choice-cards");
  cards.replaceChildren();
  choices.forEach((choice) => cards.appendChild(choice));
}

function showCategoryChoices(kind) {
  if (!appState) return;
  if (kind === "avocado") {
    showChoices("Choose a category", appState.categories.map((item) =>
      makeButton(item.name, "start_avocado", { categoryId: item.id })));
  } else {
    showChoices("Choose a Memory Chain", appState.memory_categories.map((item) =>
      makeButton(item.name, "start_memory", { categoryId: item.id })));
  }
}

const activities = [
  { title: "ABC and phonics", ids: ["letter-b"] },
  { title: "Numbers and counting", ids: ["count-blue-blocks"] },
  { title: "Colours and shapes", ids: ["find-yellow", "red-circle"] },
  { title: "Animals", ids: ["animal-fact"] },
  { title: "Stories", ids: ["story-time"] },
  { title: "Music and movement", ids: ["clap-five", "elephant-move"] },
];

function buildHome() {
  const cards = document.getElementById("home-cards");
  cards.replaceChildren();
  cards.appendChild(makeButton("Avocado", "show-avocado"));
  cards.appendChild(makeButton("Memory Chain", "show-memory"));
  for (const group of activities) {
    const prompt = (appState?.prompts || []).find((item) => group.ids.includes(item.id));
    if (prompt) cards.appendChild(makeButton(group.title, "activity", { promptId: prompt.id }));
  }
  cards.appendChild(makeButton("Parent-selected activity", "parent-activity"));
}

function speakLocally(text) {
  if (!text || !("speechSynthesis" in window)) return false;
  const voices = window.speechSynthesis.getVoices();
  const voice = voices.find((item) => item.localService && item.lang.toLowerCase().startsWith("en-gb"))
    || voices.find((item) => item.localService && item.lang.toLowerCase().startsWith("en"));
  if (!voice) return false;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.voice = voice;
  utterance.rate = 0.9;
  window.speechSynthesis.speak(utterance);
  return true;
}

function beep() {
  try {
    const Audio = window.AudioContext || window.webkitAudioContext;
    if (!Audio) return;
    const context = new Audio();
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.frequency.value = 880;
    gain.gain.value = 0.08;
    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.start();
    oscillator.stop(context.currentTime + 0.16);
    oscillator.onended = () => context.close();
  } catch (_) {
    // The visual cue remains available if browser audio is unavailable.
  }
}

function makeAnswerForm(kind) {
  const wrapper = document.createElement("form");
  wrapper.className = "answer-form";
  const input = document.createElement("input");
  input.className = "large-input";
  input.autocomplete = "off";
  input.maxLength = kind === "memory_answer" ? 300 : 100;
  input.placeholder = kind === "memory_answer" ? "Repeat the list, then add one item" : "A grown-up can help type your answer";
  input.setAttribute("aria-label", input.placeholder);
  const button = document.createElement("button");
  button.type = "submit";
  button.className = "primary-button";
  button.textContent = kind === "memory_answer" ? "Check my list" : "That's my answer";
  wrapper.append(input, button);
  wrapper.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await childAction(kind, { text: input.value });
      input.value = "";
      input.focus();
    } catch (error) {
      document.getElementById("message").textContent = error.message;
    }
  });
  return wrapper;
}

function updateVideo(state) {
  const active = state.screen === "video" && state.media_id;
  document.body.classList.toggle("video-active", Boolean(active));
  if (!active) {
    document.getElementById("video-screen").classList.add("hidden");
    if (!video.paused) video.pause();
    if (lastMediaSource) {
      video.removeAttribute("src");
      video.load();
      lastMediaSource = "";
      lastMediaCommand = -1;
    }
    return;
  }
  document.getElementById("video-screen").classList.remove("hidden");
  document.getElementById("video-caption").textContent = state.media_title || "";
  const source = `/api/media/${encodeURIComponent(state.media_id)}`;
  const newSource = source !== lastMediaSource;
  if (newSource) {
    lastMediaSource = source;
    video.src = source;
    video.load();
    lastMediaCommand = -1;
  }
  const commandSeq = Number(state.media_command_seq || 0);
  if (commandSeq !== lastMediaCommand || newSource) {
    lastMediaCommand = commandSeq;
    if (state.media_command === "pause") video.pause();
    else if (state.media_command === "seek") {
      try { video.currentTime = Number(state.media_position || 0); } catch (_) { /* Metadata may not be ready yet. */ }
      video.play().catch(() => {});
    } else if (state.media_command === "stop") video.pause();
    else video.play().catch(() => {});
  }
}

function render(state) {
  appState = state;
  if (!state) return;
  document.body.classList.toggle("parent-managed", Boolean(state.parent_managed_activity));
  renderLearning(state);
  buildHome();
  screenIds.forEach((id) => document.getElementById(id).classList.add("hidden"));
  if (state.screen === "video") {
    document.getElementById("video-screen").classList.remove("hidden");
    updateVideo(state);
    return;
  }
  updateVideo(state);
  if (state.screen === "learning") {
    document.getElementById("learning-screen").classList.remove("hidden");
  } else if (state.screen === "locked") {
    document.getElementById("locked-screen").classList.remove("hidden");
  } else if (state.screen === "ask-rocky") {
    document.getElementById("rocky-screen").classList.remove("hidden");
    document.getElementById("rocky-title").textContent = state.rocky_reply ? "Rocky got back to you!" : "Ask Rocky";
    document.getElementById("rocky-message").textContent = state.message || "";
    document.getElementById("listening-indicator").classList.toggle("hidden", !state.rocky_request_open);
    document.getElementById("rocky-done").textContent = state.rocky_request_open ? "I'm finished" : "Back home";
    if (state.rocky_request_open && !rockyTimer) {
      rockyTimer = window.setTimeout(() => {
        rockyTimer = null;
        childAction("rocky_close").catch(() => {});
      }, 25000);
    } else if (!state.rocky_request_open && rockyTimer) {
      clearTimeout(rockyTimer);
      rockyTimer = null;
    }
  } else if (state.screen === "home") {
    document.getElementById("home-screen").classList.remove("hidden");
  } else {
    document.getElementById("play-screen").classList.remove("hidden");
    document.getElementById("screen-title").textContent = state.category_name || state.activity || "Let's play";
    document.getElementById("message").textContent = state.message || "";
    document.getElementById("current-activity").textContent = state.game_state === "confirmation"
      ? "A grown-up is checking that answer."
      : (state.game_state === "ended" ? "Round complete" : "");
    const activityImage = document.getElementById("activity-image");
    const safeImage = typeof state.activity_image === "string"
      && /^\/static\/images\/[a-z0-9-]+\.svg$/.test(state.activity_image);
    activityImage.classList.toggle("hidden", !safeImage);
    if (safeImage) {
      activityImage.src = state.activity_image;
      activityImage.alt = `${state.activity || "Activity"} picture`;
    }
    const area = document.getElementById("input-area");
    area.replaceChildren();
    if (state.game === "avocado" && ["child_turn", "confirmation"].includes(state.game_state)) {
      area.appendChild(makeAnswerForm("answer"));
    } else if (state.game === "memory" && state.game_state === "child_turn") {
      area.appendChild(makeAnswerForm("memory_answer"));
      if (state.memory_picture_visible) {
        const pictures = document.createElement("div");
        pictures.className = "memory-picture-row";
        (state.memory_sequence || []).forEach((item) => {
          const card = document.createElement("span");
          card.textContent = item;
          pictures.appendChild(card);
        });
        area.appendChild(pictures);
        window.setTimeout(() => {
          if (appState?.game === "memory" && appState.memory_picture_visible) {
            childAction("hide_memory_pictures").catch(() => {});
          }
        }, Math.max(0, Number(state.memory_picture_seconds || 4)) * 1000);
      }
    }
    const used = document.getElementById("used-answers");
    used.replaceChildren();
    (state.used_answers || []).forEach((answer) => {
      const item = document.createElement("li");
      item.textContent = answer;
      used.appendChild(item);
    });
    const nickname = document.getElementById("nickname");
    nickname.textContent = state.nickname || "";
    nickname.classList.toggle("hidden", !state.nickname);
  }
  document.getElementById("connection-status").textContent = "Connected to this device";
  document.body.classList.toggle("low-animation", Boolean(state.low_animation));
  if (
    state.message && state.message !== lastSpoken && state.voice_enabled === false
    && !state.muted && !state.paused && !state.locked
    && state.screen !== "home" && state.screen !== "video"
  ) {
    if (speakLocally(state.message)) lastSpoken = state.message;
  }
}

document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const action = button.dataset.action;
  if (appState?.parent_managed_activity) return;
  try {
    if (action === "show-avocado") return showCategoryChoices("avocado");
    if (action === "show-memory") return showCategoryChoices("memory");
    if (action === "parent-activity") {
      document.getElementById("message").textContent = "Ask a grown-up to choose an activity on their phone.";
      document.getElementById("play-screen").classList.remove("hidden");
      document.getElementById("home-screen").classList.add("hidden");
      return;
    }
    if (action === "rocky_request") beep();
    if (action === "activity") {
      await childAction(action, { prompt_id: button.dataset.promptId });
    } else if (action === "start_avocado" || action === "start_memory") {
      await childAction(action, { category_id: button.dataset.categoryId });
      document.getElementById("choice-screen").classList.add("hidden");
    } else {
      await childAction(action);
    }
  } catch (error) {
    document.getElementById("connection-status").textContent = error.message;
  }
});

document.getElementById("rocky-done").addEventListener("click", () => {
  if (rockyTimer) clearTimeout(rockyTimer);
  rockyTimer = null;
  childAction("rocky_done").catch(() => {});
});

video.addEventListener("ended", () => {
  if (appState?.media_id) childAction("video_ended", { media_id: appState.media_id }).catch(() => {});
});
video.addEventListener("loadstart", () => {
  document.getElementById("video-loading").classList.remove("hidden");
});
video.addEventListener("progress", () => {
  if (!Number.isFinite(video.duration) || video.duration <= 0 || !video.buffered.length) return;
  const percent = Math.min(100, Math.round(video.buffered.end(video.buffered.length - 1) / video.duration * 100));
  document.getElementById("video-loading-progress").value = percent;
  document.getElementById("video-loading-percent").textContent = `${percent}%`;
});
video.addEventListener("playing", () => {
  document.getElementById("video-loading").classList.add("hidden");
});
video.addEventListener("waiting", () => {
  document.getElementById("video-loading").classList.remove("hidden");
});
video.addEventListener("error", () => {
  document.getElementById("video-loading").classList.remove("hidden");
  document.getElementById("video-loading").querySelector("p").textContent =
    "This video could not play. Ask a grown-up to check the file.";
});
video.addEventListener("timeupdate", () => {
  const now = Date.now();
  if (!appState?.media_id || now - lastProgressSent < 5000) return;
  lastProgressSent = now;
  fetch("/api/child/media-progress", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ media_id: appState.media_id, seconds: video.currentTime }),
  }).catch(() => {});
});
video.addEventListener("contextmenu", (event) => event.preventDefault());
video.addEventListener("keydown", (event) => event.preventDefault());
document.addEventListener("keydown", (event) => {
  if (appState?.screen === "video") event.preventDefault();
});

window.setInterval(() => {
  if (!appState?.session_started_at || appState.locked || appState.break_mode) return;
  if (lastTimerStart !== appState.session_started_at) {
    lastTimerStart = appState.session_started_at;
    breakActionSent = false;
  }
  const elapsed = Math.max(0, Math.floor(Date.now() / 1000 - appState.session_started_at));
  const limit = Number(appState.session_limit_seconds || 0);
  const reminder = Number(appState.break_reminder_seconds || 0);
  if (!breakActionSent && limit > 0 && elapsed >= limit) {
    breakActionSent = true;
    childAction("session_break").catch(() => {});
  } else if (!breakActionSent && !appState.break_prompted && reminder > 0 && elapsed >= reminder) {
    breakActionSent = true;
    childAction("session_reminder").catch(() => {});
  }
}, 1000);

fetch("/api/state").then((response) => response.json()).then(render).catch(() => {
  document.getElementById("connection-status").textContent = "The local app is starting. Please wait.";
});
const events = new EventSource("/api/events");
events.onmessage = (message) => {
  try {
    const event = JSON.parse(message.data);
    if (event.payload && event.payload.screen) render(event.payload);
  } catch (_) { /* Ignore malformed local event frames and recover on the next update. */ }
};
events.onerror = () => { document.getElementById("connection-status").textContent = "Reconnecting to this device…"; };
