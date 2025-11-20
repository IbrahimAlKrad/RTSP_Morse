import { Form, useActionData } from "react-router";
import { useEffect, useRef, useState } from "react";
import { Kafka } from "kafkajs";
import type { Route } from "./+types/home";

export function meta({ }: Route.MetaArgs) {
  return [
    { title: "Text to Morse Sound" },
    { name: "description", content: "Convert text to morse code sound via Kafka" },
  ];
}

export async function action({ request }: Route.ActionArgs) {
  const formData = await request.formData();
  const text = formData.get("text") as string;

  if (!text) {
    return { error: "Text is required" };
  }

  const kafka = new Kafka({
    clientId: "frontend-producer",
    brokers: ["localhost:9094"],
  });

  const producer = kafka.producer();

  try {
    await producer.connect();
    await producer.send({
      topic: "text_input",
      messages: [{ value: text }],
    });
    await producer.disconnect();
    console.log(`[Kafka] Sent message: "${text}"`);
    return { success: true, sent: text };
  } catch (error) {
    console.error("[Kafka] Error sending message:", error);
    return { error: "Failed to send message to Kafka" };
  }
}

export default function Home() {
  const actionData = useActionData<typeof action>();
  const [lastMessage, setLastMessage] = useState<string>("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [frequency, setFrequency] = useState(600);
  const [volume, setVolume] = useState(50);
  const [ditDuration, setDitDuration] = useState(100); // ms
  const frequencyRef = useRef(frequency);
  const volumeRef = useRef(volume);
  const ditDurationRef = useRef(ditDuration);
  const audioContextRef = useRef<AudioContext | null>(null);
  const masterGainRef = useRef<GainNode | null>(null);

  // Keep refs in sync with state
  useEffect(() => {
    frequencyRef.current = frequency;
    volumeRef.current = volume;
    ditDurationRef.current = ditDuration;
  }, [frequency, volume, ditDuration]);

  // Update Master Gain when volume changes
  useEffect(() => {
    if (masterGainRef.current && audioContextRef.current) {
      const ctx = audioContextRef.current;
      const vol = volume / 100;
      console.log(`[Audio] Volume changed to ${volume}% (${vol})`);

      // Cancel any scheduled changes to ensure immediate effect
      masterGainRef.current.gain.cancelScheduledValues(ctx.currentTime);
      masterGainRef.current.gain.setValueAtTime(vol, ctx.currentTime);
    }
  }, [volume]);

  useEffect(() => {
    console.log(`[Settings] Frequency: ${frequency}Hz, Dit Duration: ${ditDuration}ms`);
  }, [frequency, ditDuration]);

  useEffect(() => {
    // Initialize AudioContext on user interaction (first render is fine usually, but best practice is on click)
    if (!audioContextRef.current) {
      console.log("[Audio] Initializing AudioContext...");
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const masterGain = ctx.createGain();
      masterGain.gain.value = volume / 100;
      masterGain.connect(ctx.destination);

      masterGainRef.current = masterGain;
      audioContextRef.current = ctx;
      console.log("[Audio] AudioContext initialized");
    }

    console.log("[SSE] Connecting to /stream...");
    const eventSource = new EventSource("/stream");

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.morse) {
        console.log(`[Kafka Consumer] Received from 'morse_output': "${data.morse}"`);
        setLastMessage(data.morse);
        playMorse(data.morse);
      }
    };

    eventSource.onerror = (err) => {
      console.error("[SSE] Connection error:", err);
      eventSource.close();
    };

    return () => {
      console.log("[SSE] Closing connection");
      eventSource.close();
      if (audioContextRef.current) {
        console.log("[Audio] Closing AudioContext");
        audioContextRef.current.close();
        audioContextRef.current = null;
        masterGainRef.current = null;
      }
    };
  }, []);

  const playTone = (ctx: AudioContext, duration: number, startTime: number) => {
    const currentVol = volumeRef.current;

    // Double check volume to ensure absolute silence at 0
    if (currentVol <= 0) {
      return;
    }
    if (!masterGainRef.current) return;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = "sine";
    osc.frequency.value = frequencyRef.current; // Use current frequency from ref

    osc.connect(gain);
    gain.connect(masterGainRef.current); // Connect to Master Gain instead of destination

    osc.start(startTime);

    // Smooth envelope to avoid clicking (Gain is 1.0 relative to Master Gain)
    gain.gain.setValueAtTime(0, startTime);
    gain.gain.linearRampToValueAtTime(1, startTime + 0.01);
    gain.gain.setValueAtTime(1, startTime + duration - 0.01);
    gain.gain.linearRampToValueAtTime(0, startTime + duration);

    osc.stop(startTime + duration);
  };

  const playMorse = (morse: string) => {
    if (!audioContextRef.current) return;
    const ctx = audioContextRef.current;
    if (ctx.state === 'suspended') {
      ctx.resume();
    }

    setIsPlaying(true);
    console.log(`[Playback] Starting Morse playback: "${morse}"`);
    const dit = ditDurationRef.current / 1000; // Convert ms to seconds
    let currentTime = ctx.currentTime;

    // Add a small buffer to start
    currentTime += 0.1;

    for (const char of morse) {
      if (char === '.') {
        // Dot: 1 dit on
        playTone(ctx, dit, currentTime);
        // Advance: 1 dit on + 1 dit gap (intra-symbol)
        currentTime += dit * 2;
      } else if (char === '-') {
        // Dash: 3 dits on
        playTone(ctx, dit * 3, currentTime);
        // Advance: 3 dits on + 1 dit gap (intra-symbol)
        currentTime += dit * 4;
      } else if (char === ' ') {
        // Space:
        // We already have 1 dit gap from the previous symbol.
        // Target Letter Gap: 3 dits. Need to add 2.
        // Target Word Gap (3 spaces): 1 + 2 + 2 + 2 = 7 dits.
        currentTime += dit * 2;
      }
    }

    // Reset playing state after sequence finishes
    const totalDuration = currentTime - ctx.currentTime;
    console.log(`[Playback] Sequence duration: ${totalDuration.toFixed(2)}s`);

    setTimeout(() => {
      console.log("[Playback] Finished");
      setIsPlaying(false);
    }, totalDuration * 1000);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white font-sans p-4">
      <div className="max-w-md w-full bg-gray-800 rounded-xl shadow-2xl p-8 border border-gray-700">
        <h1 className="text-3xl font-bold mb-6 text-center text-blue-400 tracking-wider">
          Text to Morse Sound
        </h1>

        <Form method="post" className="space-y-6">
          <div>
            <label htmlFor="text" className="block text-sm font-medium text-gray-300 mb-2">
              Enter Text
            </label>
            <input
              type="text"
              name="text"
              id="text"
              placeholder="Hello World"
              autoComplete="off"
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-white placeholder-gray-400"
            />
          </div>

          <button
            type="submit"
            className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-bold rounded-lg shadow-lg transform transition-transform active:scale-95 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Convert & Play
          </button>
        </Form>

        <div className="mt-8 p-4 bg-gray-700/50 rounded-lg border border-gray-600">
          <label htmlFor="frequency" className="block text-sm font-medium text-gray-300 mb-2 flex justify-between">
            <span>Tone Frequency</span>
            <span className="text-blue-400">{frequency} Hz</span>
          </label>
          <input
            type="range"
            id="frequency"
            min="200"
            max="1200"
            step="50"
            value={frequency}
            onChange={(e) => setFrequency(Number(e.target.value))}
            className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
        </div>

        <div className="mt-4 p-4 bg-gray-700/50 rounded-lg border border-gray-600">
          <label htmlFor="volume" className="block text-sm font-medium text-gray-300 mb-2 flex justify-between">
            <span>Volume</span>
            <span className="text-blue-400">{volume}%</span>
          </label>
          <input
            type="range"
            id="volume"
            min="0"
            max="100"
            step="1"
            value={volume}
            onChange={(e) => setVolume(Number(e.target.value))}
            className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
        </div>

        <div className="mt-4 p-4 bg-gray-700/50 rounded-lg border border-gray-600">
          <label htmlFor="ditDuration" className="block text-sm font-medium text-gray-300 mb-2 flex justify-between">
            <span>Speed / Dit Duration</span>
            <span className="text-blue-400">{ditDuration} ms</span>
          </label>
          <input
            type="range"
            id="ditDuration"
            min="50"
            max="300"
            step="10"
            value={ditDuration}
            onChange={(e) => setDitDuration(Number(e.target.value))}
            className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
        </div>

        {actionData?.error && (
          <div className="mt-4 p-3 bg-red-900/50 border border-red-700 text-red-200 rounded-lg text-sm text-center">
            {actionData.error}
          </div>
        )}

        {lastMessage && (
          <div className="mt-8 p-6 bg-gray-900 rounded-lg border border-gray-700">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">
              Last Received Morse
            </h2>
            <div className="text-2xl font-mono text-green-400 break-all tracking-widest leading-relaxed">
              {lastMessage}
            </div>
            {isPlaying && (
              <div className="mt-2 flex items-center justify-center space-x-2 text-blue-400 text-sm animate-pulse">
                <span>🔊 Playing...</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
