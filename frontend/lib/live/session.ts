// Gemini Live session for the phone: mic + camera in, spoken audio out, tools run here.
//
// The browser connects straight to Gemini with a one-use ephemeral token from our
// backend (POST /live/token); audio never goes through FastAPI.
// Limits we design around (Live API docs): audio+video sessions end after ~2 min and a
// connection lasts ~10 min. Sliding-window compression lifts the session cap, and on
// GoAway/close we reconnect with the latest session-resumption handle.

import {
  GoogleGenAI,
  Modality,
  type FunctionCall,
  type FunctionDeclaration,
  type LiveServerMessage,
  type Session,
} from "@google/genai";
import { getLiveToken } from "@/lib/api";
import { LiveAudio } from "@/lib/live/audio";

export type LiveStatus = "idle" | "connecting" | "live" | "reconnecting" | "error";

export type ToolHandler = (args: Record<string, unknown>) => Promise<Record<string, unknown>>;

export interface LiveVoiceOptions {
  systemInstruction: () => string; // read at every (re)connect, so it can reflect UI state
  tools: FunctionDeclaration[];
  handlers: Record<string, ToolHandler>;
  onStatus: (s: LiveStatus, detail?: string) => void;
  onLine: (role: "dentist" | "assistant", text: string) => void; // one finished utterance
  onSpeaking?: (speaking: boolean) => void;
}

const FRAME_MS = 1000; // Live API accepts JPEG at <= 1 FPS
const FRAME_WIDTH = 640;
const MAX_RETRIES = 4;

export class LiveVoice {
  private session?: Session;
  private audio?: LiveAudio;
  private stream?: MediaStream;
  private video?: HTMLVideoElement;
  private canvas?: HTMLCanvasElement;
  private frameTimer?: ReturnType<typeof setInterval>;
  private speakTimer?: ReturnType<typeof setInterval>;
  private handle?: string; // session resumption handle
  private ready = false; // setupComplete received
  private stopped = true;
  private gen = 0; // connection generation; stale sockets' close events are ignored
  private retries = 0;
  private inText = "";
  private outText = "";

  constructor(private opts: LiveVoiceOptions) {}

