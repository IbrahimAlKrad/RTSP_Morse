import { EXAMPLE_TEMPLATES } from "../constants/templates";

interface ExampleTemplatesProps {
    onTemplateClick: (template: string) => void;
}

export function ExampleTemplates({ onTemplateClick }: ExampleTemplatesProps) {
    return (
        <div className="lg:col-span-1 bg-gray-800 rounded-xl shadow-2xl p-6 border border-gray-700">
            <h2 className="text-sm font-semibold text-gray-300 mb-4">
                Quick Examples
            </h2>
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
