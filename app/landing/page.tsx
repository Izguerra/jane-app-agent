import Link from 'next/link';

export default function LandingPage() {
    return (
        <div className="min-h-screen bg-[#f8fafc] dark:bg-[#101922]">
            {/* Navigation */}
            <nav className="sticky top-0 z-50 backdrop-blur-md bg-white/80 dark:bg-[#101922]/80 border-b border-gray-100 dark:border-gray-800">
                <div className="max-w-7xl mx-auto flex items-center justify-between px-6 py-4 lg:px-10">
                    <Link href="/" className="flex items-center gap-3">
                        <div className="size-10 flex items-center justify-center rounded-xl bg-[#137fec]/10">
                            <span className="text-2xl">🤖</span>
                        </div>
                        <h2 className="text-[#111418] dark:text-white text-xl font-bold">SupaAgent</h2>
                    </Link>
                    <div className="flex items-center gap-6">
                        <Link href="#features" className="text-[#111418] dark:text-white hover:text-[#137fec] transition-colors">Features</Link>
                        <Link href="#pricing" className="text-[#111418] dark:text-white hover:text-[#137fec] transition-colors">Pricing</Link>
                        <Link href="#faq" className="text-[#111418] dark:text-white hover:text-[#137fec] transition-colors">FAQ</Link>
                        <Link href="/sign-in" className="text-[#111418] dark:text-white hover:text-[#137fec] transition-colors font-medium">Log in</Link>
                        <Link href="/sign-up" className="bg-[#137fec] hover:bg-[#0b5ed7] text-white px-5 py-2 rounded-lg font-bold transition-colors">
                            Start Free Trial
                        </Link>
                    </div>
                </div>
            </nav>

            {/* FAQ Section */}
            <section id="faq" className="bg-[#f8fafc] dark:bg-[#101922] py-20">
                <div className="max-w-[960px] mx-auto px-6 lg:px-10">
                    <div className="text-center mb-12">
                        <h2 className="text-[#111418] dark:text-white text-3xl font-bold mb-2">Frequently Asked Questions</h2>
                        <p className="text-[#617589] dark:text-[#9ca3af]">Have a question that's not answered here? Reach out to our team.</p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                        {[
                            { icon: 'help', title: 'Can I change plans later?', text: 'Yes, you can upgrade or downgrade your plan at any time from your account settings. Changes take effect immediately.' },
                            { icon: 'credit_card', title: 'What happens if I hit my limit?', text: 'Your agents will pause until the next billing cycle. You can always purchase a booster pack or upgrade to keep running.' },
                            { icon: 'record_voice_over', title: 'Is voice synthesis included?', text: 'Voice capabilities are available starting on the Professional plan. The Starter plan includes text-based chat only.' },
                            { icon: 'security', title: 'Is my data secure?', text: 'Absolutely. We use enterprise-grade encryption for all data and never use your private data to train our public models.' },
                            { icon: 'schedule', title: 'How long does setup take?', text: 'Most users are up and running in under 15 minutes. Upload your knowledge base, configure your agent settings, and you\'re ready to go live.' },
                            { icon: 'integration_instructions', title: 'What integrations are supported?', text: 'We integrate with Google Calendar, Twilio, Instagram DM, SMS, and web chat. API access is available for custom integrations on Professional and Enterprise plans.' },
                            { icon: 'phone', title: 'Can I use my own phone number?', text: 'Yes! You can port your existing number or use one of ours. Each plan includes phone numbers, and you can add more as needed.' },
                            { icon: 'language', title: 'What languages are supported?', text: 'Our AI agents support 50+ languages for text chat. Voice capabilities are available in English, Spanish, French, German, and more.' },
                            { icon: 'calendar_month', title: 'Does it handle appointment booking?', text: 'Yes! Our agents can book, reschedule, and cancel appointments automatically using your Google Calendar integration with real-time availability.' },
                            { icon: 'support_agent', title: 'What kind of support do you offer?', text: 'Starter plans include email support. Professional plans get priority support with faster response times. Enterprise customers have dedicated success managers.' },
                            { icon: 'folder_open', title: 'How does the knowledge base work?', text: 'Upload documents, FAQs, or service information. Our AI learns from your content to provide accurate, context-aware responses to customer questions.' },
                            { icon: 'cancel', title: 'Can I cancel anytime?', text: 'Yes, you can cancel your subscription at any time. Your service will continue until the end of your current billing period with no penalties or fees.' }
                        ].map((faq, idx) => (
                            <div key={idx} className="flex gap-4 p-4 rounded-lg bg-white dark:bg-[#1a2632] border border-[#f0f2f4] dark:border-[#2a3441]">
                                <div className="shrink-0 pt-1">
                                    <span className="material-symbols-outlined text-[#137fec]" style={{ fontSize: '24px' }}>{faq.icon}</span>
                                </div>
                                <div>
                                    <h3 className="font-bold text-[#111418] dark:text-white mb-2">{faq.title}</h3>
                                    <p className="text-sm text-[#617589] dark:text-[#9ca3af] leading-relaxed">{faq.text}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="bg-[#f8fafc] dark:bg-[#101922] border-t border-[#e5e7eb] dark:border-[#2a3441] py-12">
                <div className="max-w-[1280px] mx-auto px-6 lg:px-10">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <div className="size-8 flex items-center justify-center rounded-lg bg-[#137fec]/10">
                                    <span className="text-2xl">🤖</span>
                                </div>
                                <span className="font-bold text-[#111418] dark:text-white">SupaAgent</span>
                            </div>
                            <p className="text-sm text-[#617589] dark:text-[#9ca3af]">Intelligent AI support for modern businesses.</p>
                        </div>

                        <div>
                            <h3 className="font-bold text-[#111418] dark:text-white mb-3">Product</h3>
                            <ul className="space-y-2 text-sm text-[#617589] dark:text-[#9ca3af]">
                                <li><Link href="#features" className="hover:text-[#137fec] transition-colors">Features</Link></li>
                                <li><Link href="#pricing" className="hover:text-[#137fec] transition-colors">Pricing</Link></li>
                            </ul>
                        </div>

                        <div>
                            <h3 className="font-bold text-[#111418] dark:text-white mb-3">Company</h3>
                            <ul className="space-y-2 text-sm text-[#617589] dark:text-[#9ca3af]">
                                <li><Link href="#" className="hover:text-[#137fec] transition-colors">About</Link></li>
                                <li><Link href="#contact" className="hover:text-[#137fec] transition-colors">Contact</Link></li>
                            </ul>
                        </div>

                        <div>
                            <h3 className="font-bold text-[#111418] dark:text-white mb-3">Legal</h3>
                            <ul className="space-y-2 text-sm text-[#617589] dark:text-[#9ca3af]">
                                <li><Link href="/privacy" className="hover:text-[#137fec] transition-colors">Privacy</Link></li>
                                <li><Link href="/terms" className="hover:text-[#137fec] transition-colors">Terms</Link></li>
                                <li><Link href="#" className="hover:text-[#137fec] transition-colors">Security</Link></li>
                            </ul>
                        </div>
                    </div>

                    <div className="pt-8 border-t border-[#e5e7eb] dark:border-[#2a3441] text-center">
                        <p className="text-sm text-[#617589] dark:text-[#9ca3af]">© 2024 SupaAgent. All rights reserved.</p>
                    </div>
                </div>
            </footer>
        </div>
    );
}
