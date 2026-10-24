"use strict";

(() => {
  const screen = document.getElementById("typing-screen");
  const menu = document.getElementById("typing-menu");
  const play = document.getElementById("typing-play");
  const letters = document.getElementById("typing-letters");
  const keyboard = document.getElementById("typing-keyboard");
  const hint = document.getElementById("typing-hint");
  const errorLabel = document.getElementById("typing-error");
  let game = null;
  let lessons = [];
  let category = "heroes";
  let busy = false;
  let audio = null;
  let cancelAudio = null;
  let controller = new AbortController();
  let currentMode = "";
  let navigating = false;

  function stopAudio() {
    controller.abort();
    controller = new AbortController();
    if (audio) {
      audio.pause();
      audio = null;
    }
    cancelAudio?.();
    cancelAudio = null;
  }

  function updateKeys() {
    const target = game?.item.word.replaceAll(" ", "") || "";
    const next = target[game?.position];
    for (const button of keyboard.querySelectorAll("button")) {
      button.disabled = busy || !game || game.complete;
      button.classList.toggle("next-key", button.textContent === next);
    }
    document.getElementById("typing-listen").disabled = busy;
  }

  function showHint(message) {
    if (!game) return;
    if (message) {
      hint.textContent = message;
      return;
    }
    if (game.complete) {
      hint.textContent = `You typed ${game.item.name}!`;
      return;
    }
    let end = 0;
    let group = "";
    for (const part of game.item.groups) {
      end += part.length;
      if (game.position < end) {
        group = part;
        break;
      }
    }
    const target = game.item.word.replaceAll(" ", "")[game.position];
    hint.textContent = group.length > 1
      ? `${group} work together. Type ${target}.`
      : `Type ${target}`;
  }

  async function sound(itemId, position, kind, token) {
    const abort = controller;
    const timeout = setTimeout(() => abort.abort(), 30000);
    let url = "";
    let player = null;
    let aborted = null;
    try {
      const response = await fetch(`/api/typing/audio/${encodeURIComponent(itemId)}/${position}/${kind}`, {
        signal: abort.signal,
      });
      if (!response.ok) throw new Error((await response.json()).error || "Typing sound could not load.");
      const blob = await response.blob();
      if (game?.token !== token || currentMode !== "typing" || abort.signal.aborted || navigating) return false;
      url = URL.createObjectURL(blob);
      player = new Audio(url);
      audio = player;
      await new Promise((resolve, reject) => {
        cancelAudio = resolve;
        aborted = () => { player.pause(); reject(new Error("Typing audio stopped or timed out.")); };
        abort.signal.addEventListener("abort", aborted, { once: true });
        player.onended = resolve;
        player.onerror = () => reject(new Error("Typing sound could not play. Check laptop volume and kiosk mode."));
        player.play().catch(reject);
      });
      return !abort.signal.aborted;
    } finally {
      clearTimeout(timeout);
      if (aborted) abort.signal.removeEventListener("abort", aborted);
      if (url) URL.revokeObjectURL(url);
      if (audio === player) {
        audio = null;
        cancelAudio = null;
      }
    }
  }

  async function say(kinds, token = game?.token, position = game?.position) {
    if (!game || game.token !== token) return;
    busy = true;
    if (controller.signal.aborted) controller = new AbortController();
    updateKeys();
    showHint("Listen...");
    const id = game.item.id;
    try {
      for (const kind of kinds) {
        if (game?.token !== token || currentMode !== "typing" || navigating) return;
        if (!await sound(id, ["name", "spell"].includes(kind) ? 0 : position, kind, token)) return;
      }
      if (kinds.includes("name") && game?.token === token && game.complete && currentMode === "typing" && !navigating) {
        await choose("advance", { token });
      }
    } catch (error) {
      if (game?.token === token && currentMode === "typing" && !navigating) {
        console.error("Hero Typing audio:", error);
        errorLabel.textContent = "Sound unavailable. Check eSpeak NG, laptop sound and the latest update, then press Hear again.";
      }
    } finally {
      if (game?.token === token) {
        busy = false;
        updateKeys();
        showHint();
      }
    }
  }

  async function command(action, extra = {}) {
    const response = await fetch("/api/child/typing", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content,
      },
      body: JSON.stringify({ action, ...extra }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Hero Typing connection failed.");
    apply(result.playback);
    return result;
  }

  async function choose(action, extra) {
    try {
      errorLabel.textContent = document.getElementById("home-game-error").textContent = "";
      await command(action, extra);
    } catch (error) {
      (screen.hidden ? document.getElementById("home-game-error") : errorLabel).textContent = error.message;
    }
  }

  async function navigate(action) {
    if (!game || navigating) return;
    navigating = true;
    stopAudio();
    try {
      await choose(action, { token: game.token });
    } finally {
      navigating = false;
      if (game && currentMode === "typing") say([game.complete ? "name" : "spell"]);
    }
  }

  async function type(key) {
    if (busy || navigating || !game || game.complete || currentMode !== "typing") return;
    const token = game.token;
    busy = true;
    updateKeys();
    errorLabel.textContent = "";
    try {
      const result = await command("key", { key, token, position: game.position });
      if (game?.token !== token || currentMode !== "typing") return;
      if (!result.accepted) {
        showHint(`Let's find ${game.item.word.replaceAll(" ", "")[game.position]}.`);
        return;
      }
      const kinds = [];
      if (result.sound) kinds.push("sound");
      if (result.blend) kinds.push("blend");
      if (game.complete) kinds.push("name");
      if (kinds.length) await say(kinds, token);
      else showHint();
    } catch (error) {
      if (game?.token === token) errorLabel.textContent = error.message;
    } finally {
      if (game?.token === token) {
        busy = false;
        updateKeys();
      }
    }
  }

  function renderLetters() {
    letters.replaceChildren();
    let index = 0;
    const groupEnds = [];
    let end = 0;
    for (const part of game.item.groups) {
      end += part.length;
      groupEnds.push(end);
    }
    for (const letter of game.item.word) {
      const span = document.createElement("span");
      span.textContent = letter === " " ? "\u00a0" : letter;
      if (letter === " ") {
        span.className = "typing-space";
      } else {
        span.className = index < game.position ? "typed-letter" : index === game.position ? "target-letter" : "";
        index += 1;
        if (groupEnds.includes(index)) span.classList.add("group-end");
      }
      letters.append(span);
    }
  }

  function renderChoices() {
    const container = document.getElementById("typing-choices");
    container.replaceChildren();
    for (const item of lessons.filter((entry) => entry.category === category)) {
      const button = document.createElement("button");
      button.className = "typing-choice";
      button.type = "button";
      const image = document.createElement("img");
      image.src = item.image;
      image.alt = "";
      const name = document.createElement("span");
      name.textContent = item.name;
      button.append(image, name);
      button.addEventListener("click", () => choose("start", { id: item.id }));
      container.append(button);
    }
    document.getElementById("typing-heroes-tab").setAttribute("aria-pressed", String(category === "heroes"));
    document.getElementById("typing-words-tab").setAttribute("aria-pressed", String(category === "words"));
  }

  async function loadCatalog() {
    if (lessons.length) return;
    const response = await fetch("/api/typing/catalog");
    if (!response.ok) throw new Error("Hero choices could not load. Close and try again.");
    lessons = (await response.json()).lessons;
    renderChoices();
  }

  window.addEventListener("tv-display", (event) => {
    const state = event.detail;
    currentMode = state.mode;
    screen.hidden = !["typing-menu", "typing"].includes(state.mode);
    if (state.mode !== "typing") {
      stopAudio();
      game = null;
      busy = false;
      if (state.mode === "typing-menu") loadCatalog().catch((error) => { errorLabel.textContent = error.message; });
      menu.hidden = state.mode !== "typing-menu";
      play.hidden = true;
      return;
    }
    const next = state.typing;
    if (!next || (game?.token === next.token && next.position < game.position)) return;
    const fresh = game?.token !== next.token;
    if (fresh) {
      stopAudio();
      busy = false;
      errorLabel.textContent = "";
    }
    game = next;
    menu.hidden = true;
    play.hidden = false;
    screen.classList.toggle("typing-success", game.complete);
    document.getElementById("typing-picture").src = game.item.image;
    document.getElementById("typing-character-name").textContent = game.item.name;
    renderLetters();
    document.getElementById("typing-celebration").hidden = !game.complete;
    updateKeys();
    if (!busy) showHint();
    if (fresh && !navigating) say([game.complete ? "name" : "spell"]);
  });

  for (const row of ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]) {
    const container = document.createElement("div");
    for (const key of row) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = key;
      button.setAttribute("aria-label", `Type ${key}`);
      button.addEventListener("click", () => type(key));
      container.append(button);
    }
    keyboard.append(container);
  }
  document.addEventListener("keydown", (event) => {
    if (currentMode !== "typing" || event.ctrlKey || event.altKey || event.metaKey) return;
    if (/^[a-z]$/i.test(event.key)) {
      event.preventDefault();
      if (!event.repeat) type(event.key);
    }
  });
  document.getElementById("typing-picture").addEventListener("error", () => {
    errorLabel.textContent = "This picture could not load. Choose another name or reload the TV.";
  });
  document.getElementById("typing-launcher").addEventListener("click", () => choose("menu"));
  document.getElementById("typing-close").addEventListener("click", () => choose("close"));
  document.getElementById("typing-choose").addEventListener("click", () => choose("menu"));
  document.getElementById("typing-next").addEventListener("click", () => navigate("next"));
  document.getElementById("typing-previous").addEventListener("click", () => navigate("previous"));
  document.getElementById("typing-listen").addEventListener("click", () => {
    errorLabel.textContent = "";
    say([game.complete ? "name" : "spell"]);
  });
  for (const [id, value] of [["typing-heroes-tab", "heroes"], ["typing-words-tab", "words"]]) {
    document.getElementById(id).addEventListener("click", () => { category = value; renderChoices(); });
  }
})();
