"use strict";

let csrf = document.querySelector('meta[name="csrf-token"]').content;
let activeSettings = {};
let categoryData = [];
let nicknameData = [];
let liveState = {};
let mediaList = [];
let learningCatalog = [];

const byId = (id) => document.getElementById(id);
const notice = (message, error = false) => {
  byId("notice").textContent = message || "";
  byId("notice").style.color = error ? "#8d2635" : "#215d3b";
};
const authMessage = (message) => { byId("auth-message").textContent = message || ""; };

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  let data;
  try { data = await response.json(); } catch (_) { data = {}; }
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
  return data;
}

function csrfHeaders(json = true) {
  const headers = { "X-CSRF-Token": csrf };
  if (json) headers["Content-Type"] = "application/json";
  return headers;
}

async function action(name, extra = {}) {
  const data = await requestJson("/api/parent/action", {
    method: "POST", headers: csrfHeaders(), body: JSON.stringify({ action: name, ...extra }),
  });
  if (data.state) paintState(data.state);
  notice("Updated the TV.");
  return data;
}

function showControls() {
  byId("auth-panel").classList.add("hidden");
  byId("controls").classList.remove("hidden");
  loadDashboard().catch((error) => notice(error.message, true));
  startLiveUpdates();
}

async function loadDashboard() {
  const data = await requestJson("/api/parent/state");
  hostname = data.hostname;
  activeSettings = data.settings || {};
  learningCatalog = data.learning_catalog || [];
  paintState(data.state);
  byId("parent-url").textContent = data.configured_url;
  byId("parent-url").href = data.configured_url;
  byId("voice-enabled").checked = Boolean(activeSettings.voice_enabled);
  byId("voice-input-enabled").checked = Boolean(activeSettings.voice_input_enabled);
  byId("speech-rate").value = activeSettings.speech_rate || 145;
  byId("speech-voice").value = activeSettings.tts_voice || "en-gb";
  byId("volume").value = data.state.volume ?? activeSettings.volume ?? 70;
  byId("muted").checked = Boolean(data.state.muted);
  byId("session-minutes").value = activeSettings.session_minutes ?? 30;
  byId("history-enabled").checked = Boolean(activeSettings.history_enabled);
  byId("break-reminder").value = activeSettings.break_reminder_minutes ?? 20;
  byId("retry-count").value = activeSettings.retries ?? 1;
  byId("memory-level").value = activeSettings.memory_level ?? 1;
  byId("nicknames-enabled").checked = activeSettings.nicknames_enabled !== false;
  byId("low-animation").checked = Boolean(activeSettings.low_animation);
  byId("voice-status").textContent = data.state.voice_available
    ? `${data.state.voice_engine || "Local speech"} is available.`
    : "Natural speech setup is required; run the latest update.sh.";
  await Promise.all([loadCategories(), loadMedia()]);
}

function paintState(state) {
  liveState = state;
  paintLearningLibrary(state);
  byId("live-message").textContent = state.message || "Ready.";
  byId("live-state").textContent = `Activity: ${state.activity || "Home"} · State: ${state.game_state || "idle"}`;
  const list = byId("answers-list");
  list.replaceChildren();
  (state.used_answers || []).forEach((answer) => {
    const item = document.createElement("li");
    item.textContent = answer;
    list.appendChild(item);
  });
  byId("answer-tools").classList.toggle("hidden", state.game_state !== "confirmation");
  byId("pending-answer").textContent = state.pending_answer || "";
  byId("rocky-status").textContent = state.rocky_request_open
    ? "A child is leaving a pretend message now. No audio was recorded."
    : state.rocky_message_pending
      ? "A request is waiting for your reply."
      : "No new request.";
  byId("video-status").textContent = state.screen === "video"
    ? `${state.media_title || "Video"} · ${state.game_state || "playing"} · ${Math.floor(state.media_position || 0)} seconds`
    : "No video playing.";
  byId("video-position").value = Math.floor(state.media_position || 0);
  const device = byId("device-status");
  device.replaceChildren();
  [
    ["Device", dataHostname()],
    ["TV screen", state.screen || "home"],
    ["Activity", state.activity || "None"],
    ["Speech recognition", state.voice_input_enabled ? (state.voice_input_available ? "Local Whisper English" : "Voice setup required") : "Off"],
    ["Microphone", state.microphone_status || "Not connected"],
  ].forEach(([label, value]) => {
    const card = document.createElement("div");
    card.className = "status-item";
    const strong = document.createElement("strong");
    strong.textContent = `${label}: `;
    card.append(strong, document.createTextNode(value));
    device.appendChild(card);
  });
  byId("microphone-state").textContent = `Laptop microphone: ${state.microphone_status || "not connected"}. Audio is never saved.`;
}

