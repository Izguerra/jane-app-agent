import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Footer } from '@/components/footer';
import { Logo } from '@/components/logo';

function Header() {
    return (
        <header className="border-b border-gray-200 bg-white">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                <Link href="/" className="flex items-center">
                    <Logo className="h-14 w-auto" />
                </Link>
                <div className="hidden md:flex items-center space-x-8">
                    <Link href="/pricing" className="text-sm font-medium text-gray-700 hover:text-gray-900">Pricing</Link>
                    <Link href="#features" className="text-sm font-medium text-gray-700 hover:text-gray-900">Features</Link>
                    <Link href="#how-it-works" className="text-sm font-medium text-gray-700 hover:text-gray-900">How It Works</Link>
                    <Link href="#faq" className="text-sm font-medium text-gray-700 hover:text-gray-900">FAQ</Link>

                    <div className="flex items-center gap-4 ml-4">
                        <Link href="/sign-in">
                            <Button variant="ghost" className="text-sm font-medium text-gray-600 hover:text-gray-900">
                                Customer Sign In
                            </Button>
                        </Link>
                        <div className="h-4 w-px bg-gray-300 mx-1"></div>
                        <Link href="/admin/sign-in">
                            <Button variant="ghost" className="text-sm font-medium">Admin Sign In</Button>
                        </Link>
                        <Link href="/sign-up">
                            <Button className="bg-orange-600 hover:bg-orange-700 text-white rounded-lg px-4 py-2 text-sm font-bold shadow-md shadow-orange-600/20">
                                Get Started
                            </Button>
                        </Link>
                    </div>
                </div>
            </div>
        </header>
    );
}

export default function MarketingLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex flex-col min-h-screen bg-gray-50">
            <Header />
            <main className="flex-1">{children}</main>
            <Footer />
        </div>
    );
}
