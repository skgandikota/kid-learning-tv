"use strict";

async function submit(endpoint, body, button, onSuccess = () => location.reload()) {
  const error = document.getElementById("error");
  button.disabled = true;
  error.textContent = "";
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content,
      },
      body: JSON.stringify(body),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Request failed.");
    onSuccess(result);
  } catch (failure) {
    error.textContent = failure.message;
  } finally {
    button.disabled = false;
  }
}

const form = document.getElementById("login");
form?.addEventListener("submit", (event) => {
  event.preventDefault();
  submit(form.dataset.endpoint, { pin: document.getElementById("pin").value }, form.querySelector("button"));
});
document.getElementById("logout")?.addEventListener("click", (event) => {
  submit("/api/logout", {}, event.currentTarget);
});
document.getElementById("food-time")?.addEventListener("click", (event) => {
  const button = event.currentTarget;
  submit("/api/parent/food-time", { enabled: button.getAttribute("aria-pressed") !== "true" }, button, (result) => {
    button.setAttribute("aria-pressed", String(result.food_time));
  });
});
for (const [id, action] of [["tv-home", "home"], ["show-clock", "clock"], ["refresh-tv", "refresh"]]) {
  document.getElementById(id)?.addEventListener("click", (event) => {
    submit("/api/parent/display", { action }, event.currentTarget, (result) => {
      document.getElementById("food-time").setAttribute("aria-pressed", String(result.playback.mode === "food"));
    });
  });
}
