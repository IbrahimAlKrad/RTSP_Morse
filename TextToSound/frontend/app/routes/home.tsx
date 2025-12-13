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
import { VisualSignal } from "../components/VisualSignal";
import { AudioVisualizer } from "../components/AudioVisualizer";
import { ViewSwitcher } from "../components/ViewSwitcher";
import { Toast } from "../components/Toast";

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
    brokers: [(process.env.KAFKA_BROKERS || "localhost:9095")],
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
  const [viewMode, setViewMode] = useState<'text' | 'visualizer'>('text');
  const [isExamplesExpanded, setIsExamplesExpanded] = useState(false);
  const [speechEnabled, setSpeechEnabled] = useState(false);
  const speechEnabledRef = useRef(speechEnabled);
  const { connectionError } = useConnectionStatus();
  const formRef = useRef<HTMLFormElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [notification, setNotification] = useState<{ message: string, visible: boolean }>({ message: "", visible: false });

  useEffect(() => {
    speechEnabledRef.current = speechEnabled;
    console.log(`[Input Mode] Switched to: ${speechEnabled ? 'SPEECH' : 'TEXT'} input`);
  }, [speechEnabled]);

  const {
    isPlaying,
    isLightOn,
    frequency,
    setFrequency,
    volume,
    setVolume,
    ditDuration,
    setDitDuration,
    playMorse,
    analyser,
  } = useMorseAudio();

  useEffect(() => {
    console.log("[SSE] Connecting to /stream for Morse messages...");
    const morseStream = new EventSource("/stream");

    morseStream.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const source = data.source || 'text';

        // Show notification for speech input regardless of enabled state (so user knows it works)
        if (source === 'speech' && data.original_text) {
          setNotification({ message: data.original_text, visible: true });
        }

        // Filter out speech if disabled
        if (source === 'speech' && !speechEnabledRef.current) {
          console.log(`[Kafka Consumer] Ignored speech input (disabled)`);
          return;
        }

        if (data.morse) {
          console.log(`[Kafka Consumer] Received from '${source}': "${data.morse}"`);
          setLastMessage(data.morse);
          playMorse(data.morse);
        }
      } catch (e) {
        console.error("Error parsing stream data", e);
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

        <Toast
          message={notification.message}
          isVisible={notification.visible}
          onClose={() => setNotification(prev => ({ ...prev, visible: false }))}
        />

        <div className={`grid grid-cols-1 gap-6 ${isExamplesExpanded ? 'lg:grid-cols-3' : 'lg:grid-cols-[1fr_auto]'}`}>
          {/* Main Form - Left/Top */}
          <div className={`bg-gray-800 rounded-xl shadow-2xl p-8 border border-gray-700 ${isExamplesExpanded ? 'lg:col-span-2' : ''}`}>

            {/* Input Method Switch */}
            <div className="flex justify-end mb-6">
              <label className="flex items-center space-x-3 cursor-pointer group">
                <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors">Enable Speech Input</span>
                <div className="relative">
                  <input
                    type="checkbox"
                    className="sr-only"
                    checked={speechEnabled}
                    onChange={(e) => setSpeechEnabled(e.target.checked)}
                  />
                  <div className={`block w-12 h-7 rounded-full transition-colors duration-300 ease-in-out ${speechEnabled ? 'bg-blue-600' : 'bg-gray-600'}`}></div>
                  <div className={`absolute left-1 top-1 bg-white w-5 h-5 rounded-full transition-transform duration-300 ease-in-out shadow-sm ${speechEnabled ? 'translate-x-5' : 'translate-x-0'}`}></div>
                </div>
              </label>
            </div>

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
                  disabled={speechEnabled}
                  placeholder={speechEnabled ? "Speech Input Active..." : "Hello World"}
                  autoComplete="off"
                  className={`w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-white placeholder-gray-400 ${speechEnabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                />
              </div>

              <button
                type="submit"
                disabled={speechEnabled}
                className={`w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-bold rounded-lg shadow-lg transform transition-transform active:scale-95 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${speechEnabled ? 'opacity-50 cursor-not-allowed hover:from-blue-500 hover:to-cyan-500' : ''}`}
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

            {/* Output Section */}
            <div className="mt-8 flex flex-col md:flex-row gap-6 items-center h-48">
              {/* Main Display Area (Text or Visualizer) */}
              <div className="flex-grow w-full flex gap-4 items-center h-full">
                {/* Vertical Switcher (Left) */}
                <ViewSwitcher viewMode={viewMode} onViewChange={setViewMode} />

                {/* Content Area */}
                <div className="flex-grow h-full relative">
                  {viewMode === 'text' ? (
                    <div className="h-full overflow-y-auto">
                      <MorseDisplay lastMessage={lastMessage} isPlaying={isPlaying} />
                    </div>
                  ) : (
                    <div className="h-full flex flex-col justify-center relative">
                      <h2 className="absolute top-6 left-6 text-xs font-semibold text-gray-400 uppercase tracking-widest z-10">
                        Audio Visualizer
                      </h2>
                      <div className="flex-grow flex items-center justify-center overflow-hidden rounded-lg border border-gray-700 bg-gray-900">
                        <AudioVisualizer analyser={analyser} />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Visual Signal - Now on the right */}
              <div className="flex-shrink-0 flex flex-col gap-4">
                <VisualSignal isLightOn={isLightOn} />
              </div>
            </div>

          </div>

          {/* Right Column - Examples */}
          <div className="flex flex-col gap-6">
            <ExampleTemplates
              onTemplateClick={handleTemplateClick}
              isExpanded={isExamplesExpanded}
              setIsExpanded={setIsExamplesExpanded}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
