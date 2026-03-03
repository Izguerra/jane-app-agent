import Link from 'next/link';

export default function TermsPage() {
    return (
        <div className="bg-[#f8fafc] dark:bg-[#101922] transition-colors duration-300">
            <main className="max-w-4xl mx-auto px-6 py-16 lg:px-10">
                <div className="bg-white dark:bg-[#1a2632] rounded-2xl shadow-lg p-8 lg:p-12">
                    <h1 className="text-4xl lg:text-5xl font-black text-[#111418] dark:text-white mb-4 font-['Space_Grotesk']">
                        Terms and Conditions
                    </h1>
                    <p className="text-[#617589] dark:text-[#9ca3af] mb-12">
                        Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                    </p>

                    <div className="prose prose-lg dark:prose-invert max-w-none">
                        <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                            1. Introduction
                        </h2>
                        <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-6">
                            Welcome to SupaAgent. These Terms and Conditions govern your use of our website and services.
                            SupaAgent is a product of <strong className="text-[#111418] dark:text-white">iCONX Solutions Inc.</strong>, a corporation registered in Ontario, Canada.
                        </p>

                        <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                            2. Acceptance of Terms
                        </h2>
                        <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-6">
                            By accessing or using SupaAgent, you agree to be bound by these Terms. If you disagree with any part of the terms,
                            you may not access the service.
                        </p>

                        <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                            3. Accounts
                        </h2>
                        <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-6">
                            When you create an account with us, you must provide information that is accurate, complete, and current at all times.
                            Failure to do so constitutes a breach of the Terms, which may result in immediate termination of your account on our Service.
                        </p>

                        <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                            4. Intellectual Property
                        </h2>
                        <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-6">
                            The Service and its original content, features, and functionality are and will remain the exclusive property of
                            iCONX Solutions Inc. and its licensors.
                        </p>

                        <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                            5. Governing Law
                        </h2>
                        <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-6">
                            These Terms shall be governed and construed in accordance with the laws of <strong className="text-[#111418] dark:text-white">Ontario, Canada</strong>,
                            without regard to its conflict of law provisions.
                        </p>

                        <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                            6. Changes
                        </h2>
                        <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-6">
                            We reserve the right, at our sole discretion, to modify or replace these Terms at any time.
                            By continuing to access or use our Service after those revisions become effective, you agree to be bound by the revised terms.
                        </p>

                        <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                            7. Contact Us
                        </h2>
                        <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-6">
                            If you have any questions about these Terms, please contact us at{' '}
                            <a href="mailto:info@supaagent.com" className="text-[#137fec] hover:text-[#0b5ed7] font-medium">
                                info@supaagent.com
                            </a>.
                        </p>
                    </div>
                </div>
            </main>
        </div>
    );
}
