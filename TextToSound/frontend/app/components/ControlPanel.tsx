interface ControlPanelProps {
    frequency: number;
    setFrequency: (value: number) => void;
    volume: number;
    setVolume: (value: number) => void;
    ditDuration: number;
    setDitDuration: (value: number) => void;
}

export function ControlPanel({
    frequency,
    setFrequency,
    volume,
    setVolume,
    ditDuration,
    setDitDuration,
}: ControlPanelProps) {
    return (
        <>
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
        </>
    );
}
