"use strict";

(() => {
  const home = document.getElementById("quiz-home");
  const screen = document.getElementById("quiz-screen");
  const menu = document.getElementById("quiz-menu");
  const slide = document.getElementById("quiz-slide");
  const complete = document.getElementById("quiz-complete");
  const image = document.getElementById("quiz-picture");
  const answer = document.getElementById("quiz-answer");
  const loader = document.getElementById("quiz-loader");
  const errorLabel = document.getElementById("quiz-tv-error");
  let current = null;
  let currentToken = "";
  let spokenToken = "";
  let receivedAt = 0;
  let audio = null;
  let audioUrl = "";
  let prepared = null;
  let pendingFallback = null;
  let fallbackToken = "";
  let context = null;
  let lastTick = -1;
  let ready = false;
  let retry = null;
  let categoriesLoaded = false;

  async function request(path, body) {
    const response = await fetch(path, body === undefined ? {} : {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content,
      },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const result = await response.json();
      throw new Error(result.error || "Quiz connection failed.");
    }
    return response.json();
  }

  function stopSound() {
    if (audio) {
      audio.onended = audio.onerror = null;
      audio.pause();
      audio = null;
    }
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    audioUrl = "";
    pendingFallback = null;
    fallbackToken = "";
    window.speechSynthesis?.cancel();
  }

  async function report(action, token, warning = "") {
    try {
      await request("/api/tv/quiz", { action, token, warning });
    } catch (error) {
      if (action === "ready") ready = false;
      if (current?.token === token) errorLabel.textContent = error.message;
    }
  }

  function gentleTick() {
    try {
      context ||= new AudioContext();
      if (context.state === "suspended") context.resume().catch(console.error);
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.frequency.value = 650;
      gain.gain.setValueAtTime(0.025, context.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, context.currentTime + 0.045);
      oscillator.connect(gain).connect(context.destination);
      oscillator.start();
      oscillator.stop(context.currentTime + 0.05);
    } catch (error) {
      console.error("Quiz ticking unavailable:", error);
    }
  }

  async function fallbackSpeech(quiz, reason) {
    if (current?.token !== quiz.token || fallbackToken === quiz.token) return;
    if (current.paused) {
      pendingFallback = { quiz, reason };
      return;
    }
    fallbackToken = quiz.token;
    if (audio) {
      audio.onended = audio.onerror = null;
      audio.pause();
      audio = null;
    }
    const synth = window.speechSynthesis;
    const voice = synth?.getVoices().find((item) => item.localService && item.lang.startsWith("en"));
    if (!voice) {
      await report("speech-done", quiz.token, `${reason} No offline browser voice is available.`);
      return;
    }
    const words = new SpeechSynthesisUtterance(quiz.item.speech || quiz.item.name);
    words.voice = voice;
    words.rate = 0.85;
    words.onend = () => report("speech-done", quiz.token, `${reason} Using the offline browser voice.`);
    words.onerror = () => report("speech-done", quiz.token, "Browser speech failed; check laptop sound.");
    synth.speak(words);
  }

  async function speak(quiz) {
    const token = quiz.token;
    let result;
    try {
      result = await prepared;
      if (current?.token !== token || current?.phase !== "answer") return;
      if (!result?.blob) {
        await fallbackSpeech(quiz, result?.error || "Local speech unavailable.");
        return;
      }
      audioUrl = URL.createObjectURL(result.blob);
      audio = new Audio(audioUrl);
      audio.onended = () => report("speech-done", token);
      audio.onerror = () => fallbackSpeech(quiz, "The local answer audio could not play.");
      if (!current.paused) {
        await audio.play();
      }
    } catch (error) {
      if (current?.token === token) await fallbackSpeech(quiz, `Local sound failed: ${error.message}`);
    }
  }

  function imageReady() {
    const quiz = current;
    if (!quiz || image.dataset.token !== quiz.token || quiz.phase !== "loading" || ready) return;
    ready = true;
    report("ready", quiz.token);
  }

  image.addEventListener("load", imageReady);
  image.addEventListener("error", () => {
    ready = false;
    errorLabel.textContent = "The picture could not load. A grown-up can choose Next on the phone.";
    if (current) report("image-error", current.token, "Quiz picture could not load on the TV. Choose Next or restart the round.");
    const token = current?.token;
    clearTimeout(retry);
    retry = setTimeout(() => {
      if (current?.token === token) image.src = current.item.image;
    }, 3000);
  });

  async function choose(body) {
    errorLabel.textContent = "";
    try {
      await request("/api/child/quiz", body);
    } catch (error) {
      errorLabel.textContent = error.message;
    }
  }

  document.getElementById("quiz-launcher").addEventListener("click", () => choose({ action: "menu" }));
  document.getElementById("quiz-close").addEventListener("click", () => choose({ action: "close" }));

  async function loadCategories() {
    if (categoriesLoaded) return;
    const data = await request("/api/quiz/catalog");
    const container = document.getElementById("quiz-categories");
    container.replaceChildren();
    for (const category of data.categories) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "quiz-tile";
      const icon = document.createElement("img");
      icon.src = category.image;
      icon.alt = "";
      const name = document.createElement("span");
      name.textContent = category.name;
      button.append(icon, name);
      button.addEventListener("click", () => choose({ action: "start", category: category.id }));
      container.append(button);
    }
    categoriesLoaded = true;
  }

  window.addEventListener("tv-display", (event) => {
    const state = event.detail;
    home.hidden = state.mode !== "blank";
    screen.hidden = !["quiz-menu", "quiz"].includes(state.mode);
    document.body.classList.toggle("quiz-interactive", !home.hidden || !screen.hidden ||
      ["matching", "typing-menu", "typing"].includes(state.mode));
    const quiz = state.quiz;
    if (screen.hidden || !quiz) {
      stopSound();
      current = null;
      currentToken = "";
      spokenToken = "";
      clearTimeout(retry);
      menu.hidden = state.mode !== "quiz-menu";
      slide.hidden = complete.hidden = true;
      if (state.mode === "quiz-menu") loadCategories().catch((error) => { errorLabel.textContent = error.message; });
      return;
    }
    current = quiz;
    receivedAt = performance.now();
    menu.hidden = true;
    slide.hidden = quiz.phase === "complete";
    complete.hidden = quiz.phase !== "complete";
    if (quiz.phase === "complete") {
      stopSound();
      return;
    }
    if (currentToken !== quiz.token) {
      stopSound();
      clearTimeout(retry);
      currentToken = quiz.token;
      spokenToken = "";
      errorLabel.textContent = "";
      lastTick = -1;
      ready = false;
      image.dataset.token = quiz.token;
      image.src = quiz.item.image;
      prepared = fetch(`/api/quiz/audio/${encodeURIComponent(quiz.category)}/${encodeURIComponent(quiz.item.id)}`)
        .then(async (response) => {
          if (!response.ok) return { error: (await response.json()).error || "Local voice unavailable." };
          return { blob: await response.blob() };
        }).catch((error) => ({ error: error.message }));
    }
    document.getElementById("quiz-round-count").textContent = `${quiz.index + 1} / ${quiz.count}`;
    answer.hidden = quiz.phase !== "answer";
    answer.textContent = quiz.phase === "answer" ? quiz.item.name : "";
    loader.hidden = quiz.phase !== "loading";
    image.hidden = quiz.phase === "loading";
    document.getElementById("quiz-clock").hidden = quiz.phase !== "question";
    if (quiz.phase === "loading" && image.complete && image.naturalWidth > 0) imageReady();
    if (quiz.phase === "answer" && spokenToken !== quiz.token && !quiz.paused) {
      spokenToken = quiz.token;
      speak(quiz);
    }
    if (quiz.paused) {
      audio?.pause();
      window.speechSynthesis?.pause();
    } else {
      if (pendingFallback) {
        const pending = pendingFallback;
        pendingFallback = null;
        fallbackSpeech(pending.quiz, pending.reason);
      }
      if (audio?.paused && !audio.ended) audio.play().catch((error) => report("speech-done", quiz.token, error.message));
      window.speechSynthesis?.resume();
    }
  });

  setInterval(() => {
    if (!current || current.phase !== "question") return;
    const remaining = Math.max(0, current.remaining - (current.paused ? 0 : (performance.now() - receivedAt) / 1000));
    const second = Math.ceil(remaining);
    document.getElementById("quiz-seconds").textContent = String(second);
    document.getElementById("quiz-time-progress").value = remaining / current.seconds;
    if (second !== lastTick && second > 0 && !current.paused && current.ticking) gentleTick();
    lastTick = second;
  }, 100);
})();
