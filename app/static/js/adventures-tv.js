"use strict";

(() => {
  const screen = document.getElementById("adventure-screen");
  const menu = document.getElementById("adventure-menu");
  const play = document.getElementById("adventure-play");
  const scene = document.getElementById("adventure-scene");
  const choices = document.getElementById("adventure-choices");
  const errorLabel = document.getElementById("adventure-error");
  const prompt = document.getElementById("adventure-prompt");
  let game = null;
  let mode = "";
  let pending = false;
  let speaking = false;
  let abort = new AbortController();
  let player = null;
  let catalogRequest = 0;
  let menuRevision = -1;

  function cancel() {
    abort.abort();
    abort = new AbortController();
    player?.pause();
    player = null;
    speaking = false;
  }

  function lockChoices() {
    choices.querySelectorAll("button").forEach((button) => {
      button.disabled = pending || speaking || game?.phase !== "play" || button.dataset.picked === "true";
    });
    document.getElementById("adventure-hear").disabled = pending || speaking;
  }

  function image(item) {
    const img = document.createElement("img");
    img.src = item.image;
    img.alt = item.name;
    img.draggable = false;
    img.addEventListener("error", () => {
      errorLabel.textContent = "A picture could not load. Reload the TV or choose another game.";
    });
    return img;
  }

  function pictureCard(item) {
    const card = document.createElement("div");
    card.className = "adventure-picture";
    const name = document.createElement("span");
    name.textContent = item.name;
    card.append(image(item), name);
    return card;
  }

  function renderScene() {
    scene.replaceChildren();
    scene.className = `adventure-${game.id}`;
    screen.classList.toggle("adventure-success", ["success", "finished"].includes(game.phase));
    if (game.phase === "finished") {
      const star = document.createElement("img");
      star.src = "/static/images/adventure-adventure.svg";
      star.alt = "Adventure complete";
      star.className = "adventure-finale";
      scene.append(star);
      return;
    }
    if (game.id === "path") {
      for (const item of game.sequence) scene.append(pictureCard(item));
      const missing = document.createElement("span");
      missing.className = "adventure-missing";
      missing.textContent = "?";
      scene.append(missing);
    } else if (game.id === "bag" && game.phase === "preview") {
      game.memory.forEach((item) => scene.append(pictureCard(item)));
    } else if (game.id === "hiding") {
      const clue = image(game.clue);
      clue.className = game.phase === "success" ? "adventure-revealed" : "adventure-silhouette";
      if (game.phase !== "success") clue.alt = "A hidden animal";
      scene.append(clue);
    } else if (["vehicle", "robot"].includes(game.id)) {
      const construction = document.createElement("div");
      construction.className = `adventure-construction ${game.id}-construction`;
      const base = document.createElement("img");
      base.src = `/static/images/adventure-${game.id}-base.svg`;
      base.alt = game.id === "vehicle" ? "Your hero vehicle" : "Your silly robot";
      construction.append(base);
      for (const [part, count] of Object.entries(game.built)) {
        const layer = document.createElement("img");
        layer.src = `/static/images/adventure-${game.id}-${part}.svg`;
        layer.alt = `${count} ${part}`;
        layer.className = "adventure-layer";
        layer.dataset.count = count;
        construction.append(layer);
      }
      if (game.id === "vehicle" && game.built.triangle) construction.classList.add("adventure-drive");
      if (game.id === "robot" && game.built.leg === 2) construction.classList.add("adventure-dance");
      scene.append(construction);
    } else {
      const mascot = document.createElement("img");
      mascot.src = `/static/images/adventure-${game.id === "rescue" ? "adventure" : game.id}.svg`;
      mascot.alt = game.id === "monster" ? "Your friendly hungry monster" : game.id === "bag" ? "Your adventure bag" : "Your rescue badge";
      mascot.className = "adventure-mascot";
      scene.append(mascot);
      if (game.id !== "monster") {
        const count = document.createElement("span");
        count.className = "adventure-collected";
        count.textContent = `${game.collected} / ${game.quantity}`;
        count.setAttribute("aria-label", `${game.collected} of ${game.quantity} collected`);
        scene.append(count);
      } else if (game.phase === "success") {
        const food = game.choices.find((item) => item.id === game.last_choice);
        if (food) scene.append(pictureCard(food));
      }
    }
  }

  function render() {
    if (!game) return;
    document.getElementById("adventure-title").textContent = game.name;
    prompt.textContent = game.prompt;
    renderScene();
    choices.replaceChildren();
    choices.hidden = game.phase === "preview" || game.phase === "finished";
    for (const item of game.choices) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "adventure-choice";
      button.dataset.choice = item.id;
      button.dataset.picked = String(item.picked);
      button.setAttribute("aria-label", game.id === "rescue" ? `Rescue puppy ${Number(item.id.split("-")[1]) + 1}` : item.name);
      button.append(pictureCard(item));
      if (item.picked) button.classList.add("adventure-picked");
      button.addEventListener("click", () => send("pick", { choice: item.id }));
      choices.append(button);
    }
    document.getElementById("adventure-ready").hidden = game.phase !== "preview";
    document.getElementById("adventure-next").hidden = game.phase !== "success";
    document.getElementById("adventure-again").hidden = game.phase !== "finished";
    lockChoices();
  }

  function wait(milliseconds, signal) {
    return new Promise((resolve, reject) => {
      const stopped = () => { clearTimeout(timer); reject(new DOMException("Stopped", "AbortError")); };
      const timer = setTimeout(() => { signal.removeEventListener("abort", stopped); resolve(); }, milliseconds);
      signal.addEventListener("abort", stopped, { once: true });
      if (signal.aborted) stopped();
    });
  }

  async function voice(key, signal) {
    const response = await fetch(`/api/adventures/audio/${key}`, {
      signal: AbortSignal.any([signal, AbortSignal.timeout(45000)]),
    });
    if (!response.ok) throw new Error((await response.json()).error || "Adventure voice could not load.");
    const blob = await response.blob();
    if (signal.aborted) throw new DOMException("Stopped", "AbortError");
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    player = audio;
    try {
      await new Promise((resolve, reject) => {
        const stop = () => { audio.pause(); finish(new DOMException("Stopped", "AbortError")); };
        const timeout = setTimeout(() => { audio.pause(); finish(new Error("Adventure voice timed out.")); }, 45000);
        function finish(error) {
          clearTimeout(timeout);
          signal.removeEventListener("abort", stop);
          if (error) reject(error); else resolve();
        }
        signal.addEventListener("abort", stop, { once: true });
        audio.onended = () => finish();
        audio.onerror = () => finish(new Error("Adventure voice could not play."));
        audio.play().catch(finish);
      });
    } finally {
      URL.revokeObjectURL(url);
      if (player === audio) player = null;
    }
  }

  async function present(feedback = null) {
    if (!game || mode !== "adventure") return;
    cancel();
    const signal = abort.signal;
    const token = game.token;
    speaking = true;
    lockChoices();
    if (feedback) prompt.textContent = feedback.text;
    try {
      if (game.spoken) await voice(feedback?.audio || game.audio, signal);
      if (signal.aborted || game?.token !== token || mode !== "adventure") return;
      if (game.phase === "preview") {
        await wait(game.spoken ? 1600 : 4500, signal);
        await send("ready");
      } else if (game.phase === "success") {
        await wait(1500, signal);
        await send("next");
      }
    } catch (error) {
      if (error.name !== "AbortError" && game?.token === token && mode === "adventure") {
        console.error("Adventure:", error);
        errorLabel.textContent = "Sound unavailable. Check volume and voice setup, or use the pictures. Hear again retries.";
      }
    } finally {
      if (!signal.aborted && game?.token === token) {
        speaking = false;
        lockChoices();
      }
    }
  }

  async function send(action, extra = {}) {
    if (pending || (action === "pick" && speaking)) return;
    pending = true;
    const oldToken = game?.token;
    cancel();
    lockChoices();
    errorLabel.textContent = "";
    try {
      const response = await fetch("/api/child/adventures", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content },
        body: JSON.stringify({ action, token: oldToken, ...extra }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Adventure request failed.");
      if (!["blank", "adventure-menu", "adventure"].includes(mode)) return;
      apply(data.playback);
      pending = false;
      if (game && data.playback.adventure?.token === game.token) present(data.feedback);
    } catch (error) {
      (screen.hidden ? document.getElementById("home-game-error") : errorLabel).textContent = error.message;
    } finally {
      pending = false;
      lockChoices();
    }
  }

  async function catalog() {
    const requestId = ++catalogRequest;
    const response = await fetch("/api/adventures/catalog");
    if (!response.ok) throw new Error("Adventure choices could not load.");
    const data = await response.json();
    if (requestId !== catalogRequest || mode !== "adventure-menu") return;
    const container = document.getElementById("adventure-games");
    container.replaceChildren();
    for (const item of data.games) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "quiz-tile";
      button.setAttribute("aria-label", item.name);
      button.append(pictureCard(item));
      button.addEventListener("click", () => send("start", { id: item.id }));
      container.append(button);
    }
    document.getElementById("adventure-menu-message").textContent = data.games.length ? "" : "A grown-up can enable games from the parent page.";
  }

  window.addEventListener("tv-display", (event) => {
    const next = event.detail;
    const oldMode = mode;
    mode = next.mode;
    screen.hidden = !["adventure", "adventure-menu"].includes(mode);
    menu.hidden = mode !== "adventure-menu";
    play.hidden = mode !== "adventure";
    if (mode !== "adventure") {
      cancel();
      game = null;
      if (mode === "adventure-menu" && (oldMode !== mode || menuRevision !== next.revision)) {
        menuRevision = next.revision;
        catalog().catch((error) => { errorLabel.textContent = error.message; });
      }
      return;
    }
    if (!next.adventure || next.adventure.token === game?.token) return;
    cancel();
    game = next.adventure;
    render();
    if (!pending) present();
  });
  document.getElementById("adventure-launcher").addEventListener("click", () => send("menu"));
  document.getElementById("adventure-close").addEventListener("click", () => send("close"));
  document.getElementById("adventure-choose").addEventListener("click", () => send("menu"));
  document.getElementById("adventure-ready").addEventListener("click", () => send("ready"));
  document.getElementById("adventure-next").addEventListener("click", () => send("next"));
  document.getElementById("adventure-again").addEventListener("click", () => send("start", { id: game?.id }));
  document.getElementById("adventure-hear").addEventListener("click", () => {
    errorLabel.textContent = "";
    if (game?.id === "bag" && game.phase === "play") send("remember");
    else present();
  });
})();
