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
                    <Link href="#features" className="text-sm font-medium text-gray-700 hover:text-gray-900">Features</Link>
                    <Link href="#how-it-works" className="text-sm font-medium text-gray-700 hover:text-gray-900">How It Works</Link>
                    <Link href="#faq" className="text-sm font-medium text-gray-700 hover:text-gray-900">FAQ</Link>
                    <Link href="#contact" className="text-sm font-medium text-gray-700 hover:text-gray-900">Contact</Link>
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
