interface VisualSignalProps {
    isLightOn: boolean;
}

export function VisualSignal({ isLightOn }: VisualSignalProps) {
    return (
        <div
            className={`
                w-24 h-24 rounded-full border-4 border-gray-700 transition-all duration-75
                ${isLightOn
                    ? "bg-yellow-400 shadow-[0_0_50px_rgba(250,204,21,0.8)] scale-110 border-yellow-200"
                    : "bg-gray-800 shadow-none scale-100"
                }
            `}
        />
    );
}
