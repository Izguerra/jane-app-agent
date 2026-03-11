import Link from 'next/link';

export function Footer() {
    return (
        <footer className="py-6 w-full text-center text-sm text-gray-500">
            <div className="flex flex-col sm:flex-row justify-center items-center space-y-2 sm:space-y-0 sm:space-x-4">
                <span>Copyright &copy; {new Date().getFullYear()} iCONX Solutions Inc. All rights reserved.</span>
                <span className="hidden sm:inline">|</span>
                <div className="space-x-4">
                    <Link href="/pricing" className="hover:text-gray-900 transition-colors">
                        Pricing
                    </Link>
                    <Link href="/terms" className="hover:text-gray-900 transition-colors">
                        Terms & Conditions
                    </Link>
                    <Link href="/privacy" className="hover:text-gray-900 transition-colors">
                        Privacy Policy
                    </Link>
                    <Link href="/delete-user" className="hover:text-gray-900 transition-colors">
                        Data Deletion
                    </Link>
                </div>
            </div>
        </footer>
    );
}