let hostname = "local device";
function dataHostname() { return hostname; }

function paintLearningLibrary(state) {
  const library = byId("learning-library");
  library.replaceChildren();
  learningCatalog.forEach((item) => {
    const enabled = (state.enabled_learning_activities || []).includes(item.id);
    const card = document.createElement("div");
    card.className = "learning-library-item";
    const title = document.createElement("h3");
    title.textContent = item.name;
    const description = document.createElement("p");
    description.textContent = item.description;
    const label = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = enabled;
    checkbox.addEventListener("change", async () => {
      checkbox.disabled = true;
      try { await action("learning_enabled", { activity_id: item.id, enabled: checkbox.checked }); }
      catch (error) {
        notice(error.message, true);
        checkbox.checked = enabled;
        checkbox.disabled = false;
      }
    });
    label.append(checkbox, document.createTextNode(` Enable ${item.name}`));
    const play = document.createElement("button");
    play.type = "button";
    play.className = "primary-button";
    play.textContent = state.learning_game?.activity_id === item.id ? "Restart on TV" : "Play on TV";
    play.disabled = !enabled;
    play.dataset.action = "start_learning";
    play.dataset.activityId = item.id;
    card.append(title, description, label, play);
    library.appendChild(card);
  });
}

async function loadCategories() {
  const data = await requestJson("/api/parent/categories");
  categoryData = data.categories || [];
  nicknameData = data.nicknames || [];
  for (const selectId of ["category-select", "category-editor-select"]) {
    const select = byId(selectId);
    const previous = select.value;
    select.replaceChildren();
    categoryData.forEach((category) => {
      const option = document.createElement("option");
      option.value = category.id;
      option.textContent = category.name;
      select.appendChild(option);
    });
    if (previous) select.value = previous;
  }
  byId("memory-select").replaceChildren();
  (liveState.memory_categories || []).forEach((category) => {
    const option = document.createElement("option");
    option.value = category.id;
    option.textContent = category.name;
    byId("memory-select").appendChild(option);
  });
  byId("prompt-select").replaceChildren();
  (liveState.prompts || []).forEach((prompt) => {
    const option = document.createElement("option");
    option.value = prompt.id;
    option.textContent = prompt.name + ": " + prompt.prompt;
    byId("prompt-select").appendChild(option);
  });
  const toggles = byId("category-toggles");
  toggles.replaceChildren();
  categoryData.forEach((category) => {
    const label = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.dataset.categoryToggle = category.id;
    checkbox.checked = (activeSettings.enabled_categories || []).includes(category.id) && category.enabled !== false;
    label.append(checkbox, document.createTextNode(` ${category.name}`));
    toggles.appendChild(label);
  });
  if (!byId("category-editor").value) loadCategoryEditor();
  byId("nickname-editor").value = JSON.stringify(nicknameData, null, 2);
}

async function loadCategoryEditor() {
  const item = categoryData.find((category) => category.id === byId("category-editor-select").value)
    || categoryData[0];
  if (item) {
    byId("category-editor-select").value = item.id;
    byId("category-editor").value = JSON.stringify(item, null, 2);
  }
}

async function loadMedia() {
  const data = await requestJson("/api/parent/media");
  mediaList = data.videos || [];
  const select = byId("video-select");
  const previous = select.value;
  select.replaceChildren();
  mediaList.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = item.title;
    select.appendChild(option);
  });
  if (previous) select.value = previous;
}

function startLiveUpdates() {
  const events = new EventSource("/api/parent/events");
  events.onmessage = (message) => {
    try {
      const event = JSON.parse(message.data);
      if (event.payload && event.payload.screen) paintState(event.payload);
      if (event.type === "MEDIA_LIBRARY_CHANGED" || event.type === "CONTENT_CHANGED") {
        loadMedia().catch(() => {});
        loadCategories().catch(() => {});
      }
    } catch (_) { /* A later full state refresh repairs missed updates. */ }
  };
  events.onerror = () => { notice("Reconnecting to the TV…"); };
}

