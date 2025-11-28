interface ViewSwitcherProps {
    viewMode: 'text' | 'visualizer';
    onViewChange: (mode: 'text' | 'visualizer') => void;
}

export function ViewSwitcher({ viewMode, onViewChange }: ViewSwitcherProps) {
    return (
        <div className="flex flex-col bg-gray-900 rounded-full p-1 border border-gray-700 shadow-inner shrink-0">
            <button
                onClick={() => onViewChange('text')}
                className={`p-3 rounded-full transition-all duration-300 ${viewMode === 'text'
                        ? 'bg-blue-500 text-white shadow-lg scale-110'
                        : 'text-gray-500 hover:text-gray-300'
                    }`}
                title="Text Output"
            >
                {/* Text Icon */}
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
                </svg>
            </button>
            <button
                onClick={() => onViewChange('visualizer')}
                className={`p-3 rounded-full transition-all duration-300 ${viewMode === 'visualizer'
                        ? 'bg-cyan-500 text-white shadow-lg scale-110'
                        : 'text-gray-500 hover:text-gray-300'
                    }`}
                title="Visualizer"
            >
                {/* Wave Icon */}
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                </svg>
            </button>
        </div>
    );
}
