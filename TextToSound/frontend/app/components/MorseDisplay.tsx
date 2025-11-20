interface MorseDisplayProps {
    lastMessage: string;
    isPlaying: boolean;
}

export function MorseDisplay({ lastMessage, isPlaying }: MorseDisplayProps) {
    if (!lastMessage) return null;

    return (
        <div className="p-6 bg-gray-900 rounded-lg border border-gray-700 h-full flex flex-col justify-center">
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
    );
}