byId("auth-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  authMessage("");
  const pin = byId("pin-input").value;
  const configured = byId("auth-form").dataset.configured === "true";
  try {
    const response = await requestJson(configured ? "/api/login" : "/api/setup", {
      method: "POST", headers: csrfHeaders(), body: JSON.stringify({ pin }),
    });
    csrf = response.csrf_token || csrf;
    document.querySelector('meta[name="csrf-token"]').content = csrf;
    showControls();
  } catch (error) { authMessage(error.message); }
});

document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const name = button.dataset.action;
  const extra = {};
  if (name === "start_avocado") extra.category_id = byId("category-select").value;
  if (name === "start_memory") extra.category_id = byId("memory-select").value;
  if (name === "activity") extra.prompt_id = byId("prompt-select").value;
  if (name === "answer") extra.text = byId("parent-answer").value;
  if (name === "memory_answer") extra.text = byId("memory-answer").value;
  if (name === "correct_answer") extra.text = byId("correct-answer").value;
  if (name === "rocky_reply") extra.text = byId("rocky-reply").value;
  if (name === "play_video") extra.media_id = byId("video-select").value;
  if (name === "start_learning") extra.activity_id = button.dataset.activityId;
  try {
    await action(name, extra);
    if (name === "answer") byId("parent-answer").value = "";
    if (name === "memory_answer") byId("memory-answer").value = "";
    if (name === "rocky_reply") byId("rocky-reply").value = "";
  } catch (error) { notice(error.message, true); }
});

byId("save-settings").addEventListener("click", async () => {
  const enabledCategories = [...document.querySelectorAll("[data-category-toggle]:checked")]
    .map((item) => item.dataset.categoryToggle);
  try {
    const response = await action("settings", { settings: {
      enabled_categories: enabledCategories,
      voice_enabled: byId("voice-enabled").checked,
      voice_input_enabled: byId("voice-input-enabled").checked,
      speech_rate: Number(byId("speech-rate").value),
      tts_voice: byId("speech-voice").value,
      session_minutes: Number(byId("session-minutes").value),
      break_reminder_minutes: Number(byId("break-reminder").value),
      retries: Number(byId("retry-count").value),
      memory_level: Number(byId("memory-level").value),
      nicknames_enabled: byId("nicknames-enabled").checked,
      low_animation: byId("low-animation").checked,
      history_enabled: byId("history-enabled").checked,
    } });
    activeSettings = response.state ? { ...activeSettings } : activeSettings;
    notice("Settings saved.");
    await loadDashboard();
  } catch (error) { notice(error.message, true); }
});

byId("volume").addEventListener("change", () => {
  action("set_volume", { volume: Number(byId("volume").value) }).catch((error) => notice(error.message, true));
});
byId("muted").addEventListener("change", () => {
  action("mute", { muted: byId("muted").checked }).catch((error) => notice(error.message, true));
});
byId("test-voice").addEventListener("click", async () => {
  try {
    const response = await action("test_voice");
    byId("voice-status").textContent = response.message || "Voice test started.";
  } catch (error) { byId("voice-status").textContent = error.message; }
});

byId("load-category").addEventListener("click", loadCategoryEditor);
byId("category-editor-select").addEventListener("change", loadCategoryEditor);
byId("save-category").addEventListener("click", async () => {
  try {
    const category = JSON.parse(byId("category-editor").value);
    await requestJson("/api/parent/categories", {
      method: "POST", headers: csrfHeaders(), body: JSON.stringify(category),
    });
    notice("Category validated and saved.");
    await loadCategories();
  } catch (error) { notice(error.message, true); }
});
byId("load-nicknames").addEventListener("click", () => {
  byId("nickname-editor").value = JSON.stringify(nicknameData, null, 2);
});
byId("save-nicknames").addEventListener("click", async () => {
  try {
    await requestJson("/api/parent/nicknames", {
      method: "POST", headers: csrfHeaders(), body: byId("nickname-editor").value,
    });
    notice("Nicknames validated and saved.");
    await loadCategories();
  } catch (error) { notice(error.message, true); }
});

