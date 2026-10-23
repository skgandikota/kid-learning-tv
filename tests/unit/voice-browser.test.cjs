"use strict";

const assert = require("node:assert/strict");
const { test } = require("node:test");
const { readFileSync } = require("node:fs");
const { resolve } = require("node:path");
const vm = require("node:vm");

function client(fetch) {
  const timers = [];
  const elements = {};
  const context = vm.createContext({
    window: {}, appState: null, fetch,
    document: {
      getElementById: (id) => elements[id] ||= { addEventListener() {} },
      querySelector: () => ({ content: "csrf" }),
    },
    setTimeout: (fn) => { timers.push(fn); return timers.length; },
    clearTimeout() {},
    render: (state) => { context.appState = state; },
  });
  vm.runInContext(readFileSync(resolve(__dirname, "../../app/static/js/voice.js"), "utf8"), context);
  const voice = context.window.offlineVoice;
  voice.report = async () => {};
  voice.enabled = true;
  return { voice, timers, context, elements };
}

test("slow CPU requests pause capture, discard queued audio and resume the same turn", async () => {
  let finish;
  const response = new Promise((resolve) => { finish = resolve; });
  const { voice, timers, elements } = client(() => response);
  let stopped = false;
  let resumed = 0;
  voice.stream = { getTracks: () => [{ stop: () => { stopped = true; } }] };
  voice.listen = async () => { resumed += 1; };
  const state = { voice_revision: 1, voice_listening_allowed: true };
  voice.queue.push(new ArrayBuffer(16000));
  const pending = voice.send(state, voice.generation);
  voice.queue.push(new ArrayBuffer(16000));
  timers[0]();
  assert.equal(stopped, true);
  assert.equal(voice.queue.length, 0);
  assert.match(elements["voice-status"].textContent, /Thinking/);
  finish({ ok: true, json: async () => ({ state }) });
  await pending;
  assert.equal(resumed, 1);
  assert.equal(voice.enabled, true);
});

test("an old request cannot strand queued microphone audio from a new turn", async () => {
  let finish;
  const oldResponse = new Promise((resolve) => { finish = resolve; });
  const urls = [];
  const current = { voice_revision: 2, voice_listening_allowed: true };
  const { voice, context } = client((url) => {
    urls.push(url);
    return urls.length === 1 ? oldResponse : Promise.resolve({ ok: true, json: async () => ({ state: current }) });
  });
  voice.queue.push(new ArrayBuffer(16000));
  const pending = voice.send({ voice_revision: 1 }, voice.generation);
  voice.stop();
  context.appState = current;
  voice.stream = {};
  voice.queue.push(new ArrayBuffer(16000));
  finish({ ok: true, json: async () => ({ state: { voice_revision: 1 } }) });
  await pending;
  await Promise.resolve();
  assert.equal(urls.length, 2);
  assert.match(urls[1], /turn=2/);
  assert.equal(voice.queue.length, 0);
});

test("a parent changing the screen during synthesis is not a permanent voice error", async () => {
  const current = { voice_revision: 2, paused: true };
  const { voice, context } = client(async (url) => url.startsWith("/api/voice/prompt")
    ? { status: 409 }
    : { json: async () => current });
  await voice.runTurn({ voice_revision: 1, voice_enabled: true }, voice.generation);
  assert.equal(context.appState, current);
  assert.equal(voice.enabled, true);
});
