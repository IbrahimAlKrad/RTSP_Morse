import { useCallback, useEffect, useRef, useState } from "react";
import { playTone, calculateMorseDuration } from "../utils/morsePlayer";

export function useMorseAudio() {
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

    // Initialize AudioContext
    useEffect(() => {
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

        return () => {
            if (audioContextRef.current) {
                console.log("[Audio] Closing AudioContext");
                audioContextRef.current.close();
                audioContextRef.current = null;
                masterGainRef.current = null;
            }
        };
    }, []);

    const playMorse = useCallback((morse: string) => {
        if (!audioContextRef.current || !masterGainRef.current) return;
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

        const currentVol = volumeRef.current;

        // Skip playback if volume is 0
        if (currentVol <= 0) {
            setIsPlaying(false);
            return;
        }

        for (const char of morse) {
            if (char === '.') {
                // Dot: 1 dit on
                playTone(ctx, masterGainRef.current, frequencyRef.current, dit, currentTime);
                // Advance: 1 dit on + 1 dit gap (intra-symbol)
                currentTime += dit * 2;
            } else if (char === '-') {
                // Dash: 3 dits on
                playTone(ctx, masterGainRef.current, frequencyRef.current, dit * 3, currentTime);
                // Advance: 3 dits on + 1 dit gap (intra-symbol)
                currentTime += dit * 4;
            } else if (char === ' ') {
                // Space: additional 2 dits (on top of the 1 dit gap from previous symbol)
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
    }, []); // Empty dependency array since we only use refs

    return {
        isPlaying,
        frequency,
        setFrequency,
        volume,
        setVolume,
        ditDuration,
        setDitDuration,
        playMorse,
    };
}