byId("video-upload").addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = byId("video-file").files[0];
  if (!file) return notice("Choose a local video file first.", true);
  if (file.size > 256 * 1024 * 1024) return notice("Video must be 256 MB or smaller.", true);
  const form = new FormData();
  form.append("title", byId("video-title").value);
  form.append("video", file, file.name);
  const progress = byId("video-upload-progress");
  progress.classList.remove("hidden");
  progress.value = 0;
  byId("video-upload-status").textContent = "Sending video to the laptop: 0%";
  try {
    await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", "/api/parent/media/upload");
      xhr.setRequestHeader("X-CSRF-Token", csrf);
      xhr.upload.onprogress = (progressEvent) => {
        if (!progressEvent.lengthComputable) return;
        const percent = Math.round(progressEvent.loaded / progressEvent.total * 100);
        progress.value = percent;
        byId("video-upload-status").textContent = `Sending video to the laptop: ${percent}%`;
      };
      xhr.onload = () => {
        let result = {};
        try { result = JSON.parse(xhr.responseText); } catch (_) { /* Use a safe error below. */ }
        if (xhr.status < 200 || xhr.status >= 300) reject(new Error(result.error || `Upload failed (${xhr.status}).`));
        else resolve(result);
      };
      xhr.onerror = () => reject(new Error("Video upload was interrupted."));
      xhr.send(form);
    });
    byId("video-upload").reset();
    await loadMedia();
    progress.value = 100;
    byId("video-upload-status").textContent = "Video saved on the laptop.";
    notice("Local video added to the parent library.");
  } catch (error) {
    byId("video-upload-status").textContent = error.message;
    notice(error.message, true);
  }
});
byId("delete-video").addEventListener("click", async () => {
  const id = byId("video-select").value;
  if (!id || !window.confirm("Remove this saved video from the laptop?")) return;
  try {
    await requestJson(`/api/parent/media/${encodeURIComponent(id)}`, {
      method: "DELETE", headers: { "X-CSRF-Token": csrf },
    });
    await loadMedia();
    notice("Video removed.");
  } catch (error) { notice(error.message, true); }
});
byId("video-position").addEventListener("change", () => {
  action("media_seek", { seconds: Number(byId("video-position").value) }).catch((error) => notice(error.message, true));
});

byId("show-qr").addEventListener("click", () => {
  const image = byId("parent-qr");
  image.src = `/api/parent/qr?cache=${Date.now()}`;
  image.classList.remove("hidden");
});
byId("import-settings").addEventListener("click", async () => {
  const file = byId("settings-import").files[0];
  if (!file) return notice("Choose a settings JSON file.", true);
  try {
    const data = JSON.parse(await file.text());
    await requestJson("/api/parent/import", {
      method: "POST", headers: csrfHeaders(), body: JSON.stringify(data),
    });
    await loadDashboard();
    notice("Settings imported.");
  } catch (error) { notice(error.message, true); }
});
byId("delete-history").addEventListener("click", async () => {
  if (!window.confirm("Delete all saved child activity history? This cannot be undone.")) return;
  if (window.prompt("Type DELETE to confirm.") !== "DELETE") return;
  try {
    await requestJson("/api/parent/history/delete", {
      method: "POST", headers: csrfHeaders(), body: JSON.stringify({ confirmation: "DELETE" }),
    });
    notice("Child activity history deleted.");
  } catch (error) { notice(error.message, true); }
});
byId("change-pin").addEventListener("click", async () => {
  try {
    await requestJson("/api/parent/pin", {
      method: "POST", headers: csrfHeaders(),
      body: JSON.stringify({ old_pin: byId("old-pin").value, new_pin: byId("new-pin").value }),
    });
    byId("old-pin").value = "";
    byId("new-pin").value = "";
    notice("Parent PIN changed.");
  } catch (error) { notice(error.message, true); }
});
byId("logout").addEventListener("click", async () => {
  try {
    await requestJson("/api/logout", { method: "POST", headers: csrfHeaders(), body: "{}" });
    window.location.reload();
  } catch (error) { notice(error.message, true); }
});

requestJson("/api/parent/state").then((data) => {
  hostname = data.hostname;
  showControls();
}).catch(() => {});
