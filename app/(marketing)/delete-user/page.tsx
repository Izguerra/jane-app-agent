import Link from 'next/link';

export default function DeleteUserPage() {
    return (
        <div className="bg-[#f8fafc] dark:bg-[#101922] transition-colors duration-300 min-h-screen">
            <main className="max-w-4xl mx-auto px-6 py-16 lg:px-10">
                <div className="bg-white dark:bg-[#1a2632] rounded-2xl shadow-lg p-8 lg:p-12">
                    <h1 className="text-4xl lg:text-5xl font-black text-[#111418] dark:text-white mb-4 font-['Space_Grotesk']">
                        Data Deletion Instructions
                    </h1>
                    <p className="text-[#617589] dark:text-[#9ca3af] mb-12">
                        How to request the removal of your SupaAgent account and associated data.
                    </p>

                    <div className="prose prose-lg dark:prose-invert max-w-none">
                        <section className="mb-10">
                            <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                                Requesting Data Deletion
                            </h2>
                            <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-6">
                                According to Meta policy and privacy regulations, you have the right to request the deletion of your personal data collected by SupaAgent.
                            </p>
                            
                            <div className="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 p-6 rounded-r-xl mb-8">
                                <h3 className="text-lg font-bold text-blue-900 dark:text-blue-100 mb-2">How to Submit Your Request:</h3>
                                <ol className="list-decimal pl-6 space-y-3 text-blue-800 dark:text-blue-200">
                                    <li>
                                        Send an email to <a href="mailto:info@supaagent.com" className="font-bold underline">info@supaagent.com</a>.
                                    </li>
                                    <li>
                                        Use the subject line: <code className="bg-white/50 dark:bg-black/50 px-2 py-1 rounded">Data Deletion Request</code>.
                                    </li>
                                    <li>
                                        Include the <strong className="text-blue-900 dark:text-white">email address</strong> associated with your account.
                                    </li>
                                    <li>
                                        Once your request is received, we will process it and permanently delete all your user records within 30 days.
                                    </li>
                                </ol>
                            </div>
                        </section>

                        <section className="mb-10">
                            <h2 className="text-2xl font-bold text-[#111418] dark:text-white mt-8 mb-4 font-['Space_Grotesk']">
                                What Data is Deleted?
                            </h2>
                            <p className="text-[#617589] dark:text-[#9ca3af] leading-relaxed mb-4">
                                When we fulfill a deletion request, we permanently remove:
                            </p>
                            <ul className="list-disc pl-6 mb-6 text-[#617589] dark:text-[#9ca3af] space-y-2">
                                <li>Account Profile (Name, Email, Social ID)</li>
                                <li>Workspace configuration and uploaded documents</li>
                                <li>Connected integrations (Meta, WhatsApp, Calendar)</li>
                                <li>Conversation logs and analytics history</li>
                            </ul>
                        </section>

                        <div className="pt-8 border-t border-slate-100 dark:border-slate-800">
                            <Link href="/" className="text-[#137fec] hover:text-[#0b5ed7] font-bold flex items-center gap-2">
                                <span>← Return to Home</span>
                            </Link>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
