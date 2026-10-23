"use strict";

let learningTimer = null;
let learningTimerKey = "";
let learningBusy = false;

function learningPicture(picture, colour = "blue") {
  const paths = {
    circle: "M50 8a42 42 0 1 0 0 84a42 42 0 1 0 0-84",
    square: "M12 12h76v76H12z",
    triangle: "M50 6L96 90H4z",
    star: "M50 4L64 34L97 38L73 61L79 95L50 79L21 95L27 61L3 38L36 34z",
  };
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 100 100");
  svg.setAttribute("aria-hidden", "true");
  svg.classList.add("learning-picture", `learning-${colour}`);
  const path = document.createElementNS(svg.namespaceURI, "path");
  path.setAttribute("d", paths[picture] || paths.circle);
  svg.appendChild(path);
  return svg;
}

async function learningMove(action, game, choice) {
  if (learningBusy) return;
  learningBusy = true;
  document.getElementById("learning-status").textContent = "";
  document.querySelectorAll("#learning-board button").forEach((button) => { button.disabled = true; });
  try {
    await childAction(action, { session_id: game.session_id, revision: game.revision, choice });
  } catch (error) {
    document.getElementById("learning-status").textContent = error.message;
  } finally {
    learningBusy = false;
    renderLearning(appState);
  }
}

function renderLearning(state) {
  const active = state?.screen === "learning" && state.learning_game;
  const game = active ? state.learning_game : null;
  const key = game ? `${game.session_id}:${game.revision}` : "";
  if ((!game?.waiting || learningTimerKey !== key || state.paused || state.locked) && learningTimer) {
    window.clearTimeout(learningTimer);
    learningTimer = null;
    learningTimerKey = "";
  }
  if (!game) return;
  document.getElementById("learning-title").textContent = game.name;
  document.getElementById("learning-message").textContent = state.paused ? "Your grown-up has paused the game." : game.message;
  document.getElementById("learning-progress").textContent =
    `${game.score} of ${game.total} ${game.activity_id === "matching-pairs" ? "pairs found" : "completed"}`;
  const target = document.getElementById("learning-target");
  const board = document.getElementById("learning-board");
  target.replaceChildren();
  board.replaceChildren();
  const blocked = Boolean(state.paused || state.locked || game.completed || game.waiting || learningBusy);
  board.classList.toggle("pairs-board", game.activity_id === "matching-pairs");
  if (game.completed) {
    target.appendChild(learningPicture("star", "yellow"));
    target.setAttribute("aria-label", "Well done!");
  } else if (game.activity_id === "count-objects") {
    target.setAttribute("aria-label", "Count these stars");
    for (let index = 0; index < Number(game.target); index += 1) {
      target.appendChild(learningPicture("star", "yellow"));
    }
  } else if (game.activity_id !== "matching-pairs") {
    const colour = game.activity_id === "match-colours";
    target.setAttribute("aria-label", `Match this ${game.target}`);
    target.appendChild(learningPicture(colour ? "circle" : game.target, colour ? game.target : "blue"));
  } else {
    target.removeAttribute("aria-label");
  }
  if (game.activity_id === "matching-pairs") {
    const colours = { circle: "red", square: "blue", triangle: "green", star: "yellow" };
    game.cards.forEach((card) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "learning-card";
      button.classList.toggle("pair-matched", card.matched);
      button.setAttribute("aria-label",
        card.picture ? `Card ${card.id + 1}: ${card.picture}${card.matched ? ", matched" : ""}` : `Card ${card.id + 1}, face down`);
      if (card.picture) button.appendChild(learningPicture(card.picture, colours[card.picture]));
      else button.textContent = "?";
      button.disabled = blocked || card.matched || Boolean(card.picture);
      button.addEventListener("click", () => learningMove("learning_answer", game, card.id));
      board.appendChild(button);
    });
  } else if (!game.completed) {
    game.options.forEach((choice) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "learning-card";
      button.setAttribute("aria-label", choice);
      if (game.activity_id === "count-objects") button.textContent = choice;
      else {
        const colour = game.activity_id === "match-colours";
        button.appendChild(learningPicture(colour ? "circle" : choice, colour ? choice : "blue"));
        const label = document.createElement("span");
        label.textContent = choice;
        button.appendChild(label);
      }
      button.disabled = blocked;
      button.addEventListener("click", () => learningMove("learning_answer", game, choice));
      board.appendChild(button);
    });
  }
  if (game.waiting && !state.paused && !state.locked && !learningTimer && !learningBusy) {
    learningTimerKey = key;
    learningTimer = window.setTimeout(() => {
      learningTimer = null;
      learningMove("learning_settle", game);
    }, 1500);
  }
}
