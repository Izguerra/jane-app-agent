'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { submitContactForm } from '@/app/(dashboard)/actions';

export function ContactForm() {
    const [status, setStatus] = useState<{ type: 'success' | 'error' | null; message: string }>({
        type: null,
        message: '',
    });
    const [isSubmitting, setIsSubmitting] = useState(false);

    async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setIsSubmitting(true);
        setStatus({ type: null, message: '' });

        const formData = new FormData(e.currentTarget);
        const result = await submitContactForm(formData);

        setStatus({
            type: result.success ? 'success' : 'error',
            message: result.message,
        });
        setIsSubmitting(false);

        if (result.success) {
            (e.target as HTMLFormElement).reset();
        }
    }

    return (
        <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-sm">
            <h3 className="text-gray-900 text-xl font-bold mb-6">Send us a message</h3>

            {status.type && (
                <div
                    className={`mb-6 p-4 rounded-lg ${status.type === 'success'
                        ? 'bg-green-50 text-green-800 border border-green-200'
                        : 'bg-red-50 text-red-800 border border-red-200'
                        }`}
                >
                    {status.message}
                </div>
            )}

            <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
                <div className="flex flex-col md:flex-row gap-5">
                    <label className="flex flex-col flex-1">
                        <p className="text-gray-900 text-sm font-medium leading-normal pb-2">Full Name</p>
                        <input
                            className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-gray-900 border border-gray-300 bg-white focus:border-orange-500 focus:ring-1 focus:ring-orange-500 h-12 placeholder:text-gray-500 p-[15px] text-base font-normal leading-normal transition-all"
                            placeholder="Jane Doe"
                            type="text"
                            name="name"
                            required
                            disabled={isSubmitting}
                        />
                    </label>
                    <label className="flex flex-col flex-1">
                        <p className="text-gray-900 text-sm font-medium leading-normal pb-2">Business Email</p>
                        <input
                            className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-gray-900 border border-gray-300 bg-white focus:border-orange-500 focus:ring-1 focus:ring-orange-500 h-12 placeholder:text-gray-500 p-[15px] text-base font-normal leading-normal transition-all"
                            placeholder="jane@company.com"
                            type="email"
                            name="email"
                            required
                            disabled={isSubmitting}
                        />
                    </label>
                </div>

                <label className="flex flex-col w-full">
                    <p className="text-gray-900 text-sm font-medium leading-normal pb-2">Subject</p>
                    <select
                        className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-gray-900 border border-gray-300 bg-white focus:border-orange-500 focus:ring-1 focus:ring-orange-500 h-12 placeholder:text-gray-500 pl-[15px] pr-10 text-base font-normal leading-normal appearance-none transition-all"
                        name="subject"
                        defaultValue=""
                        required
                        disabled={isSubmitting}
                    >
                        <option value="" disabled>Select a topic</option>
                        <option value="Sales Inquiry">Sales Inquiry</option>
                        <option value="Technical Support">Technical Support</option>
                        <option value="Partnership">Partnership</option>
                        <option value="Other">Other</option>
                    </select>
                </label>

                <label className="flex flex-col w-full">
                    <p className="text-gray-900 text-sm font-medium leading-normal pb-2">Message</p>
                    <textarea
                        className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-gray-900 border border-gray-300 bg-white focus:border-orange-500 focus:ring-1 focus:ring-orange-500 min-h-36 placeholder:text-gray-500 p-[15px] text-base font-normal leading-normal transition-all"
                        placeholder="Tell us how we can help..."
                        name="message"
                        required
                        disabled={isSubmitting}
                    ></textarea>
                </label>

                <div className="pt-2">
                    <Button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full md:w-auto min-w-[140px] h-12 px-6 bg-orange-600 hover:bg-orange-700 text-white text-base font-bold shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isSubmitting ? 'Sending...' : 'Send Message'}
                    </Button>
                </div>
            </form>
        </div>
    );
}
