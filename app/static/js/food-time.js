"use strict";

const picture = document.getElementById("food-time-image");

async function updateDisplay() {
  try {
    const response = await fetch("/api/display", { cache: "no-store" });
    if (!response.ok) throw new Error(`TV display update failed (${response.status}).`);
    const state = await response.json();
    if (typeof state.food_time !== "boolean") throw new Error("Invalid TV display state.");
    picture.hidden = !state.food_time;
  } catch (error) {
    // Keep the current picture undisturbed during a temporary connection loss.
    console.error(error);
  } finally {
    setTimeout(updateDisplay, 750);
  }
}

updateDisplay();
