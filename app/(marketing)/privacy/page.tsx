import Link from 'next/link';

export default function PrivacyPage() {
    return (
        <div className="bg-[#f8fafc] dark:bg-[#101922] transition-colors duration-300">
            <main className="max-w-4xl mx-auto px-6 py-16 lg:px-10">
                <div className="bg-white dark:bg-[#1a2632] rounded-2xl shadow-lg p-8 lg:p-12">
                    <h1 className="text-4xl lg:text-5xl font-black text-[#111418] dark:text-white mb-4 font-['Space_Grotesk']">
                        Privacy Policy
                    </h1>
                    <p className="text-[#617589] dark:text-[#9ca3af] mb-12">
                        Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                    </p>

                    <div className="prose prose-lg dark:prose-invert max-w-none">
                        <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                            1. Introduction
                        </h2>
                        <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-6">
                            SupaAgent ("us", "we", or "our") operates the SupaAgent website and application (the "Service").
                            SupaAgent is a product of <strong className="text-[#111418] dark:text-white">iCONX Solutions Inc.</strong>, based in Ontario, Canada.
                            This page informs you of our policies regarding the collection, use, and disclosure of personal data when you use our Service.
                        </p>

                        <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                            2. Information Collection and Use
                        </h2>
                        <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-4">
                            We collect several different types of information for various purposes to provide and improve our Service to you, including:
                        </p>
                        <ul className="list-disc pl-6 mb-6 text-[#617589] dark:text-[#9ca3af] space-y-2">
                            <li>Personal Data (Email address, First name and last name, Phone number)</li>
                            <li>Usage Data (Cookies, Analytics)</li>
                        </ul>

                        <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                            3. Use of Data
                        </h2>
                        <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-4">
                            iCONX Solutions Inc. uses the collected data for various purposes:
                        </p>
                        <ul className="list-disc pl-6 mb-6 text-[#617589] dark:text-[#9ca3af] space-y-2">
                            <li>To provide and maintain the Service</li>
                            <li>To notify you about changes to our Service</li>
                            <li>To provide customer care and support</li>
                            <li>To monitor the usage of the Service</li>
                        </ul>

                        <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                            4. Transfer of Data
                        </h2>
                        <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-6">
                            Your information, including Personal Data, may be transferred to — and maintained on — computers located outside of your
                            state, province, country, or other governmental jurisdiction where the data protection laws may differ than those from your jurisdiction.
                            If you are located outside Canada and choose to provide information to us, please note that we transfer the data, including Personal Data, to Canada and process it there.
                        </p>

                        <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                            5. Security of Data
                        </h2>
                        <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-6">
                            The security of your data is important to us, but remember that no method of transmission over the Internet, or method of electronic storage is 100% secure.
                        </p>

                        <h2 id="data-deletion" className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                            6. Data Deletion
                        </h2>
                        <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-4">
                            You have the right to request the deletion of your personal data held by SupaAgent. To request data deletion, please follow these steps:
                        </p>
                        <ul className="list-disc pl-6 mb-6 text-[#617589] dark:text-[#9ca3af] space-y-2">
                            <li>Send an email to <a href="mailto:info@supaagent.com" className="text-[#137fec]">info@supaagent.com</a> with the subject line "Data Deletion Request".</li>
                            <li>Include your registered email address and, if applicable, the specific account details you wish to be removed.</li>
                            <li>We will process your request and confirm deletion within 30 days.</li>
                        </ul>

                        <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                            7. Contact Us
                        </h2>
                        <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-6">
                            If you have any questions about this Privacy Policy, please contact us at{' '}
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
