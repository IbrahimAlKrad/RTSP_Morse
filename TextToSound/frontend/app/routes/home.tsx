import { Form, useActionData } from "react-router";
import { useEffect, useRef, useState } from "react";
import { Kafka } from "kafkajs";
import type { Route } from "./+types/home";
import { useMorseAudio } from "../hooks/useMorseAudio";
import { useConnectionStatus } from "../hooks/useConnectionStatus";
import { ExampleTemplates } from "../components/ExampleTemplates";
import { ControlPanel } from "../components/ControlPanel";
import { MorseDisplay } from "../components/MorseDisplay";
import { ConnectionStatus } from "../components/ConnectionStatus";

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
    brokers: [(process.env.KAFKA_BROKERS || "localhost:9094")],
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
  const { connectionError } = useConnectionStatus();
  const formRef = useRef<HTMLFormElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    isPlaying,
    frequency,
    setFrequency,
    volume,
    setVolume,
    ditDuration,
    setDitDuration,
    playMorse,
  } = useMorseAudio();

  useEffect(() => {
    console.log("[SSE] Connecting to /stream for Morse messages...");
    const morseStream = new EventSource("/stream");

    morseStream.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.morse) {
        console.log(`[Kafka Consumer] Received from 'morse_output': "${data.morse}"`);
        setLastMessage(data.morse);
        playMorse(data.morse);
      }
    };

    morseStream.onerror = (err) => {
      console.error("[SSE] Morse stream error:", err);
      morseStream.close();
    };

    return () => {
      console.log("[SSE] Closing Morse stream");
      morseStream.close();
    };
  }, [playMorse]);

  const handleTemplateClick = (template: string) => {
    if (inputRef.current && formRef.current) {
      inputRef.current.value = template;
      formRef.current.requestSubmit();
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white font-sans p-4">
      <div className="max-w-5xl w-full">
        <div className="flex items-center justify-center mb-6 relative">
          <h1 className="text-3xl font-bold text-center text-blue-400 tracking-wider">
            Text to Morse Sound
          </h1>

          {/* Status Pill */}
          <ConnectionStatus isConnected={!connectionError} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form - Left/Top */}
          <div className="lg:col-span-2 bg-gray-800 rounded-xl shadow-2xl p-8 border border-gray-700">
            <Form ref={formRef} method="post" className="space-y-6">
              <div>
                <label htmlFor="text" className="block text-sm font-medium text-gray-300 mb-2">
                  Enter Text
                </label>
                <input
                  ref={inputRef}
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

            <ControlPanel
              frequency={frequency}
              setFrequency={setFrequency}
              volume={volume}
              setVolume={setVolume}
              ditDuration={ditDuration}
              setDitDuration={setDitDuration}
            />

            {actionData?.error && (
              <div className="mt-4 p-3 bg-red-900/50 border border-red-700 text-red-200 rounded-lg text-sm text-center">
                {actionData.error}
              </div>
            )}

            <MorseDisplay lastMessage={lastMessage} isPlaying={isPlaying} />
          </div>

          {/* Examples Sidebar - Right/Bottom */}
          <ExampleTemplates onTemplateClick={handleTemplateClick} />
        </div>
      </div>
    </div>
  );
}
