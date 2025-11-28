
import { useEffect, useRef } from "react";

interface AudioVisualizerProps {
    analyser: AnalyserNode | null;
}

export function AudioVisualizer({ analyser }: AudioVisualizerProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const animationRef = useRef<number | undefined>(undefined);
    const historyRef = useRef<number[]>([]);

    // Removed the useEffect that initialized history based on width,
    // as width is no longer a prop and history length will be dynamic.

    useEffect(() => {
        const canvas = canvasRef.current;
        const container = containerRef.current;
        if (!analyser || !canvas || !container) return;

        const canvasCtx = canvas.getContext("2d");
        if (!canvasCtx) return;

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        // Resize Observer to handle dynamic sizing
        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect;
                canvas.width = width;
                canvas.height = height;
                // Reset history when canvas size changes significantly
                historyRef.current = new Array(Math.floor(width)).fill(0);
            }
        });

        resizeObserver.observe(container);

        const draw = () => {
            animationRef.current = requestAnimationFrame(draw);

            // 1. Get time domain data (waveform)
            analyser.getByteTimeDomainData(dataArray);

            // 2. Calculate RMS (Root Mean Square) amplitude for this frame
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                const amplitude = dataArray[i] - 128; // Center around 0
                sum += amplitude * amplitude;
            }
            const rms = Math.sqrt(sum / bufferLength);

            // 3. Normalize and scale
            // RMS for a full sine wave of amplitude 127 is ~90.
            // 128 / 90 ≈ 1.42. We use this to map max volume to max height.
            const value = Math.min(rms * 1.42, 128);

            // 4. Update history
            const history = historyRef.current;
            history.push(value);
            // Keep history length proportional to width (e.g., 1 pixel per frame)
            // If canvas width changes, history might be too short or too long, but that's okay.
            if (history.length > canvas.width) {
                history.shift();
            }

            // 5. Render Background
            // Clear the canvas to let the parent container's background (bg-gray-900) show through.
            canvasCtx.clearRect(0, 0, canvas.width, canvas.height);

            // 6. Render Waveform
            canvasCtx.lineWidth = 2;
            canvasCtx.strokeStyle = "#00ffff"; // Neon Cyan
            canvasCtx.shadowBlur = 10;
            canvasCtx.shadowColor = "#00ffff"; // Neon Glow

            // Create Gradient Fill
            const gradient = canvasCtx.createLinearGradient(0, 0, 0, canvas.height);
            gradient.addColorStop(0, "rgba(0, 255, 255, 0.5)");
            gradient.addColorStop(1, "rgba(0, 255, 255, 0.0)");
            canvasCtx.fillStyle = gradient;

            canvasCtx.beginPath();
            canvasCtx.moveTo(0, canvas.height);

            for (let i = 0; i < history.length; i++) {
                const v = history[i];
                // Scale to canvas height. Max value is roughly 128.
                const y = canvas.height - (v / 128) * canvas.height;
                canvasCtx.lineTo(i, y);
            }

            canvasCtx.lineTo(history.length - 1, canvas.height);
            canvasCtx.closePath();

            canvasCtx.stroke();
            canvasCtx.fill();

            // Reset shadow for next frame (grid doesn't need glow)
            canvasCtx.shadowBlur = 0;
        };

        draw();

        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
            resizeObserver.disconnect();
        };
    }, [analyser]);

    return (
        <div ref={containerRef} className="w-full h-full rounded-lg overflow-hidden border border-gray-700 shadow-lg bg-gray-900">
            <canvas
                ref={canvasRef}
                className="w-full h-full block"
            />
        </div>
    );
}
