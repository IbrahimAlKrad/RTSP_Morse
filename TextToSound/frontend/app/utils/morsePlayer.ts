/**
 * Creates and schedules a tone to be played at a specific time
 * @param ctx - AudioContext instance
 * @param masterGain - Master gain node to connect to
 * @param frequency - Frequency of the tone in Hz
 * @param duration - Duration of the tone in seconds
 * @param startTime - When to start the tone (in AudioContext time)
 */
export function playTone(
    ctx: AudioContext,
    masterGain: GainNode,
    frequency: number,
    duration: number,
    startTime: number
): void {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = "sine";
    osc.frequency.value = frequency;

    osc.connect(gain);
    gain.connect(masterGain);

    osc.start(startTime);

    // Smooth envelope to avoid clicking (Gain is 1.0 relative to Master Gain)
    gain.gain.setValueAtTime(0, startTime);
    gain.gain.linearRampToValueAtTime(1, startTime + 0.01);
    gain.gain.setValueAtTime(1, startTime + duration - 0.01);
    gain.gain.linearRampToValueAtTime(0, startTime + duration);

    osc.stop(startTime + duration);
}

/**
 * Calculates the total duration of a Morse code sequence
 * @param morse - Morse code string (dots, dashes, and spaces)
 * @param ditDuration - Duration of a single dit in milliseconds
 * @returns Total duration in seconds
 */
export function calculateMorseDuration(morse: string, ditDuration: number): number {
    const dit = ditDuration / 1000; // Convert ms to seconds
    let totalTime = 0;

    for (const char of morse) {
        if (char === '.') {
            // Dot: 1 dit on + 1 dit gap
            totalTime += dit * 2;
        } else if (char === '-') {
            // Dash: 3 dits on + 1 dit gap
            totalTime += dit * 4;
        } else if (char === ' ') {
            // Space: additional 2 dits (on top of the 1 dit gap from previous symbol)
            totalTime += dit * 2;
        }
    }

    return totalTime;
}
