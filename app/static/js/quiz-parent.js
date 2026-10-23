"use strict";

(() => {
  const panel = document.getElementById("quiz-panel");
  const errorLabel = document.getElementById("quiz-parent-error");
  let initialized = false;
  let timer = null;

  async function request(body) {
    const response = await fetch("/api/parent/quiz", body ? {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content,
      },
      body: JSON.stringify(body),
    } : { cache: "no-store" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Quiz request failed.");
    return data;
  }

  async function action(body, button) {
    button.disabled = true;
    errorLabel.textContent = "";
    try {
      await request(body);
      await refresh();
    } catch (error) {
      errorLabel.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  }

  async function refresh() {
    const data = await request();
    if (!initialized) {
      document.getElementById("quiz-duration").value = data.settings.seconds;
      document.getElementById("quiz-count").value = data.settings.count;
      document.getElementById("quiz-ticking").checked = data.settings.ticking;
      const categories = document.getElementById("parent-quiz-categories");
      categories.replaceChildren();
      for (const category of data.categories) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = `${category.name} (${category.count})${category.harder ? " - harder" : ""}`;
        button.addEventListener("click", () => action({ action: "start", category: category.id }, button));
        categories.append(button);
      }
      initialized = true;
    }
    const quiz = data.playback.quiz;
    document.getElementById("quiz-parent-status").textContent = quiz
      ? `${quiz.category}: ${quiz.index + 1}/${quiz.count}, ${quiz.phase}${quiz.paused ? " (paused)" : ""}. ${quiz.warning}`
      : data.playback.mode === "quiz-menu" ? "Choose a category on the TV." : "No quiz running.";
    document.getElementById("quiz-speech-status").textContent =
      `Voice: ${data.speech.engine}. ${data.speech.error || ""}${data.speech.available ? "" : " No speech available; check laptop setup."}`;
    document.querySelectorAll("[data-quiz-action]").forEach((button) => {
      button.disabled = !quiz && button.dataset.quizAction !== "menu" &&
        !(button.dataset.quizAction === "close" && data.playback.mode === "quiz-menu");
    });
    document.getElementById("food-time").setAttribute("aria-pressed", String(data.playback.mode === "food"));
  }

  async function poll() {
    if (panel.hidden) return;
    try {
      await refresh();
    } catch (error) {
      errorLabel.textContent = error.message;
    } finally {
      if (!panel.hidden) timer = setTimeout(poll, 1000);
    }
  }

  document.getElementById("open-quiz").addEventListener("click", (event) => {
    panel.hidden = !panel.hidden;
    event.currentTarget.setAttribute("aria-expanded", String(!panel.hidden));
    clearTimeout(timer);
    if (!panel.hidden) poll();
  });
  document.getElementById("quiz-settings").addEventListener("submit", (event) => {
    event.preventDefault();
    action({
      action: "settings",
      settings: {
        seconds: Number(document.getElementById("quiz-duration").value),
        count: Number(document.getElementById("quiz-count").value),
        ticking: document.getElementById("quiz-ticking").checked,
      },
    }, event.currentTarget.querySelector("button"));
  });
  panel.querySelectorAll("[data-quiz-action]").forEach((button) => {
    button.addEventListener("click", () => action({ action: button.dataset.quizAction }, button));
  });
})();
