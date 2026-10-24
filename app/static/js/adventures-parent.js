"use strict";

(() => {
  const panel = document.getElementById("adventures-panel");
  const errorLabel = document.getElementById("parent-adventure-error");
  const status = document.getElementById("parent-adventure-status");
  let initialized = false;
  let timer = null;
  let saved = false;
  let currentMode = "";

  async function request(body) {
    const response = await fetch("/api/parent/adventures", body ? {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content },
      body: JSON.stringify(body),
    } : { cache: "no-store" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Adventure controls could not connect.");
    return data;
  }

  async function refresh() {
    const data = await request();
    currentMode = data.playback.mode;
    if (!initialized) {
      document.getElementById("adventure-count").value = data.settings.rescue_max;
      document.getElementById("adventure-memory").value = data.settings.bag_size;
      document.getElementById("adventure-spoken").checked = data.settings.spoken;
      const container = document.getElementById("parent-adventure-games");
      container.replaceChildren();
      for (const game of data.games) {
        const row = document.createElement("label");
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.value = game.id;
        checkbox.checked = data.settings.enabled.includes(game.id);
        const name = document.createElement("span");
        name.textContent = game.name;
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = "Start";
        button.setAttribute("aria-label", `Start ${game.name}`);
        button.disabled = !data.settings.enabled.includes(game.id);
        button.addEventListener("click", (event) => {
          event.preventDefault();
          action({ action: "start", id: game.id }, button);
        });
        row.append(checkbox, name, button);
        container.append(row);
      }
      initialized = true;
    }
    const game = data.playback.adventure;
    status.textContent = (saved ? "Settings saved. " : "") + (game
      ? `${game.name}: ${game.prompt}`
      : data.playback.mode === "adventure-menu" ? "Game choices are on the TV." : "No adventure running.");
    panel.querySelector('[data-adventure-action="close"]').disabled = !["adventure", "adventure-menu"].includes(data.playback.mode);
    document.getElementById("food-time").setAttribute("aria-pressed", String(data.playback.mode === "food"));
  }

  async function action(body, button) {
    button.disabled = true;
    errorLabel.textContent = "";
    try {
      await request(body);
      if (body.action === "settings") {
        initialized = false;
        saved = true;
      }
      await refresh();
    } catch (error) {
      errorLabel.textContent = error.message;
    } finally {
      if (button.isConnected) {
        button.disabled = button.dataset.adventureAction === "close" &&
          !["adventure", "adventure-menu"].includes(currentMode);
      }
    }
  }

  async function poll() {
    if (panel.hidden) return;
    try { await refresh(); }
    catch (error) { errorLabel.textContent = error.message; }
    finally { if (!panel.hidden) timer = setTimeout(poll, 1000); }
  }

  document.getElementById("open-adventures").addEventListener("click", (event) => {
    panel.hidden = !panel.hidden;
    event.currentTarget.setAttribute("aria-expanded", String(!panel.hidden));
    clearTimeout(timer);
    if (!panel.hidden) poll();
  });
  document.getElementById("adventure-settings").addEventListener("submit", (event) => {
    event.preventDefault();
    action({ action: "settings", settings: {
      rescue_max: Number(document.getElementById("adventure-count").value),
      bag_size: Number(document.getElementById("adventure-memory").value),
      spoken: document.getElementById("adventure-spoken").checked,
      enabled: [...panel.querySelectorAll('#parent-adventure-games input:checked')].map((checkbox) => checkbox.value),
    } }, event.currentTarget.querySelector('button[type="submit"]'));
  });
  panel.querySelectorAll("[data-adventure-action]").forEach((button) => {
    button.addEventListener("click", () => action({ action: button.dataset.adventureAction }, button));
  });
})();
