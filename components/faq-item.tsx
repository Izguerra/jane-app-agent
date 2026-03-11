'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

interface FAQItemProps {
    question: string;
    answer: string;
    defaultOpen?: boolean;
}

export function FAQItem({ question, answer, defaultOpen = false }: FAQItemProps) {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <div
            className={`group flex flex-col rounded-xl border border-gray-200 bg-white transition-all duration-200 ${isOpen ? 'bg-blue-50/50 border-blue-200' : ''
                }`}
        >
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex cursor-pointer items-center justify-between gap-6 p-5 select-none text-left w-full"
            >
                <p className="text-gray-900 text-base font-bold leading-normal">{question}</p>
                <ChevronDown
                    className={`text-gray-900 transition-transform duration-300 flex-shrink-0 ${isOpen ? 'rotate-180' : ''
                        }`}
                    size={20}
                />
            </button>
            {isOpen && (
                <div className="px-5 pb-5 pt-0">
                    <p className="text-gray-600 text-base font-normal leading-relaxed">{answer}</p>
                </div>
            )}
        </div>
    );
}
