"use strict";

class OfflineVoice {
  constructor() {
    this.enabled = false;
    this.context = null;
    this.stream = null;
    this.node = null;
    this.source = null;
    this.speaker = null;
    this.generation = 0;
    this.turn = null;
    this.queue = [];
    this.sending = false;
    this.timer = null;
    this.autoChecked = false;
    this.status = "off";
    this.button = document.getElementById("start-voice");
    this.label = document.getElementById("voice-status");
    this.button.addEventListener("click", () => {
      if (this.enabled) {
        this.enabled = false;
        this.stop();
        this.setStatus("off", "Microphone off. Tap to start voice again.");
        this.button.textContent = "Start voice";
      } else this.start();
    });
  }

  async report(status) {
    if (this.status === status) return;
    this.status = status;
    try {
      const response = await fetch("/api/voice/status", {
        method: "POST", headers: this.headers(true), body: JSON.stringify({ status }),
      });
      if (!response.ok) this.label.textContent = "Could not report microphone status to parent controls.";
    } catch (error) {
      this.label.textContent = `Connection lost: ${error.message}`;
    }
  }

  headers(json = false) {
    return {
      "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content,
      ...(json ? { "Content-Type": "application/json" } : {}),
    };
  }

  setStatus(status, message) {
    this.label.textContent = message;
    this.report(status);
  }

  stopCapture() {
    if (this.node) { this.node.port.onmessage = null; this.node.disconnect(); }
    if (this.source) this.source.disconnect();
    if (this.stream) this.stream.getTracks().forEach((track) => track.stop());
    this.stream = null;
    this.node = null;
    this.source = null;
    this.queue = [];
  }

  stop() {
    this.generation += 1;
    clearTimeout(this.timer);
    if (this.speaker) this.speaker.stop();
    this.speaker = null;
    this.stopCapture();
    this.turn = null;
  }

  fail(error) {
    this.enabled = false;
    this.stop();
    this.button.textContent = "Retry voice";
    this.setStatus("error", `${error.message} Ask a grown-up to check microphone permission and offline voice setup.`);
  }

  async start() {
    try {
      if (!appState?.voice_input_enabled) throw new Error("Enable offline voice in parent controls first.");
      if (!appState.voice_input_available) throw new Error("Run scripts/setup-voice.sh on the laptop first.");
      if (!["localhost", "127.0.0.1", "[::1]"].includes(location.hostname)) {
        throw new Error("Open http://127.0.0.1:8765/ on the laptop, not its network IP.");
      }
      if (!navigator.mediaDevices?.getUserMedia) throw new Error("Microphone access is unavailable in this browser.");
      if (!this.context) {
        this.context = new AudioContext({ sampleRate: 16000 });
        await this.context.audioWorklet.addModule("/static/js/microphone-worklet.js");
      }
      await this.context.resume();
      if (this.context.sampleRate !== 16000) throw new Error("This browser cannot provide 16 kHz microphone audio.");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: {
        channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true,
      } });
      stream.getTracks().forEach((track) => track.stop());
      this.enabled = true;
      this.button.textContent = "Stop voice";
      this.update(appState);
    } catch (error) { this.fail(error); }
  }

  update(state) {
    if (!state) return;
    if (!this.enabled && !this.autoChecked && state.voice_input_enabled && state.voice_input_available) {
      this.autoChecked = true;
      navigator.permissions?.query({ name: "microphone" }).then((permission) => {
        if (permission.state === "granted" && !this.enabled) this.start();
      }).catch((error) => { this.label.textContent = `Tap Start voice to allow the microphone. ${error.message}`; });
    }
    if (!state.voice_input_enabled && this.enabled) {
      this.enabled = false;
      this.stop();
      this.button.textContent = "Start voice";
      this.setStatus("off", "Voice is off in parent controls.");
    }
    if (!this.enabled) return;
    const blocked = state.locked || state.paused || state.screen === "video";
    const turn = `${state.voice_revision}:${Boolean(blocked)}`;
    if (turn === this.turn) return;
    this.stop();
    this.turn = turn;
    const generation = this.generation;
    if (blocked) {
      this.setStatus("off", "Microphone off while paused, locked or watching a video.");
      return;
    }
    this.timer = setTimeout(() => this.runTurn(state, generation), 150);
  }

  async runTurn(state, generation) {
    try {
      if (generation !== this.generation) return;
      this.setStatus("speaking", "Listen...");
      if (!state.muted && state.voice_enabled) {
        const response = await fetch(`/api/voice/prompt?turn=${state.voice_revision}`, { headers: this.headers() });
        if (generation !== this.generation) return;
        if (!response.ok) throw new Error((await response.json()).error || "Offline voice could not speak.");
        const bytes = await response.arrayBuffer();
        const buffer = await this.context.decodeAudioData(bytes);
        if (generation !== this.generation) return;
        const speaker = this.context.createBufferSource();
        await new Promise((resolve) => {
          this.speaker = speaker;
          speaker.buffer = buffer;
          speaker.connect(this.context.destination);
          speaker.onended = resolve;
          speaker.start();
        });
        if (this.speaker === speaker) this.speaker = null;
      }
      if (generation !== this.generation) return;
      if (state.screen === "ask-rocky" && state.rocky_request_open) {
        beep();
        this.setStatus("off", "Pretend message only. The microphone is off.");
        return;
      }
      if (!state.voice_listening_allowed) {
        this.setStatus("ready", "Microphone off. Tap the cards or wait for your grown-up.");
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 400));
      if (generation !== this.generation) return;
      await this.listen(state, generation);
    } catch (error) {
      if (generation === this.generation) this.fail(error);
    }
  }

  async listen(state, generation) {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: {
      channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true,
    } });
    if (generation !== this.generation) {
      stream.getTracks().forEach((track) => track.stop());
      return;
    }
    this.stream = stream;
    this.source = this.context.createMediaStreamSource(stream);
    this.node = new AudioWorkletNode(this.context, "microphone-pcm");
    this.node.port.onmessage = (event) => {
      if (generation !== this.generation) return;
      if (this.queue.length >= 8) return this.fail(new Error("Offline recognition is too slow on this device."));
      this.queue.push(event.data);
      this.send(state, generation);
    };
    this.source.connect(this.node);
    this.node.connect(this.context.destination);
    this.setStatus("listening", "I'm listening. Your turn!");
  }

  async send(state, generation) {
    if (this.sending) return;
    this.sending = true;
    try {
      while (this.queue.length && generation === this.generation) {
        const response = await fetch(`/api/voice/audio?turn=${state.voice_revision}`, {
          method: "POST",
          headers: { ...this.headers(), "Content-Type": "application/octet-stream" },
          body: this.queue.shift(),
        });
        if (generation !== this.generation) break;
        if (response.status === 409 || response.status === 423) {
          this.stopCapture();
          const current = await fetch("/api/state").then((result) => result.json());
          render(current);
          break;
        }
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Offline recognition failed.");
        if (result.state.voice_revision !== state.voice_revision) render(result.state);
      }
    } catch (error) {
      if (generation === this.generation) this.fail(error);
    } finally {
      this.sending = false;
    }
  }
}

window.offlineVoice = new OfflineVoice();
if (appState) window.offlineVoice.update(appState);