  /** Call from a click handler: needs camera + mic permission and an unlocked AudioContext. */
  async start(video: HTMLVideoElement) {
    this.stopped = false;
    this.retries = 0;
    this.handle = undefined;
    this.opts.onStatus("connecting");
    try {
      this.audio = new LiveAudio();
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 },
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      this.video = video;
      video.srcObject = this.stream;
      await video.play().catch(() => {});
      await this.audio.startMic(this.stream, (b64) => {
        if (this.ready) this.session?.sendRealtimeInput({ audio: { data: b64, mimeType: "audio/pcm;rate=16000" } });
      });
      this.frameTimer = setInterval(() => this.sendFrame(), FRAME_MS);
      let was = false;
      this.speakTimer = setInterval(() => {
        const now = !!this.audio?.speaking;
        if (now !== was) this.opts.onSpeaking?.((was = now));
      }, 150);
      await this.open();
    } catch (e) {
      this.opts.onStatus("error", describe(e));
      await this.stop(false);
    }
  }

  async stop(report = true) {
    this.stopped = true;
    this.ready = false;
    clearInterval(this.frameTimer);
    clearInterval(this.speakTimer);
    this.session?.close();
    this.session = undefined;
    this.stream?.getTracks().forEach((t) => t.stop());
    this.stream = undefined;
    if (this.video) this.video.srcObject = null;
    await this.audio?.close().catch(() => {});
    this.audio = undefined;
    if (report) this.opts.onStatus("idle");
  }

  set muted(m: boolean) {
    if (this.audio) this.audio.muted = m;
    if (m && this.ready) this.session?.sendRealtimeInput({ audioStreamEnd: true });
  }

  /** Push context to the model mid-session (e.g. a finished Guardian result). */
  sendText(text: string) {
    if (this.ready) this.session?.sendRealtimeInput({ text });
  }

  private async open() {
    const gen = ++this.gen;
    this.ready = false;
    const tok = await getLiveToken(); // one use each, so every (re)connect mints a new one
    const ai = new GoogleGenAI({ apiKey: tok.token, httpOptions: { apiVersion: tok.api_version } });
    const session = await ai.live.connect({
      model: tok.model,
      config: {
        responseModalities: [Modality.AUDIO],
        systemInstruction: this.opts.systemInstruction(),
        tools: [{ functionDeclarations: this.opts.tools }],
        inputAudioTranscription: {},
        outputAudioTranscription: {},
        contextWindowCompression: { slidingWindow: {} },
        sessionResumption: this.handle ? { handle: this.handle } : {},
        // lets the model stay quiet for speech not meant for it (patient chatter)
        proactivity: { proactiveAudio: true },
      },
      callbacks: {
        onmessage: (m) => this.onMessage(m),
        onerror: (e) => console.warn("[live] socket error", e),
        // fires even if setup is rejected before connect() resolves — hence `gen`, not `session`
        onclose: (e) => this.onClose(gen, e.reason || `connection closed (${e.code})`),
      },
    });
    if (gen !== this.gen || this.stopped) {
      session.close();
      return;
    }
    this.session = session;
  }

  private onClose(gen: number, reason: string) {
    if (this.stopped || gen !== this.gen) return; // closed on purpose / superseded
    this.ready = false;
    this.audio?.flush();
    if (this.retries >= MAX_RETRIES) {
      this.opts.onStatus("error", reason);
      void this.stop(false);
      return;
    }
    this.retries++;
    this.opts.onStatus("reconnecting", reason);
    setTimeout(() => {
      if (!this.stopped) this.open().catch((err) => this.onClose(this.gen, describe(err)));
    }, 400 * this.retries);
  }

  private onMessage(m: LiveServerMessage) {
    if (m.setupComplete) {
      this.ready = true;
      this.retries = 0;
      this.opts.onStatus("live");
    }
    if (m.sessionResumptionUpdate?.resumable && m.sessionResumptionUpdate.newHandle) {
      this.handle = m.sessionResumptionUpdate.newHandle;
    }
    if (m.goAway) {
      // server will drop this connection soon: close it ourselves -> onClose resumes it
      console.info("[live] goAway, resuming", m.goAway.timeLeft);
      this.session?.close();
    }
    if (m.toolCall?.functionCalls?.length) void this.runTools(m.toolCall.functionCalls);

    const c = m.serverContent;
    if (!c) return;
    if (c.inputTranscription?.text) this.inText += c.inputTranscription.text;
    if (c.outputTranscription?.text) {
      this.flushIn(); // the model is answering, so the dentist's utterance is finished
      this.outText += c.outputTranscription.text;
    }
    for (const p of c.modelTurn?.parts ?? []) {
      if (p.inlineData?.data && p.inlineData.mimeType?.startsWith("audio/")) {
        this.flushIn();
        this.audio?.play(p.inlineData.data);
      }
    }
    if (c.interrupted) {
      this.audio?.flush();
      this.flushOut();
    }
    if (c.turnComplete) {
      this.flushIn();
      this.flushOut();
    }
  }

  private async runTools(calls: FunctionCall[]) {
    const functionResponses = await Promise.all(
      calls.map(async (call) => {
        const handler = call.name ? this.opts.handlers[call.name] : undefined;
        let response: Record<string, unknown>;
        try {
          response = handler ? await handler(call.args ?? {}) : { error: `unknown tool ${call.name}` };
        } catch (e) {
          response = { error: describe(e) };
        }
        return { id: call.id, name: call.name, response };
      })
    );
    this.session?.sendToolResponse({ functionResponses });
  }

  private sendFrame() {
    const v = this.video;
    if (!this.ready || !v || v.readyState < 2 || !v.videoWidth) return;
    this.canvas ??= document.createElement("canvas");
    const scale = Math.min(1, FRAME_WIDTH / v.videoWidth);
    this.canvas.width = Math.round(v.videoWidth * scale);
    this.canvas.height = Math.round(v.videoHeight * scale);
    this.canvas.getContext("2d")?.drawImage(v, 0, 0, this.canvas.width, this.canvas.height);
    const data = this.canvas.toDataURL("image/jpeg", 0.6).split(",")[1];
    if (data) this.session?.sendRealtimeInput({ video: { data, mimeType: "image/jpeg" } });
  }

  private flushIn() {
    const t = this.inText.trim();
    this.inText = "";
    if (t) this.opts.onLine("dentist", t);
  }

  private flushOut() {
    const t = this.outText.trim();
    this.outText = "";
    if (t) this.opts.onLine("assistant", t);
  }
}

function describe(e: unknown): string {
  if (e instanceof DOMException && e.name === "NotAllowedError") return "Camera/mic permission denied";
  if (e instanceof DOMException && e.name === "NotFoundError") return "No camera or microphone found";
  if (e instanceof Error) return e.message;
  return String(e);
}
