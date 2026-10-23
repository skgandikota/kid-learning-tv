class MicrophonePCM extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = new Int16Array(8000);
    this.index = 0;
  }

  process(inputs) {
    const channel = inputs[0]?.[0];
    if (!channel) return true;
    for (const value of channel) {
      const sample = Math.max(-1, Math.min(1, value));
      this.buffer[this.index++] = Math.round(sample * (sample < 0 ? 32768 : 32767));
      if (this.index === this.buffer.length) {
        this.port.postMessage(this.buffer.buffer, [this.buffer.buffer]);
        this.buffer = new Int16Array(8000);
        this.index = 0;
      }
    }
    return true;
  }
}
registerProcessor("microphone-pcm", MicrophonePCM);
