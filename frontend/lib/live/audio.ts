// Browser audio for the Gemini Live session.
// In:  mic (48 kHz float, usually) -> 16 kHz mono PCM16, base64, ~40 ms per chunk.
// Out: 24 kHz mono PCM16 base64 chunks from Gemini -> gapless playback, flushable on barge-in.

// Runs on the audio thread. `sampleRate` is a global in AudioWorkletGlobalScope.
const CAPTURE_WORKLET = `
class Pcm16Capture extends AudioWorkletProcessor {
  constructor() {
    super();
    this.step = sampleRate / 16000;
    this.pos = 0;
    this.out = new Int16Array(640);
    this.n = 0;
  }
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (!ch) return true;
    for (; this.pos < ch.length; this.pos += this.step) {
      const i = Math.floor(this.pos);
      const a = ch[i];
      const b = i + 1 < ch.length ? ch[i + 1] : a;
      const s = Math.max(-1, Math.min(1, a + (b - a) * (this.pos - i)));
      this.out[this.n++] = s < 0 ? s * 0x8000 : s * 0x7fff;
      if (this.n === this.out.length) {
        const chunk = this.out.slice();
        this.port.postMessage(chunk.buffer, [chunk.buffer]);
        this.n = 0;
      }
    }
    this.pos -= ch.length;
    return true;
  }
}
registerProcessor("pcm16-capture", Pcm16Capture);
`;

export function bytesToBase64(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let s = "";
  for (let i = 0; i < bytes.length; i += 0x8000) {
    s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  }
  return btoa(s);
}

function base64ToInt16(b64: string): Int16Array {
  const s = atob(b64);
  const bytes = new Uint8Array(s.length & ~1);
  for (let i = 0; i < bytes.length; i++) bytes[i] = s.charCodeAt(i);
  return new Int16Array(bytes.buffer);
}

/** One AudioContext for mic and speaker. Create it from a click (autoplay policy). */
export class LiveAudio {
  readonly ctx = new AudioContext();
  private node?: AudioWorkletNode;
  private source?: MediaStreamAudioSourceNode;
  private playhead = 0;
  private playing = new Set<AudioBufferSourceNode>();
  muted = false;

  async startMic(stream: MediaStream, onChunk: (b64: string) => void) {
    if (this.ctx.state === "suspended") await this.ctx.resume();
    const url = URL.createObjectURL(new Blob([CAPTURE_WORKLET], { type: "text/javascript" }));
    try {
      await this.ctx.audioWorklet.addModule(url);
    } finally {
      URL.revokeObjectURL(url);
    }
    this.source = this.ctx.createMediaStreamSource(stream);
    this.node = new AudioWorkletNode(this.ctx, "pcm16-capture");
    this.node.port.onmessage = (e: MessageEvent<ArrayBuffer>) => {
      if (!this.muted) onChunk(bytesToBase64(e.data));
    };
    this.source.connect(this.node);
    // The worklet writes no output (silence); connecting it keeps Safari pulling audio.
    this.node.connect(this.ctx.destination);
  }

  /** Queue one 24 kHz PCM16 chunk right after whatever is already scheduled. */
  play(b64: string) {
    const pcm = base64ToInt16(b64);
    if (!pcm.length) return;
    const buffer = this.ctx.createBuffer(1, pcm.length, 24000);
    const ch = buffer.getChannelData(0);
    for (let i = 0; i < pcm.length; i++) ch[i] = pcm[i] / 0x8000;
    const src = this.ctx.createBufferSource();
    src.buffer = buffer;
    src.connect(this.ctx.destination);
    const at = Math.max(this.ctx.currentTime + 0.02, this.playhead);
    src.start(at);
    this.playhead = at + buffer.duration;
    this.playing.add(src);
    src.onended = () => this.playing.delete(src);
  }

  /** Drop queued speech immediately (the dentist interrupted). */
  flush() {
    for (const s of this.playing) {
      try {
        s.stop();
      } catch {
        /* already stopped */
      }
    }
    this.playing.clear();
    this.playhead = 0;
  }

  get speaking() {
    return this.playhead > this.ctx.currentTime;
  }

  async close() {
    this.flush();
    this.source?.disconnect();
    this.node?.disconnect();
    if (this.ctx.state !== "closed") await this.ctx.close();
  }
}
