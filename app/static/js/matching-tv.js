"use strict";

(() => {
  const screen = document.getElementById("matching-screen");
  const board = document.getElementById("matching-board");
  const errorLabel = document.getElementById("matching-error");
  const homeError = document.getElementById("home-game-error");
  let game = null;
  let token = "";
  let busy = false;
  let soundContext = null;
  const sounds = new Set();

  function stopSound() {
    for (const oscillator of sounds) oscillator.stop();
    sounds.clear();
  }

  async function magicalSound(boardToken) {
    try {
      soundContext ||= new AudioContext();
      await soundContext.resume();
      if (screen.hidden || game?.token !== boardToken) return;
      for (const [index, frequency] of [660, 880, 1100, 1320].entries()) {
        const oscillator = soundContext.createOscillator();
        const gain = soundContext.createGain();
        const start = soundContext.currentTime + index * 0.09;
        oscillator.type = "sine";
        oscillator.frequency.setValueAtTime(frequency, start);
        oscillator.frequency.exponentialRampToValueAtTime(frequency * 1.12, start + 0.2);
        gain.gain.setValueAtTime(0, start);
        gain.gain.linearRampToValueAtTime(0.055, start + 0.012);
        gain.gain.exponentialRampToValueAtTime(0.001, start + 0.28);
        oscillator.connect(gain).connect(soundContext.destination);
        sounds.add(oscillator);
        oscillator.onended = () => sounds.delete(oscillator);
        oscillator.start(start);
        oscillator.stop(start + 0.3);
      }
    } catch (error) {
      console.error("Card match sound failed:", error);
      errorLabel.textContent = "The sparkle sound could not play. Check the laptop sound or reopen the kiosk.";
    }
  }

  async function command(action, index) {
    if (busy) return;
    busy = true;
    errorLabel.textContent = homeError.textContent = "";
    try {
      const response = await fetch("/api/child/matching", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content,
        },
        body: JSON.stringify({ action, token: game?.token, index }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Card match connection failed.");
      apply(data.playback);
    } catch (error) {
      const target = screen.hidden ? homeError : errorLabel;
      target.textContent = error.message;
    } finally {
      busy = false;
    }
  }

  function makeCard(index) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "matching-card";
    button.dataset.index = index;
    const inner = document.createElement("span");
    inner.className = "matching-card-inner";
    const back = document.createElement("span");
    back.className = "matching-card-back";
    back.textContent = "\u2605";
    back.setAttribute("aria-hidden", "true");
    const face = document.createElement("span");
    face.className = "matching-card-face";
    const image = document.createElement("img");
    image.alt = "";
    image.draggable = false;
    image.addEventListener("error", () => {
      errorLabel.textContent = "A picture could not load. Close Card match and try again.";
    });
    face.append(image);
    inner.append(back, face);
    button.append(inner);
    button.addEventListener("click", () => {
      if (!game || game.phase !== "playing" || button.disabled) return;
      command("flip", index);
    });
    return button;
  }

  window.addEventListener("tv-display", (event) => {
    const state = event.detail;
    screen.hidden = state.mode !== "matching";
    if (screen.hidden || !state.matching) {
      game = null;
      token = "";
      stopSound();
      return;
    }
    const next = state.matching;
    if (game && next.matches > game.matches) magicalSound(next.token);
    game = next;
    if (token !== game.token) {
      token = game.token;
      board.replaceChildren(...game.cards.map((card) => makeCard(card.index)));
      board.dataset.size = game.cards.length;
      errorLabel.textContent = "";
    }
    document.getElementById("matching-round").textContent = `Round ${game.round} / ${game.rounds} \u00b7 ${game.cards.length} cards`;
    const finished = game.phase === "complete";
    document.getElementById("matching-title").textContent = finished ? "Lovely matching!" : "Find the pair!";
    document.getElementById("matching-message").textContent = finished
      ? "You found all the pairs!"
      : game.phase === "round-done"
        ? game.round === game.rounds ? "You found all the pairs!" : "Lovely! Here comes the next round..."
        : "";
    document.getElementById("matching-again").hidden = !finished;
    board.hidden = finished;
    for (const card of game.cards) {
      const button = board.children[card.index];
      const image = button.querySelector("img");
      button.classList.toggle("face-up", card.face_up);
      button.classList.toggle("pair-found", card.face_up && game.phase === "match");
      button.classList.toggle("card-gone", card.removed);
      button.disabled = game.phase !== "playing" || card.face_up || card.removed;
      button.setAttribute("aria-label", card.removed ? `Card ${card.index + 1}, matched` :
        card.face_up ? card.name : `Card ${card.index + 1}`);
      button.setAttribute("aria-pressed", String(card.face_up));
      if (card.image && image.getAttribute("src") !== card.image) image.src = card.image;
    }
  });

  document.getElementById("matching-launcher").addEventListener("click", () => command("start"));
  document.getElementById("matching-again").addEventListener("click", () => command("start"));
  document.getElementById("matching-close").addEventListener("click", () => command("close"));
})();
