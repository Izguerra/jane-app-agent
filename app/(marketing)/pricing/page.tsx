import { PricingTable } from '@/components/pricing-table';

export default function PricingPage() {
    return (
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="text-center mb-12">
                <h1 className="text-4xl font-bold text-gray-900 mb-4">
                    Simple, Transparent Pricing
                </h1>
                <p className="text-xl text-gray-600">
                    Choose the plan that fits your business needs
                </p>
            </div>

            <PricingTable mode="public" />

            <div className="mt-16 text-center">
                <p className="text-gray-600 mb-4">
                    All plans include 14-day free trial • No credit card required
                </p>
                <p className="text-sm text-gray-500">
                    Need help choosing?{' '}
                    <a
                        href="mailto:support@supaagent.com"
                        className="text-blue-600 hover:text-blue-700"
                    >
                        Contact our team
                    </a>
                </p>
            </div>
        </div>
    );
}
