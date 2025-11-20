interface ConnectionStatusProps {
    isConnected: boolean;
}

export function ConnectionStatus({ isConnected }: ConnectionStatusProps) {
    return (
        <div className="absolute right-0">
            {!isConnected ? (
                <div className="flex items-center gap-1.5 px-3 py-1 bg-red-900/50 border border-red-700 rounded-full text-xs">
                    <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                    <span className="text-red-200">Disconnected</span>
                </div>
            ) : (
                <div className="flex items-center gap-1.5 px-3 py-1 bg-green-900/50 border border-green-700 rounded-full text-xs">
                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                    <span className="text-green-200">Connected</span>
                </div>
            )}
        </div>
    );
}
