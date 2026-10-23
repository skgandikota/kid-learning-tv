"use strict";

async function submit(endpoint, body, button) {
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
    if (!response.ok) throw new Error(result.error || "Sign-in failed.");
    location.reload();
  } catch (failure) {
    error.textContent = failure.message;
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
