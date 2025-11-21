interface MorseDisplayProps {
    lastMessage: string;
    isPlaying: boolean;
}

export function MorseDisplay({ lastMessage, isPlaying }: MorseDisplayProps) {
    return (
        <div className="p-6 bg-gray-900 rounded-lg border border-gray-700 h-full flex flex-col justify-center items-center relative text-center">
            <h2 className="absolute top-6 left-6 text-xs font-semibold text-gray-400 uppercase tracking-widest z-10">
                Last Received Morse
            </h2>
            <div className="text-2xl font-mono text-green-400 break-all tracking-widest leading-relaxed px-4">
                {lastMessage || (
                    <span className="text-gray-500 italic">No message yet...</span>
                )}
            </div>
            {isPlaying && (
                <div className="mt-4 flex items-center justify-center space-x-2 text-blue-400 text-sm animate-pulse">
                    <span>🔊 Playing...</span>
                </div>
            )}
        </div>
    );
}
