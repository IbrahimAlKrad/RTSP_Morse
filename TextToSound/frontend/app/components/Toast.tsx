import { useEffect, useState } from "react";

interface ToastProps {
    message: string;
    isVisible: boolean;
    onClose: () => void;
    duration?: number;
}

export function Toast({ message, isVisible, onClose, duration = 4000 }: ToastProps) {
    const [show, setShow] = useState(isVisible);

    useEffect(() => {
        setShow(isVisible);
        if (isVisible) {
            const timer = setTimeout(() => {
                setShow(false);
                onClose();
            }, duration);
            return () => clearTimeout(timer);
        }
    }, [isVisible, duration, onClose]);

    if (!show && !isVisible) return null;

    return (
        <div
            className={`fixed top-4 right-4 z-50 transform transition-all duration-500 ease-out ${show ? "translate-x-0 opacity-100" : "translate-x-full opacity-0"
                }`}
        >
            <div className="bg-gray-800/90 backdrop-blur-md border-l-4 border-blue-500 text-white px-6 py-4 rounded shadow-2xl flex items-center gap-4 min-w-[300px]">
                <div className="bg-blue-500/20 p-2 rounded-full">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-6 w-6 text-blue-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                        />
                    </svg>
                </div>
                <div>
                    <h4 className="font-bold text-sm text-blue-400 uppercase tracking-wider">
                        Speech Detected
                    </h4>
                    <p className="text-gray-200 text-sm mt-1">{message}</p>
                </div>
                <button
                    onClick={() => {
                        setShow(false);
                        onClose();
                    }}
                    className="ml-auto text-gray-400 hover:text-white transition-colors"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-5 w-5"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                    >
                        <path
                            fillRule="evenodd"
                            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                            clipRule="evenodd"
                        />
                    </svg>
                </button>
            </div>
        </div>
    );
}
