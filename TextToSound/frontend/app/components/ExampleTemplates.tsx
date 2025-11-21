import { EXAMPLE_TEMPLATES } from "../constants/templates";

interface ExampleTemplatesProps {
    onTemplateClick: (template: string) => void;
    isExpanded: boolean;
    setIsExpanded: (expanded: boolean) => void;
}

export function ExampleTemplates({ onTemplateClick, isExpanded, setIsExpanded }: ExampleTemplatesProps) {
    if (!isExpanded) {
        // Collapsed state: Tiny icon button only
        return (
            <button
                onClick={() => setIsExpanded(true)}
                className="w-12 h-12 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-xl shadow-lg transition-all hover:scale-110 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center justify-center"
                title="Quick Examples"
            >
                {/* Lightbulb Icon */}
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
            </button>
        );
    }

    // Expanded state: Full panel
    return (
        <div className="lg:col-span-1 bg-gray-800 rounded-xl shadow-2xl p-6 border border-gray-700 transition-all">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-sm font-semibold text-gray-300">
                    Quick Examples
                </h2>
                <button
                    onClick={() => setIsExpanded(false)}
                    className="text-gray-400 hover:text-gray-200 transition-colors focus:outline-none"
                    title="Collapse"
                >
                    {/* X Icon */}
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
            <div className="flex flex-col gap-2">
                {EXAMPLE_TEMPLATES.map((template) => (
                    <button
                        key={template}
                        type="button"
                        onClick={() => onTemplateClick(template)}
                        className="px-4 py-2.5 bg-gray-700 hover:bg-blue-600 text-gray-200 hover:text-white text-sm rounded-lg border border-gray-600 hover:border-blue-500 transition-all transform hover:scale-105 active:scale-95 focus:outline-none focus:ring-2 focus:ring-blue-500 text-left"
                    >
                        {template}
                    </button>
                ))}
            </div>
        </div>
    );
}
